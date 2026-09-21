from pydantic import BaseModel, Field


# Voice Expense Parsing (Gemini / Uplift STT output)
class VoiceExpenseRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=1000)


class ParsedExpenseItem(BaseModel):
    description: str
    amount: float
    category: str
    icon: str = "restaurant"


class VoiceExpenseImpact(BaseModel):
    current_safe_daily: float
    new_safe_daily: float
    days_remaining: int


class VoiceExpenseResponse(BaseModel):
    parsed_items: list[ParsedExpenseItem]
    total: float
    impact: VoiceExpenseImpact | None = None


# Affordability Check
class AffordabilityRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    amount: float = Field(..., gt=0)


class AffordabilityImpact(BaseModel):
    metric: str
    subtitle: str
    before: float
    after: float
    icon: str


class AffordabilityResponse(BaseModel):
    verdict: str  # safe, safe_with_tradeoff, dangerous
    verdict_label: str
    explanation: str
    buffer_percentage: float
    impacts: list[AffordabilityImpact]


# Uplift AI Voice Session
class VoiceSessionResponse(BaseModel):
    session_token: str
    ws_url: str
    voice_id: str
