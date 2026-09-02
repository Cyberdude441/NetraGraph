"""
NetraGraph Telemetry Configuration.
Controls OpenTelemetry tracing and Prometheus metrics collection settings.
"""
from __future__ import annotations

import os
from pydantic import BaseModel, Field


class TelemetryConfig(BaseModel):
    """Telemetry configuration options for production observability."""

    OTEL_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("OTEL_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    OTEL_SERVICE_NAME: str = Field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "netragraph-backend")
    )
    OTEL_SERVICE_VERSION: str = Field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_VERSION", "2.5.0")
    )
    OTEL_ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "production")
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    )
    PROMETHEUS_METRICS_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() in ("true", "1", "yes")
    )


telemetry_config = TelemetryConfig()
