import logging
from typing import Optional, Dict, List
from datetime import datetime

# import instructor
# import openai

from beanie import Document
from pydantic import Field, ConfigDict
from atomic_agents.agents.base_agent import BaseAgent
# from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

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

    def run_agent(self) -> BaseAgent:
        """Run an atomic-agent instance based on Agent"""
        if not self._agent:
            # 1. Configure the client based on model
            # Support models supported by atomic-agents
            # According to model selected:
            # # api_key comes from user config
            # # base_url comes from LLMConfig
            from database.database import retrieve_llm_config
            llm_config = retrieve_llm_config(model=self.llm_model)
            logger.info(llm_config)
            # client = instructor.from_openai(
            #     openai.OpenAI(api_key=self.llm_api_key, base_url=llm_config.base_url),
            #     mode=instructor.Mode.MD_JSON
            # )
            # 2. Dynamically create input/output schemas if defined
            # 3. Create system prompt generator
            # 4. Create agent config
            # 5. Create the agent instance
        return self._agent

    class Settings:
        name = "agents"
