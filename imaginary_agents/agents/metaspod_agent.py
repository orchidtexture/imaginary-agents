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
from imaginary_agents.context_providers import (
    TrendingMemesProvider, PreviousPostProvider
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


class MetasPodAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the MetasPodAgent."""

    trending_memes: str = Field(
        ..., description="Memes currently trending on pump.fun"
    )


class MetasPodAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the MetasPodAgent."""

    tweet_content: str = Field(
        ...,
        description="The content of the tweet to post."
        )


previous_post_provider = PreviousPostProvider(title="Previous Post")
trending_memes_provider = TrendingMemesProvider(title="Trending Memes")

# Create the question answering agent
metas_pod_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an engaging social media manager",
                "You specialize in creating hype-driven, meme-friendly content"
            ],
            steps=[
                "Read the trending memes",
                (
                    "Craft a post only using all the trending meme words ",
                    "capitalized"
                ),
                (
                    "Don't add any additional words that suggest the ",
                    "memecoin performance"
                ),
                "Add a proper emoji after each word",
                "Post it on X"
            ],
            output_instructions=[
                "Write a cryptic post only a few capitalized words"
            ],
            context_providers={
                "previous_post": previous_post_provider,
                "trending_memes": trending_memes_provider
            },
        ),
        input_schema=MetasPodAgentInputSchema,
        output_schema=MetasPodAgentOutputSchema,
    )
)
