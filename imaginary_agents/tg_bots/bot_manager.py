import os
import logging
from fastapi import HTTPException
from typing import Dict, List

from imaginary_agents.tg_bots.bot import TelegramAgentBot
from imaginary_agents.tg_bots.db import (
    bot_registry_collection,
    bot_users_collection
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                    # print(doc)
                    token = doc["token"]
                    bot_id = doc["_id"]
                    agent_id = doc["agent_id"]
                    agent_name = doc.get("agent_name")
                    background = doc.get("background")
                    steps = doc.get("steps")
                    output_instructions = doc.get("output_instructions")
                    llm_api_key = doc.get("llm_api_key")
                    self.bot_configs[token] = {
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "background": background,
                        "steps": steps,
                        "output_instructions": output_instructions,
                        "llm_api_key": llm_api_key
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
                    "agent_id": config["agent_id"],
                    "token": token,
                    "agent_name": config["agent_name"],
                    "background": config["background"],
                    "steps": config["steps"],
                    "output_instructions": config["output_instructions"],
                    "llm_api_key": config["llm_api_key"],
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
        return f"{public_url}/api/v1/bots/telegram/webhook/{token}"

    def start_bot(
        self, 
        agent_id: str,
        token: str,
        agent_name: str, 
        background: List[str],
        steps: List[str], 
        output_instructions: List[str],
        llm_api_key: str,
        ):
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
                output_instructions,
                llm_api_key
            )
            self.bot_registry[token] = bot_instance
            self.bot_configs[token] = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "background": background,
                "steps": steps,
                "output_instructions": output_instructions,
                "llm_api_key": llm_api_key,
            }
            self._save_registry(True)
            webhook_url = self.get_webhook_url(token)
            bot_instance.set_webhook(webhook_url)
            return {
                "message": f"Bot started with webhook set to {webhook_url}"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def stop_bot(self, agent_id: str):
        bot = self.collection.find_one({"agent_id": agent_id})
        token = bot.get("token")
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

    def get_bot(self, agent_id: str):
        bot = self.collection.find_one({"agent_id": agent_id})
        token = bot.get("token")
        running_bots = bot_manager.list_bots()
        if token in running_bots["running_bots"]:
            return {"running": True}
        else:
            return {"running": False}

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
                config["llm_api_key"],
            )
        return self.bot_registry[token]


bot_manager = BotManager()
