from typing import Any
import httpx
from config import API_BASE_URL, REQUEST_TIMEOUT

class NetworkAPIClient:
    def __init__(self) -> None:
        self.base_url = API_BASE_URL
        self.timeout = REQUEST_TIMEOUT

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            response = await client.get(url, params=params)

            response.raise_for_status()

            return response.json()