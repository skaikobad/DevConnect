from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text()


def test_auth_service_exposes_auth_routes():
    assert '@app.get("/health")' in MAIN
    assert '@app.post("/register")' in MAIN
    assert '@app.post("/login")' in MAIN
    assert '@app.get("/me")' in MAIN
    assert "CryptContext" in MAIN
    assert "create_token" in MAIN
