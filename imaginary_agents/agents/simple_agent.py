import instructor
import openai
from pydantic import Field, create_model
from typing import Dict, Any, List
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator
)
from atomic_agents.agents.base_agent import (
    BaseAgent,
    BaseAgentConfig,
    BaseIOSchema
)

DEEPSEEK_API_URL = "https://api.deepseek.com"


class SimpleAgent(BaseAgent):
    """Simple Agent that receives input instructions and returns an output."""

    def __init__(
        self,
        input_schema_fields: Dict[str, Dict[str, Any]],
        output_schema_fields: Dict[str, Dict[str, Any]],
        background: List[str],
        steps: List[str],
        output_instructions: List[str],
        api_key: str = None,
        llm_provider: str = "deepseek",
        model: str = "deepseek-chat"
    ):
        """
        Initialize the SimpleAgent with dynamic schema definitions.

        Args:
            input_schema_fields: Dictionary of input fields
                {name: {type, description}}
            output_schema_fields: Dictionary of output fields
                {name: {type, description}}
            background: List of background context statements
            steps: List of steps the agent should follow
            output_instructions: List of instructions for output formatting
            api_key: OpenAI API key (defaults to env var)
            model: OpenAI model to use
        """

        # Create dynamic input and output schemas
        SimpleAgentInputSchema = create_model(
            'SimpleAgentInputSchema',
            __base__=BaseIOSchema,
            __doc__="Input schema for the SimpleAgent that defines the expected input structure.",
            **{
                name: (field_def['type'], Field(
                    ...,
                    description=field_def['description']
                ))
                for name, field_def in input_schema_fields.items()
            }
        )

        SimpleAgentOutputSchema = create_model(
            'SimpleAgentOutputSchema',
            __base__=BaseIOSchema,
            __doc__="Output schema for the SimpleAgent that defines the response structure.",
            **{
                name: (field_def['type'], Field(
                    ..., description=field_def['description']
                ))
                for name, field_def in output_schema_fields.items()
            }
        )

        if llm_provider == "deepseek":  # TODO: make multi provider dinamically
            # Create Deepseek client
            client = instructor.from_openai(
                openai.OpenAI(
                    api_key=api_key,
                    base_url=DEEPSEEK_API_URL,
                ),
                mode=instructor.Mode.MD_JSON
            )
        else:
            # Create OpenAI client
            client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        # Create agent config
        config = BaseAgentConfig(
            client=client,
            model=model,
            system_prompt_generator=SystemPromptGenerator(
                background=background,
                steps=steps,
                output_instructions=output_instructions
            ),
            input_schema=SimpleAgentInputSchema,
            output_schema=SimpleAgentOutputSchema
        )

        # Initialize base agent
        super().__init__(config)
