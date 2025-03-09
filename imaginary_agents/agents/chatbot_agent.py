import instructor
import openai
from typing import List
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator
)
from atomic_agents.agents.base_agent import BaseAgentConfig, BaseAgent


class ChatbotAgent(BaseAgent):
    """Agent that interacts with the user through a chatbot interface."""

    def __init__(
        self,
        background: List[str],
        steps: List[str],
        output_instructions: List[str],
        llm_api_key: str = None,
        model: str = "gpt-4"
    ):
        """
        Initialize the SimpleAgent with dynamic schema definitions.

        Args:
            background: List of background context statements
            steps: List of steps the agent should follow
            output_instructions: List of instructions for output formatting
            llm_api_key: OpenAI API key (defaults to env var)
            model: OpenAI model to use
        """

        # API key handling
        if not llm_api_key:
            raise ValueError(
                "API key must be provided"
            )

        # Create OpenAI client
        client = instructor.from_openai(
            openai.OpenAI(api_key=llm_api_key)
        )

        # Create agent config
        config = BaseAgentConfig(
            client=client,
            model=model,
            system_prompt_generator=SystemPromptGenerator(
                background=background,
                steps=steps,
                output_instructions=output_instructions
            )
        )

        # Initialize base agent
        super().__init__(config)
