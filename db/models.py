# memebot2/db/models.py
"""
Declaración de tablas SQLAlchemy (async).

• Token     – metadata y señales de cada par evaluado
• Position  – posiciones abiertas/cerradas por el bot
"""

from __future__ import annotations

import datetime as _dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Token(Base):
    __tablename__ = "tokens"

    # ——— claves ———
    address: Mapped[str] = mapped_column(String, primary_key=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(16))
    name: Mapped[Optional[str]] = mapped_column(String(64))

    # ——— métricas on-chain ———
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime)
    liquidity: Mapped[float] = mapped_column(Float)
    vol24h: Mapped[float] = mapped_column(Float)
    holders: Mapped[int] = mapped_column(Integer)

    # ——— señales ———
    rug_score: Mapped[int] = mapped_column(Integer, default=0)
    cluster_bad: Mapped[bool] = mapped_column(Boolean, default=False)
    social_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    trend: Mapped[Optional[str]] = mapped_column(String(8))
    insider_sig: Mapped[bool] = mapped_column(Boolean, default=False)
    score_total: Mapped[int] = mapped_column(Integer, default=0)

    # ——— metadatos descubrimiento ———
    discovered_via: Mapped[Optional[str]] = mapped_column(String(16))
    discovered_at: Mapped[Optional[_dt.datetime]] = mapped_column(DateTime)

    # ——— relaciones ———
    positions: Mapped[list["Position"]] = relationship(back_populates="token")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Token {self.symbol or self.address[:4]} score={self.score_total}>"


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ——— relación token ———
    address: Mapped[str] = mapped_column(
        String,
        ForeignKey("tokens.address", ondelete="CASCADE"),
    )
    token: Mapped[Token] = relationship(back_populates="positions")

    symbol: Mapped[Optional[str]] = mapped_column(String(16))
    qty: Mapped[float] = mapped_column(Float)
    buy_price_usd: Mapped[float] = mapped_column(Float)
    opened_at: Mapped[_dt.datetime] = mapped_column(DateTime)
    highest_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)

    # ——— cierre ———
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_at: Mapped[Optional[_dt.datetime]] = mapped_column(DateTime)
    close_price_usd: Mapped[Optional[float]] = mapped_column(Float)
    exit_tx_sig: Mapped[Optional[str]] = mapped_column(String(128))

    def __repr__(self) -> str:  # pragma: no cover
        state = "closed" if self.closed else "open"
        return f"<Position {self.symbol or self.address[:4]} qty={self.qty} {state}>"
