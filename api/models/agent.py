import logging
from typing import Optional, Dict, List
from datetime import datetime

import instructor
import openai

from config import settings

from beanie import Document
from pydantic import Field, ConfigDict, create_model
from atomic_agents.agents.base_agent import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInputSchema,
    BaseAgentOutputSchema
)
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent(Document):
    """
    MongoDB document model for storing agent configurations
    Uses composition to create BaseAgent instances when needed
    """
    name: str = Field(..., description="Name of the agent")
    llm_model: str = Field(..., description="The identifier of the model to use")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    background: Optional[List[str]] = Field(
        default=None,
        description="Background context for the agent"
    )
    steps: Optional[List[str]] = Field(
        default=None,
        description="Steps the agent follows"
    )
    output_instructions: Optional[List[str]] = Field(
        default=None,
        description="Instructions for output formatting"
    )
    # Schema definitions (stored as metadata)
    input_schema_fields: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Input schema field definitions"
    )
    output_schema_fields: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Output schema field definitions"
    )
    tg_bot_token: Optional[str] = Field(
        default=None,
        description="Telegram bot token if applicable"
    )
    running: Optional[bool] = Field(
        default=False,
        description="Whether the agent is currently running"
    )

    # Non-persisted field for the agent instance (Beanie will ignore this)
    _agent: Optional[BaseAgent] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Mini Daniel",
                "llm_model": "deepseek-chat",
                "background": [
                    "You are an experienced technical project manager",
                    "You excel at organizing complex product requirements and tasks",
                    "You document everything for developing secure products"
                ],
                "steps": [
                    "Analyze the provided notes from a technical meeting",
                    "Classify and organize the topics",
                    "Create a summary to understand the decisions made in that meeting"
                ],
                "output_instructions": [
                    "You thrive on technical environments",
                    "You can create simple, comprehensive summaries"
                ],
                "input_schema_fields": {
                    "notes": {
                        "type": "str",
                        "description": "The notes from the technical meeting"
                    }
                },
                "output_schema_fields": {
                    "summary": {
                        "type": "str",
                        "description": "The summary of the technical meeting"
                    }
                },
                "tg_bot_token": "some_token"
            }
        }
    )

    def validate_input_fields(self, input_fields):
        """
        Creates Input Schema dinamically based on Agent's input_schema_fields
        and validates received input fields against it
        """

        for field_name, field_def in self.input_schema_fields.items():
            field_type_str = field_def.get("type", "str").lower()

            # Get Python type from mapping
            field_type = settings.TYPE_MAPPING.get(field_type_str, str)
            # Check if required field is present
            if field_name not in input_fields:
                raise ValueError(f"Missing required input field: {field_name}")
            # Type validation
            value = input_fields[field_name]
            if not isinstance(value, field_type):
                type_name = field_type.__name__
                raise ValueError(
                    f"Input field '{field_name}' must be a {type_name}"
                )

        return True

    def setup_dynamic_schema(self, schema_fields):
        """
        Creates Output Schema dinamically based on Agent's output_schema_fields
        """
        # Define fields for dynamic schema
        fields = {}
        annotations = {}

        for field_name, field_def in schema_fields.items():
            field_type_str = field_def.get("type", "str").lower()
            field_desc = field_def.get("description", "")

            # Get Python type from mapping
            field_type = settings.TYPE_MAPPING.get(field_type_str, str)
            # Add field to schema definition
            annotations[field_name] = field_type
            fields[field_name] = (
                field_type, Field(..., description=field_desc)
            )

        # Create dynamic input schema class
        dynamic_schema = create_model(
            'DynamicSchema',
            __base__=BaseIOSchema,
            __doc__="""
                Dynamic schema for agent input/output.
                Fields are defined based on agent's input/output schema fields.
            """,
            **fields
        )

        logger.info(f"Created dynamic schema with fields: {annotations}")
        return dynamic_schema

    async def run(
        self,
        llm_api_key: str,
        input_fields: Optional[Dict[str, any]]
    ) -> BaseAgent:
        """Run an atomic-agent instance based on Agent"""
        if not self._agent:
            # 1. Configure the client based on model
            # Support models supported by atomic-agents
            from database.database import retrieve_llm_config_by_model

            llm_config = await retrieve_llm_config_by_model(model=self.llm_model)

            client = instructor.from_openai(
                openai.OpenAI(
                    api_key=llm_api_key,
                    base_url=llm_config.base_url
                ),
                mode=instructor.Mode.MD_JSON
            )
            # 2. Dynamically create input/output schemas if defined
            if self.input_schema_fields and self.output_schema_fields:
                try:
                    self.validate_input_fields(input_fields)
                except ValueError as e:
                    raise ValueError(
                        f"Validation error: {str(e)}"
                    )
                dynamic_input_schema = self.setup_dynamic_schema(
                    self.input_schema_fields
                )
                dynamic_output_schema = self.setup_dynamic_schema(
                    self.output_schema_fields
                )
            else:
                dynamic_input_schema = None

            # 3. Create system prompt generator
            system_prompt_generator = SystemPromptGenerator(
                background=self.background,
                steps=self.steps,
                output_instructions=self.output_instructions
            )
            # 4. Create agent config
            config = BaseAgentConfig(
                client=client,
                model=self.llm_model,
                system_prompt_generator=system_prompt_generator,
                input_schema=dynamic_input_schema if dynamic_input_schema else (
                    BaseAgentInputSchema  # TODO: how it handles if no schema is defined
                ),
                output_schema=dynamic_output_schema if dynamic_output_schema else (
                    BaseAgentOutputSchema
                ),
            )
            # 5. Create the agent instance
            self._agent = BaseAgent(config)
            agent_response = self._agent.run(dynamic_input_schema(**input_fields))
        return agent_response.dict()

    class Settings:
        name = "agents"
