import logging
from typing import Optional, Dict, List, Union, Any
from datetime import datetime

import instructor
import openai

from config import settings

from beanie import Document
from pydantic import Field, ConfigDict, create_model
from atomic_agents.agents.base_agent import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInputSchema
)
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from imaginary_agents import tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

registered_tools = [  # TODO: assign dinamically perhaps from db
    {
        "tool": tools.BrowserUseTool,
        "input_schema": tools.BrowserUseToolInputSchema,
        "output_schema": tools.BrowserUseToolOutputSchema,
    },
    {
        "tool": tools.CrawlerTool,
        "input_schema": tools.CrawlerToolInputSchema,
        "output_schema": tools.CrawlerToolOutputSchema,
    }
]


class Agent(Document):
    """
    MongoDB document model for storing agent configurations
    Uses composition to create BaseAgent instances when needed
    """
    name: str = Field(..., description="Name of the agent")
    llm_model: str = Field(..., description="The identifier of the model to use")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    type: str = Field(
        default="simple",
        description="Type of agent (e.g., orchestrator, simple)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the agent"
    )
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
    tools_available: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="List of tools available to the agent"
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

    def setup_output_schema(self, tools, tools_desc):
        tool_names = []
        tool_input_schemas = []
        for tool_name, tool_info in tools.items():
            tool_names.append(tool_name)

            # Get the input schema
            input_schema = self.setup_dynamic_schema(tool_info["input_schema_fields"])
            tool_input_schemas.append(input_schema)

        # Create a Union type for tool parameters
        # For Python's typing system, we need to handle the Union differently
        # based on number of schemas
        if len(tool_input_schemas) > 1:
            # Create a Union of all input schemas
            tool_parameters_type = Union[tuple(tool_input_schemas)]
        else:
            # If there's only one schema, use it directly
            tool_parameters_type = tool_input_schemas[0]

        OrchestratorOutputSchema = create_model(
            'OrchestratorAgentOutputSchema',
            __base__=BaseIOSchema,
            __doc__="""
                Combined output schema for the Orchestrator Agent.
                Contains the tool/s to use and its parameters.
            """,
            tool=(
                str,
                Field(..., description=f"The tool to use: {tools_desc}")
            ),
            tool_parameters=(
                tool_parameters_type,  # Using Union of input schemas
                Field(..., description="The parameters for the selected tool")
            ),
        )
        logger.info("schema created")
        return OrchestratorOutputSchema

    def setup_orchestrator_config(self, tools):
        """
        Appends Tool information to background and output instructions
        """
        tools_usage = [
            f"Use the {tool_name} tool if the request matches its description: {
                tool_info['description']
            }"
            for tool_name, tool_info in tools.items()
        ]

        tools_desc = ", ".join([f"'{name}'" for name in tools.keys()])

        background = [
            (
                "You are an Orchestrator Agent that decides between using: ",
                f"{tools_desc} tools based on user input."
            )
        ]
        background.extend(tools_usage)
        output_instructions = [
            f"Analyze the input to determine whether it requires: {tools_desc}.",
            "When uncertain, don't choose any tool.",
            "Format the output using the appropriate schema.",
        ]

        return background, output_instructions, tools_desc

    async def run(
        self,
        llm_api_key: str,
        input_message: str
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
            # # 2. Dynamically create input/output schemas if defined
            # if self.input_schema_fields:
            #     try:
            #         self.validate_input_fields(input_fields)
            #     except ValueError as e:
            #         raise ValueError(
            #             f"Validation error: {str(e)}"
            #         )
            #     dynamic_input_schema = self.setup_dynamic_schema(
            #         self.input_schema_fields
            #     )
            # else:
            #     dynamic_input_schema = None

            tools = self.tools_available
            if not tools:
                raise ValueError("No tools available for this agent")

            background, output_instructions, tools_desc = self.setup_orchestrator_config(
                tools
            )

            output_schema = self.setup_output_schema(tools, tools_desc)
            logger.info(f"Output schema: {output_schema}")

            if self.background:
                background.extend(self.background)
            if self.output_instructions:
                output_instructions.extend(self.output_instructions)

            # 3. Create system prompt generator
            system_prompt_generator = SystemPromptGenerator(
                background=background,
                steps=self.steps,
                output_instructions=output_instructions
            )
            # 4. Create agent config
            config = BaseAgentConfig(
                client=client,
                model=self.llm_model,
                system_prompt_generator=system_prompt_generator,
                output_schema=output_schema
            )
            # 5. Create the agent instance
            self._agent = BaseAgent(config)
            agent_response = self._agent.run(
                BaseAgentInputSchema(chat_message=input_message)
            )
        return agent_response.dict()

    class Settings:
        name = "agents"
