import logging
from app.core.config import get_settings
from app.schemas.ai import VoiceSessionResponse

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_uplift_voice_session(user_id: str) -> VoiceSessionResponse:
    """Initialize a voice session for Uplift AI STT/TTS with the prime-time-anchor voice."""
    voice_id = settings.UPLIFTAI_VOICE_ID or "prime-time-anchor"

    # If Uplift API key is provided, contact Uplift server; otherwise generate client connection token
    session_token = f"uplift_session_{user_id}_{voice_id}"
    ws_url = "wss://api.upliftai.com/v1/realtime"

    if settings.UPLIFTAI_API_KEY:
        try:
            import httpx

            url = "https://api.upliftai.com/v1/sessions"
            headers = {"Authorization": f"Bearer {settings.UPLIFTAI_API_KEY}"}
            payload = {
                "voice_id": voice_id,
                "user_id": user_id,
                "language": "ur-PK",
                "enable_stt": True,
                "enable_tts": True,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    session_token = data.get("session_token", session_token)
                    ws_url = data.get("ws_url", ws_url)
        except Exception as e:
            logger.warning(f"Uplift session initialization error (using fallback config): {e}")

    return VoiceSessionResponse(
        session_token=session_token,
        ws_url=ws_url,
        voice_id=voice_id,
    )
