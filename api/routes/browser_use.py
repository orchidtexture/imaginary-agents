import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from imaginary_agents.tools.browser_use_tool import BrowserUseTool, BrowserUseToolConfig

from dotenv import load_dotenv

load_dotenv()

STEEL_API_KEY = os.getenv("STEEL_API_KEY")
STEEL_BASE_URL = "wss://connect.steel.dev"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/browser-use", tags=["Crawler Agents"])


class ToolRunRequest(BaseModel):

    task: str
    llm_api_key: str
    llm_provider: str
    llm_model: str
    local_browser: Optional[bool] = False
    STEEL_API_KEY: Optional[str] = None


@router.post("/run")
async def run_tool(config: ToolRunRequest):
    try:
        logger.info("Running browser-use tool")

        if config.local_browser:
            browser_use_tool = BrowserUseTool(config=BrowserUseToolConfig(
                llm_api_key=config.llm_api_key,
                llm_provider=config.llm_provider,
                llm_model=config.llm_model,
            ))
        else:
            browser_use_tool = BrowserUseTool(
                config=BrowserUseToolConfig(
                    STEEL_API_KEY=STEEL_API_KEY,
                    STEEL_BASE_URL=STEEL_BASE_URL,
                    llm_api_key=config.llm_api_key,
                    llm_provider=config.llm_provider,
                    llm_model=config.llm_model,
                )
            )

        try:
            browser_use_input = BrowserUseTool.input_schema(task=config.task)
            response = browser_use_tool.run(browser_use_input)
            return response
        except Exception as e:
            raise ValueError(f"Invalid request body data: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
