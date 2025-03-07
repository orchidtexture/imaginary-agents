from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from imaginary_agents.tools.crawler_tool import CrawlerTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/crawler", tags=["Crawler Agents"])

# schema = {
#             "name": "Youtube Channel About",
#             "baseSelector": "ytd-about-channel-renderer",
#             "fields": [
#                 {
#                     "name": "About Channel Renderer",
#                     "type": "nested",
#                     "selector": "div[id='about-container']",
#                     "fields": [
#                         {
#                             "name": "Description Container",
#                             "type": "nested",
#                             "selector": "yt-attributed-string",
#                             "fields": [
#                                 {
#                                     "name": "Description",
#                                     "type": "text",
#                                     "selector": "span"
#                                 }
#                             ]
#                         },
#                         {
#                             "name": "Additional Information",
#                             "type": "nested",
#                             "selector": "div[id='additional-info-container']",
#                             "fields": [
#                                 {
#                                     "name": "Table",
#                                     "type": "nested",
#                                     "selector": "table",
#                                     "fields": [
#                                         {
#                                             "name": "Body",
#                                             "type": "nested",
#                                             "selector": "tbody",
#                                             "fields": [
#                                                 {
#                                                     "name": "Subscribers Count",
#                                                     "type": "text",
#                                                     "selector": "tr:nth-child(4) td:nth-child(2)",
#                                                 },
#                                                 {
#                                                     "name": "Videos Count",
#                                                     "type": "text",
#                                                     "selector": "tr:nth-child(5) td:nth-child(2)",
#                                                 },
#                                                 {
#                                                     "name": "Views Count",
#                                                     "type": "text",
#                                                     "selector": "tr:nth-child(6) td:nth-child(2)",
#                                                 },
#                                                 {
#                                                     "name": "Channel Creation Date",
#                                                     "type": "text",
#                                                     "selector": "tr:nth-child(7) td:nth-child(2) yt-attributed-string span span"
#                                                 },
#                                                 {
#                                                     "name": "Channel Country",
#                                                     "type": "text",
#                                                     "selector": "tr:nth-child(8) td:nth-child(2)"
#                                                 },
#                                             ]
#                                         }
#                                     ]
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         }


class ToolRunRequest(BaseModel):
    website_url: str
    crawl_instruction: Optional[str] = None
    schema: Optional[str] = None
    agent_name: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


@router.post("/run")
async def run_tool(config: ToolRunRequest):
    try:
        logger.info("Running crawler tool")

        crawler_tool = CrawlerTool()

        if config.crawl_instruction and config.schema:
            raise ValueError("Only one of 'crawl_instruction' or 'schema' should be provided.")

        if not config.website_url:
            raise ValueError("Website URL is required.")

        if config.crawl_instruction:  # TODO: add validation for all required fields
            try:
                crawler_input = CrawlerTool.input_schema(
                    crawl_instruction=config.crawl_instruction,
                    website_url=config.website_url
                )
                response = crawler_tool.run(crawler_input)
                return response
            except Exception as e:
                raise ValueError(f"Invalid request body data: {str(e)}")
        elif config.schema:
            try:
                crawler_input = CrawlerTool.input_schema(
                    schema=config.schema,
                    website_url=config.website_url
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
