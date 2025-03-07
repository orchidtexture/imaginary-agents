import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from typing import Optional
from pydantic import Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool


################
# INPUT SCHEMA #
################
class CrawlerToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool for crawling the web.
    Returns a structured response fetched from the web.
    """

    crawl_instruction: Optional[str] = Field(
        None,
        description="Crawling instruction."
    )
    website_url: str = Field(
        description="URL of the website to crawl."
    )
    schema: Optional[str] = Field(
        None, description="JSON schema for the crawling instruction."
    )
    api_key: Optional[str] = Field(
        None, description="API key for the LLM provider."
    )
    model: Optional[str] = Field(
        None, description=""
    )

    # response_format: Literal["json", "html"] = Field()...


####################
# OUTPUT SCHEMA(S) #
####################
class CrawlerToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the crawling tool."""

    result: str = Field(description="Crawling result as string.")  # Maybe here we can change the type to a more structured one depending on response_format


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

        schema_dict = json.loads(params.schema) if isinstance(params.schema, str) else params.schema

        extraction_strategy = JsonCssExtractionStrategy(
            schema_dict,
            verbose=True
        )

        # Place the strategy in the CrawlerRunConfig
        config = CrawlerRunConfig(
            # e.g., pass js_code or wait_for if the page is dynamic
            # wait_for="css:.crypto-row:nth-child(20)"
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

        config = CrawlerRunConfig(
            js_code="document.querySelector('button.truncated-text-wiz__absolute-button').click()",
            wait_for="""
            js:() => {
                const linksSection = document.querySelector('#links-section');
                return !!(linksSection && linksSection.textContent.trim() !== '');
            }
            """,
            simulate_user=True,
            magic=True,
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

        async with AsyncWebCrawler(verbose=True) as crawler:
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

        This method creates an event loop in a separate thread to run the asynchronous operations.

        Args:
            params (CrawlerToolInputSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            CrawlerToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the base URL is not provided.
            Exception: If the request to SearxNG fails.
        """

        with ThreadPoolExecutor() as executor:
            return executor.submit(
                asyncio.run, self.run_crawler(params)
            ).result()
