from collections.abc import AsyncGenerator

import httpx

from src.core.config import setting


async def get_parserdoc_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=setting.parserdoc_url.rstrip("/"),
        timeout=httpx.Timeout(setting.parserdoc_timeout_seconds),
    ) as client:
        yield client
