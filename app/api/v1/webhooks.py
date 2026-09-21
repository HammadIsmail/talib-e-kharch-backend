import logging
from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@router.post("/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(None),
):
    """Handle incoming RevenueCat subscription webhook events."""
    expected_token = settings.REVENUECAT_WEBHOOK_AUTH_TOKEN or settings.REVENUECAT_WEBHOOK_SECRET
    if expected_token:
        clean_auth = authorization.replace("Bearer ", "").strip() if authorization else ""
        if clean_auth != expected_token and authorization != expected_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")

    data = await request.json()
    event = data.get("event", {})
    event_type = event.get("type")
    app_user_id = event.get("app_user_id")

    logger.info(f"RevenueCat webhook received: {event_type} for user: {app_user_id}")

    if not app_user_id:
        return {"status": "ignored_no_user_id"}

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.id == app_user_id))
        user = result.scalar_one_or_none()
        if not user:
            # Check by revenuecat_id
            result = await db.execute(select(User).where(User.revenuecat_id == app_user_id))
            user = result.scalar_one_or_none()

        if user:
            if event_type in ("INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE"):
                user.tier = "premium"
                user.revenuecat_id = app_user_id
            elif event_type in ("CANCELLATION", "EXPIRATION"):
                user.tier = "free"

            db.add(user)
            await db.commit()
            logger.info(f"Updated user {user.id} tier to {user.tier}")

    return {"status": "success"}
