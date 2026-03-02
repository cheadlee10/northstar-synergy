"""
analytics.py — advanced query endpoints for Northstar dashboard
Imported by app.py
"""
import sqlite3, json
from fastapi import APIRouter
from database import DB_PATH, get_db

router = APIRouter(prefix="/api")

PERIOD_SQL = {
    "today":   "date(snap_date) = date('now','localtime')",
    "week":    "date(snap_date) >= date('now','localtime','-7 days')",
    "month":   "strftime('%Y-%m',snap_date) = strftime('%Y-%m','now','localtime')",
    "quarter": "snap_date >= date('now','localtime','start of year','+' || (((cast(strftime('%m','now') as int)-1)/3)*3) || ' months')",
    "year":    "strftime('%Y',snap_date) = strftime('%Y','now','localtime')",
    "all":     "1=1",
}

BET_PERIOD_SQL = {
    "today":   "date(bet_date) = date('now','localtime')",
    "week":    "date(bet_date) >= date('now','localtime','-7 days')",
    "month":   "strftime('%Y-%m',bet_date) = strftime('%Y-%m','now','localtime')",
    "quarter": "strftime('%Y-%m',bet_date) >= strftime('%Y-%m',date('now','localtime','-3 months'))",
    "year":    "strftime('%Y',bet_date) = strftime('%Y','now','localtime')",
    "all":     "1=1",
}

# ── KALSHI LIVE SUMMARY ────────────────────────────────────────────────────────
@router.get("/kalshi/summary")
async def kalshi_summary():
    db = await get_db()
    try:
        # Latest snapshot for live balance
        cur = await db.execute("SELECT * FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 1")
        latest = dict((await cur.fetchone()) or {})

        # Daily P&L — last 30 days, one snapshot per day (end-of-day LAST snapshot)
        cur = await db.execute("""
            WITH daily_eod AS (
                SELECT *
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (
                               PARTITION BY snap_date
                               ORDER BY snapshot_ts DESC
                           ) AS rn
                    FROM kalshi_snapshots
                )
                WHERE rn = 1
            )
            SELECT snap_date,
                   total_pnl_cents AS max_pnl,
                   balance_cents AS max_bal,
                   total_fills AS max_fills,
                   win_count AS wins,
                   loss_count AS losses
            FROM daily_eod
            ORDER BY snap_date DESC LIMIT 30
        """)
        daily = [dict(r) for r in await cur.fetchall()]

        # Category breakdown (latest snapshot)
        categories = {}
        if latest:
            categories = {
                "weather": round((latest.get("weather_pnl_cents") or 0) / 100, 2),
                "crypto":  round((latest.get("crypto_pnl_cents") or 0) / 100, 2),
                "econ":    round((latest.get("econ_pnl_cents") or 0) / 100, 2),
                "market_making": round((latest.get("mm_pnl_cents") or 0) / 100, 2),
                "lip_rewards":   round((latest.get("lip_rewards_cents") or 0) / 100, 2),
            }

        # Period P&L — calculate balance change using end-of-day LAST snapshots
        periods = {}
        for period, cond in PERIOD_SQL.items():
            # First EOD snapshot in period
            cur = await db.execute(f"""
                WITH daily_eod AS (
                    SELECT *
                    FROM (
                        SELECT *,
                               ROW_NUMBER() OVER (
                                   PARTITION BY snap_date
                                   ORDER BY snapshot_ts DESC
                               ) AS rn
                        FROM kalshi_snapshots
                    )
                    WHERE rn = 1
                )
                SELECT balance_cents
                FROM daily_eod
                WHERE {cond}
                ORDER BY snap_date ASC
                LIMIT 1
            """)
            first = await cur.fetchone()
            start_bal = (first[0] if first else 0) or 0

            # Last EOD snapshot in period
            cur = await db.execute(f"""
                WITH daily_eod AS (
                    SELECT *
                    FROM (
                        SELECT *,
                               ROW_NUMBER() OVER (
                                   PARTITION BY snap_date
                                   ORDER BY snapshot_ts DESC
                               ) AS rn
                        FROM kalshi_snapshots
                    )
                    WHERE rn = 1
                )
                SELECT balance_cents, total_fills, win_count, loss_count
                FROM daily_eod
                WHERE {cond}
                ORDER BY snap_date DESC
                LIMIT 1
            """)
            last = await cur.fetchone()

            if last:
                end_bal = (last[0] or 0)
                pnl = (end_bal - start_bal) / 100
                periods[period] = {
                    "pnl_usd":  round(pnl, 2),
                    "fills":    last[1] or 0,
                    "wins":     last[2] or 0,
                    "losses":   last[3] or 0,
                }

        return {
            "live": {
                "balance_usd":    round((latest.get("balance_cents") or 0) / 100, 2),
                "total_pnl_usd":  round((latest.get("total_pnl_cents") or 0) / 100, 2),
                "open_positions": latest.get("open_positions") or 0,
                "total_orders":   latest.get("total_orders") or 0,
                "total_fills":    latest.get("total_fills") or 0,
                "win_count":      latest.get("win_count") or 0,
                "loss_count":     latest.get("loss_count") or 0,
                "last_update":    latest.get("snapshot_ts"),
            },
            "categories":   categories,
            "periods":       periods,
            "daily":         list(reversed(daily)),
        }
    finally:
        await db.close()

