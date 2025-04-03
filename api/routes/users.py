from fastapi import APIRouter, Depends
from fief_client import FiefUserInfo
from api.auth import auth

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/self")
async def get_user(user: FiefUserInfo = Depends(auth.current_user())):
    print("User info:", user)
    return user
