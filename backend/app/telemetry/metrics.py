"""
Prometheus Metrics Instrumentation for NetraGraph AI.
Defines strictly low-cardinality metrics for HTTP traffic, database health, graph queries, ML inference, and authentication security.
"""
from __future__ import annotations

import re
import time
from typing import Optional
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
)

# ============================================================
# 1. HTTP Traffic & Gateway Metrics
# ============================================================
HTTP_REQUESTS_TOTAL = Counter(
    "netragraph_http_requests_total",
    "Total HTTP requests processed by the API gateway",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "netragraph_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_ERRORS_TOTAL = Counter(
    "netragraph_http_errors_total",
    "Total HTTP error responses returned (4xx and 5xx)",
    ["method", "endpoint", "error_type"],
)

# ============================================================
# 2. PostgreSQL Relational & Pool Metrics
# ============================================================
DB_POOL_UTILIZATION = Gauge(
    "netragraph_db_pool_utilization",
    "Active PostgreSQL connection pool utilization percentage (0-100)",
    ["database"],
)

DB_QUERIES_TOTAL = Counter(
    "netragraph_db_queries_total",
    "Total PostgreSQL database operations executed",
    ["operation", "status"],
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "netragraph_db_query_duration_seconds",
    "PostgreSQL query execution latency in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

# ============================================================
# 3. Neo4j Knowledge Graph Metrics
# ============================================================
NEO4J_QUERIES_TOTAL = Counter(
    "netragraph_neo4j_queries_total",
    "Total Neo4j Cypher queries and graph operations executed",
    ["operation", "status"],
)

NEO4J_QUERY_DURATION_SECONDS = Histogram(
    "netragraph_neo4j_query_duration_seconds",
    "Neo4j graph query execution latency in seconds",
    ["operation"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

NEO4J_ERRORS_TOTAL = Counter(
    "netragraph_neo4j_errors_total",
    "Total Neo4j graph database errors encountered",
    ["error_type"],
)

# ============================================================
# 4. Machine Learning Inference Metrics (Models A-E)
# ============================================================
ML_INFERENCE_TOTAL = Counter(
    "netragraph_ml_inference_total",
    "Total forensic ML predictions executed across Models A-E",
    ["model_name", "status"],
)

ML_INFERENCE_DURATION_SECONDS = Histogram(
    "netragraph_ml_inference_duration_seconds",
    "ML model inference computation latency in seconds",
    ["model_name"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

ML_INFERENCE_ERRORS_TOTAL = Counter(
    "netragraph_ml_inference_errors_total",
    "Total ML model inference failures or feature validation errors",
    ["model_name", "error_type"],
)

# ============================================================
# 5. Authentication & OTP Lifecycle Security Metrics
# ============================================================
AUTH_EVENTS_TOTAL = Counter(
    "netragraph_auth_events_total",
    "Authentication, OTP issuance, verification, and logout events",
    ["event_type", "status"],
)

# ============================================================
# 6. Real-time WebSocket Metrics
# ============================================================
WEBSOCKET_CONNECTIONS_ACTIVE = Gauge(
    "netragraph_websocket_connections_active",
    "Number of currently open WebSocket connections",
)


# ============================================================
# Low-Cardinality Normalization & Metric Helpers
# ============================================================
_UUID_OR_ID_REGEX = re.compile(
    r"/(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+|[A-Z]{2,}-[A-Za-z0-9_-]+|[a-zA-Z0-9_-]*\d[a-zA-Z0-9_-]*)"
)


def normalize_endpoint(path: str) -> str:
    """
    Normalizes dynamic URL paths to maintain strict low-cardinality in Prometheus.
    Replaces UUIDs, numeric IDs, and long entity identifiers with '{id}'.
    """
    if not path or path == "/":
        return "/"
    
    # Strip query parameters if present
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        return "/"

    # Normalize entity IDs, Case IDs, Evidence IDs, User IDs
    normalized = _UUID_OR_ID_REGEX.sub("/{id}", clean_path)
    return normalized


def record_http_metrics(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Records HTTP request count, latency, and errors."""
    endpoint = normalize_endpoint(path)
    status_str = str(status_code)
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_str).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration_seconds)
    
    if status_code >= 400:
        error_type = f"{status_code // 100}xx"
        HTTP_ERRORS_TOTAL.labels(method=method, endpoint=endpoint, error_type=error_type).inc()


def record_ml_inference(model_name: str, duration_seconds: float, success: bool, error_type: Optional[str] = None) -> None:
    """Records ML inference execution metrics for Models A-E."""
    status = "success" if success else "failure"
    ML_INFERENCE_TOTAL.labels(model_name=model_name, status=status).inc()
    ML_INFERENCE_DURATION_SECONDS.labels(model_name=model_name).observe(duration_seconds)
    if not success and error_type:
        ML_INFERENCE_ERRORS_TOTAL.labels(model_name=model_name, error_type=error_type).inc()


def record_auth_event(event_type: str, status: str) -> None:
    """
    Records authentication events (e.g. otp_request, otp_verify, login, logout, refresh).
    Status: success, failure, rate_limited, expired.
    """
    AUTH_EVENTS_TOTAL.labels(event_type=event_type, status=status).inc()


def record_neo4j_query(operation: str, duration_seconds: float, success: bool, error_type: Optional[str] = None) -> None:
    """Records Neo4j Cypher and Graph execution metrics."""
    status = "success" if success else "failure"
    NEO4J_QUERIES_TOTAL.labels(operation=operation, status=status).inc()
    NEO4J_QUERY_DURATION_SECONDS.labels(operation=operation).observe(duration_seconds)
    if not success and error_type:
        NEO4J_ERRORS_TOTAL.labels(error_type=error_type).inc()


def get_metrics_payload() -> tuple[bytes, str]:
    """Generates the Prometheus metrics exposition payload and content type."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
