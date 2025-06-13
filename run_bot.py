# memebot2/run_bot.py
"""
⏯️  Orquestador principal del sniper de memecoins sobre Solana.

• Descubre pares ↦ los evalúa con filtros/analytics ↦ compra vía trader.buyer.
• Supervisa las posiciones abiertas ↦ aplica lógica de salidas (TP/SL/trailing/
  max-holding) ↦ vende vía trader.seller.
• Todo el flujo es asíncrono y persiste tanto tokens analizados como posiciones
  en SQLite mediante SQLAlchemy async.

Ejecuta con:

    python -m memebot2.run_bot
o  python run_bot.py              (si tu CWD es la raíz del repo)

Requiere:
    - .env con las claves y umbrales necesarios.
    - Base de datos inicializada:  python -m memebot2.db.database
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import logging
import time
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

# ─── módulos internos ──────────────────────────────────────────
from memebot2.config import config, exits
from memebot2.db.database import SessionLocal, async_init_db
from memebot2.db.models import Position, Token
from memebot2.fetcher import (
    dexscreener,
    helius_cluster as clusters,
    pumpfun,
    rugcheck,
    socials,
)
from memebot2.analytics import filters, insider, trend
from memebot2.trader import buyer, seller
from memebot2.utils.descubridor_pares import fetch_candidate_pairs
from memebot2.utils.lista_pares import agregar_si_nuevo, eliminar_par, obtener_pares

# ─── logging global ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
log = logging.getLogger("run_bot")
logging.getLogger("pumpfun").setLevel(logging.DEBUG)

# ─── short-cuts de parámetros .env / config ───────────────────
DISCOVERY_INTERVAL: int = config.DISCOVERY_INTERVAL
SLEEP_SECONDS: int = config.SLEEP_SECONDS
VALIDATION_BATCH_SIZE: int = config.VALIDATION_BATCH_SIZE
TRADE_AMOUNT_SOL: float = config.TRADE_AMOUNT_SOL

TP_PCT: float = exits.TAKE_PROFIT_PCT
SL_PCT: float = exits.STOP_LOSS_PCT
TRAILING_PCT: float = exits.TRAILING_PCT
MAX_HOLDING_H: int = exits.MAX_HOLDING_H


# ╭──────────────────────────────────────────────────────────────╮
# │                       BUY PIPELINE                          │
# ╰──────────────────────────────────────────────────────────────╯
async def _evaluate_and_buy(token: dict, session: SessionLocal) -> None:
    """
    Enriquece `token` con señales avanzadas y ejecuta compra si procede.
    Persiste tanto el token como la posición abierta.
    """
    log.debug("▶ Eval %s", token.get('symbol', token['address'][:4]))

    # Fast-fail
    if not filters.basic_filters(token):
        log.debug("   ✗ filtros básicos")
        return

    # Señales externas 💡
    token["rug_score"] = await rugcheck.check_token(token["address"])
    token["cluster_bad"] = await clusters.suspicious_cluster(token["address"])
    token["social_ok"] = await socials.has_socials(token["address"])
    token["trend"] = await trend.trend_signal(token["address"])
    token["insider_sig"] = insider.insider_alert(token["address"])
    token["score_total"] = filters.total_score(token)

    log.debug("   → score=%s", token["score_total"])

    if token["score_total"] < config.MIN_SCORE_TOTAL:
        log.info("DESCARTADO %s (score=%s)",
                 token.get("symbol", token['address'][:4]), token["score_total"])
        return

    # Guarda token en BD (idempotente gracias a merge)
    try:
        session.merge(Token(**token))
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        log.warning("DB merge Token: %s", e)

    # ⇢ COMPRA
    if TRADE_AMOUNT_SOL <= 0:
        log.warning("TRADE_AMOUNT_SOL=0  – modo simulación, no se opera")
        return

    buy_resp = await buyer.buy(token["address"], TRADE_AMOUNT_SOL)
    qty = buy_resp.get("qty", 0)            # depende de trader.buyer implementation
    price_usd = buy_resp.get("price_usd")   # idem (si GMGN lo devuelve)

    pos = Position(
        address=token["address"],
        symbol=token.get("symbol"),
        qty=qty,
        buy_price_usd=price_usd,
        opened_at=_dt.datetime.utcnow(),
        highest_pnl_pct=0.0,
    )
    try:
        session.add(pos)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        log.warning("DB add Position: %s", e)

    log.warning("✔ COMPRADO %s %s", token.get("symbol", "?"), token["address"])


# ╭──────────────────────────────────────────────────────────────╮
# │                     EXIT STRATEGY LOOP                      │
# ╰──────────────────────────────────────────────────────────────╯
async def _load_open_positions(session: SessionLocal) -> Sequence[Position]:
    stmt = select(Position).where(Position.closed.is_(False))
    return (await session.execute(stmt)).scalars().all()


async def _should_exit(
    pos: Position,
    current_price_usd: float,
    now: _dt.datetime,
) -> bool:
    """
    Devuelve True si se cumple alguno de los criterios de salida.
    Actualiza `pos.highest_pnl_pct` en memoria según sea necesario.
    """
    pnl_pct = ((current_price_usd - pos.buy_price_usd) / pos.buy_price_usd) * 100

    # Trailing stop ➟ primero actualizamos el máximo
    if pnl_pct > pos.highest_pnl_pct:
        pos.highest_pnl_pct = pnl_pct

    trailing_cond = pnl_pct <= pos.highest_pnl_pct - TRAILING_PCT
    tp_cond = pnl_pct >= TP_PCT
    sl_cond = pnl_pct <= -SL_PCT   # SL_PCT es positivo en config
    age_h = (now - pos.opened_at).total_seconds() / 3600
    max_hold_cond = age_h >= MAX_HOLDING_H

    return trailing_cond or tp_cond or sl_cond or max_hold_cond


async def _check_positions(session: SessionLocal) -> None:
    """
    Recorre las posiciones abiertas y aplica las reglas de salida.
    Si corresponde, envía la orden de venta y cierra la posición en BD.
    """
    positions = await _load_open_positions(session)
    if not positions:
        return

    for pos in positions:
        pair = await dexscreener.get_pair(pos.address)
        if not pair or not pair.get("price_usd"):
            continue

        now = _dt.datetime.utcnow()
        if not await _should_exit(pos, pair["price_usd"], now):
            continue

        # 👉 VENTA
        sell_resp = await seller.sell(pos.address, pos.qty)
        pos.closed = True
        pos.closed_at = now
        pos.close_price_usd = pair["price_usd"]
        pos.exit_tx_sig = sell_resp.get("signature")

        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            log.warning("DB update Position: %s", e)

        log.warning("💸 VENDIDO %s  pnl=%.1f%%  sig=%s",
                    pos.symbol or pos.address[:4],
                    ((pos.close_price_usd - pos.buy_price_usd) /
                     pos.buy_price_usd) * 100,
                    pos.exit_tx_sig[:6] if pos.exit_tx_sig else "–")


# ╭──────────────────────────────────────────────────────────────╮
# │                         MAIN LOOP                           │
# ╰──────────────────────────────────────────────────────────────╯
async def main_loop() -> None:
    await async_init_db()
    session = SessionLocal()

    last_discovery = 0.0
    log.info(
        "Bot listo  (discover=%ss, lote=%s, pausa=%ss, sl/tp/trail=%s/%s/%s)",
        DISCOVERY_INTERVAL,
        VALIDATION_BATCH_SIZE,
        SLEEP_SECONDS,
        SL_PCT,
        TP_PCT,
        TRAILING_PCT,
    )

    while True:
        now = time.monotonic()

        # ── 1) descubrimiento de nuevos pares ───────────────────
        if now - last_discovery >= DISCOVERY_INTERVAL:
            log.debug("🔎 Descubriendo candidatos")
            for addr in await fetch_candidate_pairs():
                agregar_si_nuevo(addr)
            last_discovery = now

        # ── 2) stream PumpFun (tokens recién minteados) ─────────
        for tok in await pumpfun.get_latest_pumpfun():
            await _evaluate_and_buy(tok, session)

        # ── 3) validación de la lista de pares pendientes ───────
        pending = obtener_pares()[:VALIDATION_BATCH_SIZE]
        log.debug("🗒️  Validando %s pares pendientes", len(pending))
        for pair_addr in pending:
            tok = await dexscreener.get_pair(pair_addr)
            if tok:
                await _evaluate_and_buy(tok, session)
            eliminar_par(pair_addr)

        # ── 4) gestión de posiciones abiertas (salidas) ─────────
        await _check_positions(session)

        await asyncio.sleep(SLEEP_SECONDS)


# ╭──────────────────────────────────────────────────────────────╮
# │                     ENTRY POINT CLI                         │
# ╰──────────────────────────────────────────────────────────────╯
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        log.info("⏹️  Bot detenido por usuario")
