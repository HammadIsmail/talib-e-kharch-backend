from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in development / serverless initialization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend API for Talib-e-Kharch - Student Expense Tracker",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS middleware for Expo React Native and Web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check probe."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}


# Mount all API endpoints
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")
