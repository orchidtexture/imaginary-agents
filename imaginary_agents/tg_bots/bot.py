import logging
from imaginary_agents.helpers.encription_helper import decrypt_secret, encrypt_secret
import telebot
from typing import List
from .commands import register_commands
from .utils.process_AI_agent_response import (
    process_AI_agent_response,
    agent_memory_update
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramAgentBot:
    def __init__(
        self,
        token: str,
        agent_name: str,
        background: List[str],
        steps: List[str],
        output_instructions: List[str],
        llm_api_key: str
    ):
        self.token = token
        self.agent_name = agent_name
        self.background = background
        self.steps = steps
        self.output_instructions = output_instructions
        self.llm_api_key = llm_api_key
        self.bot = telebot.TeleBot(self.token)
        self.register_handlers()

    def register_handlers(self):
        """Register bot command handlers."""
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            self.bot.send_message(message.chat.id, "Welcome to the bot!")

        register_commands(self.bot)

        @self.bot.message_handler(func=lambda message: True)
        def reply_handler(message):
            try:
                response = process_AI_agent_response(
                    self,
                    message.chat.id,
                    message.text
                )
                self.bot.send_message(message.chat.id, response["reply"])
                agent_memory_update(
                    response["user_agent"],
                    message.chat.id,
                    response["bot_id"]
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def set_webhook(self, webhook_url: str):
        try:
            self.bot.remove_webhook()
            success = self.bot.set_webhook(webhook_url)
            if success:
                logger.info(f"Webhook set for bot: {webhook_url}")
            else:
                logger.error(f"Failed to set webhook for {webhook_url}")
        except Exception as e:
                logger.error(f"Error setting webhook: {e}")

    def remove_webhook(self):
        self.bot.remove_webhook()
        logger.info(f"Webhook removed for bot {self.token[:8]}")

    def process_webhook(self, update):
        self.bot.process_new_updates([telebot.types.Update.de_json(update)])
