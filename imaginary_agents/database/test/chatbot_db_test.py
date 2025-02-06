import os
import unittest
from unittest.mock import patch
from pymongo.errors import DuplicateKeyError
from pymongo.collection import ObjectId
from imaginary_agents.database.chatbot_db import ChatBotDBManager

# FILE: imaginary_agents/database/test_chatbot_db.py


class TestChatBotDBManager(unittest.TestCase):

    @patch('imaginary_agents.database.chatbot_db.MongoClient')
    def setUp(self, MockMongoClient):
        self.mock_client = MockMongoClient.return_value
        self.mock_db = self.mock_client[
            os.getenv("MONGO_DB_NAME", "imaginary_agents")
        ]
        self.mock_chatbots_collection = self.mock_db["chatbots"]
        self.mock_users_collection = self.mock_db["users"]
        self.chatbot_db_manager = ChatBotDBManager()

    def test_register_chatbot_duplicate(self):
        # Arrange
        bot_name = "test_bot"
        platform = "telegram"
        owner_id = "507f1f77bcf86cd799439011"
        encrypted_token = "encrypted_token"
        existing_chatbot_id = "507f1f77bcf86cd799439012"

        self.mock_chatbots_collection.insert_one.side_effect = \
            DuplicateKeyError("Duplicate key error")
        self.mock_chatbots_collection.find_one.return_value = {
            "_id": existing_chatbot_id
        }

        # Act
        result = self.chatbot_db_manager.register_chatbot(
            bot_name,
            platform,
            owner_id,
            encrypted_token
        )

        # Assert
        self.assertEqual(result, existing_chatbot_id)
        self.mock_chatbots_collection.find_one.assert_called_once_with(
            {"bot_name": bot_name, "owner_id": ObjectId(owner_id)}
        )


if __name__ == '__main__':
    unittest.main()