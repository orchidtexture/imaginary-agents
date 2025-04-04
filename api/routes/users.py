import logging
from fastapi import APIRouter, Depends
from fief_client import FiefUserInfo
from api.auth import current_user

from database.database import retrieve_user_by_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/self")
async def get_user(fiefUser: FiefUserInfo = Depends(current_user)):
    logging.info("##########", fiefUser)
    # fetch user from db by email
    user = await retrieve_user_by_email(fiefUser['email'])
    if not user:
        return {"error": "User not found"}
    return {
        "email": user.email
    }
