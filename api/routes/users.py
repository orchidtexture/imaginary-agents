import logging
from fastapi import APIRouter, Depends, HTTPException
from fief_client import FiefUserInfo
from api.auth import current_user
from api.models import User
from pydantic import BaseModel, Field, ConfigDict

from database.database import add_user

from database.database import retrieve_user_by_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class CreateUserRequest(BaseModel):
    """Request model for creating an User"""
    email: str = Field(..., description="The user email address")
    llm_api_keys: list[dict] = Field(
        ...,
        description="List of API keys for different LLM providers"
    )

    # Reuse the same example schema
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "example@mail.com",
                "llm_api_keys": [
                    {
                        "provider": "openai",
                        "api_key": "sk-xxxxxxxxxxxxxxxxxxxx"
                    },
                    {
                        "provider": "anthropic",
                        "api_key": "sk-xxxxxxxxxxxxxxxxxxxx"
                    }
                ]
            }
        }
    )


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


@router.post("/register")
async def register_user(config: CreateUserRequest):
    """
    Registers a new User
    :return: The newly registered User
    """
    try:
        # Convert request model to LLMConfig and save it
        # Model dump bc request model has same fields as LLMConfig model
        new_user = User(**config.model_dump())
        res = await add_user(new_user)
        return res
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
