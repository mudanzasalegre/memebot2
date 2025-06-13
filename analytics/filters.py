"""
analytics/filters.py
────────────────────
Filtrado rápido + scoreado agregado antes de disparar la compra.

• basic_filters()  → descarta cuanto antes tokens sin mínimos básicos.
• total_score()    → suma ponderada de varias señales para ranking final.
• should_buy()     → azúcar sintáctico = filtros + score >= MIN_SCORE_TOTAL
"""

from __future__ import annotations

import datetime as _dt

from ..config import (           # ← import directo gracias a __init__.py
    MAX_AGE_DAYS,
    MIN_HOLDERS,
    MIN_LIQUIDITY_USD,
    MIN_VOL_USD_24H,
    MAX_24H_VOLUME,
    MIN_SCORE_TOTAL,
)

# --------------------------------------------------------------------------- #
def basic_filters(token: dict) -> bool:
    """
    Comprueba requisitos **mínimos** antes de rug-check, helius, etc.

    token debe contener como mínimo:
        • created_at   (datetime, tz-aware)
        • holders      (int)
        • liquidity    (float USD)
        • vol24h       (float USD)
    """
    # 1) antigüedad
    age_days = (
        _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
        - token["created_at"]
    ).days
    if age_days > MAX_AGE_DAYS:
        return False

    # 2) liquidez + volumen
    if token.get("liquidity", 0) < MIN_LIQUIDITY_USD:
        return False
    if token["vol24h"] < MIN_VOL_USD_24H or token["vol24h"] > MAX_24H_VOLUME:
        return False

    # 3) distribución mínima de holders
    if token["holders"] < MIN_HOLDERS:
        return False

    return True


# --------------------------------------------------------------------------- #
def total_score(tok: dict) -> int:
    """
    Suma ponderada de señales. Ajusta pesos a tu gusto:

        – Métricas on-chain (liquidez, volumen, holders)
        – RugCheck score
        – Concentración de holders (cluster_bad=False suma)
        – Socials presentes
        – Ausencia de alertas de insiders
    """
    score = 0

    # ——— on-chain básicos ———
    score += 15 if tok.get("liquidity", 0) >= MIN_LIQUIDITY_USD * 2 else 0
    score += 20 if tok["vol24h"] >= MIN_VOL_USD_24H * 3 else 0
    score += 10 if tok["holders"] >= MIN_HOLDERS * 2 else 0

    # ——— riesgo & señales ———
    score += 15 if tok.get("rug_score", 0) >= 70 else 0
    score += 15 if not tok.get("cluster_bad", False) else 0
    score += 10 if tok.get("social_ok", False) else 0
    score += 10 if not tok.get("insider_sig", False) else 0

    return score


# --------------------------------------------------------------------------- #
def should_buy(tok: dict) -> bool:
    """True si pasa basic_filters y score ≥ MIN_SCORE_TOTAL."""
    return basic_filters(tok) and total_score(tok) >= MIN_SCORE_TOTAL
