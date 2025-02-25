import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from pydantic import BaseModel


from imaginary_agents.tg_bots.bot import TelegramAgentBot
from imaginary_agents.tg_bots.db import (
    bot_registry_collection,
    bot_users_collection
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Imaginary Agents Bot API",
    description="API for interacting with various AI agent Bots",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BotStartRequest(BaseModel):
    agent_name: str
    background: List[str]
    steps: List[str]
    output_instructions: List[str]


class BotManager:
    def __init__(self):
        self.bot_registry: Dict[str, TelegramAgentBot] = {}
        self.bot_configs: Dict[str, dict] = {}
        self.collection = bot_registry_collection
        self.users_collection = bot_users_collection
        self._load_registry()

    def _load_registry(self):
        try:
            docs = self.collection.find({})
            for doc in docs:
                if doc["isRunning"] is True:
                    token = doc["token"]
                    bot_id = doc["_id"]
                    agent_name = doc.get("agent_name")
                    background = doc.get("background")
                    steps = doc.get("steps")
                    output_instructions = doc.get("output_instructions")
                    self.bot_configs[token] = {
                        "bot_id": bot_id,
                        "agent_name": agent_name,
                        "background": background,
                        "steps": steps,
                        "output_instructions": output_instructions
                    }
                    bot_instance = self.get_bot_instance(token)
                    self.bot_registry[token] = bot_instance
            logger.info(
                "Loaded %d bot configurations from MongoDB",
                len(self.bot_configs)
            )
        except Exception as e:
            logger.error(
                "Failed to load bot configurations from MongoDB: %s",
                e
            )

    def _save_registry(self, isRunning):
        try:
            for token, config in self.bot_configs.items():
                data = {
                    "token": token,
                    "agent_name": config["agent_name"],
                    "background": config["background"],
                    "steps": config["steps"],
                    "output_instructions": config["output_instructions"],
                    "isRunning": isRunning
                }
                logger.info("Saving bot configuration to MongoDB: %s", data)
                result = self.collection.find_one_and_update(
                    {"token": token},
                    {"$set": data},
                    upsert=True,
                    return_document=True
                )
                if result:
                    self.bot_configs[token]["bot_id"] = result["_id"]
            logger.info(
                "Saved %d bot configurations to MongoDB",
                len(self.bot_configs)
            )
        except Exception as e:
            logger.error("Failed to save bot configurations to MongoDB: %s", e)

    def get_webhook_url(self, token: str) -> str:
        public_url = os.getenv("PUBLIC_URL")
        if not public_url:
            raise ValueError("PUBLIC_URL must be set in .env file")
        return f"{public_url}/bots/telegram/webhook/{token}"

    def start_bot(self, token: str, agent_name: str, background: List[str],
                  steps: List[str], output_instructions: List[str]):
        if token in self.bot_registry and self.bot_registry[token] is not None:
            raise HTTPException(
                status_code=400,
                detail="Bot is already running."
            )
        try:
            bot_instance = TelegramAgentBot(
                token,
                agent_name,
                background,
                steps,
                output_instructions
            )
            self.bot_registry[token] = bot_instance
            self.bot_configs[token] = {
                "agent_name": agent_name,
                "background": background,
                "steps": steps,
                "output_instructions": output_instructions,
            }
            self._save_registry(True)
            webhook_url = self.get_webhook_url(token)
            bot_instance.set_webhook(webhook_url)
            return {
                "message": f"Bot started with webhook set to {webhook_url}"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def stop_bot(self, token: str):
        if token not in self.bot_registry or self.bot_registry[token] is None:
            raise HTTPException(status_code=404, detail="Bot not found.")
        try:
            self._save_registry(False)  # Update isRunning before del registry
            bot_instance = self.bot_registry[token]
            bot_instance.remove_webhook()
            del self.bot_registry[token]
            del self.bot_configs[token]
        except Exception as e:
            raise HTTPException(status_code=409, detail=str(e))
        return {"message": "Bot stopped and webhook removed."}

    def list_bots(self):
        return {"running_bots": list(self.bot_configs.keys())}

    def get_bot_instance(self, token: str) -> TelegramAgentBot:
        if token not in self.bot_configs:
            raise HTTPException(
                status_code=404, detail="Bot configuration not found."
            )
        if self.bot_registry.get(token) is None:
            config = self.bot_configs[token]
            self.bot_registry[token] = TelegramAgentBot(
                token,
                config["agent_name"],
                config["background"],
                config["steps"],
                config["output_instructions"],
            )
        return self.bot_registry[token]


bot_manager = BotManager()


@app.post("/bots/telegram/start_bot/{token}")
def start_bot(token: str, req: BotStartRequest):
    return bot_manager.start_bot(
        token,
        agent_name=req.agent_name,
        background=req.background,
        steps=req.steps,
        output_instructions=req.output_instructions
    )


@app.post("/bots/telegram/stop_bot/{token}")
def stop_bot(token: str):
    return bot_manager.stop_bot(token)


@app.get("/bots/telegram/list_bots")
def list_bots():
    return bot_manager.list_bots()


@app.get("/bots/telegram/get_bot_status/{token}")
def bot_status(token: str):
    running_bots = bot_manager.list_bots()
    if token in running_bots["running_bots"]:
        return {"running": True}
    else:
        return {"running": False}


@app.post("/bots/telegram/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token not in bot_manager.bot_configs:
        raise HTTPException(status_code=404, detail="Bot not found.")
    update = await request.json()
    chat_id = update.get("message", {}).get("chat", {}).get("id")
    if chat_id:
        bot_id = bot_manager.bot_configs[token].get("bot_id")
        if bot_id:
            bot_manager.users_collection.update_one(
                {"bot_id": bot_id, "telegram_user_id": chat_id},
                {"$set": {
                    "bot_id": bot_id,
                    "telegram_user_id": chat_id
                }},
                upsert=True
            )
    bot_instance = bot_manager.get_bot_instance(token)
    bot_instance.process_webhook(update)
    return {"status": "ok"}


@app.get("/bots/telegram/bot_details/{token}")
def bot_details(token: str):
    if token not in bot_manager.bot_configs:
        raise HTTPException(status_code=404, detail="Bot not found.")
    bot_instance = bot_manager.get_bot_instance(token)
    webhook_url = bot_manager.get_webhook_url(token)
    return {
        "token": token[:8],
        "isRunning": True,  # If bot exists in bot_configs, it is running
        "webhook_url": webhook_url,
        "agent_name": bot_instance.agent_name,
        "background": bot_instance.background,
        "steps": bot_instance.steps,
        "output_instructions": bot_instance.output_instructions,
    }
