import os
from typing import Optional

import redis
from prometheus_client import Counter
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from .common import add_cors, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics

app = FastAPI(title="CloudConnect Analytics Service", version="1.1.0")
add_cors(app)
add_prometheus_metrics(app, "analytics-service")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POST_CREATE_QUEUE = os.getenv("POST_CREATE_QUEUE", "cloudconnect:queue:post-create")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
IMPRESSIONS_TRACKED_TOTAL = Counter("devconnect_impressions_tracked_total", "Post impressions tracked by the Analytics Service.", ["service"])

class ImpressionRequest(BaseModel):
    post_ids: list[int] = []
    post_id: Optional[int] = None
    source: str = "feed"

@app.on_event("startup")
def startup():
    # init_db() creates/updates all shared tables under a PostgreSQL advisory lock.
    # This avoids CREATE TABLE race conditions when many services start together.
    init_db()

@app.get("/health")
def health():
    redis_status = "unavailable"
    try:
        redis_status = "ok" if r.ping() else "unavailable"
    except Exception:
        redis_status = "unavailable"
    return {"service": "analytics-service", "status": "ok", "redis": redis_status, "post_create_queue": POST_CREATE_QUEUE}

@app.post("/impressions")
def track_impressions(payload: ImpressionRequest, user=Depends(get_current_user)):
    all_ids = list(payload.post_ids or [])
    if payload.post_id is not None:
        all_ids.append(payload.post_id)
    clean_ids = sorted(set([int(x) for x in all_ids if int(x) > 0]))[:50]
    inserted = 0
    with engine.begin() as conn:
        for post_id in clean_ids:
            exists = conn.execute(text("SELECT id FROM posts WHERE id=:id"), {"id": post_id}).first()
            if exists:
                conn.execute(
                    text("INSERT INTO post_impressions (post_id, user_id, source) VALUES (:post_id, :user_id, :source)"),
                    {"post_id": post_id, "user_id": user["id"], "source": payload.source[:80]},
                )
                inserted += 1
    try:
        if inserted:
            r.incrby("cloudconnect:analytics:impressions_tracked", inserted)
            IMPRESSIONS_TRACKED_TOTAL.labels("analytics-service").inc(inserted)
    except Exception:
        pass
    return {"tracked": inserted, "source": payload.source}

@app.get("/metrics")
def metrics(user=Depends(get_current_user)):
    with engine.begin() as conn:
        totals = conn.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM users) AS users,
            (SELECT COUNT(*) FROM posts) AS posts,
            (SELECT COUNT(*) FROM comments) AS comments,
            (SELECT COUNT(*) FROM post_likes) AS post_likes,
            (SELECT COUNT(*) FROM comment_likes) AS comment_likes,
            (SELECT COUNT(*) FROM post_impressions) AS impressions,
            (SELECT COUNT(*) FROM post_jobs WHERE status='queued') AS queued_post_jobs,
            (SELECT COUNT(*) FROM post_jobs WHERE status='processing') AS processing_post_jobs,
            (SELECT COUNT(*) FROM post_jobs WHERE status='completed') AS completed_post_jobs,
            (SELECT COUNT(*) FROM post_jobs WHERE status='failed') AS failed_post_jobs
        """)).mappings().first()
        daily_rows = conn.execute(text("""
        WITH days AS (
          SELECT generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, INTERVAL '1 day')::date AS day
        )
        SELECT d.day::text AS day,
          COALESCE(p.posts, 0) AS posts,
          COALESCE(c.comments, 0) AS comments,
          COALESCE(i.impressions, 0) AS impressions
        FROM days d
        LEFT JOIN (SELECT created_at::date AS day, COUNT(*) AS posts FROM posts GROUP BY 1) p ON p.day = d.day
        LEFT JOIN (SELECT created_at::date AS day, COUNT(*) AS comments FROM comments GROUP BY 1) c ON c.day = d.day
        LEFT JOIN (SELECT created_at::date AS day, COUNT(*) AS impressions FROM post_impressions GROUP BY 1) i ON i.day = d.day
        ORDER BY d.day ASC
        """)).mappings().all()
        top_posts = conn.execute(text("""
        SELECT p.id, p.content, u.name AS author_name,
          COALESCE(i.impressions, 0) AS impressions,
          COALESCE(l.likes, 0) AS likes,
          COALESCE(c.comments, 0) AS comments
        FROM posts p
        JOIN users u ON u.id = p.user_id
        LEFT JOIN (SELECT post_id, COUNT(*) AS impressions FROM post_impressions GROUP BY post_id) i ON i.post_id = p.id
        LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM post_likes GROUP BY post_id) l ON l.post_id = p.id
        LEFT JOIN (SELECT post_id, COUNT(*) AS comments FROM comments GROUP BY post_id) c ON c.post_id = p.id
        ORDER BY impressions DESC, likes DESC, comments DESC, p.created_at DESC
        LIMIT 5
        """)).mappings().all()
    engagement = int(totals["post_likes"] or 0) + int(totals["comment_likes"] or 0) + int(totals["comments"] or 0)
    queue_depth = None
    redis_status = "unavailable"
    processed_by_worker = 0
    try:
        queue_depth = r.llen(POST_CREATE_QUEUE)
        processed_by_worker = int(r.get("cloudconnect:analytics:queued_posts_processed") or 0)
        redis_status = "ok"
    except Exception:
        pass
    return {
        "totals": {**dict(totals), "engagements": engagement},
        "daily": [dict(row) for row in daily_rows],
        "top_posts": [dict(row) for row in top_posts],
        "queue": {
            "redis_status": redis_status,
            "queue_name": POST_CREATE_QUEUE,
            "queue_depth": queue_depth,
            "processed_by_worker": processed_by_worker,
            "description": "Post creation requests are accepted by Post Service, pushed to Redis Queue, and inserted into PostgreSQL by Worker Service."
        },
        "notes": "Impressions are stored in PostgreSQL. Post creation is processed asynchronously through Redis Queue + Worker Service."
    }
