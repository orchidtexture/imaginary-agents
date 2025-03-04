import logging
from .utils.process_AI_agent_response import process_AI_agent_response

# Logger setup
logger = logging.getLogger(__name__)

CHANNEL_ID = "-1002402928244"


def get_channel_name(bot):
    """Fetches the channel name using bot.get_chat()."""
    try:
        chat = bot.get_chat(CHANNEL_ID)  # Fetches chat info
        return chat.title  # Returns the channel name
    except Exception as e:
        logger.error(f"Failed to fetch channel name: {e}")
        return "Unknown Channel"  # Fallback if error occurs


def register_commands(agent):
    """Registers custom bot commands."""

    bot = agent.bot

    @bot.message_handler(commands=['post'])
    def ask_for_message(message):
        """Ask user what to post."""
        user_id = message.chat.id
        channel_name = get_channel_name(bot)
        bot.send_message(
            user_id,
            f"Send the message you want me to reply in *{channel_name}*."
        )
        bot.register_next_step_handler(
            message,
            post_to_channel,
            agent,
            channel_name
        )


def post_to_channel(message, agent, channel_name):
    """Post user message to channel."""
    user_message = message.text
    user_id = message.chat.id
    bot = agent.bot

    if not user_message:  # Ensure the message is not empty
        bot.send_message(user_id, "❌ Invalid message. Please try again.")
        return

    try:
        logger.info("Posting to channel")
        response = process_AI_agent_response(agent, user_id, user_message)
        bot.send_message(CHANNEL_ID, response["reply"])
        bot.send_message(
            user_id,
            f"✅ A response has been posted successfully to *{channel_name}*!"
        )
    except Exception as e:
        logger.error(f"Error posting to channel: {e}")
        bot.send_message(user_id, "❌ Failed to post in the channel.")
