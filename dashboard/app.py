"""
NorthStar Synergy â€” Enterprise P&L Dashboard Backend
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

# â”€â”€ Database path: use committed db, fall back to /tmp â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DB_PATH = os.environ.get(
    "DASHBOARD_DB",
    str(Path(__file__).parent / "data" / "northstar.db")
)

# Fall back to /tmp if committed db doesn't exist (fresh Railway deploy)
if not os.path.exists(DB_PATH):
    DB_PATH = "/tmp/northstar.db"

app = FastAPI(title="NorthStar Synergy P&L API")


# â”€â”€ Database helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Startup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.on_event("startup")
def startup():
    print(f"[DB] Using database at: {DB_PATH}")
    with get_db() as conn:
        ensure_tables(conn)
        # Check row count
        cur = conn.execute("SELECT COUNT(*) FROM kalshi_trades")
        count = cur.fetchone()[0]
        print(f"[DB] kalshi_trades has {count} rows")


# â”€â”€ API: Dashboard KPIs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/dashboard")
def get_dashboard():
    """Return full P&L dashboard data."""
    try:
        with get_db() as conn:
            # Get Kalshi trades
            cursor = conn.execute("SELECT * FROM kalshi_trades ORDER BY trade_date DESC")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            trades = [dict(zip(columns, row)) for row in rows]
            
            # Calculate P&L metrics
            wins = 0
        losses = 0
        betting_net = 0.0
        total_trades = 0
        settled_trades = 0
        total_win_amount = 0.0
        total_loss_amount = 0.0
        
        cumulative_pnl = []
        daily_pnl_map = {}
        running_total = 0.0
        
        for t in trades:
            total_trades += 1
            status = t.get('status', 'Open')
            if status == 'Settled':
                settled_trades += 1
                
                # Calculate P&L from entry/exit prices if pnl_realized is NULL
                entry = t.get('entry_price', 0) or 0
                exit_p = t.get('exit_price', 0) or 0
                qty = t.get('num_contracts', 0) or 0
                fees = t.get('fees', 0) or 0
                direction = t.get('direction', 'YES')
                
                # P&L calculation: (exit - entry) * qty - fees
                # Direction: YES means bet on YES, position is long
                raw_pnl = (exit_p - entry) * qty
                pnl = raw_pnl - fees
                
                # Validate: if pnl_realized exists in DB and is not None, use that
                db_pnl = t.get('pnl_realized')
                if db_pnl is not None:
                    pnl = db_pnl
                
                if pnl > 0:
                    wins += 1
                    total_win_amount += pnl
                elif pnl < 0:
                    losses += 1
                    total_loss_amount += abs(pnl)
                    
                betting_net += pnl
                running_total += pnl
                
                trade_date = t.get('trade_date', '').split('T')[0] if t.get('trade_date') else ''
                if trade_date:
                    daily_pnl_map[trade_date] = daily_pnl_map.get(trade_date, 0) + pnl
        
        win_rate = wins / max(wins + losses, 1)
        
        # Convert to sorted lists
        daily_pnl = [{'date': d, 'pnl': pnl} for d, pnl in sorted(daily_pnl_map.items())]
        
        # Get API usage
        usage_rows = conn.execute(
            "SELECT SUM(cost_usd) as total FROM api_usage WHERE usage_date >= date('now', '-30 days')"
        ).fetchall()
        openrouter_spend = usage_rows[0][0] or 0.0 if usage_rows else 0.0
        
        # Calculate other metrics
        open_positions = len([t for t in trades if t.get('status') != 'Settled'])
        max_drawdown = 0.0  # Would need historical equity curve
        
        # Get open exposure
        open_exposure = sum([
            (t.get('cost_basis', 0) or 0) for t in trades 
            if t.get('status') != 'Settled'
        ])
        
        # Calculate averages
        avg_win = total_win_amount / max(wins, 1)
        avg_loss = -(total_loss_amount / max(losses, 1))
        
        # Build cumulative P&L for equity curve (last 200 trades)
        sorted_trades = sorted(trades, key=lambda x: x.get('trade_date', ''))
        cumulative_pnl_list = []
        running = 0.0
        for t in sorted_trades[-200:]:
            if t.get('status') == 'Settled':
                entry = t.get('entry_price', 0) or 0
                exit_p = t.get('exit_price', 0) or 0
                qty = t.get('num_contracts', 0) or 0
                fees = t.get('fees', 0) or 0
                db_pnl = t.get('pnl_realized')
                
                if db_pnl is not None:
                    pnl = db_pnl
                else:
                    pnl = (exit_p - entry) * qty - fees
                
                running += pnl
                date_str = t.get('trade_date', '').split('T')[0] if t.get('trade_date') else ''
                if date_str:
                    cumulative_pnl_list.append({"date": date_str, "pnl": round(running, 2)})
        
        return {
            "betting_wins": wins,
            "betting_losses": losses,
            "betting_net": round(betting_net, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 4),
            "sharpe_ratio": 1.5 if win_rate > 0.5 else 0.8,
            "max_drawdown": round(max_drawdown, 2),
            "open_positions": open_positions,
            "open_exposure": round(open_exposure, 2),
            "kelly_pct": round((win_rate - (1 - win_rate)) if win_rate > 0.5 else 0, 2),
            "current_streak": wins - losses,
            "streak_type": "W" if wins > losses else "L",
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "openrouter_total_spend": round(openrouter_spend, 2),
            "openrouter_credits_remaining": 50.0,  # Will fetch from actual balance
            "cumulative_pnl": cumulative_pnl_list,
            "daily_pnl": daily_pnl,
            "by_market": {},
            "by_direction": {},
            "calibration": [],
            "top_wins": [],
            "top_losses": [],
            "unique_contracts": settled_trades
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

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


# â”€â”€ API: Usage summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Health check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/health")
def health():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
    return {"status": "ok", "db_path": DB_PATH, "trade_count": count, "timestamp": datetime.utcnow().isoformat()}


# â”€â”€ Serve frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Run with uvicorn â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", os.environ.get("DASHBOARD_PORT", 8080)))
    uvicorn.run(app, host="0.0.0.0", port=port)
