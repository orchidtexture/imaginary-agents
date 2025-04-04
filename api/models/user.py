from beanie import Document
from pydantic import Field, ConfigDict
from typing import Dict


class User(Document):
    """
    MongoDB document model for storing Users
    """
    email: str = Field(..., description="The user email address")
    llm_api_keys: Dict[str, str] = Field(
        ...,
        description="Dictionary of API keys for different LLM providers"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "example@mail.com",
                "llm_api_keys": {
                    "openai": "sk-xxxxxxxxxxxxxxxxxxxx",
                    "anthropic": "sk-xxxxxxxxxxxxxxxxxxxx"
                }
            }
        }
    )

    class Settings:
        name = "users"
