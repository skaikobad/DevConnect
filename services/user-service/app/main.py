from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from .common import add_cors, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics
app = FastAPI(title="CloudConnect User Service", version="1.0.0")
add_cors(app)
add_prometheus_metrics(app, "user-service")
class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    bio: str = Field(default="", max_length=500)
@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"service": "user-service", "status": "ok"}
@app.get("/profile")
def profile(user=Depends(get_current_user)): return user
@app.put("/profile")
def update_profile(payload: ProfileUpdate, user=Depends(get_current_user)):
    with engine.begin() as conn:
        row = conn.execute(text("UPDATE users SET name=:name, bio=:bio WHERE id=:id RETURNING id, name, email, bio, role, created_at"), {"id": user["id"], "name": payload.name, "bio": payload.bio}).mappings().first()
    return dict(row)
@app.get("/users/{user_id}")
def get_user(user_id: int):
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id, name, email, bio, role, created_at FROM users WHERE id=:id"), {"id": user_id}).mappings().first()
    if not row: raise HTTPException(status_code=404, detail="User not found")
    return dict(row)
