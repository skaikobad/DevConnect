from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from .common import add_cors, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics
app = FastAPI(title="CloudConnect Like Service", version="1.0.0")
add_cors(app)
add_prometheus_metrics(app, "like-service")
@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"service": "like-service", "status": "ok"}
@app.post("/posts/{post_id}/toggle")
def toggle_post_like(post_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        if not conn.execute(text("SELECT id FROM posts WHERE id=:id"), {"id": post_id}).first(): raise HTTPException(status_code=404, detail="Post not found")
        existing = conn.execute(text("SELECT id FROM post_likes WHERE post_id=:post_id AND user_id=:user_id"), {"post_id": post_id, "user_id": user["id"]}).mappings().first()
        if existing:
            conn.execute(text("DELETE FROM post_likes WHERE id=:id"), {"id": existing["id"]}); liked = False
        else:
            conn.execute(text("INSERT INTO post_likes (post_id, user_id) VALUES (:post_id, :user_id)"), {"post_id": post_id, "user_id": user["id"]}); liked = True
        count = conn.execute(text("SELECT COUNT(*) FROM post_likes WHERE post_id=:post_id"), {"post_id": post_id}).scalar_one()
    return {"post_id": post_id, "liked": liked, "like_count": count}
@app.get("/posts/{post_id}")
def post_like_summary(post_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM post_likes WHERE post_id=:post_id"), {"post_id": post_id}).scalar_one()
        liked = conn.execute(text("SELECT 1 FROM post_likes WHERE post_id=:post_id AND user_id=:user_id"), {"post_id": post_id, "user_id": user["id"]}).first() is not None
    return {"post_id": post_id, "liked": liked, "like_count": count}
