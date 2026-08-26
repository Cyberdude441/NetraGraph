from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router

app = FastAPI(
    title="NetraGraph AI – Criminal Network Analysis Backend",
    description=(
        "Production-grade backend service powering AI crime data ingestion, "
        "named entity extraction, NetworkX knowledge graph generation, "
        "risk scoring, and multi-hop investigative reasoning."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes under /api
app.include_router(api_router)


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "NetraGraph AI Backend",
        "status": "ONLINE",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "ingest": "POST /api/ingest",
            "entities": "GET /api/entities",
            "network": "GET /api/network/{id}",
            "profile": "GET /api/profile/{id}",
            "analyze": "POST /api/analyze",
        },
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "HEALTHY",
        "graphEngine": "NetworkX MultiDiGraph Online",
        "database": "InMemory Intelligence Store Synchronized",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
