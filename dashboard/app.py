import json, os, re, asyncio
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from database import init_db, get_db
from analytics import router as analytics_router

app = FastAPI(title="Northstar Synergy Dashboard")
app.include_router(analytics_router)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SCALPER_DIR = r"C:\Users\chead\.openclaw\workspace-scalper"

# ── Startup ────────────────────────────────────────────────────────────────────
async def _background_sync():
    """Auto-sync Scalper data every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        try:
            from auto_populate import run_all
            run_all()
        except Exception as e:
            print(f"[AutoSync] Error: {e}")

@app.on_event("startup")
async def startup():
    await init_db()
    # Run initial sync
    try:
        from auto_populate import run_all
        r = run_all()
        print(f"[Startup Sync] {r}")
    except Exception as e:
        print(f"[Startup Sync] Error: {e}")
    asyncio.create_task(_background_sync())

# ── Root ───────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# ══════════════════════════════════════════════════════════════════════════════
# BETS
# ══════════════════════════════════════════════════════════════════════════════
class BetIn(BaseModel):
    bet_date: str
    sport: str
    game: str
    book: str = "Kalshi"
    bet_type: str = "ML"
    stake: float
    odds: Optional[str] = None
    odds_decimal: Optional[float] = None
    result: str = "PENDING"
    profit_loss: float = 0
    edge_pct: Optional[float] = None
    notes: Optional[str] = None

@app.get("/api/bets")
async def list_bets(limit: int = 200):
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM bets ORDER BY bet_date DESC, id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

@app.post("/api/bets")
async def add_bet(bet: BetIn):
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO bets (bet_date,sport,game,book,bet_type,stake,odds,odds_decimal,result,profit_loss,edge_pct,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (bet.bet_date, bet.sport, bet.game, bet.book, bet.bet_type, bet.stake,
              bet.odds, bet.odds_decimal, bet.result, bet.profit_loss, bet.edge_pct, bet.notes))
        await db.commit()
        return {"id": cur.lastrowid}
    finally:
        await db.close()

@app.put("/api/bets/{bet_id}")
async def update_bet(bet_id: int, bet: BetIn):
    db = await get_db()
    try:
        await db.execute("""
            UPDATE bets SET bet_date=?,sport=?,game=?,book=?,bet_type=?,stake=?,odds=?,
            odds_decimal=?,result=?,profit_loss=?,edge_pct=?,notes=? WHERE id=?
        """, (bet.bet_date, bet.sport, bet.game, bet.book, bet.bet_type, bet.stake,
              bet.odds, bet.odds_decimal, bet.result, bet.profit_loss, bet.edge_pct, bet.notes, bet_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

@app.delete("/api/bets/{bet_id}")
async def delete_bet(bet_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM bets WHERE id=?", (bet_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

# ── Sync Scalper logs into bets table ─────────────────────────────────────────
@app.post("/api/bets/sync-scalper")
async def sync_scalper():
    log_path = os.path.join(SCALPER_DIR, "pick_performance_log.jsonl")
    if not os.path.exists(log_path):
        return {"synced": 0, "error": "pick_performance_log.jsonl not found"}
    db = await get_db()
    synced = 0
    try:
        cur = await db.execute("SELECT game FROM bets WHERE book='Kalshi'")
        existing = {r[0] for r in await cur.fetchall()}
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                except:
                    continue
                game = rec.get("game") or rec.get("team") or str(rec)
                if game in existing:
                    continue
                result = rec.get("result", "PENDING")
                stake = float(rec.get("stake", 0) or 0)
                pl = float(rec.get("profit_loss", 0) or 0)
                if result == "WIN" and pl == 0:
                    pl = stake
                elif result == "LOSS" and pl == 0:
                    pl = -stake
                await db.execute("""
                    INSERT INTO bets (bet_date,sport,game,book,bet_type,stake,odds,result,profit_loss,edge_pct)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    rec.get("date", str(date.today())),
                    rec.get("sport", "NCAAB"),
                    game, "Kalshi",
                    rec.get("bet_type", "ML"),
                    stake,
                    str(rec.get("odds", "")),
                    result, pl,
                    rec.get("edge_pct", None)
                ))
                existing.add(game)
                synced += 1
        await db.commit()
        return {"synced": synced}
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# JOHN'S BUSINESS
# ══════════════════════════════════════════════════════════════════════════════
class JobIn(BaseModel):
    job_date: str
    client_name: str
    job_description: Optional[str] = None
    status: str = "quoted"
    invoice_amount: float
    paid: int = 0
    paid_date: Optional[str] = None
    notes: Optional[str] = None

