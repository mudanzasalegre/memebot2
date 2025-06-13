# memebot2/fetcher/pumpfun.py
"""
Detecta *mints* recientes de Pump Fun vía Bitquery GraphQL y
devuelve una lista de tokens ya enriquecidos (dicts DexScreener).

• Requiere `BITQUERY_TOKEN` en .env.
• Si el token falta o la respuesta trae errores, devuelve [] y el bot
  continua sin interrumpirse.
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import List

import aiohttp
import tenacity

from ..config import BITQUERY_TOKEN
from . import dexscreener

log = logging.getLogger("pumpfun")

API_BASE = "https://streaming.bitquery.io/graphql"
PUMPFUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

QUERY = f"""
{{ solana(network: solana) {{
    smartContractCalls(
      options: {{desc: "time", limit: 20}}
      smartContractMethod: {{is: "initializeMint"}}
      txSender: {{is: "{PUMPFUN_PROGRAM}"}}
    ) {{
      call {{ smartContract }}
      time
    }}
}}}}
"""

HEADERS = {
    "Authorization": f"Bearer {BITQUERY_TOKEN}",
    "Content-Type": "application/json",
}

# ───────────────────── helper seguro ───────────────────────────
async def _safe_json(resp: aiohttp.ClientResponse) -> dict | None:
    try:
        return await resp.json()
    except Exception as e:
        txt = await resp.text()
        log.warning("[PumpFun] JSON decode error %s – body=%s", e, txt[:120])
        return None


# ───────────────────── fast-exit si no hay token ───────────────
if not BITQUERY_TOKEN:

    async def get_latest_pumpfun() -> List[dict]:  # type: ignore
        return []

    log.warning("[PumpFun] BITQUERY_TOKEN vacío → módulo deshabilitado")

# ───────────────────── implementación completa ─────────────────
else:

    @tenacity.retry(
        wait=tenacity.wait_fixed(2),
        stop=tenacity.stop_after_attempt(3),
        reraise=False,
    )
    async def _graphql() -> list[str]:
        """
        Devuelve lista de mint addresses o [] si algo va mal.
        Nunca lanza excepción hacia arriba.
        """
        async with aiohttp.ClientSession() as s:
            async with s.post(
                API_BASE,
                json={"query": QUERY},
                headers=HEADERS,
                timeout=20,
            ) as r:
                if r.status == 401:
                    log.error("[PumpFun] 401 – token OAuth inválido o caducado")
                    return []
                if r.status != 200:
                    log.warning("[PumpFun] HTTP %s – %s", r.status, await r.text())
                    return []

                data = await _safe_json(r)
                if not data or "errors" in data:
                    log.debug("[PumpFun] GraphQL errors: %s", data.get("errors") if data else "empty body")
                    return []

        calls = (
            data.get("data", {})  # type: ignore[arg-type]
            .get("solana", {})
            .get("smartContractCalls", [])
        )
        return [c["call"]["smartContract"] for c in calls if c.get("call")]

    _seen: set[str] = set()     # cache anti-spam

    async def get_latest_pumpfun() -> List[dict]:
        """
        Lista de dicts estilo DexScreener con claves extra:
            discovered_via = "pumpfun"
            discovered_at  = timestamp
        """
        out: list[dict] = []

        for mint in await _graphql():
            if mint in _seen:
                continue
            _seen.add(mint)

            tok = await dexscreener.get_pair(mint)
            if tok:
                tok["discovered_via"] = "pumpfun"
                tok["discovered_at"] = _dt.datetime.utcnow()
                out.append(tok)

        if out:
            log.debug("[PumpFun] nuevos mints %s", [t["symbol"] for t in out])

        return out
