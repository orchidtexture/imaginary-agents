import os
import json
import hashlib
import base64
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from pymongo import MongoClient
from pymongo.collection import ObjectId
from pymongo.errors import DuplicateKeyError

# Load environment variables
load_dotenv()


class ChatBotDBManager:
    """
        Handles MongoDB interactions for chatbot user memory across platforms.
    """

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[os.getenv("MONGO_DB_NAME", "imaginary_agents")]
        self.users_collection = self.db["users"]  # Platform users
        self.chatbots_collection = self.db["chatbots"]  # Chatbots
        # Ensure unique index on bot_name and owner_id
        self.chatbots_collection.create_index(
            [("bot_name", 1), ("owner_id", 1)], 
            unique=True
        )
        self.chatbot_users_collection = self.db["chatbot_users"]

    @staticmethod
    def encrypt_bot_token(token: str, key: str) -> str:
        """Encrypts the bot token using AES encryption."""
        key = hashlib.sha256(key.encode()).digest()  # Derive AES key
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt_bot_token(encrypted_token: str, key: str) -> str:
        """Decrypts the bot token using AES encryption."""
        key = hashlib.sha256(key.encode()).digest()  # Derive AES key
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.decrypt(encrypted_token.encode()).decode()

    def register_user(self, api_key: str):
        """Registers a platform user."""
        user = self.users_collection.find_one({"api_key": api_key})
        if user:
            return user["_id"]  # Return existing user_id

        user_entry = {
            "api_key": api_key,
            "chatbot_ids": []
        }
        result = self.users_collection.insert_one(user_entry)
        return result.inserted_id  # Return new user _id

    def register_chatbot(
        self, bot_name: str,
        platform: str,
        owner_id: str,
        encrypted_token: str
    ):
        """Registers a chatbot and ensures it exists in the database."""
        try:
            bot_entry = {
                "bot_name": bot_name,
                "platform": platform,
                "owner_id": ObjectId(owner_id),
                "encrypted_bot_token": encrypted_token,
                "chatbot_users_ids": []  # Empty initially
            }
            result = self.chatbots_collection.insert_one(bot_entry)

            # Link chatbot to user
            self.users_collection.update_one(
                {"_id": ObjectId(owner_id)},
                {"$push": {"chatbot_ids": result.inserted_id}}
            )
            return result.inserted_id  # Return new chatbot _id
        except DuplicateKeyError:
            chatbot = self.chatbots_collection.find_one(
                {"bot_name": bot_name, "owner_id": ObjectId(owner_id)}
            )
            return chatbot["_id"]  # Return existing chatbot_id

    def register_chatbot_user(self, telegram_user_id: int, chatbot_id: str):
        """Registers a Telegram user under a chatbot."""
        chatbot_user = self.chatbot_users_collection.find_one(
            {"telegram_user_id": telegram_user_id}
        )
        if chatbot_user:
            return chatbot_user["_id"]  # Return existing chatbot_user_id

        user_entry = {
            "telegram_user_id": telegram_user_id,
            "bot_memories": None  # Empty memory initially
        }
        result = self.chatbot_users_collection.insert_one(user_entry)

        # Link chatbot_user to chatbot
        self.chatbots_collection.update_one(
            {"_id": ObjectId(chatbot_id)},
            {"$addToSet": {"chatbot_users_ids": result.inserted_id}}
        )
        return result.inserted_id  # Return new chatbot_user _id

    def link_chatbot_user(self, chatbot_id: str, chatbot_user_id: str):
        """
            Links a chatbot user to a chatbot by adding their ID to
             chatbot_users_ids array.
        """
        self.chatbots_collection.update_one(
            {"_id": ObjectId(chatbot_id)},
            {"$addToSet": {
                "chatbot_users_ids": ObjectId(chatbot_user_id)
            }}  # Prevents duplicates
        )

    def get_bot_by_id(self, chatbot_id: str):
        """Retrieves bot details using _id."""
        return self.chatbots_collection.find_one({"_id": ObjectId(chatbot_id)})

    def get_bot_token(self, chatbot_id: str, key: str) -> str:
        """Retrieves and decrypts the bot token for a chatbot."""
        bot = self.get_bot_by_id(chatbot_id)
        if bot and "encrypted_bot_token" in bot:
            return self.decrypt_bot_token(bot["encrypted_bot_token"], key)
        return None

    def store_user_memory(self, telegram_user_id: int, memory_dump: dict):
        """Stores or updates a user's memory."""
        memory_json = json.dumps(memory_dump)  # Convert to string
        self.chatbot_users_collection.update_one(
            {"telegram_user_id": telegram_user_id},
            {"$set": {"bot_memories": memory_json}},
            upsert=True
        )

    def get_user_memory(self, telegram_user_id: int):
        """Retrieves user memory."""
        user = self.chatbot_users_collection.find_one(
            {"telegram_user_id": telegram_user_id},
            {"bot_memories"}
        )
        return json.loads(
            user["bot_memories"]
        ) if user and user["bot_memories"] else None

    def close_connection(self):
        """Closes the MongoDB connection."""
        self.client.close()


# Singleton instance for reuse across bots
chatbot_db = ChatBotDBManager()
