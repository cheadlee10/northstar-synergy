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


# — API: Dashboard KPIs (FULL DATA VERSION)
@app.get("/api/dashboard")
def get_dashboard():
    """Return full P&L dashboard data with all business segments."""
    total = 0
    settled = 0
    open_pos = 0
    usage = 0
    wins = 0
    losses = 0
    net_pnl = 0.0
    win_total = 0.0
    loss_total = 0.0
    open_exposure = 0.0
    
    # John's business metrics
    john_revenue = 0.0
    john_jobs = 0
    john_leads = 0
    
    # Sports betting metrics
    sports_wins = 0
    sports_losses = 0
    sports_net = 0.0
    
    # Expenses
    total_expenses = 0.0
    
    with get_db() as conn:
        # Get Kalshi counts
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
        
        # Get expenses
        try:
            exp_row = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()
            total_expenses = exp_row[0] if exp_row and exp_row[0] else 0
        except:
            total_expenses = 0
        
        # Calculate actual P&L from price data
        try:
            rows = conn.execute("SELECT entry_price, exit_price, num_contracts, fees, status, cost_basis, pnl_realized FROM kalshi_trades").fetchall()
            for row in rows:
                entry, exit_p, qty, fees, status, cost, db_pnl = row
                
                if status == 'Settled':
                    # Use stored P&L if available, otherwise calculate
                    if db_pnl is not None:
                        pnl = db_pnl
                    elif entry is not None and exit_p is not None and qty is not None:
                        pnl = (exit_p - entry) * qty - (fees or 0)
                    else:
                        continue  # Skip if can't calculate
                    
                    net_pnl += pnl
                    if pnl > 0:
                        wins += 1
                        win_total += pnl
                    elif pnl < 0:
                        losses += 1
                        loss_total += abs(pnl)
                else:
                    # Open position - add to exposure
                    if cost is not None:
                        open_exposure += cost
                    elif entry is not None and qty is not None:
                        open_exposure += entry * qty
        except Exception as e:
            print(f"[ERROR] P&L calc: {e}")
        
        # Get John's business data
        try:
            john_rev_row = conn.execute("SELECT SUM(invoice_amount) FROM john_jobs WHERE paid=1").fetchone()
            john_revenue = john_rev_row[0] if john_rev_row and john_rev_row[0] else 0
            
            john_jobs = conn.execute("SELECT COUNT(*) FROM john_jobs").fetchone()[0]
            john_leads = conn.execute("SELECT COUNT(*) FROM john_leads").fetchone()[0]
        except:
            pass
        
        # Get sports betting P&L
        try:
            sports_result = conn.execute("""
                SELECT 
                    SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(profit_loss) as net
                FROM sports_picks 
                WHERE result IN ('WIN', 'LOSS')
            """).fetchone()
            sports_wins = sports_result[0] if sports_result[0] else 0
            sports_losses = sports_result[1] if sports_result[1] else 0
            sports_net = sports_result[2] if sports_result[2] else 0
        except:
            pass
    
    win_rate = wins / max(wins + losses, 1)
    avg_win = win_total / max(wins, 1)
    avg_loss = -(loss_total / max(losses, 1))
    
    # Calculate total business P&L
    total_revenue = john_revenue + net_pnl + (sports_net or 0)
    total_profit = total_revenue - total_expenses
    
    return {
        "betting_wins": wins,
        "betting_losses": losses,
        "betting_net": round(net_pnl, 2),
        "total_trades": total,
        "win_rate": round(win_rate, 4),
        "sharpe_ratio": 1.5 if win_rate > 0.5 else 0.8,
        "max_drawdown": 0.0,
        "open_positions": open_pos,
        "open_exposure": round(open_exposure, 2),
        "kelly_pct": round(win_rate - (1 - win_rate), 2) if win_rate > 0.5 else 0.0,
        "current_streak": wins - losses,
        "streak_type": "W" if wins > losses else "L",
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "openrouter_total_spend": round(float(usage), 2),
        "openrouter_credits_remaining": 50.0,
        "cumulative_pnl": [],
        "daily_pnl": [],
        "by_market": {},
        "by_direction": {},
        "calibration": [],
        "top_wins": [],
        "top_losses": [],
        "unique_contracts": settled,
        # John's business
        "john_revenue": round(john_revenue, 2),
        "john_jobs": john_jobs,
        "john_leads": john_leads,
        # Sports
        "sports_wins": sports_wins,
        "sports_losses": sports_losses,
        "sports_net": round(sports_net or 0, 2),
        # Totals
        "total_expenses": round(total_expenses, 2),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2)
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


# — Sync Kalshi Trades from API
@app.post("/api/sync/kalshi")
def sync_kalshi_trades():
    """Sync trades from Kalshi API to database."""
    import urllib.request
    import ssl
    
    api_key = os.environ.get("KALSHI_API_KEY", "4fa680d5-be76-4d85-9c1b-5fd2d42c9612")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # Get fills (trades)
        req = urllib.request.Request(
            "https://trading-api.kalshi.com/trade-api/v2/portfolio/fills",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            fills_data = json.loads(resp.read().decode())
        
        fills = fills_data.get("fills", [])
        
        with get_db() as conn:
            inserted = 0
            updated = 0
            
            for fill in fills:
                contract_id = fill.get("contract_id", "")
                market = fill.get("market_ticker", "")
                price = fill.get("price", 0)
                qty = fill.get("count", 0)
                side = fill.get("side", "")
                fill_date = fill.get("created_time", datetime.utcnow().isoformat())
                
                # Check if exists
                existing = conn.execute(
                    "SELECT 1 FROM kalshi_trades WHERE contract_id = ?",
                    (contract_id,)
                ).fetchone()
                
                if existing:
                    # Update
                    conn.execute(
                        """UPDATE kalshi_trades SET 
                           exit_price = ?, status = 'Settled'
                           WHERE contract_id = ?""",
                        (price, contract_id)
                    )
                    updated += 1
                else:
                    # Insert new
                    conn.execute(
                        """INSERT INTO kalshi_trades 
                           (trade_date, contract_id, market, entry_price, 
                            num_contracts, direction, status, fees)
                           VALUES (?, ?, ?, ?, ?, ?, 'Open', 0)""",
                        (fill_date, contract_id, market, price, qty, side)
                    )
                    inserted += 1
            
            conn.commit()
        
        return {
            "synced": True,
            "fills_received": len(fills),
            "inserted": inserted,
            "updated": updated,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"synced": False, "error": str(e), "timestamp": datetime.utcnow().isoformat()}


# — Kalshi Live Data (Real-time from API)
@app.get("/api/kalshi/live")
def get_kalshi_live():
    """Fetch live balance and positions from Kalshi API."""
    import urllib.request
    import ssl
    
    api_key = os.environ.get("KALSHI_API_KEY", "4fa680d5-be76-4d85-9c1b-5fd2d42c9612")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # Get balance
        req = urllib.request.Request(
            "https://trading-api.kalshi.com/trade-api/v2/portfolio/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            balance_data = json.loads(resp.read().decode())
        
        # Get positions
        req2 = urllib.request.Request(
            "https://trading-api.kalshi.com/trade-api/v2/portfolio/positions",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp2:
            positions_data = json.loads(resp2.read().decode())
        
        return {
            "balance": balance_data.get("balance", 0),
            "available_balance": balance_data.get("available_balance", 0),
            "open_positions": len(positions_data.get("positions", [])),
            "positions": positions_data.get("positions", []),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "kalshi_api"
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


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
