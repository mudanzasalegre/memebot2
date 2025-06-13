memebot2/                     # 📦 paquete raíz (importable)
│
├── run_bot.py                # ⏯️  Orquestador principal (v1, ampliado)
│
├── README.md                 # 📝 Guía instalación/uso (renovado)
├── requirements.txt          # 📜 Dependencias (actualizado)
├── .env.example              # 🔐 Plantilla de variables sensibles (nuevo)
│
├── config/
│   ├── __init__.py           # ↩️  Alias de importación (“from config import …”)
│   ├── config.py             # ⚙️  Carga .env + parámetros globales (v1, ajustado)
│   └── exits.py              # 📈 Umbrales TP/SL/trailing—para reutilizar (nuevo)
│
├── fetcher/                  # 🌐 Wrappers de APIs externas
│   ├── __init__.py
│   ├── dexscreener.py        # v1
│   ├── helius_cluster.py     # v1
│   ├── rugcheck.py           # v1
│   ├── pumpfun.py            # v1 (pendiente de implementar consulta)
│   ├── socials.py            # v1
│   └── __deprecated__/       # APIs que quizá descartemos más adelante
│
├── analytics/                # 🧠 Scoreo y señales
│   ├── __init__.py
│   ├── filters.py            # v1 (ajustar umbrales)
│   ├── trend.py              # 📊 Tendencias de precio/volumen (nuevo o portado)
│   └── insider.py            # 👀 Detección de insiders (nuevo o portado)
│
├── trader/                   # 💸 Ejecución y firma de órdenes
│   ├── __init__.py
│   ├── gmgn.py               # v1 (compra/venta vía GMGN)
│   ├── sol_signer.py         # v1 (firma local)
│   ├── buyer.py              # 🛒 Lógica de construcción de tx BUY (nuevo wrapper)
│   └── seller.py             # 💰 Lógica de construcción de tx SELL (nuevo wrapper)
│
├── db/                       # 🗄️  Persistencia
│   ├── __init__.py
│   ├── database.py           # SQLAlchemy async (v1)
│   └── models.py             # Declaración Token y quizá WalletTx (nuevo)
│
├── data/                     # 📂 Artefactos en disco
│   ├── memebotdatabase.db    # SQLite (creado en runtime)
│   └── pares_procesados.txt  # Cache de tokens ya vistos (migrado)
│
├── utils/                    # 🔧 Pequeñas utilidades desacopladas
│   ├── lista_pares.py        # v1 (gestionador de pendientes)
│   └── descubridor_pares.py  # v1 (scraper DexScreener)
│
└── tests/                    # 🧪 Pytest unit + integration (opcional, nuevo)
    └── …                     # Ejemplos de fixtures y pruebas async



# 🐇 memebot2 – Solana Meme-Sniper v2

Un bot **asíncrono** que descubre, puntúa y opera memecoins recién listadas en
Solana.  Combina señales on-chain y off-chain (DexScreener, RugCheck, Helius,
PumpFun, redes sociales) y ejecuta órdenes de compra/venta firmadas localmente.

---

## ⚡ Características
| Módulo | Función |
|--------|---------|
| **fetcher/**  | Wrappers de APIs externas (DexScreener, RugCheck, Helius, PumpFun…). |
| **analytics/**| Filtros & scoring avanzado, tendencia EMA/RSI, alerta de insiders. |
| **trader/**   | Compra/Venta vía GMGN, firma con Solders, control TP/SL/Trailing. |
| **db/**       | SQLite async para tokens evaluados y posiciones abiertas. |
| **utils/**    | Descubridor masivo de pares, caché de procesados. |
| **run_bot.py**| Orquestador principal, loop async de compra y salida. |

---

## 🛠 Instalación rápida

```bash
# clona el repo
git clone https://github.com/<tu-usuario>/memebot2.git && cd memebot2

# Python 3.12+ recomendado
python -m venv .venv && source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m memebot2.db.database      # crea tablas SQLite en /data/memebotdatabase.db

python -m memebot2.run_bot          # o:  python run_bot.py
