from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Literal
import logging
from imaginary_agents.agents.simple_agent import SimpleAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agents"])


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
        return type_mapping.get(self.type, str)
        # default to str if type not found


class AgentRunRequest(BaseModel):
    type: Literal["simple"]  # Add more types as needed
    input_schema_fields: Dict[str, SchemaField]
    output_schema_fields: Dict[str, SchemaField]
    background: List[str]
    steps: List[str]
    output_instructions: List[str]
    input_data: Dict[str, Any]

    @validator('input_data')
    def validate_input_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError("input_data must be a dictionary")
        return v


@router.post("/run")
async def run_agent(config: AgentRunRequest):
    try:
        logger.info(f"Initializing agent of type: {config.type}")

        if config.type == "simple":
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
                output_instructions=config.output_instructions
            )

            # Validate input data against dynamic schema
            try:
                input_instance = agent.input_schema(**config.input_data)
            except Exception as e:
                raise ValueError(f"Invalid input data: {str(e)}")

            response = agent.run(input_instance)
            return response.dict()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Agent type '{config.type}' not implemented"
            )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
