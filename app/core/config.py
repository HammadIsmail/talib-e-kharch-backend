from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "Talib-e-Kharch"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/talib_e_kharch"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Uplift AI
    UPLIFTAI_API_KEY: str = ""
    UPLIFTAI_VOICE_ID: str = "prime-time-anchor"

    # RevenueCat
    REVENUECAT_WEBHOOK_SECRET: str = ""
    REVENUECAT_WEBHOOK_AUTH_TOKEN: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:8081"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
