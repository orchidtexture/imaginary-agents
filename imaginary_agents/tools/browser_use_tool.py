import asyncio
from steel import Steel
from pydantic import Field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class BrowserUseToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool that connects to browser-use.
    Returns a response fetched from the web.
    """

    task: str = Field(description="Task for browser-use agent.")
    llm_api_key: str = Field(description="API key for the LLM provider.")
    llm_provider: str = Field(description="LLM provider to use for extraction.")
    llm_model: str = Field(description="LLM model to use.")


####################
# OUTPUT SCHEMA(S) #
####################
class BrowserUseToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the browser-use tool."""

    result: str = Field(description="browser-use agent result as string.")


#################
# CONFIGURATION #
#################
class BrowserUseToolConfig(BaseToolConfig):
    """Configuration for the BrowserUseTool"""

    STEEL_API_KEY: Optional[str] = Field(None, description="steel.dev API key.")
    STEEL_BASE_URL: Optional[str] = Field(None, description="Base URL for Steel API.")


class BrowserUseTool(BaseTool):
    """
    Tool for running the browser-use agent based on the task.

    Attributes:
        input_schema (BrowserUseToolInputSchema): The schema for the input data.
        output_schema (BrowserUseToolOutputSchema): The schema for the output data.
    """

    input_schema = BrowserUseToolInputSchema
    output_schema = BrowserUseToolOutputSchema

    def __init__(self, config: BrowserUseToolConfig):
        """
        Initializes the BrowserUseTool.

        Args:
            config (BrowserUseToolConfig): Configuration for the tool
        """
        super().__init__(config)
        self.session = None
        self.steel_client = None

        if config.STEEL_API_KEY:
            # Initialize Steel client and create session
            self.steel_client = Steel(steel_api_key=config.STEEL_API_KEY)

            # Create Steel session to get remote browser instance for your
            # browser-use agent.
            print("Creating Steel session...")
            self.session = self.steel_client.sessions.create(
                # Uncomment and configure as needed:
                # use_proxy=True,
                # solve_captcha=True,
                # session_timeout=1800000,
                # user_agent='MyCustomUserAgent/1.0',
            )
            print(
                f"\033[1;93mSteel Session created!\033[0m\n"
                f"View session at \033[1;37m{self.session.session_viewer_url}\033[0m\n"
            )

            cdp_url = f"{
                config.STEEL_BASE_URL
            }?apiKey={config.STEEL_API_KEY}&sessionId={self.session.id}"
            self.browser = Browser(config=BrowserConfig(cdp_url=cdp_url))
        else:
            # Add local browser config
            self.browser = Browser(config=BrowserConfig())

        self.browser_context = BrowserContext(browser=self.browser)

    async def run_browser_use(
        self,
        params: BrowserUseToolInputSchema
    ) -> BrowserUseToolOutputSchema:
        """
        Runs a browser-use agent.

        Args:
            params (BrowserUseToolInputSchema): The input parameters

        Returns:
            BrowserUseToolOutputSchema: The retrieval results
        """

        # Create a ChatOpenAI model for agent reasoning
        # You can use any browser-use compatible model you want here like Anthropic,
        # Deepseek, Gemini, etc. See supported models here:
        # https://docs.browser-use.com/customize/supported-models
        model = ChatOpenAI(
            # base_url=f"{DEEPSEEK_API_URL}/v1",
            model=params.llm_model,
            temperature=0.3,
            api_key=params.llm_api_key
        )

        # Instantiate the agent
        agent = Agent(
            task=params.task,
            llm=model,
            browser=self.browser,
            browser_context=self.browser_context,
        )

        # Run the agent and handle cleanup
        try:
            history = await agent.run()
            result = history.final_result()
            print(result)
            return result
        except Exception as e:
            error_msg = f"Error: {e}"
            print(error_msg)
            return error_msg
        finally:
            # Clean up resources
            try:
                if self.browser_context:
                    await self.browser_context.close()
            except Exception as e:
                print(f"Error closing browser context: {e}")
            try:
                if self.browser:
                    await self.browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")
            try:
                if self.session and self.steel_client:
                    self.steel_client.sessions.release(self.session.id)
            except Exception as e:
                print(f"Error releasing session: {e}")

    def run(self, params: BrowserUseToolInputSchema) -> BrowserUseToolOutputSchema:
        """
        Runs the BrowserUseTool synchronously with the given parameters.

        This method creates an event loop in a separate thread to run
        the asynchronous operations.

        Args:
            params (BrowserUseToolInputSchema):
                The input parameters for the tool, adhering to the input schema.

        Returns:
            BrowserUseToolOutputSchema:
                The output of the tool, adhering to the output schema.
        """

        def run_async():
            # Create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Run the coroutine until complete
                result = loop.run_until_complete(self.run_browser_use(params))
                if result is None:
                    result = "No result returned from browser-use agent"
                return result
            finally:
                # Clean up the loop properly
                loop.close()

        with ThreadPoolExecutor() as executor:
            result = executor.submit(run_async).result()
            return BrowserUseToolOutputSchema(result=result)
