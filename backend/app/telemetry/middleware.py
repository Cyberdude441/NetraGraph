"""
Pure ASGI Telemetry Middleware for NetraGraph AI.
Captures HTTP request latency, status codes, Prometheus metrics, and OpenTelemetry spans.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from app.telemetry.metrics import record_http_metrics
from app.telemetry.tracing import get_tracer
from opentelemetry.trace import Status, StatusCode


class TelemetryMiddleware:
    """Production ASGI Middleware for distributed tracing and metrics collection."""

    def __init__(self, app: Any):
        self.app = app
        self.tracer = get_tracer("netragraph.http")

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        # Exclude internal health and metrics probes from heavy tracing if necessary
        is_metrics_path = path == "/metrics"
        start_time = time.perf_counter()
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        if is_metrics_path:
            # Simple pass-through for Prometheus scraper to prevent self-observing feedback loops
            await self.app(scope, receive, send_wrapper)
            return

        span_name = f"HTTP {method} {path}"
        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.target", path)
            span.set_attribute("http.scheme", scope.get("scheme", "http"))

            try:
                await self.app(scope, receive, send_wrapper)
                span.set_attribute("http.status_code", status_code)
                if status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                status_code = 500
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
            finally:
                duration_seconds = time.perf_counter() - start_time
                record_http_metrics(method, path, status_code, duration_seconds)