# ── KALSHI TIMESERIES ──────────────────────────────────────────────────────────
@router.get("/kalshi/timeseries")
async def kalshi_timeseries():
    db = await get_db()
    try:
        cur = await db.execute("""
            WITH daily_eod AS (
                SELECT *
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (
                               PARTITION BY snap_date
                               ORDER BY snapshot_ts DESC
                           ) AS rn
                    FROM kalshi_snapshots
                )
                WHERE rn = 1
            )
            SELECT snap_date,
                   total_pnl_cents AS total_pnl,
                   balance_cents AS balance,
                   weather_pnl_cents AS weather,
                   crypto_pnl_cents AS crypto,
                   econ_pnl_cents AS econ,
                   mm_pnl_cents AS mm
            FROM daily_eod
            ORDER BY snap_date
        """)
        rows = await cur.fetchall()
        return [{"date": r[0],
                 "total_pnl": round((r[1] or 0)/100, 2),
                 "balance": round((r[2] or 0)/100, 2),
                 "weather": round((r[3] or 0)/100, 2),
                 "crypto":  round((r[4] or 0)/100, 2),
                 "econ":    round((r[5] or 0)/100, 2),
                 "mm":      round((r[6] or 0)/100, 2)} for r in rows]
    finally:
        await db.close()

# ── SPORTS PICKS ────────────────────────────────────────────────────────────────
@router.get("/sports-picks")
async def sports_picks():
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM sports_picks ORDER BY pick_date DESC, id DESC")
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()

# ── SPORTS PROFITABILITY ────────────────────────────────────────────────────────
@router.get("/sports-picks/profitability")
async def sports_profitability():
    db = await get_db()
    try:
        # By sport
        cur = await db.execute("""
            SELECT sport,
                   COUNT(*) total, SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
                   SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) losses,
                   SUM(profit_loss) total_pl, SUM(stake) total_staked,
                   AVG(edge_val) avg_edge
            FROM sports_picks WHERE result != 'PENDING'
            GROUP BY sport ORDER BY total_pl DESC
        """)
        by_sport = [dict(r) for r in await cur.fetchall()]

        # By edge bucket
        cur = await db.execute("""
            SELECT edge_bucket,
                   COUNT(*) total, SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
                   SUM(profit_loss) total_pl, SUM(stake) total_staked
            FROM sports_picks WHERE result != 'PENDING' AND edge_bucket IS NOT NULL
            GROUP BY edge_bucket ORDER BY edge_bucket
        """)
        by_edge = [dict(r) for r in await cur.fetchall()]

        # By framing type
        cur = await db.execute("""
            SELECT framing_type,
                   COUNT(*) total, SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
                   SUM(profit_loss) total_pl
            FROM sports_picks WHERE result != 'PENDING' AND framing_type IS NOT NULL
            GROUP BY framing_type ORDER BY total_pl DESC
        """)
        by_framing = [dict(r) for r in await cur.fetchall()]

        # P&L by period
        cur = await db.execute("""
            SELECT strftime('%Y-%m', pick_date) month,
                   COUNT(*) total, SUM(profit_loss) pl,
                   SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins
            FROM sports_picks WHERE result != 'PENDING'
            GROUP BY month ORDER BY month
        """)
        by_month = [dict(r) for r in await cur.fetchall()]

        # Top games by P&L
        cur = await db.execute("""
            SELECT game, pick, sport, pick_date, ml, edge_val, result, profit_loss
            FROM sports_picks WHERE result != 'PENDING'
            ORDER BY profit_loss DESC LIMIT 20
        """)
        top_picks = [dict(r) for r in await cur.fetchall()]

        return {
            "by_sport":   by_sport,
            "by_edge":    by_edge,
            "by_framing": by_framing,
            "by_month":   by_month,
            "top_picks":  top_picks,
        }
    finally:
        await db.close()

