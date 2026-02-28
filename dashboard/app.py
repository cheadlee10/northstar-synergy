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

# ── Database path: use committed db, fall back to /tmp ────────────────
DB_PATH = os.environ.get(
    "DASHBOARD_DB",
    str(Path(__file__).parent / "data" / "northstar.db")
)

# Fall back to /tmp if committed db doesn't exist (fresh Railway deploy)
if not os.path.exists(DB_PATH):
    DB_PATH = "/tmp/northstar.db"

app = FastAPI(title="NorthStar Synergy P&L API")


# ── Database helpers ──────────────────────────────────────────────────
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


# ── Startup ───────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    print(f"[DB] Using database at: {DB_PATH}")
    with get_db() as conn:
        ensure_tables(conn)
        # Check row count
        cur = conn.execute("SELECT COUNT(*) FROM kalshi_trades")
        count = cur.fetchone()[0]
        print(f"[DB] kalshi_trades has {count} rows")


# ── API: Dashboard KPIs ──────────────────────────────────────────────
@app.get("/api/dashboard")
def get_dashboard():
    """Complete P&L dashboard KPIs computed from kalshi_trades."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM kalshi_trades").fetchall()

    trades = [dict(r) for r in rows]
    settled = [t for t in trades if t.get("status") == "Settled"]
    open_pos = [t for t in trades if t.get("status") == "Open"]

    def calc_pnl(t):
        try:
            entry = float(t.get("entry_price") or 0)
            exit_ = float(t.get("exit_price") or 0)
            qty = float(t.get("num_contracts") or 0)
            fees = float(t.get("fees") or 0)
            return (exit_ - entry) * qty - fees
        except (TypeError, ValueError):
            return 0.0

    # Per-trade P&L
    pnls = [(t, calc_pnl(t)) for t in settled]
    wins = [(t, p) for t, p in pnls if p > 0]
    losses = [(t, p) for t, p in pnls if p < 0]
    total_pnl = sum(p for _, p in pnls)

    # Win rate by unique contract (not raw fills)
    by_contract = {}
    for t, p in pnls:
        cid = t.get("contract_id", "unknown")
        by_contract.setdefault(cid, 0.0)
        by_contract[cid] += p
    contract_wins = sum(1 for v in by_contract.values() if v > 0)
    contract_total = max(len(by_contract), 1)
    win_rate = contract_wins / contract_total

    # Open exposure
    exposure = sum(
        float(t.get("cost_basis") or 0) or
        (float(t.get("entry_price") or 0) * float(t.get("num_contracts") or 0))
        for t in open_pos
    )

    # Daily P&L for Sharpe
    daily_pnl = {}
    for t, p in pnls:
        d = (t.get("trade_date") or "")[:10]
        daily_pnl.setdefault(d, 0.0)
        daily_pnl[d] += p
    daily_vals = list(daily_pnl.values())
    avg_daily = sum(daily_vals) / max(len(daily_vals), 1)
    std_daily = (sum((v - avg_daily) ** 2 for v in daily_vals) / max(len(daily_vals), 1)) ** 0.5
    sharpe = (avg_daily / std_daily * (252 ** 0.5)) if std_daily > 0 else 0

    # Max drawdown
    peak = 0.0
    max_dd = 0.0
    running = 0.0
    sorted_pnls = sorted(pnls, key=lambda x: x[0].get("trade_date", ""))
    for _, p in sorted_pnls:
        running += p
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    # Kelly criterion
    avg_win = sum(p for _, p in wins) / max(len(wins), 1)
    avg_loss = abs(sum(p for _, p in losses) / max(len(losses), 1))
    kelly = (win_rate - ((1 - win_rate) / (avg_win / max(avg_loss, 0.01)))) if avg_loss > 0 else 0

    # By market category
    by_market = {}
    for t, p in pnls:
        m = t.get("market") or "Other"
        by_market.setdefault(m, {"wins": 0, "losses": 0, "pnl": 0.0, "count": 0})
        by_market[m]["pnl"] += p
        by_market[m]["count"] += 1
        if p > 0:
            by_market[m]["wins"] += 1
        else:
            by_market[m]["losses"] += 1

    # By direction
    by_dir = {}
    for t, p in pnls:
        d = t.get("direction") or "YES"
        by_dir.setdefault(d, {"pnl": 0.0, "count": 0, "wins": 0})
        by_dir[d]["pnl"] += p
        by_dir[d]["count"] += 1
        if p > 0:
            by_dir[d]["wins"] += 1

    # Calibration buckets
    buckets = {"0-20": [], "20-40": [], "40-60": [], "60-80": [], "80-100": []}
    for t, p in pnls:
        price = float(t.get("entry_price") or 0) * 100
        if price < 20:
            key = "0-20"
        elif price < 40:
            key = "20-40"
        elif price < 60:
            key = "40-60"
        elif price < 80:
            key = "60-80"
        else:
            key = "80-100"
        buckets[key].append(1 if p > 0 else 0)
    calibration = []
    for rng, outcomes in buckets.items():
        calibration.append({
            "range": rng,
            "actual_win_rate": (sum(outcomes) / len(outcomes)) if outcomes else 0,
            "count": len(outcomes),
        })

    # Cumulative P&L series (last 200 trades)
    cum = 0.0
    cum_series = []
    for t, p in sorted_pnls[-200:]:
        cum += p
        cum_series.append({
            "date": (t.get("trade_date") or "")[:10],
            "pnl": round(cum, 2),
        })

    # Daily P&L series for bar chart
    daily_series = [{"date": k, "pnl": round(v, 2)} for k, v in sorted(daily_pnl.items())]

    # Top wins and losses
    top_wins = sorted(pnls, key=lambda x: x[1], reverse=True)[:5]
    top_losses = sorted(pnls, key=lambda x: x[1])[:5]

    # Streak analysis
    current_streak = 0
    streak_type = None
    for _, p in reversed(sorted_pnls):
        if streak_type is None:
            streak_type = "W" if p > 0 else "L"
            current_streak = 1
        elif (p > 0 and streak_type == "W") or (p <= 0 and streak_type == "L"):
            current_streak += 1
        else:
            break

    # OpenRouter costs (static for now until API is wired)
    api_spend = float(os.environ.get("OPENROUTER_TOTAL_SPEND", 2274.64))
    credits_left = float(os.environ.get("OPENROUTER_CREDITS_LEFT", 60.36))

    return {
        "betting_wins": round(sum(p for _, p in wins), 2),
        "betting_losses": round(sum(p for _, p in losses), 2),
        "betting_net": round(total_pnl, 2),
        "open_positions": len(open_pos),
        "open_exposure": round(exposure, 2),
        "win_rate": round(win_rate, 4),
        "total_trades": len(settled),
        "unique_contracts": len(by_contract),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown": round(max_dd, 2),
        "kelly_pct": round(kelly, 4),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "current_streak": current_streak,
        "streak_type": streak_type or "N/A",
        "openrouter_total_spend": api_spend,
        "openrouter_credits_remaining": credits_left,
        "by_market": by_market,
        "by_direction": by_dir,
        "calibration": calibration,
        "cumulative_pnl": cum_series,
        "daily_pnl": daily_series[-60:],
        "top_wins": [
            {"market": t.get("market"), "contract": t.get("contract_id"), "entry": t.get("entry_price"), "pnl": round(p, 2)}
            for t, p in top_wins
        ],
        "top_losses": [
            {"market": t.get("market"), "contract": t.get("contract_id"), "entry": t.get("entry_price"), "pnl": round(p, 2)}
            for t, p in top_losses
        ],
    }


# ── API: All Kalshi trades (for Ledger tab) ──────────────────────────
@app.get("/api/kalshi-trades")
def get_kalshi_trades():
    """Return all kalshi trades for the ledger and analytics."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM kalshi_trades ORDER BY trade_date DESC"
        ).fetchall()
    return {"trades": [dict(r) for r in rows], "count": len(rows)}


# ── API: Usage summary ───────────────────────────────────────────────
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


# ── Health check ─────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
    return {"status": "ok", "db_path": DB_PATH, "trade_count": count, "timestamp": datetime.utcnow().isoformat()}


# ── Serve frontend ───────────────────────────────────────────────────
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


# ── Run with uvicorn ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("DASHBOARD_PORT", 8080)))
    uvicorn.run(app, host="0.0.0.0", port=port)
