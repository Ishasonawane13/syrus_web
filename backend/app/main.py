"""
FastAPI Application Entrypoint for AI Trading Copilot.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables, AsyncSessionLocal
from app.api import api_router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed demo account if enabled
    await create_tables()
    if settings.SEED_DEMO_DATA:
        async with AsyncSessionLocal() as session:
            await seed_database(session)
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Safe AI Trading Copilot — Paper Trading Platform with Deterministic Risk Engine",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes at root and /api for client flexibility
app.include_router(api_router)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": "/health",
    }
