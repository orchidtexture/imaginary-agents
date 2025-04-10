import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

from api.server import app
from api.auth import current_user

from api.models import LLMConfig, Agent, User
from config.db import _client, _db

# Mock user to override auth
mock_user = {
    "email": "test@example.com",
    "llm_api_keys": {
        "test_llm_provider": "sk-xxxxxxxxxxxxxxxxxxxx",
    },
    "is_admin": True,
    "agents": [],
    "api_keys": [],
}


@pytest.fixture()
def override_dependencies():
    user = User(
        email=mock_user["email"],
        llm_api_keys={
            "test_llm_provider": "sk-xxxxxxxxxxxxxxxxxxxx",
        },
        is_admin=mock_user["is_admin"],  # TODO: create non-admin user as well
        agents=[],
        api_keys=[]
    )
    app.dependency_overrides[current_user] = lambda: user
    yield
    app.dependency_overrides = {}


@pytest.fixture()
async def client_test():
    """
    Create an instance of the client.
    :return: yield HTTP client.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac


@pytest.fixture(autouse=True)
async def mock_db_connection(scope="function"):
    """
    Replace the MongoDB connection with a mock for testing.
    This runs automatically for all tests.
    """

    # Save original globals properly
    original_client = _client
    original_db = _db

    # Set up mock client and database
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client.get_database(name="imaginary_agents_test")

    # Override the global variables
    import config.db
    config.db._client = mock_client
    config.db._db = mock_db

    # Initialize Beanie with the mock database
    document_models = [
        LLMConfig,
        Agent,
        User
        # Add other document models here
    ]
    await init_beanie(document_models=document_models, database=mock_db)

    yield mock_db

    # Restore original globals after test
    config.db._client = original_client
    config.db._db = original_db


@pytest.fixture
async def sample_llm_configs():
    """Add sample LLM configs to the mock database."""
    # Create and insert test data
    sample_configs = [
        LLMConfig(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            provider="deepseek"
        ),
        LLMConfig(
            model="test_model",
            base_url="https://api.test.com",
            provider="test_llm_provider"
        )
    ]

    created_configs = []
    for config in sample_configs:
        created = await config.create()
        created_configs.append(created)

    yield created_configs


@pytest.fixture
async def sample_agent(scope="function"):
    """Add sample Agent to the mock database."""
    # Create and insert test data

    sample_agent = Agent(  # TODO: add input and output schema
        name="Test Daniel",
        llm_model="test_model",
        background=[
            "You are a test agent",
            "Your name is Mini Daniel",
            "You help the user test the system"
        ],
        input_schema_fields={
            "notes": {
                "type": "str",
                "description": "The notes from the technical meeting"
            }
        },
        output_schema_fields={
            "summary": {
                "type": "str",
                "description": "The summary of the technical meeting"
            }
        }
    )

    created_agent = await sample_agent.create()

    yield created_agent


@pytest.fixture
async def sample_user(scope="function"):
    """Add sample User to the mock database."""
    # Create and insert test data

    sample_user = User(
        email=mock_user["email"],
        llm_api_keys={
            "test_llm_provider": "sk-xxxxxxxxxxxxxxxxxxxx",
        },
        is_admin=mock_user["is_admin"],
        agents=[],
        api_keys=[]
    )

    created_user = await sample_user.create()

    yield created_user
