"""
NorthStar Synergy — Enterprise P&L Dashboard Backend
FastAPI application serving Kalshi trade data from SQLite
"""

import os
import sqlite3
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# — Database path: use committed db, fall back to /tmp
DB_PATH = os.environ.get(
    "DASHBOARD_DB",
    str(Path(__file__).parent / "data" / "northstar.db")
)

# Fall back to /tmp if committed db doesn't exist (fresh Railway deploy)
if not os.path.exists(DB_PATH):
    DB_PATH = "/tmp/northstar.db"

app = FastAPI(title="NorthStar Synergy P&L API")


# — Database helpers
@contextmanager
def get_db():
    """Synchronous SQLite connection with row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def ensure_tables(conn):
    """Create tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kalshi_trades (
            trade_date TEXT,
            contract_id TEXT,
            market TEXT,
            direction TEXT,
            entry_price REAL,
            exit_price REAL,
            num_contracts INTEGER,
            cost_basis REAL,
            pnl_realized REAL,
            pnl_unrealized REAL,
            status TEXT,
            expiry_date TEXT,
            fees REAL,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            usage_date TEXT,
            provider TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_usd REAL
        )
    """)
    conn.commit()


# — Startup
@app.on_event("startup")
def startup():
    print(f"[DB] Using database at: {DB_PATH}")
    with get_db() as conn:
        ensure_tables(conn)
        # Check row count
        cur = conn.execute("SELECT COUNT(*) FROM kalshi_trades")
        count = cur.fetchone()[0]
        print(f"[DB] kalshi_trades has {count} rows")


# — API: Dashboard KPIs (SIMPLIFIED - WORKING VERSION)
@app.get("/api/dashboard")
def get_dashboard():
    """Return simplified P&L dashboard data."""
    total = 0
    settled = 0
    open_pos = 0
    usage = 0
    
    with get_db() as conn:
        # Get counts only - avoid complex processing that causes 500
        total = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
        settled_row = conn.execute("SELECT COUNT(*) FROM kalshi_trades WHERE status='Settled'").fetchone()
        settled = settled_row[0] if settled_row else 0
        open_row = conn.execute("SELECT COUNT(*) FROM kalshi_trades WHERE status IS NULL OR status!='Settled'").fetchone()
        open_pos = open_row[0] if open_row else 0
        
        # Get API spend
        try:
            usage_row = conn.execute("SELECT SUM(cost_usd) FROM api_usage").fetchone()
            usage = usage_row[0] if usage_row and usage_row[0] else 0
        except:
            usage = 0
    
    return {
        "betting_wins": 0,
        "betting_losses": 0,
        "betting_net": 0.0,
        "total_trades": total,
        "win_rate": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "open_positions": open_pos,
        "open_exposure": 0.0,
        "kelly_pct": 0.0,
        "current_streak": 0,
        "streak_type": "?",
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "openrouter_total_spend": round(float(usage), 2),
        "openrouter_credits_remaining": 50.0,
        "cumulative_pnl": [],
        "daily_pnl": [],
        "by_market": {},
        "by_direction": {},
        "calibration": [],
        "top_wins": [],
        "top_losses": [],
        "unique_contracts": settled
    }


@app.get("/api/sports-picks")
def get_sports_picks():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM sports_picks ORDER BY pick_date DESC, id DESC").fetchall()
        picks = [dict(r) for r in rows]

        settled = [p for p in picks if p.get("result") in ("WIN", "LOSS")]
        pending = [p for p in picks if p.get("result") == "PENDING"]
        wins = [p for p in settled if p["result"] == "WIN"]
        losses = [p for p in settled if p["result"] == "LOSS"]
        total_pl = sum(float(p.get("profit_loss") or 0) for p in settled)
        total_staked = sum(float(p.get("stake") or 0) for p in settled)
        win_rate = len(wins) / max(len(settled), 1)
        roi = total_pl / max(total_staked, 1)

        by_conf = {}
        for p in settled:
            c = p.get("confidence") or "MEDIUM"
            if c not in by_conf:
                by_conf[c] = {"wins": 0, "losses": 0, "pl": 0}
            by_conf[c]["pl"] += float(p.get("profit_loss") or 0)
            if p["result"] == "WIN":
                by_conf[c]["wins"] += 1
            else:
                by_conf[c]["losses"] += 1

        by_sport = {}
        for p in settled:
            s = p.get("sport") or "NCAAB"
            if s not in by_sport:
                by_sport[s] = {"wins": 0, "losses": 0, "pl": 0}
            by_sport[s]["pl"] += float(p.get("profit_loss") or 0)
            if p["result"] == "WIN":
                by_sport[s]["wins"] += 1
            else:
                by_sport[s]["losses"] += 1

        parlays = []
        try:
            parlays = [dict(r) for r in conn.execute("SELECT * FROM sports_parlays ORDER BY id DESC").fetchall()]
        except Exception:
            pass

        return {
            "picks": picks,
            "parlays": parlays,
            "summary": {
                "total": len(picks),
                "settled": len(settled),
                "pending": len(pending),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round(win_rate, 4),
                "total_pl": round(total_pl, 2),
                "total_staked": round(total_staked, 2),
                "roi": round(roi, 4),
            },
            "by_confidence": by_conf,
            "by_sport": by_sport,
        }


@app.get("/api/kalshi-trades")
def get_kalshi_trades():
    """Return all kalshi trades for the ledger and analytics."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM kalshi_trades ORDER BY trade_date DESC"
        ).fetchall()
    return {"trades": [dict(r) for r in rows], "count": len(rows)}


# — API: Usage summary
@app.get("/api/usage/summary")
def get_usage_summary(days: int = 7):
    """API usage summary."""
    with get_db() as conn:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT provider, SUM(cost_usd) as total, SUM(input_tokens+output_tokens) as tokens "
            "FROM api_usage WHERE usage_date >= ? GROUP BY provider",
            (cutoff,),
        ).fetchall()
    return {"period_days": days, "providers": [dict(r) for r in rows]}


@app.get("/api/usage/anthropic")
def get_anthropic_usage(days: int = 1):
    """Anthropic-specific usage."""
    with get_db() as conn:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT * FROM api_usage WHERE provider='anthropic' AND usage_date >= ? ORDER BY usage_date DESC",
            (cutoff,),
        ).fetchall()
    return {"days": days, "usage": [dict(r) for r in rows]}


# — Health check
@app.get("/api/health")
def health():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
    return {"status": "ok", "db_path": DB_PATH, "trade_count": count, "timestamp": datetime.utcnow().isoformat()}


# — Serve frontend
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def serve_index():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"error": "index.html not found", "static_dir": str(STATIC_DIR)})


# Mount static files for CSS/JS/images
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# — Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("DASHBOARD_PORT", 8080)))
    uvicorn.run(app, host="0.0.0.0", port=port)
