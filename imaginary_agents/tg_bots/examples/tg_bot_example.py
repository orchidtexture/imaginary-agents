import telebot
from atomic_agents.agents.base_agent import (
    BaseAgentInputSchema,
    BaseAgent,
    AgentMemory
)
from imaginary_agents.agents.community_manager_agent import (
    community_manager_agent_config
)

bot = telebot.TeleBot("Your bot token")

user_memory = { # User memory dump example
    "history": [
        {
            "role": "user",
            "content": {
                "class_name":
                "atomic_agents.agents.base_agent.BaseAgentInputSchema",
                "data": {"chat_message": "hi"}
            },
                "turn_id": "45a42dc7-57be-4f04-901f-96aa2d79d665"
        },
    ]
}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "GMGM")


@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    """Handles user messages with persistent memory per user."""
    print("📩 New message received")
    chat_id = message.chat.id
    user_message = message.text

    # Initialize a fresh agent for this user
    user_agent = BaseAgent(community_manager_agent_config) # TODO: change to example agent

    if user_memory is not None:
        user_agent.memory.load(user_memory)  # Load user-specific memory

    # Attempt to process the user's message
    try:
        reply = user_agent.run(
            BaseAgentInputSchema(chat_message=user_message)
        )
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        bot_reply = (
            "I'm having trouble processing your request. ",
            "Please try again later."
        )

    # Send the reply (fallback message if an error occurs)
    bot.reply_to(message, bot_reply)

    # Store the bot's response and updated memory (overwriting previous memory)
    # Dump can be stored in a DB and fetched to load next time reply_handler executes
    # memory_dump = user_agent.memory.dump()

    # Reset the memory AFTER storing it (prepares for next interaction)
    user_agent.memory = AgentMemory(max_messages=20)


if __name__ == "__main__":
    bot.infinite_polling()
