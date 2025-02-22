import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Use an environment variable if available; otherwise default to localhost.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.imaginary_agents_api

bot_registry_collection = db.bot_registry
bot_users_collection = db.bot_users
