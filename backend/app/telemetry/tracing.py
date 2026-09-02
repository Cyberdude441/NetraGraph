"""
OpenTelemetry Distributed Tracing Engine for NetraGraph AI.
Provides span management, contextual tracing, and sensitive payload scrubbing with graceful offline fallback.
"""
from __future__ import annotations

import functools
import inspect
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Status, StatusCode

from app.telemetry.config import telemetry_config

logger = logging.getLogger("NetraGraphTelemetry")

# Sensitive attribute filter list
SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "secret",
    "jwt_secret_key",
    "otp",
    "otp_code",
    "salt",
    "otp_hash",
    "credentials",
    "authorization",
    "cookie",
    "set-cookie",
    "smtp_password",
    "database_url",
    "database_sync_url",
    "neo4j_password",
}


def _sanitize_attributes(attributes: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitizes trace attributes to prevent secret or PII leakage into tracing backends."""
    if not attributes:
        return {}
    clean: Dict[str, Any] = {}
    for key, value in attributes.items():
        lower_key = str(key).lower()
        if any(s in lower_key for s in SENSITIVE_KEYS):
            clean[key] = "[REDACTED]"
        elif isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)[:200]
    return clean


# Global Tracer Initialization
_tracer_provider: Optional[TracerProvider] = None


def init_tracer() -> trace.Tracer:
    """Initializes and returns the global OpenTelemetry Tracer."""
    global _tracer_provider
    if _tracer_provider is None:
        resource = Resource.create(
            {
                "service.name": telemetry_config.OTEL_SERVICE_NAME,
                "service.version": telemetry_config.OTEL_SERVICE_VERSION,
                "deployment.environment": telemetry_config.OTEL_ENVIRONMENT,
            }
        )
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        logger.info("OpenTelemetry Tracer initialized for service: %s", telemetry_config.OTEL_SERVICE_NAME)

    return trace.get_tracer("netragraph.core", telemetry_config.OTEL_SERVICE_VERSION)


def get_tracer(name: str = "netragraph.core") -> trace.Tracer:
    """Returns the OpenTelemetry tracer instance."""
    if _tracer_provider is None:
        return init_tracer()
    return trace.get_tracer(name, telemetry_config.OTEL_SERVICE_VERSION)


@contextmanager
def trace_span(
    span_name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Generator[trace.Span, None, None]:
    """
    Context manager for creating a traced span with sanitized attributes.
    Gracefully handles exceptions and records error status without breaking business logic.
    """
    tracer = get_tracer()
    sanitized = _sanitize_attributes(attributes)
    with tracer.start_as_current_span(span_name) as span:
        if sanitized:
            for k, v in sanitized.items():
                span.set_attribute(k, v)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def traced(span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> Callable:
    """Decorator to automatically trace synchronous or asynchronous functions."""
    def decorator(func: Callable) -> Callable:
        target_name = span_name or f"{func.__module__}.{func.__name__}"

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with trace_span(target_name, attributes):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with trace_span(target_name, attributes):
                    return func(*args, **kwargs)
            return sync_wrapper

    return decorator
