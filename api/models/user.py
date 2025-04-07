from beanie import Document, Link
from pydantic import Field, ConfigDict
from typing import Dict, List

from .api_key import APIKey


class User(Document):
    """
    MongoDB document model for storing Users
    """
    email: str = Field(..., description="The user email address")
    llm_api_keys: Dict[str, str] = Field(
        ...,
        description="Dictionary of API keys for different LLM providers"
    )
    api_keys: List[Link[APIKey]] = Field(
        default=[],
        description="List of API keys associated with the user"
    )
    is_admin: bool = Field(
        default=False,
        description="Flag indicating if the user is an admin"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "example@mail.com",
                "llm_api_keys": {
                    "openai": "sk-xxxxxxxxxxxxxxxxxxxx",
                    "anthropic": "sk-xxxxxxxxxxxxxxxxxxxx"
                },
                "api_keys": ["some_api_key_id"],
                "is_admin": False
            }
        }
    )

    class Settings:
        name = "users"
