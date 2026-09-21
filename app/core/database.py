from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

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
    # Strip query params from url
    if "?" in db_url:
        db_url = db_url.split("?")[0]
    connect_args["ssl"] = True

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
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
