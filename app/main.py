from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in development / serverless initialization
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning(f"Database table verification notice: {e}")
    yield
    # Shutdown
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend API for Talib-e-Kharch - Student Expense Tracker",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS middleware for Expo React Native and Web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root entry point with service status and documentation links."""
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.get("/api", tags=["Root"])
async def api_root():
    return RedirectResponse(url="/docs")


@app.get("/api/docs", include_in_schema=False)
async def api_docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/api/health", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check probe."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}


# Mount all API endpoints
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")