@app.get("/api/jobs")
async def list_jobs():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM john_jobs ORDER BY job_date DESC, id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

@app.post("/api/jobs")
async def add_job(job: JobIn):
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO john_jobs (job_date,client_name,job_description,status,invoice_amount,paid,paid_date,notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (job.job_date, job.client_name, job.job_description, job.status,
              job.invoice_amount, job.paid, job.paid_date, job.notes))
        await db.commit()
        return {"id": cur.lastrowid}
    finally:
        await db.close()

@app.put("/api/jobs/{job_id}")
async def update_job(job_id: int, job: JobIn):
    db = await get_db()
    try:
        await db.execute("""
            UPDATE john_jobs SET job_date=?,client_name=?,job_description=?,status=?,
            invoice_amount=?,paid=?,paid_date=?,notes=? WHERE id=?
        """, (job.job_date, job.client_name, job.job_description, job.status,
              job.invoice_amount, job.paid, job.paid_date, job.notes, job_id))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM john_jobs WHERE id=?", (job_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# API USAGE / TOKEN COSTS
# ══════════════════════════════════════════════════════════════════════════════
class ApiUsageIn(BaseModel):
    usage_date: str
    provider: str
    model: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float
    notes: Optional[str] = None

@app.get("/api/api-usage")
async def list_api_usage():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM api_usage ORDER BY usage_date DESC, id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

@app.post("/api/api-usage")
async def add_api_usage(entry: ApiUsageIn):
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO api_usage (usage_date,provider,model,tokens_in,tokens_out,cost_usd,notes)
            VALUES (?,?,?,?,?,?,?)
        """, (entry.usage_date, entry.provider, entry.model, entry.tokens_in,
              entry.tokens_out, entry.cost_usd, entry.notes))
        await db.commit()
        return {"id": cur.lastrowid}
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# EXPENSES
# ══════════════════════════════════════════════════════════════════════════════
class ExpenseIn(BaseModel):
    expense_date: str
    segment: str
    description: str
    amount: float
    category: Optional[str] = None

@app.get("/api/expenses")
async def list_expenses():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM expenses ORDER BY expense_date DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

@app.post("/api/expenses")
async def add_expense(exp: ExpenseIn):
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO expenses (expense_date,segment,description,amount,category)
            VALUES (?,?,?,?,?)
        """, (exp.expense_date, exp.segment, exp.description, exp.amount, exp.category))
        await db.commit()
        return {"id": cur.lastrowid}
    finally:
        await db.close()

@app.delete("/api/expenses/{exp_id}")
async def delete_expense(exp_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM expenses WHERE id=?", (exp_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# REVENUE
# ══════════════════════════════════════════════════════════════════════════════
class RevenueIn(BaseModel):
    revenue_date: str
    segment: str
    description: str
    amount: float

@app.get("/api/revenue")
async def list_revenue():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM revenue ORDER BY revenue_date DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

@app.post("/api/revenue")
async def add_revenue(rev: RevenueIn):
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO revenue (revenue_date,segment,description,amount)
            VALUES (?,?,?,?)
        """, (rev.revenue_date, rev.segment, rev.description, rev.amount))
        await db.commit()
        return {"id": cur.lastrowid}
    finally:
        await db.close()

@app.delete("/api/revenue/{rev_id}")
async def delete_revenue(rev_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM revenue WHERE id=?", (rev_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# API USAGE (Anthropic)
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/usage/anthropic")
async def get_anthropic_usage(days: int = 1):
    """Get Anthropic API usage for last N days"""
    db = await get_db()
    try:
        # Total spend
        cur = await db.execute(
            """SELECT 
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')""",
            (days,)
        )
        total = await cur.fetchone()

        # By model
        cur = await db.execute(
            """SELECT 
                model,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')
            GROUP BY model
            ORDER BY total_cost DESC""",
            (days,)
        )
        by_model = [dict(r) for r in await cur.fetchall()]

        # By agent (from notes field: "agent:cliff")
        cur = await db.execute(
            """SELECT 
                CASE 
                    WHEN notes LIKE 'agent:%' THEN SUBSTR(notes, 7)
                    ELSE 'unknown'
                END as agent_id,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')
            GROUP BY agent_id
            ORDER BY total_cost DESC""",
            (days,)
        )
        by_agent = [dict(r) for r in await cur.fetchall()]

        # Daily breakdown
        cur = await db.execute(
            """SELECT 
                usage_date,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')
            GROUP BY usage_date
            ORDER BY usage_date DESC""",
            (days,)
        )
        by_date = [dict(r) for r in await cur.fetchall()]

        return {
            "period_days": days,
            "total": dict(total) if total else {"total_tokens": 0, "total_cost": 0, "request_count": 0},
            "by_model": by_model,
            "by_agent": by_agent,
            "by_date": by_date,
            "provider": "anthropic"
        }
    finally:
        await db.close()

