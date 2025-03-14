from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging
from imaginary_agents.tools.crawler_tool import CrawlerTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/crawler", tags=["Crawler Agents"])


class SchemaField(BaseModel):
    type: str  # Type name as string ("str", "int", etc.)
    description: str

    def get_python_type(self) -> type:
        """Convert string type name to Python type."""
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list
        }
        return type_mapping.get(self.type, str)  # default to str if type not found


class ToolRunRequest(BaseModel):
    website_url: str
    crawl_instruction: Optional[str] = None
    schema: Optional[str] = None
    crawler_config: Optional[dict] = {}
    agent_name: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None,
    llm_extraction_schema: Optional[Dict[str, SchemaField]] = None
    llm_extraction_extra_args: Optional[dict] = {}


@router.post("/run")
async def run_tool(config: ToolRunRequest):
    try:
        logger.info("Running crawler tool")

        crawler_tool = CrawlerTool()

        if config.crawl_instruction and config.schema:
            raise ValueError(
                "Only one of 'crawl_instruction' or 'schema' should be provided."
            )

        if not config.website_url:
            raise ValueError("Website URL is required.")

        if config.crawl_instruction:  # TODO: add validation for all required fields
            try:
                # Ensure llm_extraction_schema exists
                if config.llm_extraction_schema:
                    # Convert the type string to Python type for each schema field
                    processed_schema = {}
                    for field_name, field_info in config.llm_extraction_schema.items():
                        processed_schema[field_name] = {
                            'type': field_info.get_python_type(),
                            'description': field_info.description
                        }

                    crawler_input = CrawlerTool.input_schema(
                        crawl_instruction=config.crawl_instruction,
                        website_url=config.website_url,
                        config=config.crawler_config,
                        api_key=config.llm_api_key,
                        llm_provider=config.llm_provider,
                        llm_model=config.llm_model,
                        llm_extraction_schema=processed_schema,
                        llm_extraction_extra_args=config.llm_extraction_extra_args
                    )
                    response = crawler_tool.run(crawler_input)
                    if response is not None:
                        return response
                    else:
                        raise ValueError("Crawler tool failed to run")
                else:
                    raise ValueError(
                        "llm_extraction_schema is required when using crawl_instruction"
                    )
            except Exception as e:
                raise ValueError(f"Error: {str(e)}")
        elif config.schema:
            try:
                crawler_input = CrawlerTool.input_schema(
                    schema=config.schema,
                    website_url=config.website_url,
                    config=config.crawler_config
                )
                response = crawler_tool.run(crawler_input)
                return response
            except Exception as e:
                raise ValueError(f"Invalid request body data: {str(e)}")
        else:
            return {
                "message": "Agent initialized successfully, but no input data provided."
            }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
