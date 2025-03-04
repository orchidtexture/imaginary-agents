import os
import json
import subprocess
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Literal, Optional
import logging
from imaginary_agents.agents.simple_agent import SimpleAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/simple", tags=["Simple Agents"])

load_dotenv()

# API Key setup temporary, this should come from database
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key in the environment variable OPENAI_API_KEY."
    )


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
    type: Literal["simple", "telegram"]
    input_schema_fields: Optional[Dict[str, SchemaField]] = None
    output_schema_fields: Optional[Dict[str, SchemaField]] = None
    background: List[str]
    steps: List[str]
    output_instructions: List[str]
    input_data: Optional[Dict[str, Any]] = None
    imaginary_agents_api_key: str
    encrypted_bot_token: Optional[str] = None
    agent_name: Optional[str] = None

    @validator('input_data')
    def validate_input_data(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("input_data must be a dictionary")
        return v


@router.post("/run")
async def run_agent(config: AgentRunRequest):
    try:
        logger.info(f"Initializing agent of type: {config.type}")

        if config.type == "simple":
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
                api_key=API_KEY
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

        elif config.type == "telegram":
            logger.info("Launching Telegram bot with PM2...")

            # Use encrypted_bot_token as the unique identifier
            bot_instance_id = config.encrypted_bot_token[:32]

            if not bot_instance_id:
                raise ValueError(
                    "encrypted_bot_token is required for Telegram bots"
                )

            # Create an environment dict from scratch
            env = {
                'PYTHONUNBUFFERED': '1',  # Ensure Python output is unbuffered
                'BACKGROUND': json.dumps(config.background),
                'STEPS': json.dumps(config.steps),
                'OUTPUT_INSTRUCTIONS': json.dumps(config.output_instructions),
                'LLM_API_KEY': API_KEY,
                'ENCRYPTED_BOT_TOKEN': config.encrypted_bot_token,
                'IMAGINARY_AGENTS_API_KEY': config.imaginary_agents_api_key,
                'AGENT_NAME': config.agent_name,
                'BOT_INSTANCE_ID': bot_instance_id
            }

            try:
                # Start the bot using PM2
                process_name = f"telegram-bot-{bot_instance_id}"

                command = [
                    "pm2",
                    "start",
                    "imaginary_agents/tg_bots/telegram_agent_bot.py",
                    "--name", process_name,
                    "--interpreter", "python3"
                ]

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    env={**os.environ, **env}
                )

                # Check PM2 process status using jlist
                pm2_jlist_command = ["pm2", "jlist"]
                pm2_jlist_result = subprocess.run(
                    pm2_jlist_command,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Parse the JSON output
                processes = json.loads(pm2_jlist_result.stdout)

                # Find the process with the correct name
                process = next(
                    (p for p in processes if p["name"] == process_name), None
                )

                if process and process["pm2_env"]["status"] == "online":
                    logger.info(
                        f"Telegram bot {process_name} started with PM2"
                    )
                    return {
                        "status": "success",
                        "message": f"Telegram bot {
                            process_name
                        } started with PM2",
                        "agent_name": config.agent_name,
                        "bot_instance_id": bot_instance_id,
                        "pm2_pid": process["pid"]
                    }
                else:
                    logger.error(
                        f"Failed to start Telegram bot {
                            process_name
                        } with PM2: {result.stderr}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to start Telegram bot {
                            process_name
                        } with PM2: {result.stderr}"
                    )

            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Failed to start Telegram bot with PM2: {e.stderr}"
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to start Telegram bot with PM2: {e.stderr}"
                )
            except Exception as e:
                logger.error(f"Failed to start Telegram bot: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start Telegram bot: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Agent type '{config.type}' not implemented"
            )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions to prevent double handling
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
