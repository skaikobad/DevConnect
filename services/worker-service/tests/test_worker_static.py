from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_worker_uses_redis_queue_and_post_jobs_table():
    worker = (ROOT / "app" / "worker.py").read_text()
    assert "cloudconnect:queue:post-create" in worker
    assert "post_jobs" in worker
    assert "rpop" in worker or "blpop" in worker
