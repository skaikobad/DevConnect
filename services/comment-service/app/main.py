from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from .common import add_cors, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics

app = FastAPI(title="CloudConnect Comment Service", version="1.1.0")
add_cors(app)
add_prometheus_metrics(app, "comment-service")

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
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

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"service": "comment-service", "status": "ok", "supports_public_images": True}

@app.get("/posts/{post_id}/comments")
def list_comments(post_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        if not conn.execute(text("SELECT id FROM posts WHERE id=:id"), {"id": post_id}).first():
            raise HTTPException(status_code=404, detail="Post not found")
        q = """
        SELECT c.id, c.post_id, c.content, c.image_url, c.created_at, u.id AS user_id, u.name AS author_name,
        COALESCE(cl.like_count, 0) AS like_count,
        EXISTS(SELECT 1 FROM comment_likes x WHERE x.comment_id = c.id AND x.user_id = :current_user_id) AS liked_by_me
        FROM comments c JOIN users u ON u.id = c.user_id
        LEFT JOIN (SELECT comment_id, COUNT(*) AS like_count FROM comment_likes GROUP BY comment_id) cl ON cl.comment_id = c.id
        WHERE c.post_id = :post_id ORDER BY c.created_at ASC
        """
        rows = conn.execute(text(q), {"post_id": post_id, "current_user_id": user["id"]}).mappings().all()
    return [dict(r) for r in rows]

@app.post("/posts/{post_id}/comments")
def create_comment(post_id: int, payload: CommentCreate, user=Depends(get_current_user)):
    image_url = normalize_public_image_url(payload.image_url)
    with engine.begin() as conn:
        if not conn.execute(text("SELECT id FROM posts WHERE id=:id"), {"id": post_id}).first():
            raise HTTPException(status_code=404, detail="Post not found")
        row = conn.execute(
            text("""
            INSERT INTO comments (post_id, user_id, content, image_url)
            VALUES (:post_id, :user_id, :content, :image_url)
            RETURNING id, post_id, user_id, content, image_url, created_at
            """),
            {"post_id": post_id, "user_id": user["id"], "content": payload.content, "image_url": image_url}
        ).mappings().first()
    return dict(row)

@app.post("/comments/{comment_id}/like/toggle")
def toggle_comment_like(comment_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        if not conn.execute(text("SELECT id FROM comments WHERE id=:id"), {"id": comment_id}).first():
            raise HTTPException(status_code=404, detail="Comment not found")
        existing = conn.execute(text("SELECT id FROM comment_likes WHERE comment_id=:comment_id AND user_id=:user_id"), {"comment_id": comment_id, "user_id": user["id"]}).mappings().first()
        if existing:
            conn.execute(text("DELETE FROM comment_likes WHERE id=:id"), {"id": existing["id"]})
            liked = False
        else:
            conn.execute(text("INSERT INTO comment_likes (comment_id, user_id) VALUES (:comment_id, :user_id)"), {"comment_id": comment_id, "user_id": user["id"]})
            liked = True
        count = conn.execute(text("SELECT COUNT(*) FROM comment_likes WHERE comment_id=:comment_id"), {"comment_id": comment_id}).scalar_one()
    return {"comment_id": comment_id, "liked": liked, "like_count": count}
