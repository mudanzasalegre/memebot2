# memebot2/fetcher/rugcheck.py
from __future__ import annotations

import aiohttp
import tenacity

from ..config import RUGCHECK_API_BASE, RUGCHECK_API_KEY

if not (RUGCHECK_API_BASE and RUGCHECK_API_KEY):

    async def check_token(address: str) -> int:  # type: ignore
        return 0             # puntuación nula si RugCheck desactivado

    print(
        "[RugCheck] Deshabilitado: añade RUGCHECK_API_BASE y RUGCHECK_API_KEY a .env"
    )
else:
    HEADERS = {"Authorization": f"Bearer {RUGCHECK_API_KEY}"}

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3))
    async def check_token(address: str) -> int:
        url = f"{RUGCHECK_API_BASE.rstrip('/')}/score/{address}"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=HEADERS) as r:
                if r.status == 404:
                    return 0
                r.raise_for_status()
                data = await r.json()
        return int(data.get("score", 0))
