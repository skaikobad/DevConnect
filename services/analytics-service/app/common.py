import os, time
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cloudconnect:cloudconnect123@postgres:5432/cloudconnect")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-local-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "10080"))
DB_INIT_LOCK_ID = int(os.getenv("DB_INIT_LOCK_ID", "987654321"))
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def add_cors(app):
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def wait_for_db():
    for _ in range(30):
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            time.sleep(2)
    raise RuntimeError("Database is not available")

def init_db():
    """Initialize shared local training schema safely.

    Multiple containers start at the same time in Docker Compose. PostgreSQL can
    still hit a CREATE TABLE race even with IF NOT EXISTS, so we use a PostgreSQL
    advisory lock to ensure only one service initializes or upgrades the shared
    schema at a time.
    """
    wait_for_db()
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": DB_INIT_LOCK_ID})
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                bio TEXT DEFAULT '',
                role VARCHAR(40) DEFAULT 'student',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                image_url TEXT DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """))
            conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT NULL;"))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS post_likes (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(post_id, user_id)
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                image_url TEXT DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """))
            conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT NULL;"))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comment_likes (
                id SERIAL PRIMARY KEY,
                comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(comment_id, user_id)
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS post_jobs (
                id UUID PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                image_url TEXT DEFAULT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'queued',
                post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
                error TEXT DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS post_impressions (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                source VARCHAR(80) DEFAULT 'feed',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """))
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": DB_INIT_LOCK_ID})

def create_token(user_id: int, email: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    return jwt.encode({"sub": str(user_id), "email": email, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        payload = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id, name, email, bio, role, created_at FROM users WHERE id = :id"), {"id": user_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)