@app.post("/api/usage/sync-anthropic")
async def sync_anthropic_usage():
    """Sync Anthropic usage from tracker to dashboard"""
    try:
        from sync_anthropic_usage import sync_to_dashboard
        result = await sync_to_dashboard()
        return result
    except ImportError:
        return {"error": "sync_anthropic_usage module not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/usage/summary")
async def get_usage_summary(days: int = 7):
    """Get all API usage summary"""
    db = await get_db()
    try:
        # All providers
        cur = await db.execute(
            """SELECT 
                provider,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE usage_date >= date('now', '-' || ? || ' days')
            GROUP BY provider
            ORDER BY total_cost DESC""",
            (days,)
        )
        by_provider = [dict(r) for r in await cur.fetchall()]

        # Grand total
        cur = await db.execute(
            """SELECT 
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE usage_date >= date('now', '-' || ? || ' days')""",
            (days,)
        )
        grand_total = await cur.fetchone()

        return {
            "period_days": days,
            "grand_total": dict(grand_total) if grand_total else {},
            "by_provider": by_provider
        }
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY ENDPOINT — powers the dashboard KPIs and charts
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/dashboard")
async def get_dashboard():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM kalshi_trades")
        rows = [dict(r) for r in await cur.fetchall()]

        settled = [r for r in rows if r.get("status") == "Settled"]
        open_pos = [r for r in rows if r.get("status") == "Open"]

        def pnl(r):
            try:
                return (float(r["exit_price"] or 0) - float(r["entry_price"] or 0)) * float(r["num_contracts"] or 0) - float(r["fees"] or 0)
            except:
                return 0

        settled_pnl = [pnl(r) for r in settled]
        wins = sum(p for p in settled_pnl if p > 0)
        losses = sum(p for p in settled_pnl if p < 0)
        net = sum(settled_pnl)
        win_rate = len([p for p in settled_pnl if p > 0]) / max(len(settled_pnl), 1)
        exposure = sum(float(r.get("cost_basis") or 0) for r in open_pos)

        return {
            "betting_wins": round(wins, 2),
            "betting_losses": round(losses, 2),
            "betting_net": round(net, 2),
            "open_positions": len(open_pos),
            "open_exposure": round(exposure, 2),
            "win_rate": round(win_rate, 4),
            "total_trades": len(settled),
            "openrouter_total_spend": 2274.64,
            "openrouter_credits_remaining": 60.36,
        }
    finally:
        await db.close()

@app.get("/api/kalshi-trades")
async def get_kalshi_trades(limit: int = 500):
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM kalshi_trades ORDER BY trade_date DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in await cur.fetchall()]
        return rows
    finally:
        await db.close()

