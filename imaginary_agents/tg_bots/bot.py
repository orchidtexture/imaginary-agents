import os
import logging
import telebot
from typing import List
from imaginary_agents.agents.chatbot_agent import ChatbotAgent
from atomic_agents.agents.base_agent import (
    BaseAgentInputSchema,
    # AgentMemory
)
from imaginary_agents.tg_bots.db import (
    bot_registry_collection,
    bot_users_collection
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_API_KEY = os.getenv("LLM_API_KEY")


class TelegramAgentBot:
    def __init__(
        self,
        token: str,
        agent_name: str,
        background: List[str],
        steps: List[str],
        output_instructions: List[str]
    ):
        self.token = token
        self.agent_name = agent_name
        self.background = background
        self.steps = steps
        self.output_instructions = output_instructions
        self.bot = telebot.TeleBot(self.token)
        self.register_handlers()

    def process_AI_agent_response(self, chat_id, user_message):
        """Handles AI-based message processing."""

    # # Determine bot_id by either fetching directly from the DB in
    # # development or using in-memory config
    # # (the latter would be managed by bot_manager)
    # if os.getenv("DEVELOPMENT", "false").lower() in ("true", "1", "yes"):
    #     # In development mode, query the DB directly.
    #     config_doc = bot_registry_collection.find_one({"token": self.token})
    #     bot_id = config_doc.get("_id") if config_doc else None
    #     logger.info(
    #         f"Fetched bot_id from DB in development mode: {bot_id}"
    #     )
    # else:
    #     from imaginary_agents.tg_bots.bot_manager_v2 import bot_manager
    #     # Attempt to get bot_id from in-memory registry first.
    #     bot_config = bot_manager.bot_configs.get(self.token, {})
    #     bot_id = bot_config.get("bot_id")
    #     if not bot_id:
    #         # Fallback to querying the DB if bot_id is not found in memory.
    #         config_doc = bot_registry_collection.find_one(
    #             {"token": self.token}
    #         )
    #         bot_id = config_doc.get("_id") if config_doc else None

        # Initialize AI agent, possibly passing bot_memory if desired.
        user_agent = ChatbotAgent(
            background=self.background,
            steps=self.steps,
            output_instructions=self.output_instructions,
            llm_api_key=LLM_API_KEY
        )
        config_doc = bot_registry_collection.find_one({"token": self.token})
        bot_id = config_doc.get("_id") if config_doc else None

        # Fetch stored user memory from the bot_users collection using bot_id.
        record = bot_users_collection.find_one({
            "bot_id": bot_id,
            "telegram_user_id": chat_id
        })
        bot_memory = record.get("bot_memory")

        if bot_memory is not None:
            user_agent.memory.load(bot_memory)
            print(f"Memory loaded for user {chat_id}")

        # Run AI agent
        try:
            print("running agent")
            reply = user_agent.run(
                BaseAgentInputSchema(chat_message=user_message)
            )
            bot_reply = reply.chat_message
        except Exception as e:
            print(f"AI Error: {e}")
            bot_reply = (
                "I'm having trouble processing your request. ",
                "Please try again later."
            )

        self.bot.send_message(chat_id, bot_reply)

        # Store updated memory
        memory_dump = user_agent.memory.dump()

        # Update the bot_memory in the database for this user
        result = bot_users_collection.update_one(
            {"bot_id": bot_id, "telegram_user_id": chat_id},
            {"$set": {"bot_memory": memory_dump}},
            upsert=True
        )
        logger.info(f"Update result: {result.raw_result}")

        # Re-read the document to verify the update
        record_after = bot_users_collection.find_one({
            "bot_id": bot_id,
            "telegram_user_id": chat_id
        })
        logger.info(f"Record after update: {record_after}")

        # # Reset agent memory for future interactions
        # user_agent.memory = AgentMemory(max_messages=20)

    def register_handlers(self):
        """Register bot command handlers."""
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            self.bot.send_message(message.chat.id, "Welcome to the bot!")

        @self.bot.message_handler(func=lambda message: True)
        def reply_handler(message):
            try:
                self.process_AI_agent_response(message.chat.id, message.text)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def set_webhook(self, webhook_url: str):
        self.bot.remove_webhook()
        success = self.bot.set_webhook(webhook_url)
        if success:
            logger.info(f"Webhook set for bot: {webhook_url}")
        else:
            logger.error(f"Failed to set webhook for {webhook_url}")

    def remove_webhook(self):
        self.bot.remove_webhook()
        logger.info(f"Webhook removed for bot {self.token[:8]}")

    def process_webhook(self, update):
        self.bot.process_new_updates([telebot.types.Update.de_json(update)])
