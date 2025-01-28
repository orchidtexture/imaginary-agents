import os
from dotenv import load_dotenv
import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import (
    BaseIOSchema,
    BaseAgent,
    BaseAgentConfig
)
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator
)

load_dotenv()

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable"
        "or in the environment variable OPENAI_API_KEY."
    )


class MemecoinLoreAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the MemecoinLoreAgent."""

    descriptions: str = Field(
        ..., description="The descriptions of the memecoins."
    )


class MemecoinLoreAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the MemecoinLoreAgent."""

    lore: str = Field(
        ...,
        description="The generated lore of the memecoins."
        )


# Create the question answering agent
memecoin_lore_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a creative, bold writer that creates memecoin lore",
                "You understand crypto culture",
                "You know how to create memes based on the current trends."
            ],
            steps=[
                "Read a series of descriptions created by devs that launch memecoins.",
                "Use the descriptions to create a lore for the meme that is engaging.",
                # "Make the lore around 500 characters max"
            ],
            output_instructions=[
                "Incorporate playful, meme-friendly language.",
            ],
        ),
        input_schema=MemecoinLoreAgentInputSchema,
        output_schema=MemecoinLoreAgentOutputSchema,
    )
)
