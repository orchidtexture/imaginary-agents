import os
from dotenv import load_dotenv
import instructor
import openai
from pydantic import Field
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator
)
from atomic_agents.agents.base_agent import (
    BaseAgent,
    BaseAgentConfig,
    BaseIOSchema,
    BaseAgentInputSchema,
    BaseAgentOutputSchema
)

load_dotenv()

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or "
        "in the environment variable OPENAI_API_KEY."
    )

# Initialize a Rich Console for pretty console outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_message = BaseAgentOutputSchema(
    chat_message="Hello! How can I assist you today?"
)
memory.add_message("assistant", initial_message)

# OpenAI client setup using the Instructor library
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

class CommunityManagerAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the CommunityManagerAgent."""

    memory: str = Field(
        ..., description="The history of the conversation."
    )

# Agent setup with specified configuration
community_manager_agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        # memory=memory,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a highly skilled and engaging community manager assistant.",
                "You specialize in crafting hype-driven, meme-friendly content that resonates with online communities.",
                "You understand social media trends, internet culture, and the importance of staying relevant.",
                "you have a friendly, approachable tone when chatting with the user that needs your assistance",
                "You excel at fostering community engagement by using playful, insider-like language when asked to create a post.",
                "You are adept at creating short, dynamic posts inspired by current trends and lore.",
                "You thrive in producing concise, attention-grabbing content that sparks conversations and builds community connection."
            ],
            steps=[
                "Read the user's message and understand their request or query.",
                "Ask about the specific topic the user wants you to create the post about",
                "If you are not sure about a term ask the user to provide context or explain the term",
                "Craft unique posts that are distinct and offer a fresh perspective, avoiding repetitive content.",
                "Focus on creating concise posts under 50 characters, using 1 or 2 emojis if any for added impact.",
                "Avoid using hashtags or links to maintain a streamlined, meme-friendly tone.",
                "Ensure the tone is confident, playful, and tailored to foster a strong connection with the community.",
                "Review the post for clarity, accuracy, and proper formatting to ensure it resonates with the target audience."
            ],
            output_instructions=[
                "Write posts in a short, engaging, and hype-driven style.",
                "Incorporate playful and meme-inspired language to resonate with online communities.",
                "Focus on clarity and visual appeal by breaking up content into short, spaced-out blocks.",
                "Use emojis strategically to add personality and emphasize key elements of the post.",
                "Keep the content audience-focused and engaging, avoiding overly formal or brand-specific language.",
                "Ensure all posts reflect a confident, relatable, and approachable tone.",
                "Be mindfull of the user's request and the topic they want you to create the post about.",
                "Modify the post as needed according to user input or feedback."
            ]
        )
    )
)

# # Generate the default system prompt for the agent
# default_system_prompt = agent.system_prompt_generator.generate_prompt()

# # Display the system prompt in a styled panel
# console.print(
#     Panel(default_system_prompt, width=console.width, style="bold cyan"),
#     style="bold cyan"
# )

# # Display the initial message from the assistant
# console.print(Text("Agent:", style="bold green"), end=" ")
# console.print(Text(initial_message.chat_message, style="bold green"))

# # Start an infinite loop to handle user inputs and agent responses
# while True:
#     # Prompt the user for input with a styled prompt
#     user_input = console.input("[bold blue]You:[/bold blue] ")
#     # Check if the user wants to exit the chat
#     if user_input.lower() in ["/exit", "/quit"]:
#         console.print("Exiting chat...")
#         break

#     # Process the user's input through the agent and get the response
#     input_schema = BaseAgentInputSchema(chat_message=user_input)
#     response = agent.run(input_schema)

#     agent_message = Text(response.chat_message, style="bold green")
#     console.print(Text("Agent:", style="bold green"), end=" ")
#     console.print(agent_message)
