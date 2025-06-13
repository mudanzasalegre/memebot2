# memebot2/db/database.py
"""
Motor SQLite asíncrono + helper CLI.

Funciona tanto si se ejecuta como:
    python -m memebot2.db.database
como:
    python -m db.database          (dentro de la raíz del repo)

• Si SQLITE_DB es relativa, se crea SIEMPRE bajo memebot2/data/.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# ────────────────────────── localizar paquete ─────────────────
HERE = Path(__file__).resolve()
PKG_ROOT = HERE.parents[1]            # …/memebot2
REPO_ROOT = PKG_ROOT.parent           # carpeta que contiene memebot2/

# Garantiza que REPO_ROOT esté en PYTHONPATH (para import memebot2)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ────────────────────────── importar config ───────────────────
try:
    # ruta normal (cuando se llama como memebot2.db.database)
    from ..config import SQLITE_DB
except ImportError:
    # ruta alternativa (cuando se llama como db.database)
    from memebot2.config import SQLITE_DB  # type: ignore

# ────────────────── calcular ruta definitiva de la BD ─────────
sqlite_path = Path(SQLITE_DB).expanduser()
if not sqlite_path.is_absolute():
    sqlite_path = (PKG_ROOT / sqlite_path).resolve()

sqlite_path.parent.mkdir(parents=True, exist_ok=True)
DB_PATH: Path = sqlite_path

# ───────────────── Declarative Base / Engine / Session ────────
class Base(DeclarativeBase):  # type: ignore
    """Declarative base (async)."""

engine: AsyncEngine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH.as_posix()}",
    echo=False,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ────────────────────── Init / migrate helper ─────────────────
async def async_init_db() -> None:
    """
    Crea las tablas si no existen. Usado por el bot y como CLI standalone.
    """
    from . import models  # noqa: F401  — registra modelos

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # WAL = mejor concurrencia
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

    print(f"[DB] OK  →  {DB_PATH}")


# ────────────────────────── CLI helper ────────────────────────
if __name__ == "__main__":
    asyncio.run(async_init_db())
