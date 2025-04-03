from beanie import Document
from pydantic import Field, ConfigDict


class User(Document):
    """
    MongoDB document model for storing Users
    """
    email: str = Field(..., description="The model identifier")
    base_url: str = Field(..., description="Base URL for the LLM provider API")
    provider: str = Field(
        ...,
        description="The provider name (e.g., 'openai', 'anthropic')"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com",
                "provider": "deepseek"
            }
        }
    )

    class Settings:
        name = "llm_configs"