@app.get("/api/summary")
async def summary():
    db = await get_db()
    try:
        # --- Betting ---
        cur = await db.execute("SELECT COUNT(*) c, SUM(profit_loss) pl, SUM(stake) staked, result FROM bets GROUP BY result")
        bet_rows = await cur.fetchall()
        bet_stats = {"total_pl": 0, "wins": 0, "losses": 0, "pending": 0, "total_staked": 0}
        for r in bet_rows:
            bet_stats["total_pl"] += (r["pl"] or 0)
            bet_stats["total_staked"] += (r["staked"] or 0)
            if r["result"] == "WIN":   bet_stats["wins"] = r["c"]
            elif r["result"] == "LOSS": bet_stats["losses"] = r["c"]
            elif r["result"] == "PENDING": bet_stats["pending"] = r["c"]
        total_settled = bet_stats["wins"] + bet_stats["losses"]
        bet_stats["win_rate"] = round(bet_stats["wins"] / total_settled * 100, 1) if total_settled else 0
        bet_stats["roi"] = round(bet_stats["total_pl"] / bet_stats["total_staked"] * 100, 2) if bet_stats["total_staked"] else 0

        # --- John's Business ---
        cur = await db.execute("SELECT COUNT(*) c, SUM(invoice_amount) total, SUM(CASE WHEN paid=1 THEN invoice_amount ELSE 0 END) collected, SUM(CASE WHEN paid=0 THEN invoice_amount ELSE 0 END) outstanding FROM john_jobs")
        jr = dict(await cur.fetchone())

        # --- API Costs ---
        cur = await db.execute("SELECT SUM(cost_usd) total, provider FROM api_usage GROUP BY provider")
        api_rows = await cur.fetchall()
        api_total = sum(r["total"] or 0 for r in api_rows)
        api_by_provider = {r["provider"]: round(r["total"] or 0, 4) for r in api_rows}

        # --- Expenses ---
        cur = await db.execute("SELECT SUM(amount) total FROM expenses")
        exp_total = (await cur.fetchone())[0] or 0

        # --- Revenue ---
        cur = await db.execute("SELECT SUM(amount) total FROM revenue")
        rev_total = (await cur.fetchone())[0] or 0

        # --- P&L by month (last 6 months, betting) ----
        cur = await db.execute("""
            SELECT strftime('%Y-%m', bet_date) mo, SUM(profit_loss) pl
            FROM bets WHERE result != 'PENDING'
            GROUP BY mo ORDER BY mo DESC LIMIT 6
        """)
        monthly_bets = [dict(r) for r in await cur.fetchall()]

        # --- John revenue by client ---
        cur = await db.execute("""
            SELECT client_name, SUM(invoice_amount) total, SUM(CASE WHEN paid=1 THEN invoice_amount ELSE 0 END) paid
            FROM john_jobs GROUP BY client_name ORDER BY total DESC
        """)
        john_clients = [dict(r) for r in await cur.fetchall()]

        # --- Net P&L company-wide ---
        total_revenue = rev_total + (jr["collected"] or 0) + max(0, bet_stats["total_pl"])
        total_costs = exp_total + api_total + max(0, -bet_stats["total_pl"])
        net_pl = (rev_total + (jr["collected"] or 0) + bet_stats["total_pl"]) - exp_total - api_total

        return {
            "summary": {
                "total_revenue": round(rev_total + (jr["collected"] or 0), 2),
                "total_expenses": round(exp_total + api_total, 2),
                "net_pl": round(net_pl, 2),
            },
            "betting": {**bet_stats, "total_pl": round(bet_stats["total_pl"], 2)},
            "john": {
                "jobs": jr["c"] or 0,
                "invoiced": round(jr["total"] or 0, 2),
                "collected": round(jr["collected"] or 0, 2),
                "outstanding": round(jr["outstanding"] or 0, 2),
            },
            "api_costs": {
                "total": round(api_total, 4),
                "by_provider": api_by_provider,
            },
            "monthly_betting_pl": list(reversed(monthly_bets)),
            "john_clients": john_clients,
        }
    finally:
        await db.close()

# ══════════════════════════════════════════════════════════════════════════════
# BETTING P&L TIMESERIES
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/bets/timeseries")
async def bet_timeseries():
    db = await get_db()
    try:
        cur = await db.execute("""
            SELECT bet_date, SUM(profit_loss) daily_pl
            FROM bets WHERE result != 'PENDING'
            GROUP BY bet_date ORDER BY bet_date
        """)
        rows = await cur.fetchall()
        running = 0
        series = []
        for r in rows:
            running += (r["daily_pl"] or 0)
            series.append({"date": r["bet_date"], "daily_pl": round(r["daily_pl"] or 0, 2), "cumulative": round(running, 2)})
        return series
    finally:
        await db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8765, reload=False)
