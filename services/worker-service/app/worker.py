import json
import os
import time
from prometheus_client import Counter, Gauge, start_http_server
from datetime import datetime, timezone

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cloudconnect:cloudconnect123@postgres:5432/cloudconnect")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POST_CREATE_QUEUE = os.getenv("POST_CREATE_QUEUE", "cloudconnect:queue:post-create")
PROCESSED_EVENTS_LIST = os.getenv("PROCESSED_EVENTS_LIST", "cloudconnect:events:processed")
FAILED_EVENTS_LIST = os.getenv("FAILED_EVENTS_LIST", "cloudconnect:events:failed")
ANALYTICS_CACHE_KEY = os.getenv("ANALYTICS_CACHE_KEY", "cloudconnect:analytics:metrics")
DB_INIT_LOCK_ID = int(os.getenv("DB_INIT_LOCK_ID", "987654321"))
WORKER_METRICS_PORT = int(os.getenv("WORKER_METRICS_PORT", "9100"))

WORKER_JOBS_PROCESSED_TOTAL = Counter(
    "devconnect_worker_jobs_processed_total",
    "Post creation jobs successfully processed by the Worker Service.",
    ["service"],
)
WORKER_JOBS_FAILED_TOTAL = Counter(
    "devconnect_worker_jobs_failed_total",
    "Post creation jobs that failed in the Worker Service.",
    ["service"],
)
WORKER_QUEUE_DEPTH = Gauge(
    "devconnect_worker_queue_depth",
    "Current Redis post-create queue depth seen by the Worker Service.",
    ["queue"],
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def wait_for_dependencies():
    while True:
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            r.ping()
            print("worker-service: PostgreSQL and Redis are ready", flush=True)
            return
        except (OperationalError, redis.RedisError) as exc:
            print(f"worker-service: waiting for dependencies: {exc}", flush=True)
            time.sleep(2)


def ensure_job_table():
    """Create shared tables safely before the worker consumes queue messages.

    The worker may start at the same time as the API services. An advisory lock
    prevents PostgreSQL DDL race conditions during local Docker startup.
    """
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
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": DB_INIT_LOCK_ID})


def process_post_create(event: dict):
    job_id = event["job_id"]
    user_id = int(event["user_id"])
    content = event["content"]
    image_url = event.get("image_url")

    with engine.begin() as conn:
        job = conn.execute(
            text("""
            UPDATE post_jobs
            SET status='processing', updated_at=NOW()
            WHERE id=:id AND status='queued'
            RETURNING id
            """),
            {"id": job_id},
        ).mappings().first()
        if not job:
            print(f"worker-service: skipped job {job_id}; not queued", flush=True)
            return

        post = conn.execute(
            text("""
            INSERT INTO posts (user_id, content, image_url)
            VALUES (:user_id, :content, :image_url)
            RETURNING id
            """),
            {"user_id": user_id, "content": content, "image_url": image_url},
        ).mappings().first()

        conn.execute(
            text("""
            UPDATE post_jobs
            SET status='completed', post_id=:post_id, updated_at=NOW()
            WHERE id=:id
            """),
            {"id": job_id, "post_id": post["id"]},
        )

    today = datetime.now(timezone.utc).date().isoformat()
    pipe = r.pipeline()
    pipe.incr("cloudconnect:analytics:queued_posts_processed")
    pipe.incr(f"cloudconnect:analytics:daily:{today}:posts")
    pipe.delete(ANALYTICS_CACHE_KEY)
    pipe.lpush(PROCESSED_EVENTS_LIST, json.dumps({**event, "post_id": post["id"], "processed_at": datetime.now(timezone.utc).isoformat()}))
    pipe.ltrim(PROCESSED_EVENTS_LIST, 0, 99)
    pipe.execute()
    WORKER_JOBS_PROCESSED_TOTAL.labels("worker-service").inc()
    print(f"worker-service: completed post job {job_id} -> post {post['id']}", flush=True)


def mark_failed(event: dict, error: str):
    job_id = event.get("job_id")
    if job_id:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE post_jobs SET status='failed', error=:error, updated_at=NOW() WHERE id=:id"),
                {"id": job_id, "error": error[:500]},
            )
    r.lpush(FAILED_EVENTS_LIST, json.dumps({"event": event, "error": error, "failed_at": datetime.now(timezone.utc).isoformat()}))
    r.ltrim(FAILED_EVENTS_LIST, 0, 99)
    WORKER_JOBS_FAILED_TOTAL.labels("worker-service").inc()


def main():
    start_http_server(WORKER_METRICS_PORT)
    print(f"worker-service: Prometheus metrics exposed on :{WORKER_METRICS_PORT}/metrics", flush=True)
    wait_for_dependencies()
    ensure_job_table()
    print(f"worker-service: listening on Redis queue {POST_CREATE_QUEUE}", flush=True)
    while True:
        try:
            WORKER_QUEUE_DEPTH.labels(POST_CREATE_QUEUE).set(r.llen(POST_CREATE_QUEUE))
        except Exception:
            pass
        item = r.blpop(POST_CREATE_QUEUE, timeout=5)
        if not item:
            continue
        _, raw = item
        try:
            event = json.loads(raw)
            if event.get("event_type") == "post.create.requested":
                process_post_create(event)
            else:
                print(f"worker-service: unknown event {event}", flush=True)
        except Exception as exc:
            print(f"worker-service: failed to process event: {exc}", flush=True)
            try:
                mark_failed(json.loads(raw), str(exc))
            except Exception:
                pass


if __name__ == "__main__":
    main()
