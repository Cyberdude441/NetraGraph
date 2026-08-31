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
from app.api.router import api_router as legacy_api_router
from services.graph_builder import graph_builder
from services.investigation_graph import investigation_graph_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NetraGraphAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NetraGraph AI Backend Layer & Neo4j Graph Engine...")
    graph_builder.rebuild_all_graphs()
    investigation_graph_service.initialize_formal_investigation_graph()
    logger.info("Neo4j Knowledge Graph initialized successfully.")
    yield
    logger.info("Shutting down NetraGraph AI Backend Layer.")


app = FastAPI(
    title="NetraGraph AI — Backend Intelligence API Layer",
    description="Production-grade Cyber Cell & NCRB Open Government Data Intelligence Grid",
    version="2.5.0",
    lifespan=lifespan,
)

# Enable CORS for frontend client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Dedicated API Routers under /api
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
        "database": "Neo4j Knowledge Graph Engine",
        "connectors": "Open Government Data (data.gov.in) NCRB Feeds",
        "ai_engine": "Graph RAG (Google Gemini & NVIDIA Nemotron)",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "code": 200}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
