from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import init_db
from app.api.router import api_router
from app.api.websocket import ws_router
from app.utils.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    if settings.ENVIRONMENT != "testing":
        try:
            await init_db()
            if settings.SEED_DATABASE:
                from app.utils.seeder import run_seed
                await run_seed()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Database init skipped or deferred: {e}")
    yield


app = FastAPI(
    title="AI Coal Mine Governance System",
    description="Production-style SIH prototype for smart compliance monitoring",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
