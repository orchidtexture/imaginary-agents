import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fief_client import FiefUserInfo
from api.auth import current_user

from database.database import retrieve_user_by_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/self")
async def get_user(fiefUser: FiefUserInfo = Depends(current_user)):
    # fetch user from db by email
    user = await retrieve_user_by_email(fiefUser['email'])
    if not user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {
        "email": user.email
    }
