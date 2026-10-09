from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SERVICES = {
    "frontend",
    "auth-service",
    "user-service",
    "post-service",
    "like-service",
    "comment-service",
    "analytics-service",
    "worker-service",
    "postgres",
    "redis",
}


def test_docker_compose_has_all_devconnect_services():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    assert EXPECTED_SERVICES.issubset(set(compose["services"].keys()))


def test_frontend_nginx_routes_all_api_services():
    nginx = (ROOT / "frontend" / "nginx.conf").read_text()
    for route in ["auth", "user", "post", "like", "comment", "analytics"]:
        assert f"/api/{route}/" in nginx


def test_kubernetes_manifests_exist_for_core_workloads():
    required = [
        "00-namespace.yaml",
        "10-configmap.yaml",
        "20-postgres.yaml",
        "21-redis.yaml",
        "30-auth-service.yaml",
        "31-user-service.yaml",
        "32-post-service.yaml",
        "33-like-service.yaml",
        "34-comment-service.yaml",
        "35-analytics-service.yaml",
        "36-worker-service.yaml",
        "40-frontend.yaml",
        "50-ingress.yaml",
    ]
    for file_name in required:
        assert (ROOT / "k8s" / "base" / file_name).exists()
