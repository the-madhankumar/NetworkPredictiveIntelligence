import os

API_BASE_URL = os.getenv(
    "NETWORK_API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

REQUEST_TIMEOUT = float(
    os.getenv("NETWORK_API_TIMEOUT", "10")
)