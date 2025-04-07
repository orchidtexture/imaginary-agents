import logging
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import uuid4

from api.auth import current_user, admin_user
from api.models.user import User
from api.models.api_key import APIKey

from database.database import add_user, add_api_key


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class CreateUserRequest(BaseModel):
    """Request model for creating a new user"""
    email: str = Field(..., description="The user email address")
    llm_api_keys: Dict[str, str] = Field(
        default={},
        description="Dictionary of API keys for different LLM providers"
    )

    # Reuse the same example schema
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "email@example.com",
                "llm_api_keys": {
                    "openai": "sk-xxxxxxxxxxxxxxxxxxxx",
                    "anthropic": "sk-xxxxxxxxxxxxxxxxxxxx"
                },
            }
        }
    )


@router.get("/self")
async def get_user(user: User = Depends(current_user)):
    if not user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {
        "email": user.email
    }


@router.post("/create")
async def create_user(config: CreateUserRequest, user: User = Depends(admin_user)):
    api_key = APIKey(
        key=f"sk-{uuid4().hex}"  # Generate a random API key with prefix
    )
    await add_api_key(api_key)  # Save the API key to the database
    new_user = User(
        email=config.email,
        llm_api_keys=config.llm_api_keys,
        api_keys=[api_key]
    )
    await add_user(new_user)
    return {
        "email": new_user.email,
        "apiKey": api_key.key,
    }
