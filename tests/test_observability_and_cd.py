from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FASTAPI_SERVICES = [
    "auth-service",
    "user-service",
    "post-service",
    "like-service",
    "comment-service",
    "analytics-service",
]


def test_fastapi_services_expose_prometheus_endpoint():
    for service in FASTAPI_SERVICES:
        main = (ROOT / "services" / service / "app" / "main.py").read_text()
        metrics = (ROOT / "services" / service / "app" / "metrics.py").read_text()
        requirements = (ROOT / "services" / service / "requirements.txt").read_text()
        assert "add_prometheus_metrics(app" in main
        assert '@app.get("/prometheus"' in metrics
        assert "devconnect_http_requests_total" in metrics
        assert "prometheus-client" in requirements


def test_worker_exposes_prometheus_metrics_server():
    worker = (ROOT / "services" / "worker-service" / "app" / "worker.py").read_text()
    requirements = (ROOT / "services" / "worker-service" / "requirements.txt").read_text()
    assert "start_http_server(WORKER_METRICS_PORT)" in worker
    assert "devconnect_worker_jobs_processed_total" in worker
    assert "devconnect_worker_queue_depth" in worker
    assert "prometheus-client" in requirements


def test_kubernetes_servicemonitors_exist():
    base = (ROOT / "k8s" / "base" / "60-servicemonitors.yaml").read_text()
    kustomization = (ROOT / "k8s" / "base" / "kustomization.yaml").read_text()
    assert "kind: ServiceMonitor" in base
    assert "devconnect-fastapi-services" in base
    assert "devconnect-worker-service" in base
    assert "path: /prometheus" in base
    assert "path: /metrics" in base
    assert "60-servicemonitors.yaml" in kustomization


def test_cadvisor_manifest_is_containerd_friendly():
    manifest = (ROOT / "k8s" / "monitoring" / "cadvisor-daemonset.yaml").read_text()
    assert "/var/lib/containerd" in manifest
    assert "/var/lib/kubelet" in manifest
    assert "/run/containerd" in manifest
    assert "kind: ServiceMonitor" in manifest


def test_github_actions_has_runtime_verification_and_branded_email():
    workflow = (ROOT / ".github" / "workflows" / "ci-cd.yml").read_text()
    assert "Verify ArgoCD Runtime Deployment" in workflow
    assert "kubectl -n argocd get application devconnect" in workflow
    assert "rollout status deployment/frontend" in workflow
    assert "bongoDev DevConnect CI/CD" in workflow
    assert "html_body" in workflow
    assert "smtp.gmail.com" not in workflow  # configured via secret, not hard-coded
