import time
from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS_TOTAL = Counter(
    "devconnect_http_requests_total",
    "Total HTTP requests handled by DevConnect FastAPI services.",
    ["service", "method", "path", "status"],
)
REQUEST_DURATION_SECONDS = Histogram(
    "devconnect_http_request_duration_seconds",
    "HTTP request duration in seconds for DevConnect FastAPI services.",
    ["service", "method", "path"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "devconnect_http_requests_in_progress",
    "In-flight HTTP requests for DevConnect FastAPI services.",
    ["service", "method", "path"],
)


def _route_template(request):
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def add_prometheus_metrics(app, service_name: str):
    """Expose Prometheus-compatible app metrics at /prometheus.

    The Analytics Service already uses /metrics for the product dashboard JSON API,
    so this project exposes Prometheus metrics consistently at /prometheus.
    """

    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        if request.url.path == "/prometheus":
            return await call_next(request)

        method = request.method
        raw_path = request.url.path
        REQUESTS_IN_PROGRESS.labels(service_name, method, raw_path).inc()
        started = time.perf_counter()
        status = "500"
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        finally:
            path = _route_template(request) or raw_path
            duration = time.perf_counter() - started
            REQUESTS_IN_PROGRESS.labels(service_name, method, raw_path).dec()
            REQUEST_DURATION_SECONDS.labels(service_name, method, path).observe(duration)
            REQUESTS_TOTAL.labels(service_name, method, path, status).inc()

    @app.get("/prometheus", include_in_schema=False)
    def prometheus_metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
