from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Optional
import logging
from imaginary_agents.agents.simple_agent import SimpleAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/simple", tags=["Simple Agents"])


class SchemaField(BaseModel):
    type: str  # Type name as string ("str", "int", etc.)
    description: str

    def get_python_type(self) -> type:
        """Convert string type name to Python type."""
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list
        }
        return type_mapping.get(self.type, str)  # default to str if type not found


class AgentRunRequest(BaseModel):
    input_schema_fields: Optional[Dict[str, SchemaField]] = None
    output_schema_fields: Optional[Dict[str, SchemaField]] = None
    background: List[str]
    steps: List[str]
    output_instructions: List[str]
    input_data: Optional[Dict[str, Any]] = None
    agent_name: Optional[str] = None
    llm_api_key: str
    llm_provider: str
    llm_model: str

    @validator('input_data')
    def validate_input_data(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("input_data must be a dictionary")
        return v


@router.post("/run")
async def run_agent(config: AgentRunRequest):
    try:
        logger.info("Running agent")

        if not config.input_schema_fields or not config.output_schema_fields:
            raise ValueError(
                "Simple agent requires input and output schema fields"
            )

        # Convert schema fields to the format SimpleAgent expects
        input_fields = {
            name: {
                "type": field.get_python_type(),
                "description": field.description
            }
            for name, field in config.input_schema_fields.items()
        }
        output_fields = {
            name: {
                "type": field.get_python_type(),
                "description": field.description
            }
            for name, field in config.output_schema_fields.items()
        }

        agent = SimpleAgent(
            input_schema_fields=input_fields,
            output_schema_fields=output_fields,
            background=config.background,
            steps=config.steps,
            output_instructions=config.output_instructions,
            api_key=config.llm_api_key,
            llm_provider=config.llm_provider,
            model=config.llm_model
        )

        # Validate input data against dynamic schema
        if config.input_data:
            try:
                input_instance = agent.input_schema(**config.input_data)
                response = agent.run(input_instance)
                return response.dict()
            except Exception as e:
                raise ValueError(f"Invalid input data: {str(e)}")
        else:
            return {
                "message": "Agent initialized successfully, but no input data provided."
            }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions to prevent double handling
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
