# memebot2/fetcher/socials.py
from __future__ import annotations

import aiohttp
import tenacity

from ..config import DEX_API_BASE

PROFILE_URL = f"{DEX_API_BASE.rstrip('/')}/token-profiles/latest/v1"


@tenacity.retry(wait=tenacity.wait_fixed(2))
async def has_socials(address: str) -> bool:
    async with aiohttp.ClientSession() as s:
        async with s.get(PROFILE_URL) as r:
            r.raise_for_status()
            data = await r.json()

    for profile in data:
        if (
            profile["tokenAddress"].lower() == address.lower()
            and profile.get("links")
        ):
            return True
    return False
