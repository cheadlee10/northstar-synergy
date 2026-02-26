import aiosqlite
import os
import tempfile

# For Railway deployment: use temp directory if data folder doesn't exist
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Running on Railway - use temp storage
    DB_PATH = os.path.join(tempfile.gettempdir(), "northstar.db")
else:
    # Local development - use relative path
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "northstar.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    bet_date TEXT NOT NULL,
    sport TEXT NOT NULL,
    game TEXT NOT NULL,
    book TEXT DEFAULT 'Kalshi',
    bet_type TEXT DEFAULT 'ML',
    stake REAL NOT NULL,
    odds TEXT,
    odds_decimal REAL,
    result TEXT DEFAULT 'PENDING',
    profit_loss REAL DEFAULT 0,
    edge_pct REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS john_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    job_date TEXT NOT NULL,
    client_name TEXT NOT NULL,
    job_description TEXT,
    status TEXT DEFAULT 'quoted',
    invoice_amount REAL NOT NULL,
    paid INTEGER DEFAULT 0,
    paid_date TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    usage_date TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd REAL NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    expense_date TEXT NOT NULL,
    segment TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    revenue_date TEXT NOT NULL,
    segment TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS john_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT (datetime('now')),
    lead_date TEXT NOT NULL,
    source TEXT,
    client_name TEXT NOT NULL,
    service TEXT,
    estimated_value REAL DEFAULT 0,
    status TEXT DEFAULT 'new',
    notes TEXT,
    external_id TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS kalshi_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_ts TEXT NOT NULL UNIQUE,
    snap_date TEXT NOT NULL,
    balance_cents INTEGER DEFAULT 0,
    daily_pnl_cents INTEGER DEFAULT 0,
    total_pnl_cents INTEGER DEFAULT 0,
    open_positions INTEGER DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    total_fills INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    total_fees_cents INTEGER DEFAULT 0,
    weather_pnl_cents INTEGER DEFAULT 0,
    crypto_pnl_cents INTEGER DEFAULT 0,
    econ_pnl_cents INTEGER DEFAULT 0,
    mm_pnl_cents INTEGER DEFAULT 0,
    lip_rewards_cents INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sports_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_date TEXT NOT NULL,
    sport TEXT,
    game TEXT NOT NULL,
    pick TEXT,
    ml INTEGER,
    open_ml INTEGER,
    edge_val REAL,
    model_prob REAL,
    framing_type TEXT,
    edge_bucket TEXT,
    confidence TEXT,
    result TEXT DEFAULT 'PENDING',
    stake REAL DEFAULT 0,
    profit_loss REAL DEFAULT 0,
    UNIQUE(pick_date, game, pick)
);
"""

async def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    print(f"[DB] Initialized at {DB_PATH}")
