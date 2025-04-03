import os
from fastapi.security import OAuth2AuthorizationCodeBearer
from fief_client import FiefAsync
from fief_client.integrations.fastapi import FiefAuth
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Load environment variables
FIEF_BASE_URL = os.getenv("FIEF_BASE_URL")
FIEF_CLIENT_ID = os.getenv("FIEF_CLIENT_ID")
FIEF_CLIENT_SECRET = os.getenv("FIEF_CLIENT_SECRET")

if not all([FIEF_BASE_URL, FIEF_CLIENT_ID, FIEF_CLIENT_SECRET]):
    raise ("Fief environment variables not set. Auth will be disabled.")

# Create Fief client
fief = FiefAsync(
    FIEF_BASE_URL,
    FIEF_CLIENT_ID,
    FIEF_CLIENT_SECRET,
)

# Create OAuth2 scheme
scheme = OAuth2AuthorizationCodeBearer(
    f"{FIEF_BASE_URL}/authorize",
    f"{FIEF_BASE_URL}/api/token",
    scopes={"openid": "openid", "offline_access": "offline_access"},
    auto_error=False,
)

auth = FiefAuth(fief, scheme)
logger.info("Auth components initialized successfully")
