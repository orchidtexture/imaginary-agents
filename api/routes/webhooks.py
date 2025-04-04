import logging
import hmac
import time
from hashlib import sha256
from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
from api.models import User
from database.database import add_user, retrieve_user_by_email
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class FiefUserEvent(BaseModel):
    """Simplified model for Fief user events"""
    id: str
    email: str
    event_type: str


async def verify_fief_signature(request: Request):
    """Verify that the webhook is coming from Fief"""

    if not settings.FIEF_WEBHOOK_SECRET:
        logger.warning("No FIEF_WEBHOOK_SECRET configured")
        return False

    timestamp = request.headers.get("X-Fief-Webhook-Timestamp")
    signature = request.headers.get("X-Fief-Webhook-Signature")
    payload = (await request.body()).decode("utf-8")

    # Check if timestamp and signature are there
    if timestamp is None or signature is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Check if timestamp is not older than 5 minutes
    if int(time.time()) - int(timestamp) > 5 * 60:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Compute signature
    message = f"{timestamp}.{payload}"
    hash = hmac.new(
        settings.FIEF_WEBHOOK_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=sha256,
    )
    computed_signature = hash.hexdigest()

    return hmac.compare_digest(signature, computed_signature)


@router.post("/fief")
async def fief_webhook(request: Request):
    """Handle webhooks from Fief"""
    # Verify signature
    is_valid = await verify_fief_signature(request)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Parse the webhook payload
    try:
        body = await request.json()
        event_type = body.get("type")

        if event_type in ["user.created", "user.updated"]:
            user_data = body.get("data", {})
            email = user_data.get("email")

            if not email:
                return Response(status_code=status.HTTP_400_BAD_REQUEST)

            # Check if user exists in our DB
            existing_user = await retrieve_user_by_email(email)

            if existing_user and event_type == "user.updated":
                # TODO: Update existing user if needed
                # (You might want to sync specific fields from Fief)
                return Response(status_code=status.HTTP_200_OK)

            elif not existing_user and event_type == "user.created":
                # Create new user in our database
                new_user = User(
                    email=email,
                    llm_api_keys=[]  # Empty by default
                )
                await add_user(new_user)

            return Response(status_code=status.HTTP_200_OK)

        # Return 200 for other event types we don't process
        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing Fief webhook: {str(e)}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
