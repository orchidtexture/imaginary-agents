import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.database import retrieve_llm_configs, add_llm_config

from api.models import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm/config", tags=["LLM Configs"])


class CreateLLMConfigRequest(BaseModel):
    """Request model for creating an LLM configuration"""
    model: str = Field(..., description="The model identifier")
    base_url: str = Field(..., description="Base URL for the LLM provider API")
    provider: str = Field(
        ...,
        description="The provider name (e.g., 'openai', 'anthropic')"
    )

    # Reuse the same example schema
    model_config = {
        "json_schema_extra": {
            "example": {
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com",
                "provider": "deepseek"
            }
        }
    }


@router.get("/list")
async def get_llm_configs():
    """
    Retrieve available LLM configurations
    :return: list of LLM Configurations
    """
    try:
        llm_configs = await retrieve_llm_configs()
        return {'llm_configs': llm_configs}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_llm_config(config: CreateLLMConfigRequest):
    """
    Create a new LLM configuration
    :return: The newly created LLM Config
    """
    try:
        # Convert request model to LLMConfig and save it
        # Model dump bc request model has same fields as LLMConfig model
        new_config = LLMConfig(**config.model_dump())
        res = await add_llm_config(new_config)
        return res
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
