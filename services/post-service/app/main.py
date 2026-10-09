import json
import os
import uuid
from typing import Optional

import redis
from prometheus_client import Counter
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from .common import add_cors, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics

app = FastAPI(title="CloudConnect Post Service", version="1.2.0")
add_cors(app)
add_prometheus_metrics(app, "post-service")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POST_CREATE_QUEUE = os.getenv("POST_CREATE_QUEUE", "cloudconnect:queue:post-create")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
POST_CREATE_REQUESTS_TOTAL = Counter("devconnect_post_create_requests_total", "Post creation requests accepted and queued.", ["service"])

class PostCreate(BaseModel):
    content: str = Field(min_length=2, max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=2048)

def normalize_public_image_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not (value.startswith("https://") or value.startswith("http://")):
        raise HTTPException(status_code=400, detail="Image URL must be a public http:// or https:// URL")
    return value

def ensure_queue_tables():
    # Shared tables are initialized by init_db() under a PostgreSQL advisory lock.
    # This function is kept for readability and future queue-specific migrations.
    return

@app.on_event("startup")
def startup():
    init_db()
    ensure_queue_tables()

@app.get("/health")
def health():
    redis_status = "unavailable"
    try:
        redis_status = "ok" if redis_client.ping() else "unavailable"
    except Exception:
        redis_status = "unavailable"
    return {
        "service": "post-service",
        "status": "ok",
        "supports_public_images": True,
        "redis_queue": redis_status,
        "queue_name": POST_CREATE_QUEUE,
    }

@app.get("/posts")
def list_posts(user=Depends(get_current_user)):
    q = """
    SELECT p.id, p.content, p.image_url, p.created_at, u.id AS user_id, u.name AS author_name, u.email AS author_email,
    COALESCE(pl.like_count, 0) AS like_count, COALESCE(c.comment_count, 0) AS comment_count,
    EXISTS(SELECT 1 FROM post_likes l WHERE l.post_id = p.id AND l.user_id = :current_user_id) AS liked_by_me
    FROM posts p JOIN users u ON u.id = p.user_id
    LEFT JOIN (SELECT post_id, COUNT(*) AS like_count FROM post_likes GROUP BY post_id) pl ON pl.post_id = p.id
    LEFT JOIN (SELECT post_id, COUNT(*) AS comment_count FROM comments GROUP BY post_id) c ON c.post_id = p.id
    ORDER BY p.created_at DESC
    """
    with engine.begin() as conn:
        rows = conn.execute(text(q), {"current_user_id": user["id"]}).mappings().all()
    return [dict(r) for r in rows]

@app.post("/posts", status_code=202)
def create_post(payload: PostCreate, user=Depends(get_current_user)):
    """Accept a post creation request and place it on Redis Queue.

    The Worker Service consumes this queue and inserts the post into PostgreSQL.
    This demonstrates async post creation and handling many post requests without
    blocking the main API request.
    """
    image_url = normalize_public_image_url(payload.image_url)
    job_id = str(uuid.uuid4())
    event = {
        "event_type": "post.create.requested",
        "job_id": job_id,
        "user_id": user["id"],
        "content": payload.content,
        "image_url": image_url,
    }
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO post_jobs (id, user_id, content, image_url, status)
            VALUES (:id, :user_id, :content, :image_url, 'queued')
            """),
            {"id": job_id, "user_id": user["id"], "content": payload.content, "image_url": image_url},
        )
    try:
        redis_client.rpush(POST_CREATE_QUEUE, json.dumps(event))
    except Exception as exc:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE post_jobs SET status='failed', error=:error, updated_at=NOW() WHERE id=:id"),
                {"id": job_id, "error": f"Redis queue unavailable: {exc}"[:500]},
            )
        raise HTTPException(status_code=503, detail="Post queue is unavailable. Please check Redis and worker-service.")

    return {
        "queued": True,
        "job_id": job_id,
        "status": "queued",
        "message": "Post request accepted. Worker Service will create the post from Redis Queue.",
    }

@app.get("/posts/jobs/{job_id}")
def get_post_job(job_id: str, user=Depends(get_current_user)):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
            SELECT id, user_id, status, post_id, error, created_at, updated_at
            FROM post_jobs
            WHERE id=:id AND user_id=:user_id
            """),
            {"id": job_id, "user_id": user["id"]},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Post job not found")
    return dict(row)

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        row = conn.execute(text("SELECT user_id FROM posts WHERE id=:id"), {"id": post_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="You can delete only your own posts")
        conn.execute(text("DELETE FROM posts WHERE id=:id"), {"id": post_id})
    return {"deleted": True, "post_id": post_id}
