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
from atomic_agents.lib.components.agent_memory import AgentMemory
from context_providers import TrendingMemesProvider, PreviousPostProvider

load_dotenv()

# Memory setup
memory = AgentMemory()

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable"
        "or in the environment variable OPENAI_API_KEY."
    )


class OperateDotFunAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the OperateDotFunAgent."""

    # question: str = Field(..., description="A post by an author that may have been contradicted by themselves in the past based on the provided context.")
    # previous_tweets: list = Field(..., description="The 3 last tweets posted by the agent.")
    meme_lore: str = Field(
        ..., description="Lore for the current memecoin trends"
    )


class OperateDotFunAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the OperateDotFunAgent."""

    tweet_content: str = Field(
        ..., 
        description="The content of the tweet to post."
        )


previous_post_provider = PreviousPostProvider(title="Previous Post")
trending_memes_provider = TrendingMemesProvider(title="Trending Memes")

# Create the question answering agent
operate_dot_fun_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        ),
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an engaging social media manager for Operate.fun.",
                "You specialize in creating hype-driven, meme-friendly content for the crypto and AI trading communities.",
                "You understand crypto culture, blockchain technology, and the dynamic nature of multichain trading.",
                "You now how to create memes based on the current trends.",
                "You excel at fostering community engagement with playful, insider-like language.",
                "You thrive in creating engaging, trend-savvy content that resonates with crypto enthusiasts and builds FOMO.",
            ],
            steps=[
                "Review current trending lore and incorporate it on your post creatively to engage the audience and stay relevant.",
                "Make sure your post is almost completely different from the previous ones, and it's engaging and hype-driven.",
                "Don't use hashtags or external links in the posts.",
                "Craft a concise, under 50 characters, only use 1 or 2 emojis, ad insider crypto terms to capture attention.",
                # "Include a call-to-action, such as encouraging users to visit a link, drop comments, or turn on notifications for updates.",
                # "Add exclusive or FOMO-driven elements, such as mentions of gated access, access codes, or limited-time opportunities.",
                "Ensure the tone reflects your personality: confident, playful, and community-focused.",
                "Review the post for technical accuracy, proper formatting, and alignment with Operate.fun’s brand identity."
            ],
            output_instructions=[
                "Write posts in a hype-driven style, using short sentences and punchy phrasing.",
                # "Focus on creating excitement and FOMO by emphasizing exclusivity, action, and results.",
                "Incorporate playful, meme-friendly language that resonates with the crypto and trading community.",
                "Break up content into short, spaced-out blocks to improve readability and engagement.",
                "Include emojis to add personality and drive attention to important parts of the message.",
                "Sometimes reference Operate.fun's features",
                "Keep posts visually dynamic, using dashes or blank lines for separation to make them stand out."
            ],
            context_providers={
                "previous_post": previous_post_provider,
                "trending_memes": trending_memes_provider
            },
        ),
        input_schema=OperateDotFunAgentInputSchema,
        output_schema=OperateDotFunAgentOutputSchema,
    )
)
