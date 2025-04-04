from beanie import Document
from pydantic import Field, ConfigDict


class User(Document):
    """
    MongoDB document model for storing Users
    """
    email: str = Field(..., description="The user email address")
    llm_api_keys: list[dict] = Field(
        ...,
        description="List of API keys for different LLM providers"
    )

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

    class Settings:
        name = "users"
