import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Normalize database URL for SQLAlchemy asyncpg
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Remove url query params that asyncpg does not accept in connection string
connect_args = {}
if "sslmode" in db_url or "neon.tech" in db_url or "channel_binding" in db_url:
    if "?" in db_url:
        db_url = db_url.split("?")[0]
    connect_args["ssl"] = True

# Use NullPool for serverless environments (Vercel / AWS Lambda) to prevent closed event loop issues
engine = create_async_engine(
    db_url,
    echo=False,
    poolclass=NullPool,
    connect_args=connect_args,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async_session_factory = async_session


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db():
    """Dependency that provides a database session per request."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
