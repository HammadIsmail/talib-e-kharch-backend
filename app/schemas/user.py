from datetime import datetime
from pydantic import BaseModel, Field

try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d{4,6}$")


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d{4,6}$")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    tier: str
    trial_ends_at: datetime | None = None
    currency: str
    monthly_reset_day: int
    daily_benchmark: float
    biometric_enabled: bool
    daily_digest: bool
    voice_language: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfileUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    monthly_reset_day: int | None = Field(None, ge=1, le=28)
    daily_benchmark: float | None = Field(None, gt=0)
    biometric_enabled: bool | None = None
    daily_digest: bool | None = None
    voice_language: str | None = None
    pin: str | None = Field(None, min_length=4, max_length=6, pattern=r"^\d{4,6}$")
