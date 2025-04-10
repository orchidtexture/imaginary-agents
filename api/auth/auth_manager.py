from fastapi import Depends, HTTPException, Header
from typing import Optional

from api.models.user import User
from database.database import retrieve_user_by_api_key


async def get_api_key_from_header(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    return x_api_key


async def current_user(api_key: str = Depends(get_api_key_from_header)) -> User:
    user = await retrieve_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
