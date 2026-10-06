import os

MODEL = os.getenv(
    "CLAUDE_MODEL",
    "claude-haiku-4-5"
)

API_BASE_URL = os.getenv(
    "NETWORK_API_BASE_URL",
    "http://127.0.0.1:8000"
)