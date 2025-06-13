"""
Capa delgada sobre gmgn.buy:

• Modo demo cuando TRADE_AMOUNT_SOL <= 0
• Devuelve un dict homogéneo:
    {
      qty_lamports : int
      signature    : str
      route        : dict   # raw JSON de GMGN
    }
"""

from __future__ import annotations
import logging
from typing import Dict

from ..config import TRADE_AMOUNT_SOL
from . import gmgn

log = logging.getLogger("buyer")


def _parse_route(resp: dict) -> dict:
    route = resp.get("route", {})
    quote = route.get("quote", {})
    qty_lamports = int(quote.get("outAmount", "0"))
    return {
        "qty_lamports": qty_lamports,
        "signature": resp.get("signature"),
        "route": route,
    }


async def buy(token_addr: str, amount_sol: float) -> Dict[str, object]:
    """
    Compra real o simulada.

    • Si amount_sol <= 0 → demo (no-onchain).
    • Devuelve qty_lamports, signature y raw route.
    """
    if amount_sol <= 0:
        log.info("[buyer] SIMULACIÓN: no se envía orden real (amount=0)")
        return {
            "qty_lamports": 0,
            "signature": "SIMULATION",
            "route": {},
        }

    resp = await gmgn.buy(token_addr, amount_sol)
    return _parse_route(resp)
