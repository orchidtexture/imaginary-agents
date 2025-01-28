import requests
from typing import Optional
from pydantic import Field

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class PumpDotFunTrendsToolInputSchema(BaseIOSchema):
    """
    Schema for input to retrieve trending memecoins info from pumpdotfun.
    Returns the execution results including stdout, stderr, and runtime metrics
    """

    # No input parameters are needed for this tool
    pass


####################
# OUTPUT SCHEMA(S) #
####################
class PumpDotFunTrendsToolOutputSchema(BaseIOSchema):
    """Schema representing the output from retrieving trending memecoins info
        from pumpdotfun"""

    success: bool = Field(
        ...,
        description="Whether the api call was successful"
    )
    trending: Optional[list] = Field(
        None, description="Trending memecoins"
    )


#################
# CONFIGURATION #
#################
class PumpDotFunTrendsToolConfig(BaseToolConfig):
    """Configuration for the PumpDotFunTrendsTool"""

    base_url: str = Field(
        default="https://frontend-api-v3.pump.fun",
        description="Base URL for the service",
    )
    timeout: int = Field(
        default=30, description="Timeout in seconds for api call"
    )


#####################
# MAIN TOOL & LOGIC #
#####################
class PumpDotFunTrendsTool(BaseTool):
    """
    Tool for retrieving a list of trending memecoins by making a GET request
        to the Pump.fun API.

    Attributes:
        input_schema (PumpDotFunTrendsToolInputSchema):
            The schema for the input data
        output_schema (PumpDotFunTrendsToolOutputSchema):
            The schema for the output data
    """

    input_schema = PumpDotFunTrendsToolInputSchema
    output_schema = PumpDotFunTrendsToolOutputSchema

    def __init__(
        self,
        config: PumpDotFunTrendsToolConfig = PumpDotFunTrendsToolConfig()
    ):
        """
        Initializes the PumpDotFunTrendsTool.

        Args:
            config (PumpDotFunTrendsToolConfig): Configuration for the tool
        """
        super().__init__(config)
        self.base_url = config.base_url
        self.timeout = config.timeout

    def run(self) -> PumpDotFunTrendsToolOutputSchema:
        """
        Retrieves a list of strings from the specified API endpoint.

        Args:
            params (PumpDotFunTrendsToolInputSchema): The input parameters

        Returns:
            PumpDotFunTrendsToolOutputSchema: The retrieval results
        """
        try:
            response = requests.get(
                f"{self.base_url}/metas/current",
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Extract the list of words
            trending = [item["word"] for item in data]

            return PumpDotFunTrendsToolOutputSchema(
                success=True,
                trending=trending
            )
        except requests.RequestException:
            return PumpDotFunTrendsToolOutputSchema(
                success=False,
                trending=None
            )
