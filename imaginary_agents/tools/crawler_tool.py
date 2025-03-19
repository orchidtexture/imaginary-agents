import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from typing import Dict, Any, Optional
from pydantic import Field, BaseModel, create_model
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
    BrowserConfig
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool

from dotenv import load_dotenv

load_dotenv()

STEEL_API_KEY = os.getenv("STEEL_API_KEY")


################
# INPUT SCHEMA #
################
class CrawlerToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool for crawling the web.
    Returns a structured response fetched from the web.
    """

    crawl_instruction: Optional[str] = Field(None, description="Crawling instruction.")
    website_url: str = Field(description="URL of the website to crawl.")
    schema: Optional[str] = Field(
        None,
        description="JSON schema for the crawling instruction."
    )
    api_key: Optional[str] = Field(None, description="API key for the LLM provider.")
    config: Optional[dict] = Field(description="Configuration for the crawler.")
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider to use for extraction."
    )
    llm_model: Optional[str] = Field(None, description="LLM model to use.")
    llm_extraction_schema: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="LLM extraction schema fields."
    )
    llm_extraction_extra_args: Optional[Dict[str, Any]] = Field(
        None,
        description="Extra arguments for LLM extraction."
    )
    local_crawling: Optional[bool] = Field(
        False,
        description="Whether to use local browser or Steel for crawling."
    )

    # response_format: Literal["json", "html"] = Field()...


####################
# OUTPUT SCHEMA(S) #
####################
class CrawlerToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the crawling tool."""

    result: str = Field(description="Crawling result as string.")
    # Maybe here we can change type to a more structured one depending on response_format


class CrawlerTool(BaseTool):
    """
    Tool for performing crawling on a website based on the instruction.

    Attributes:
        input_schema (CrawlerToolInputSchema): The schema for the input data.
        output_schema (CrawlerToolOutputSchema): The schema for the output data.
    """

    input_schema = CrawlerToolInputSchema
    output_schema = CrawlerToolOutputSchema

    def __init__(self):
        """
        Initializes the CrawlerTool.
        """
        super().__init__()

    async def run_crawler(self, params):
        # Define the JSON schema (XPath version)

        if params.schema:
            schema_dict = json.loads(
                params.schema
            ) if isinstance(
                params.schema,
                str
            ) else params.schema

            extraction_strategy = JsonCssExtractionStrategy(
                schema_dict,
                verbose=True
            )
        else:
            # Create dynamic schema
            LlmExtractionSchema = create_model(
                'LlmExtractionSchema',
                __base__=BaseModel,
                __doc__="LLM extraction schema.",
                **{
                    name: (field_def['type'], Field(
                        ...,
                        description=field_def['description']
                    ))
                    for name, field_def in params.llm_extraction_schema.items()
                }
            )

            # Rebuild the model to fully define it
            LlmExtractionSchema.model_rebuild()

            provider = f"{params.llm_provider}/{params.llm_model}"
            print(f"Using provider: {provider}")
            print("api_key:", params.api_key)

            extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(
                    provider=provider,
                    api_token=params.api_key
                ),
                schema=LlmExtractionSchema.model_json_schema(),
                extraction_type="schema",
                instruction=params.crawl_instruction,
                extra_args=params.llm_extraction_extra_args,
            )

        if params.local_crawling:
            # Using local browser for the crawler
            browser_config = BrowserConfig(
                headless=True,
                verbose=True,
                browser_type="chromium"
            )
        else:
            # Using steel.dev for the browser
            cdp_url = f"wss://connect.steel.dev?apiKey={STEEL_API_KEY}"

            browser_config = BrowserConfig(
                headless=True,
                verbose=True,
                use_managed_browser=True,
                browser_type="chromium",
                cdp_url=cdp_url
            )

        # Place the strategy in the CrawlerRunConfig
        config_kwargs = {
            "extraction_strategy": extraction_strategy,
            "cache_mode": CacheMode.BYPASS,
        }

        # Dynamically add parameters from config_values if they have valid values
        for key, value in params.config.items():
            # Skip the extraction_strategy as we've already added it
            if key == "extraction_strategy" or key == "cache_mode":
                continue

            # Only add non-None and non-empty values
            if value is not None and (not isinstance(value, str) or value.strip()):
                config_kwargs[key] = value

        # Create the config with dynamic parameters
        config = CrawlerRunConfig(**config_kwargs)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=params.website_url,
                config=config
            )

            if not result.success:
                print("Crawl failed:", result.error_message)
                return

            # 5. Parse the extracted JSON
            data = json.loads(result.extracted_content)
            print(f"Extracted {len(data)} coin entries")
            return json.dumps(data[0], indent=2) if data else "No data found"

    def run(self, params: CrawlerToolInputSchema) -> CrawlerToolOutputSchema:
        """
        Runs the CrawlerTool synchronously with the given parameters.

        This method creates an event loop in a separate thread to run
        the asynchronous operations.

        Args:
            params (CrawlerToolInputSchema):
                The input parameters for the tool, adhering to the input schema.

        Returns:
            CrawlerToolOutputSchema:
                The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the base URL is not provided.
            Exception: If the request to SearxNG fails.
        """

        with ThreadPoolExecutor() as executor:
            return executor.submit(
                asyncio.run, self.run_crawler(params)
            ).result()
