from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from api.crime import router as crime_router
from api.graph import router as graph_router
from api.analytics import router as analytics_router
from api.ncrb import router as ncrb_router
from api.ai import router as ai_router
from api.cyber_intelligence import router as cyber_router
from api.system import router as system_router
from api.auth import router as auth_router
from app.api.router import api_router as legacy_api_router
from app.database.postgres import check_db_health, init_db
from services.graph_builder import graph_builder
from services.investigation_graph import investigation_graph_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NetraGraphAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NetraGraph AI Backend Layer, PostgreSQL Schema & Neo4j Engine...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"PostgreSQL initialization notice: {e}")
    graph_builder.rebuild_all_graphs()
    investigation_graph_service.initialize_formal_investigation_graph()
    logger.info("PostgreSQL & Neo4j Knowledge Graph initialized successfully.")
    yield
    logger.info("Shutting down NetraGraph AI Backend Layer.")


from app.auth.config import auth_config


class SecurityHeadersMiddleware:
    """Production HTTP Security Headers Middleware (pure ASGI implementation)."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"x-xss-protection", b"1; mode=block"))
                headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                headers.append((b"permissions-policy", b"geolocation=(), microphone=(), camera=()"))
                if auth_config.COOKIE_SECURE:
                    headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app = FastAPI(
    title="NetraGraph AI — Backend Intelligence API Layer",
    description="Production-grade Cyber Cell & NCRB Open Government Data Intelligence Grid",
    version="2.5.0",
    lifespan=lifespan,
)

from app.telemetry import TelemetryMiddleware, get_metrics_payload

# Enable Telemetry & Distributed Tracing
app.add_middleware(TelemetryMiddleware)

# Enable Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS for frontend client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Dedicated API Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(ncrb_router, prefix="/api")
app.include_router(crime_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(cyber_router, prefix="/api")
app.include_router(system_router, prefix="/api")

# Mount Legacy /api Routers (Cases, Evidence, Audit) for complete backward compatibility
app.include_router(legacy_api_router)


@app.get("/")
def root():
    return {
        "status": "ONLINE",
        "system": "NetraGraph AI Backend Intelligence Core",
        "version": "2.5.0",
        "database": "Neo4j Knowledge Graph Engine & PostgreSQL Relational Layer",
        "connectors": "Open Government Data (data.gov.in) NCRB Feeds",
        "ai_engine": "Graph RAG (Google Gemini & NVIDIA Nemotron)",
        "auth": "Passwordless Gmail OTP & RBAC",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "code": 200}


@app.get("/metrics", tags=["System"])
def metrics_endpoint():
    """
    Prometheus metrics exposition endpoint.
    Returns standard Prometheus text format metrics for scraping.
    """
    from fastapi import Response
    payload, content_type = get_metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.get("/health/db", tags=["System"])
async def db_health_check():
    return await check_db_health()


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    Readiness probe for container orchestration.
    Validates database and graph engine readiness without leaking internal secrets.
    """
    from fastapi import Response, status
    from database.neo4j import neo4j_db
    
    db_status = await check_db_health()
    is_db_ready = db_status.get("status") == "HEALTHY" and db_status.get("connected", False)
    
    # Graph engine readiness (live Neo4j connection or synchronized in-memory NetworkX graph)
    is_graph_ready = (
        len(neo4j_db._nx_ncrb.nodes) > 0 or 
        len(neo4j_db._nx_evidence.nodes) > 0 or 
        neo4j_db.is_connected
    )
    
    if is_db_ready and is_graph_ready:
        return {
            "status": "READY",
            "code": 200,
            "services": {
                "database": "HEALTHY",
                "graph_engine": "HEALTHY",
            },
        }
    
    db_state = "HEALTHY" if is_db_ready else "DEGRADED"
    graph_state = "HEALTHY" if is_graph_ready else "DEGRADED"
    return Response(
        content=f'{{"status":"NOT_READY","code":503,"services":{{"database":"{db_state}","graph_engine":"{graph_state}"}}}}',
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        media_type="application/json",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
