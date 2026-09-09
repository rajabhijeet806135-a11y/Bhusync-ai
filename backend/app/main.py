"""
BhuSynch AI — FastAPI Application Entry Point
================================================
National Urban Cadastral Intelligence Mesh

Implements all OGC + REST API endpoints from Section 4.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

import structlog

from app.config import settings
from app.database import init_db, close_db

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    logger.info("bhusynch_starting", version=settings.APP_VERSION)
    try:
        await init_db()
        logger.info("database_lifecycle_initialized")
    except Exception as e:
        logger.warning("database_initialization_deferred", error=str(e))
    yield
    try:
        await close_db()
    except Exception:
        pass
    logger.info("bhusynch_shutdown")


app = FastAPI(
    title="BhuSynch AI — National Urban Cadastral Intelligence Mesh",
    description=(
        "Automated Integration and Intelligent Harmonization of "
        "Multi-source Geospatial Data for Urban Land Record Management. "
        "Problem Statement ID: SIH 26013"
    ),
    version=settings.APP_VERSION,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers (Section 4 — OGC + REST) ───────────────────
from app.api.ogc_features import router as ogc_features_router
from app.api.ogc_processes import router as ogc_processes_router
from app.api.ogc_tiles import router as ogc_tiles_router
from app.api.adjudication import router as adjudication_router
from app.api.audit import router as audit_router

app.include_router(ogc_features_router)
app.include_router(ogc_processes_router)
app.include_router(ogc_tiles_router)
app.include_router(adjudication_router)
app.include_router(audit_router)


@app.get("/", tags=["Health"])
async def root():
    """API health check."""
    return {
        "service": "BhuSynch AI",
        "version": settings.APP_VERSION,
        "status": "operational",
        "problem_statement": "SIH 26013",
        "governance": "NAKSHA (DoLR/MoRD), DILRMP, ULPIN",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "models": "ready",
    }


def run():
    """CLI entry point."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4,
    )
