from fastapi import Depends, FastAPI, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from .common import add_cors, create_token, engine, get_current_user, init_db
from .metrics import add_prometheus_metrics

app = FastAPI(title="CloudConnect Auth Service", version="1.0.0")
add_cors(app)
add_prometheus_metrics(app, "auth-service")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"service": "auth-service", "status": "ok"}
@app.post("/register")
def register(payload: RegisterRequest):
    password_hash = pwd_context.hash(payload.password)
    try:
        with engine.begin() as conn:
            row = conn.execute(text("INSERT INTO users (name, email, password_hash) VALUES (:name, :email, :password_hash) RETURNING id, name, email, bio, role, created_at"), {"name": payload.name, "email": payload.email.lower(), "password_hash": password_hash}).mappings().first()
    except Exception:
        raise HTTPException(status_code=409, detail="Email already exists")
    return {"token": create_token(row["id"], row["email"]), "user": dict(row)}
@app.post("/login")
def login(payload: LoginRequest):
    with engine.begin() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": payload.email.lower()}).mappings().first()
    if not row or not pwd_context.verify(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = {k: row[k] for k in ["id", "name", "email", "bio", "role", "created_at"]}
    return {"token": create_token(row["id"], row["email"]), "user": user}
@app.get("/me")
def me(user=Depends(get_current_user)): return user
