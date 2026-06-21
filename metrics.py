from prometheus_client import Counter, Histogram, make_asgi_app

# ── Request counters ────────────────────────────────────────────────
forecast_requests_total = Counter(
    "forecast_requests_total",
    "Total forecast requests",
    ["sku", "mode", "status"]
)

alerts_requests_total = Counter(
    "alerts_requests_total",
    "Total alerts requests",
    ["status"]
)

upload_requests_total = Counter(
    "upload_requests_total",
    "Total CSV upload requests",
    ["status"]
)

auth_requests_total = Counter(
    "auth_requests_total",
    "Total auth requests",
    ["endpoint", "status"]
)

# ── Latency histograms ──────────────────────────────────────────────
forecast_latency_seconds = Histogram(
    "forecast_latency_seconds",
    "Forecast processing time in seconds",
    ["mode"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
)

alerts_latency_seconds = Histogram(
    "alerts_latency_seconds",
    "Alerts processing time in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# ── Cache metrics ────────────────────────────────────────────────────
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["layer"]  # "memory" or "redis"
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses"
)

# ── Mountable ASGI app for /metrics endpoint ────────────────────────
metrics_app = make_asgi_app()