import telebot
import os
# import time
# import schedule
from dotenv import load_dotenv

from atomic_agents.agents.base_agent import BaseAgentInputSchema, BaseAgent
from imaginary_agents.agents.operate_dot_fun import (
    operate_dot_fun_agent,
    OperateDotFunAgentInputSchema,
    previous_post_provider,
    trending_memes_provider
)
from imaginary_agents.agents.memecoin_lore_agent import (
    memecoin_lore_agent,
    MemecoinLoreAgentInputSchema
)
from imaginary_agents.tools.pump_dot_fun_trends_tool import (
    PumpDotFunTrendsTool
)
from imaginary_agents.tools.memecoin_descriptions_tool import (
    MemecoinDescriptionsTool,
    MemecoinDescriptionsToolInputSchema
)
from imaginary_agents.agents.community_manager_agent import (
    community_manager_agent_config
)

# Load environment variables from the .env file
load_dotenv()

# Get the token and channel ID from the environment variables
API_TOKEN = os.getenv("TELEBOT_API_TOKEN")
CHANNEL_ID = os.getenv("OPERATE_DOT_FUN_DEVS_CHANNEL_ID")

if not API_TOKEN:
    raise ValueError("No TELEBOT_API_TOKEN found in .env file")
if not CHANNEL_ID:
    raise ValueError("No OPERATE_DOT_FUN_DEVS_CHANNEL_ID found in .env file")

bot = telebot.TeleBot(API_TOKEN)

trending_memecoin_tool = PumpDotFunTrendsTool()
memecoin_descriptions_tool = MemecoinDescriptionsTool()


# Define a handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⏰ Time to OPERATE")


# Define a handler for other text messages
@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    community_manager_agent = BaseAgent(community_manager_agent_config)
    reply = community_manager_agent.run(
        BaseAgentInputSchema(chat_message=message.text)
    )
    bot.reply_to(message, reply.chat_message)
    dump_last_20_messages(message.chat.id)


def post_to_channel(message):
    """Post a message to the specified channel."""
    try:
        bot.send_message(CHANNEL_ID, message)
        print(f"Message posted successfully: {message}")
    except Exception as e:
        print(f"Error posting message: {e}")


def create_post_with_agent():
    """Generate content using agents."""
    try:
        # Retrieve trending memecoins
        trending_memes = trending_memecoin_tool.run()
        # Generate memecoin lore
        memecoin_descriptions_tool_output = memecoin_descriptions_tool.run(
            MemecoinDescriptionsToolInputSchema(tag=trending_memes.trending[0])
        )
        # Pass to memecoin_lore_agent
        memecoin_lore_agent_output = memecoin_lore_agent.run(
            MemecoinLoreAgentInputSchema(
                descriptions=memecoin_descriptions_tool_output.descriptions
            )
        )

        print(f"{'-'*80}")
        print(f"Lore for {trending_memes.trending[0]}")
        print(memecoin_lore_agent_output.lore)
        print(f"{'-'*80}")

        # Generate final post content
        operate_dot_fun_output = operate_dot_fun_agent.run(
            OperateDotFunAgentInputSchema(
                meme_lore=memecoin_lore_agent_output.lore
            )
        )

        # Update providers
        previous_post_provider.content_items.append(
            operate_dot_fun_output.tweet_content
        )
        trending_memes_provider.memes = trending_memes.trending

        return operate_dot_fun_output.tweet_content

    except Exception as e:
        print(f"Error: {str(e)}")
        return (
            "⚠️ Unable to generate post content. "
            "Please check logs for details."
        )


# Function to be run every 10 minutes
def channel_post():
    """Generate content and post it to the channel."""
    content = create_post_with_agent()
    if content:
        post_to_channel(content)


def dump_last_20_messages(chat_id):
    """Fetch and print the last 20 messages for a specific chat."""
    try:
        updates = bot.get_updates()
        messages = [
            update.message for update in updates if update.message
            and update.message.chat.id == chat_id
        ]
        last_20_messages = messages[-20:]
        for msg in last_20_messages:
            print(f"Chat ID: {msg.chat.id}, Message: {msg.text}")
    except Exception as e:
        print(f"Error fetching chat history: {e}")


if __name__ == "__main__":
    # channel_post()  # Post first at start
    # # Schedule the periodic post every 10 seconds
    # schedule.every(10).minutes.do(channel_post)

    # # Run the schedule in a loop
    # print("Starting scheduled posting every 10 minutes...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)  # Sleep for 1 second to prevent high CPU usage

    # Start polling for new messages
    bot.infinity_polling()
