import requests
from typing import Optional
from pydantic import Field

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class MemecoinDescriptionsToolInputSchema(BaseIOSchema):
    """
    Schema for input to retrieve descriptions of memecoins by tag on pumpdotfun
    Returns the memecoin descriptions in a string
    """

    tag: str = Field(..., description="The tag of the memecoin to search for")


####################
# OUTPUT SCHEMA(S) #
####################
class MemecoinDescriptionsToolOutputSchema(BaseIOSchema):
    """Schema representing the output from retrieving descriptions of memecoins
        by tag from pumpdotfun"""

    success: bool = Field(
        ...,
        description="Whether the api call was successful"
    )
    descriptions: Optional[str] = Field(
        ...,
        description="the descriptions of the memecoins"
    )


#################
# CONFIGURATION #
#################
class MemecoinDescriptionsToolConfig(BaseToolConfig):
    """Configuration for the MemecoinDescriptionsTool"""

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
class MemecoinDescriptionsTool(BaseTool):
    """
    Tool for descriptions of memecoins by making a GET request to the
        Pump.fun API.

    Attributes:
        input_schema (MemecoinDescriptionsToolInputSchema):
            The schema for the input data
        output_schema (MemecoinDescriptionsToolOutputSchema):
            The schema for the output data
    """

    input_schema = MemecoinDescriptionsToolInputSchema
    output_schema = MemecoinDescriptionsToolOutputSchema

    def __init__(
        self,
        config: MemecoinDescriptionsToolConfig = (
            MemecoinDescriptionsToolConfig()
        )
    ):
        """
        Initializes the MemecoinDescriptionsTool.

        Args:
            config (MemecoinDescriptionsToolConfig): Configuration for the tool
        """
        super().__init__(config)
        self.base_url = config.base_url
        self.timeout = config.timeout

    # TODO: extract the retrieval logic into a separate tool
    def run(
        self,
        params: MemecoinDescriptionsToolInputSchema
    ) -> MemecoinDescriptionsToolOutputSchema:
        """
        Retrieves memecoins descriptions by tag from pumpdotfun.

        Args:
            params (MemecoinDescriptionsToolInputSchema): The input parameters

        Returns:
            MemecoinDescriptionsToolOutputSchema: The retrieval results
        """
        try:
            endpoint = (
                f"{self.base_url}/coins?meta={params.tag}&includeNsfw=false"
            )
            response = requests.get(
                endpoint,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Extract the list of descriptions
            descriptions_list = [
                item["description"] for item in data
                if "description" in item
                and item["description"]
            ]

            descriptions = ", ".join(descriptions_list)

            return MemecoinDescriptionsToolOutputSchema(
                success=True,
                descriptions=(
                    f"Descriptions of memecoins with the tag {params.tag}, "
                    f"are: {descriptions}"
                )
            )
        except requests.RequestException as e:
            print("Error", e)
            return MemecoinDescriptionsToolOutputSchema(
                success=False,
                descriptions=None
            )
