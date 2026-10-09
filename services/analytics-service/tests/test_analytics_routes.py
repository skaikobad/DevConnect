from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text()


def test_analytics_service_exposes_metrics_and_impressions():
    assert '@app.get("/health")' in MAIN
    assert '@app.get("/metrics")' in MAIN
    assert '@app.post("/impressions")' in MAIN
    assert "cloudconnect:queue:post-create" in MAIN
    assert "queue_depth" in MAIN
    assert "processed_by_worker" in MAIN
