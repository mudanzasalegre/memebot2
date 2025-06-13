# memebot2/fetcher/helius_cluster.py
# ------------------------------------------------------------------
# Replacement for BubbleMaps: returns cluster_bad = True|False
# ------------------------------------------------------------------

from __future__ import annotations

import aiohttp
import logging

from ..config import HELIUS_API_BASE, HELIUS_API_KEY

# ---------- Tuning ----------
MAX_SHARE_TOP10 = 0.20          # 20 % of total supply
TOP_N = 10                      # how many holders to sum
TIMEOUT = 10                    # seconds
# -----------------------------------------------------------------


async def suspicious_cluster(token_mint: str) -> bool:
    """
    True → too much supply in Top-10 holders (potential rug),
    False → distribution looks healthy.
    """
    if not HELIUS_API_KEY or not HELIUS_API_BASE:
        logging.debug("[Helius] disabled (no API key)")
        return False            # neutral

    url = (
        f"{HELIUS_API_BASE}/v0/token/{token_mint}/holders"
        f"?limit=20&api-key={HELIUS_API_KEY}"
    )

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=TIMEOUT) as r:
                if r.status != 200:
                    logging.warning("[Helius] %s %s", r.status, await r.text())
                    return False
                data = await r.json()
    except Exception as e:
        logging.warning("[Helius] error %s", e)
        return False

    if not data:
        return False

    total_supply = sum(int(h["amountRaw"]) for h in data)
    top_sum = sum(int(h["amountRaw"]) for h in data[:TOP_N])

    share = top_sum / total_supply if total_supply else 0
    cluster_bad = share > MAX_SHARE_TOP10

    logging.debug(
        "[Helius] share_top10 %.2f%% -> cluster_bad=%s",
        share * 100,
        cluster_bad,
    )
    return cluster_bad
