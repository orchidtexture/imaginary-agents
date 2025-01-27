import os
from dotenv import load_dotenv
import instructor
import openai
from pydantic import Field, HttpUrl
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory

load_dotenv()

# Memory setup
memory = AgentMemory()

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )

class PreviousPostProvider(SystemPromptContextProviderBase):
    # should we retrieve previous posts dinamically or from a db of our own??
    def __init__(self, title):
        super().__init__(title)
        self.content_items: List[ContentItem] = []

    def get_info(self) -> str:
        return "\n\n".join(
            [
                f"Content:\n{item}\n{'-' * 80}"
                for item in enumerate(self.content_items, 1)
            ]
        )

class OperateDotFunAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the OperateDotFunAgent."""

    # question: str = Field(..., description="A post by an author that may have been contradicted by themselves in the past based on the provided context.")
    # previous_tweets: list = Field(..., description="The 3 last tweets posted by the agent.")


class OperateDotFunAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the OperateDotFunAgent."""

    tweet_content: str = Field(
        ..., 
        description="The content of the tweet to post."
        )

previous_post_provider = PreviousPostProvider(title="Previous Post")

# Create the question answering agent
operate_dot_fun_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))),
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a bold and engaging social media manager for Operate.fun.",
                "You specialize in creating hype-driven, meme-friendly content for the crypto and AI trading communities.",
                "You understand crypto culture, blockchain technology, and the dynamic nature of multichain trading.",
                "You are skilled at promoting Operate.fun's chain-agnostic, AI-powered trading solutions with confidence and creativity.",
                "You excel at fostering community engagement by balancing technical accuracy with playful, insider-like language.",
                "You know how to amplify Operate.fun’s features, such as infinite scalability, hands-free operations, and exclusive access, through concise and compelling posts.",
                "You thrive in creating engaging, trend-savvy content that resonates with crypto enthusiasts and builds FOMO."
            ],
            steps=[
                "Analyze current trends and discussions in the crypto and blockchain space to identify relevant topics.",
                "Incorporate Operate.fun's key features, such as chain-agnostic support, AI-powered trading, and infinite scalability, into the post messaging.",
                "Craft a concise, under 240 characters, engaging post using bold language, emojis, and insider crypto terms to capture attention.",
                "Include a call-to-action, such as encouraging users to visit a link, drop comments, or turn on notifications for updates.",
                "Add exclusive or FOMO-driven elements, such as mentions of gated access, access codes, or limited-time opportunities.",
                "Ensure the tone reflects your personality: confident, playful, and community-focused.",
                "Review the post for technical accuracy, proper formatting, and alignment with Operate.fun’s brand identity."
            ],
            output_instructions=[
                "Ensure each post is concise, 240 characters or less, engaging, and easy to understand. Don't repeat your previous post.",
                "Use bold language, emojis, and insider crypto terms to maintain a playful and confident tone.",
                "Incorporate Operate.fun's core messaging, highlighting features like AI-driven trading, chain-agnostic compatibility, and infinite scalability.",
                "Balance technical accuracy with an approachable, meme-friendly style.",
                "Avoid overly complex language unless it adds value to the target audience."
            ],
            context_providers={"previous_post": previous_post_provider}
        ),
        # input_schema=OperateDotFunAgentInputSchema,
        output_schema=OperateDotFunAgentOutputSchema,
    )
)