# ── ENHANCED SUMMARY WITH PERIOD ────────────────────────────────────────────────
@router.get("/summary/period")
async def summary_by_period(period: str = "all"):
    cond = BET_PERIOD_SQL.get(period, "1=1")
    db = await get_db()
    try:
        # Betting P&L
        cur = await db.execute(f"""
            SELECT SUM(profit_loss) pl, SUM(stake) staked,
                   SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
                   SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) losses,
                   COUNT(*) total
            FROM bets WHERE {cond}
        """)
        br = dict(await cur.fetchone())

        # John's business for period
        jcond = cond.replace("bet_date", "job_date")
        cur = await db.execute(f"""
            SELECT SUM(invoice_amount) invoiced,
                   SUM(CASE WHEN paid=1 THEN invoice_amount ELSE 0 END) collected,
                   COUNT(*) jobs
            FROM john_jobs WHERE {jcond}
        """)
        jr = dict(await cur.fetchone())

        # API costs for period
        acond = cond.replace("bet_date", "usage_date")
        cur = await db.execute(f"SELECT SUM(cost_usd) total FROM api_usage WHERE {acond}")
        api_cost = (await cur.fetchone())[0] or 0

        # Revenue for period
        rcond = cond.replace("bet_date", "revenue_date")
        cur = await db.execute(f"SELECT SUM(amount) total FROM revenue WHERE {rcond}")
        rev = (await cur.fetchone())[0] or 0

        # Expenses for period
        econd = cond.replace("bet_date", "expense_date")
        cur = await db.execute(f"SELECT SUM(amount) total FROM expenses WHERE {econd}")
        exp = (await cur.fetchone())[0] or 0

        bet_pl = br["pl"] or 0
        john_collected = jr["collected"] or 0
        net = (rev + john_collected + bet_pl) - (exp + api_cost)

        return {
            "period": period,
            "net_pl": round(net, 2),
            "betting": {
                "pl": round(bet_pl, 2),
                "staked": round(br["staked"] or 0, 2),
                "wins": br["wins"] or 0,
                "losses": br["losses"] or 0,
                "total": br["total"] or 0,
                "win_rate": round((br["wins"] or 0) / max(1, (br["wins"] or 0) + (br["losses"] or 0)) * 100, 1),
                "roi": round(bet_pl / max(1, br["staked"] or 1) * 100, 2),
            },
            "john": {
                "jobs": jr["jobs"] or 0,
                "invoiced": round(jr["invoiced"] or 0, 2),
                "collected": round(jr["collected"] or 0, 2),
            },
            "api_cost": round(api_cost, 4),
            "revenue": round(rev, 2),
            "expenses": round(exp, 2),
        }
    finally:
        await db.close()

# ── FULL SYNC TRIGGER ────────────────────────────────────────────────────────────
@router.post("/sync")
async def trigger_sync():
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from auto_populate import run_all
        result = run_all()
    except Exception as e:
        from sync_scalper import sync
        result = sync()
        result['auto_populate_error'] = str(e)
    return result
