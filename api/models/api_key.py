from beanie import Document
from pydantic import Field, ConfigDict


class APIKey(Document):
    """
    MongoDB document model for storing API keys
    """
    key: str = Field(..., description="The model identifier")
    # owner: Link[User] = Field(..., description="Owner of the API key")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "some_key"
            }
        }
    )

    class Settings:
        name = "api_keys"
