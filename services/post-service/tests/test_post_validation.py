from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text()


def test_post_service_exposes_queue_routes_and_public_images():
    assert '@app.get("/health")' in MAIN
    assert '@app.get("/posts")' in MAIN
    assert '@app.post("/posts"' in MAIN
    assert '@app.get("/posts/jobs/{job_id}")' in MAIN
    assert "normalize_public_image_url" in MAIN
    assert "post.create.requested" in MAIN
    assert "redis_client.rpush" in MAIN


def test_post_service_validates_public_http_image_urls():
    assert 'value.startswith("https://")' in MAIN
    assert 'value.startswith("http://")' in MAIN
    assert "Image URL must be a public" in MAIN
