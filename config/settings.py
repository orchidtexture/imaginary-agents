import os
from dotenv import load_dotenv

load_dotenv()

FIEF_WEBHOOK_SECRET: str = os.getenv("FIEF_WEBHOOK_SECRET", "")

TYPE_MAPPING = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}
