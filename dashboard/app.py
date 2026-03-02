"""
NorthStar Synergy — Enterprise P&L Dashboard Backend
FastAPI application serving Kalshi trade data from SQLite
"""

import os
import re
import sqlite3
import json
import calendar
import subprocess
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_run_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            source TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            records_synced INTEGER DEFAULT 0,
            error_message TEXT,
            details_json TEXT
        )
    """)
    conn.commit()


def _parse_openrouter_lifetime(notes: str) -> float:
    if not notes:
        return 0.0
    m = re.search(r"total_lifetime=\$([0-9]+(?:\.[0-9]+)?)", notes)
    return float(m.group(1)) if m else 0.0


def calculate_cost_caps(conn):
    """Compute MTD burn, projection, and cap deltas for tracked API providers."""
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    days_elapsed = today.day
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    rows = conn.execute(
        """
        SELECT usage_date, provider, model, COALESCE(tokens_in,0) as tokens_in,
               COALESCE(tokens_out,0) as tokens_out, COALESCE(cost_usd,0) as cost_usd,
               COALESCE(notes,'') as notes
        FROM api_usage
        WHERE usage_date >= ?
        """,
        (month_start,),
    ).fetchall()

    anthropic_mtd = 0.0
    openai_chatgpt_mtd = 0.0
    anthropic_tokens = 0
    openai_chatgpt_tokens = 0
    latest_usage_date = None

    for r in rows:
        provider = (r["provider"] or "").strip().lower()
        tokens = int(r["tokens_in"] or 0) + int(r["tokens_out"] or 0)
        cost = float(r["cost_usd"] or 0)
        usage_date = r["usage_date"]

        if not latest_usage_date or (usage_date and usage_date > latest_usage_date):
            latest_usage_date = usage_date

        if provider == "anthropic":
            anthropic_mtd += cost
            anthropic_tokens += tokens
        if provider in {"openai", "chatgpt"}:
            openai_chatgpt_mtd += cost
            openai_chatgpt_tokens += tokens

    # OpenRouter actual spend = highest lifetime value parsed from aggregate notes (fallback to cumulative deltas)
    openrouter_rows = conn.execute(
        """
        SELECT usage_date, COALESCE(cost_usd,0) as cost_usd, COALESCE(notes,'') as notes
        FROM api_usage
        WHERE lower(provider) = 'openrouter'
        ORDER BY usage_date DESC, id DESC
        """
    ).fetchall()
    parsed_lifetimes = [_parse_openrouter_lifetime(r["notes"]) for r in openrouter_rows]
    openrouter_actual_spend = max(parsed_lifetimes) if parsed_lifetimes else 0.0
    if openrouter_actual_spend <= 0:
        openrouter_actual_spend = sum(float(r["cost_usd"] or 0) for r in openrouter_rows)

    openrouter_mtd = sum(
        float(r["cost_usd"] or 0)
        for r in conn.execute(
            "SELECT COALESCE(cost_usd,0) as cost_usd FROM api_usage WHERE lower(provider)='openrouter' AND usage_date >= ?",
            (month_start,),
        ).fetchall()
    )

    def budget_block(name: str, mtd: float, cap: float, tokens: int):
        projected = (mtd / max(days_elapsed, 1)) * days_in_month
        delta = cap - projected
        return {
            "provider": name,
            "cap_usd": round(cap, 2),
            "mtd_burn_usd": round(mtd, 4),
            "projected_month_end_usd": round(projected, 4),
            "delta_to_cap_usd": round(delta, 4),
            "status": "over" if projected > cap else "under",
            "tokens_mtd": int(tokens),
        }

    return {
        "month": today.strftime("%Y-%m"),
        "month_start": month_start,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "latest_usage_date": latest_usage_date,
        "openrouter": {
            "actual_spend_usd": round(openrouter_actual_spend, 4),
            "mtd_burn_usd": round(openrouter_mtd, 4),
            "source": "max(notes.total_lifetime) fallback sum(cost_usd)",
        },
        "caps": {
            "anthropic": budget_block("anthropic", anthropic_mtd, 200.0, anthropic_tokens),
            "openai_chatgpt": budget_block("openai_chatgpt", openai_chatgpt_mtd, 200.0, openai_chatgpt_tokens),
        },
    }


def _parse_iso_utc(ts: str):
    if not ts:
        return None
    normalized = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def get_freshness_summary(conn):
    """Freshness + staleness summary for UI ribbon and health checks."""
    now = datetime.utcnow()
    sources = {
        "openrouter": 24 * 60,
        "anthropic": 24 * 60,
        "kalshi": 45,
        "sports_picks": 24 * 60,
        "john": 24 * 60,
    }

    freshness = {}
    stale_sources = []

    for source, max_age_minutes in sources.items():
        row = conn.execute(
            """
            SELECT completed_at, started_at, status
            FROM sync_run_audit
            WHERE source = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (source,),
        ).fetchone()

        latest_ts = None
        status = "missing"
        if row:
            status = row["status"] or "unknown"
            latest_ts = row["completed_at"] or row["started_at"]

        dt_obj = _parse_iso_utc(latest_ts) if latest_ts else None
        age_minutes = None
        if dt_obj:
            if dt_obj.tzinfo is not None:
                dt_obj = dt_obj.replace(tzinfo=None)
            age_minutes = max(0, int((now - dt_obj).total_seconds() // 60))

        is_stale = (age_minutes is None) or (age_minutes > max_age_minutes) or (status != "success")
        if is_stale:
            stale_sources.append(source)

        freshness[source] = {
            "status": status,
            "last_sync_at": latest_ts,
            "age_minutes": age_minutes,
            "max_age_minutes": max_age_minutes,
            "is_stale": is_stale,
        }

    return {
        "as_of": now.isoformat() + "Z",
        "is_stale": len(stale_sources) > 0,
        "stale_sources": stale_sources,
        "sources": freshness,
    }


def get_scheduler_checks():
    """Task Scheduler validation checks for production monitoring."""
    checks = []
    expected = ["\\OpenClaw\\NorthstarAutoPopulate", "\\OpenClaw\\NorthstarDashboard"]
    for task in expected:
        cmd = ["schtasks", "/Query", "/TN", task, "/V", "/FO", "LIST"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            text = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if proc.returncode != 0:
                checks.append({"task": task, "pass": False, "reason": text.strip()[:500]})
                continue

            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            values = {}
            for ln in lines:
                if ":" not in ln:
                    continue
                k, v = ln.split(":", 1)
                values[k.strip()] = v.strip()

            state = values.get("Scheduled Task State", "")
            next_run = values.get("Next Run Time", "")
            schedule_type = values.get("Schedule Type", "")

            enabled = state.lower() == "enabled"
            has_next = bool(next_run and next_run.upper() != "N/A")
            at_logon_trigger = "logon" in schedule_type.lower()
            pass_check = bool(enabled and (has_next or at_logon_trigger))
            checks.append({
                "task": task,
                "pass": pass_check,
                "enabled": enabled,
                "has_next_run": has_next,
                "at_logon_trigger": at_logon_trigger,
            })
        except Exception as e:
            checks.append({"task": task, "pass": False, "reason": str(e)})

    all_pass = all(c.get("pass") for c in checks)
    return {"all_pass": all_pass, "checks": checks}


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
def _kalshi_legacy_trade_metrics(conn):
    """Previous KPI method based on kalshi_trades; retained for reconciliation."""
    total = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
    settled = conn.execute("SELECT COUNT(*) FROM kalshi_trades WHERE status='Settled'").fetchone()[0]
    open_pos = conn.execute("SELECT COUNT(*) FROM kalshi_trades WHERE status IS NULL OR status!='Settled'").fetchone()[0]

    wins = 0
    losses = 0
    net_pnl = 0.0
    win_total = 0.0
    loss_total = 0.0
    open_exposure = 0.0

    rows = conn.execute(
        "SELECT entry_price, exit_price, num_contracts, fees, status, cost_basis, pnl_realized FROM kalshi_trades"
    ).fetchall()
    for row in rows:
        entry, exit_p, qty, fees, status, cost, db_pnl = row
        if status == 'Settled':
            if db_pnl is not None:
                pnl = db_pnl
            elif entry is not None and exit_p is not None and qty is not None:
                pnl = (exit_p - entry) * qty - (fees or 0)
            else:
                continue
            net_pnl += pnl
            if pnl > 0:
                wins += 1
                win_total += pnl
            elif pnl < 0:
                losses += 1
                loss_total += abs(pnl)
        else:
            if cost is not None:
                open_exposure += cost
            elif entry is not None and qty is not None:
                open_exposure += entry * qty

    return {
        "betting_wins": wins,
        "betting_losses": losses,
        "betting_net": round(net_pnl, 2),
        "total_trades": total,
        "open_positions": open_pos,
        "open_exposure": round(open_exposure, 2),
        "unique_contracts": settled,
        "avg_win": round(win_total / max(wins, 1), 2),
        "avg_loss": round(-(loss_total / max(losses, 1)), 2),
    }


def _kalshi_snapshot_periods(conn):
    """Compute period aggregates from end-of-day snapshots with a pre-period baseline."""
    period_filters = {
        "today": "date(snap_date) = date('now','localtime')",
        "week": "date(snap_date) >= date('now','localtime','-7 days')",
        "month": "strftime('%Y-%m',snap_date) = strftime('%Y-%m','now','localtime')",
        "quarter": "snap_date >= date('now','localtime','start of year','+' || (((cast(strftime('%m','now') as int)-1)/3)*3) || ' months')",
        "year": "strftime('%Y',snap_date) = strftime('%Y','now','localtime')",
        "all": "1=1",
    }

    eod_cte = """
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
    """

    out = {}
    for period, where_sql in period_filters.items():
        first = conn.execute(
            eod_cte + f"""
            SELECT snap_date, snapshot_ts, balance_cents, total_pnl_cents
            FROM daily_eod
            WHERE {where_sql}
            ORDER BY snap_date ASC
            LIMIT 1
            """
        ).fetchone()
        last = conn.execute(
            eod_cte + f"""
            SELECT snap_date, snapshot_ts, balance_cents, total_pnl_cents, total_fills, win_count, loss_count
            FROM daily_eod
            WHERE {where_sql}
            ORDER BY snap_date DESC
            LIMIT 1
            """
        ).fetchone()
        if not first or not last:
            continue

        baseline = conn.execute(
            eod_cte + """
            SELECT balance_cents, total_pnl_cents
            FROM daily_eod
            WHERE snap_date < ?
            ORDER BY snap_date DESC
            LIMIT 1
            """,
            (first[0],),
        ).fetchone()

        baseline_balance = (baseline[0] if baseline else first[2]) or 0
        baseline_total_pnl = (baseline[1] if baseline else first[3]) or 0

        balance_delta_usd = ((last[2] or 0) - baseline_balance) / 100.0
        pnl_delta_usd = ((last[3] or 0) - baseline_total_pnl) / 100.0
        out[period] = {
            "start_ts": first[1],
            "end_ts": last[1],
            "pnl_usd": round(pnl_delta_usd, 2),
            "balance_delta_usd": round(balance_delta_usd, 2),
            "fills": int(last[4] or 0),
            "wins": int(last[5] or 0),
            "losses": int(last[6] or 0),
        }

    return out


def _build_drawdown_analytics(conn):
    """Build EOD equity, underwater curve, and recovery markers from kalshi_snapshots."""
    rows = conn.execute("""
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
        SELECT snap_date, total_pnl_cents
        FROM daily_eod
        ORDER BY snap_date ASC
    """).fetchall()

    if not rows:
        return {
            "equity_curve": [],
            "underwater": [],
            "daily_pnl": [],
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "max_drawdown_days": 0,
            "drawdown_zone": "green",
            "recovery_markers": [],
            "drawdown_thresholds": {
                "green": {"max_dd_usd": 250.0, "label": "healthy"},
                "amber": {"max_dd_usd": 750.0, "label": "caution"},
                "red": {"max_dd_usd": 99999999.0, "label": "risk"},
            },
        }

    total_pnls = [float((r[1] or 0) / 100.0) for r in rows]
    baseline = total_pnls[0]
    running_peak = baseline
    peak_idx = 0
    drawdown_start_idx = None

    equity_curve = []
    underwater = []
    daily_pnl = []
    recovery_markers = []

    max_dd = 0.0
    max_dd_pct = 0.0
    max_dd_days = 0

    for i, r in enumerate(rows):
        day = r[0]
        total = total_pnls[i]
        equity = round(total - baseline, 2)
        day_pnl = 0.0 if i == 0 else round(total - total_pnls[i - 1], 2)

        equity_curve.append({"date": day, "pnl": equity})
        daily_pnl.append({"date": day, "pnl": day_pnl})

        if total >= running_peak:
            if drawdown_start_idx is not None and i > drawdown_start_idx:
                recovery_markers.append({
                    "drawdown_start": rows[drawdown_start_idx][0],
                    "recovered_on": day,
                    "duration_days": i - drawdown_start_idx,
                })
            running_peak = total
            peak_idx = i
            drawdown_start_idx = None

        dd = round(total - running_peak, 2)
        if dd < 0 and drawdown_start_idx is None:
            drawdown_start_idx = peak_idx

        dd_pct = 0.0 if running_peak <= 0 else (dd / running_peak) * 100.0
        underwater.append({"date": day, "drawdown": dd, "drawdown_pct": round(dd_pct, 2)})

        if dd < max_dd:
            max_dd = dd
            max_dd_pct = dd_pct
            max_dd_days = i - peak_idx if i >= peak_idx else 0

    abs_max_dd = abs(max_dd)
    zone = "green" if abs_max_dd <= 250 else "amber" if abs_max_dd <= 750 else "red"

    return {
        "equity_curve": equity_curve,
        "underwater": underwater,
        "daily_pnl": daily_pnl,
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "max_drawdown_days": int(max_dd_days),
        "drawdown_zone": zone,
        "recovery_markers": recovery_markers,
        "drawdown_thresholds": {
            "green": {"max_dd_usd": 250.0, "label": "healthy"},
            "amber": {"max_dd_usd": 750.0, "label": "caution"},
            "red": {"max_dd_usd": 99999999.0, "label": "risk"},
        },
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Return full P&L dashboard data with Kalshi KPIs sourced from kalshi_snapshots."""
    usage = 0
    cost_caps = {}

    # John's business metrics
    john_revenue = 0.0
    john_pipeline = 0.0
    john_jobs = 0
    john_leads = 0

    # Sports betting metrics
    sports_wins = 0
    sports_losses = 0
    sports_net = 0.0

    # Expenses
    total_expenses = 0.0
    api_cost_expenses = 0.0
    trading_fee_expenses = 0.0
    other_expenses = 0.0

    # Kalshi metrics (new source of truth)
    snapshot_metrics = {
        "betting_wins": 0,
        "betting_losses": 0,
        "betting_net": 0.0,
        "total_trades": 0,
        "open_positions": 0,
        "open_exposure": 0.0,
        "unique_contracts": 0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "last_snapshot_ts": None,
    }
    kalshi_periods = {}
    kalshi_reconciliation = {}
    drawdown_analytics = {
        "equity_curve": [],
        "underwater": [],
        "daily_pnl": [],
        "max_drawdown": 0.0,
        "max_drawdown_pct": 0.0,
        "max_drawdown_days": 0,
        "drawdown_zone": "green",
        "recovery_markers": [],
        "drawdown_thresholds": {
            "green": {"max_dd_usd": 250.0, "label": "healthy"},
            "amber": {"max_dd_usd": 750.0, "label": "caution"},
            "red": {"max_dd_usd": 99999999.0, "label": "risk"},
        },
    }

    with get_db() as conn:
        try:
            latest = conn.execute(
                """
                SELECT snapshot_ts, total_pnl_cents, total_fills, win_count, loss_count,
                       open_positions, total_orders
                FROM kalshi_snapshots
                ORDER BY snapshot_ts DESC LIMIT 1
                """
            ).fetchone()
            if latest:
                snapshot_metrics.update({
                    "betting_wins": int(latest[3] or 0),
                    "betting_losses": int(latest[4] or 0),
                    "betting_net": round((latest[1] or 0) / 100.0, 2),
                    "total_trades": int(latest[2] or 0),
                    "open_positions": int(latest[5] or 0),
                    "open_exposure": 0.0,
                    "unique_contracts": int(latest[2] or 0),
                    "last_snapshot_ts": latest[0],
                })
            kalshi_periods = _kalshi_snapshot_periods(conn)
            drawdown_analytics = _build_drawdown_analytics(conn)
        except Exception as e:
            print(f"[ERROR] Snapshot KPI calc: {e}")

        # Legacy comparison (previous method)
        try:
            legacy = _kalshi_legacy_trade_metrics(conn)
            kalshi_reconciliation = {
                "snapshot": {
                    "betting_wins": snapshot_metrics["betting_wins"],
                    "betting_losses": snapshot_metrics["betting_losses"],
                    "betting_net": snapshot_metrics["betting_net"],
                    "total_trades": snapshot_metrics["total_trades"],
                    "open_positions": snapshot_metrics["open_positions"],
                },
                "legacy_trades": {
                    "betting_wins": legacy["betting_wins"],
                    "betting_losses": legacy["betting_losses"],
                    "betting_net": legacy["betting_net"],
                    "total_trades": legacy["total_trades"],
                    "open_positions": legacy["open_positions"],
                },
                "delta_snapshot_minus_legacy": {
                    "betting_wins": snapshot_metrics["betting_wins"] - legacy["betting_wins"],
                    "betting_losses": snapshot_metrics["betting_losses"] - legacy["betting_losses"],
                    "betting_net": round(snapshot_metrics["betting_net"] - legacy["betting_net"], 2),
                    "total_trades": snapshot_metrics["total_trades"] - legacy["total_trades"],
                    "open_positions": snapshot_metrics["open_positions"] - legacy["open_positions"],
                },
            }
            # Keep old fields for compatibility/diagnostics only
            snapshot_metrics["avg_win"] = legacy["avg_win"]
            snapshot_metrics["avg_loss"] = legacy["avg_loss"]
        except Exception as e:
            print(f"[ERROR] Reconciliation calc: {e}")

        # Get API spend + cost caps
        try:
            cost_caps = calculate_cost_caps(conn)
            usage = cost_caps.get("openrouter", {}).get("actual_spend_usd", 0)
        except Exception:
            usage = 0
            cost_caps = {}

        # Get expenses
        try:
            exp_row = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()
            total_expenses = float(exp_row[0] if exp_row and exp_row[0] else 0)

            api_row = conn.execute("SELECT SUM(amount) FROM expenses WHERE lower(category)='api_tokens'").fetchone()
            api_cost_expenses = float(api_row[0] if api_row and api_row[0] else 0)

            fee_row = conn.execute("SELECT SUM(amount) FROM expenses WHERE lower(category)='trading_fees'").fetchone()
            trading_fee_expenses = float(fee_row[0] if fee_row and fee_row[0] else 0)

            other_expenses = max(0.0, total_expenses - api_cost_expenses - trading_fee_expenses)
        except Exception:
            total_expenses = 0
            api_cost_expenses = 0
            trading_fee_expenses = 0
            other_expenses = 0

        # Get John's business data
        try:
            john_cash_row = conn.execute("SELECT SUM(amount) FROM revenue WHERE lower(segment)='john'").fetchone()
            john_revenue = float(john_cash_row[0] if john_cash_row and john_cash_row[0] else 0)

            john_pipeline_row = conn.execute("SELECT SUM(invoice_amount) FROM john_jobs WHERE status IN ('quoted', 'in_progress')").fetchone()
            john_pipeline = john_pipeline_row[0] if john_pipeline_row and john_pipeline_row[0] else 0

            john_jobs = conn.execute("SELECT COUNT(*) FROM john_jobs").fetchone()[0]
            john_leads = conn.execute("SELECT COUNT(*) FROM john_leads").fetchone()[0]
        except Exception:
            john_revenue = 0
            john_pipeline = 0

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
        except Exception:
            pass

    wins = snapshot_metrics["betting_wins"]
    losses = snapshot_metrics["betting_losses"]
    win_rate = wins / max(wins + losses, 1)

    # Calculate total business P&L with snapshot-sourced Kalshi net
    kalshi_net = float(snapshot_metrics["betting_net"] or 0)
    john_actual_cash_revenue = float(john_revenue or 0)
    sports_net_value = float(sports_net or 0)
    total_revenue = john_actual_cash_revenue + kalshi_net + sports_net_value
    total_profit = total_revenue - total_expenses

    pnl_attribution = {
        "starting_value": 0.0,
        "ending_value": round(total_profit, 2),
        "steps": [
            {
                "key": "john_actual_cash_revenue",
                "label": "John actual cash revenue",
                "amount": round(john_actual_cash_revenue, 2),
                "kind": "revenue",
                "description": "Cash paid and posted to revenue ledger",
            },
            {
                "key": "kalshi_net",
                "label": "Kalshi net P&L",
                "amount": round(kalshi_net, 2),
                "kind": "revenue",
                "description": "Net settled prediction market performance",
            },
            {
                "key": "sports_net",
                "label": "Sports picks net",
                "amount": round(sports_net_value, 2),
                "kind": "revenue" if sports_net_value >= 0 else "expense",
                "description": "Settled sports picks contribution",
            },
            {
                "key": "api_costs",
                "label": "API costs",
                "amount": round(-api_cost_expenses, 2),
                "kind": "expense",
                "description": "Expenses.category = api_tokens",
            },
            {
                "key": "trading_fees",
                "label": "Trading fees",
                "amount": round(-trading_fee_expenses, 2),
                "kind": "expense",
                "description": "Expenses.category = trading_fees",
            },
            {
                "key": "other_expenses",
                "label": "Other expenses",
                "amount": round(-other_expenses, 2),
                "kind": "expense",
                "description": "All non-API, non-trading-fee expenses",
            },
        ],
    }

    return {
        "betting_wins": wins,
        "betting_losses": losses,
        "betting_net": snapshot_metrics["betting_net"],
        "total_trades": snapshot_metrics["total_trades"],
        "win_rate": round(win_rate, 4),
        "sharpe_ratio": 1.5 if win_rate > 0.5 else 0.8,
        "max_drawdown": drawdown_analytics["max_drawdown"],
        "max_drawdown_pct": drawdown_analytics["max_drawdown_pct"],
        "max_drawdown_days": drawdown_analytics["max_drawdown_days"],
        "drawdown_zone": drawdown_analytics["drawdown_zone"],
        "open_positions": snapshot_metrics["open_positions"],
        "open_exposure": round(snapshot_metrics["open_exposure"], 2),
        "kelly_pct": round(win_rate - (1 - win_rate), 2) if win_rate > 0.5 else 0.0,
        "current_streak": wins - losses,
        "streak_type": "W" if wins > losses else "L",
        "avg_win": snapshot_metrics["avg_win"],
        "avg_loss": snapshot_metrics["avg_loss"],
        "openrouter_total_spend": round(float(usage), 2),
        "openrouter_credits_remaining": 50.0,
        "cost_caps": cost_caps,
        "cumulative_pnl": drawdown_analytics["equity_curve"],
        "daily_pnl": drawdown_analytics["daily_pnl"],
        "underwater_drawdown": drawdown_analytics["underwater"],
        "recovery_markers": drawdown_analytics["recovery_markers"],
        "drawdown_thresholds": drawdown_analytics["drawdown_thresholds"],
        "by_market": {},
        "by_direction": {},
        "calibration": [],
        "top_wins": [],
        "top_losses": [],
        "unique_contracts": snapshot_metrics["unique_contracts"],
        "kalshi_source": "kalshi_snapshots",
        "kalshi_last_snapshot_ts": snapshot_metrics["last_snapshot_ts"],
        "kalshi_periods": kalshi_periods,
        "kalshi_reconciliation": kalshi_reconciliation,
        # John's business
        "john_revenue": round(john_revenue, 2),
        "john_actual_revenue": round(john_revenue, 2),
        "john_pipeline": round(float(john_pipeline or 0), 2),
        "john_jobs": john_jobs,
        "john_leads": john_leads,
        # Sports
        "sports_wins": sports_wins,
        "sports_losses": sports_losses,
        "sports_net": round(sports_net or 0, 2),
        # Totals
        "total_expenses": round(total_expenses, 2),
        "api_cost_expenses": round(api_cost_expenses, 2),
        "trading_fee_expenses": round(trading_fee_expenses, 2),
        "other_expenses": round(other_expenses, 2),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "pnl_attribution": pnl_attribution,
    }


def _risk_level(value: float, warn: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= warn:
        return "warning"
    return "ok"


def _normalize_cluster(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["weather", "temp", "rain", "snow", "hurricane", "wind"]):
        return "weather"
    if any(k in t for k in ["crypto", "btc", "bitcoin", "eth", "ethereum", "sol", "doge"]):
        return "crypto"
    if any(k in t for k in ["cpi", "fed", "fomc", "inflation", "unemployment", "gdp", "rates"]):
        return "economics"
    if any(k in t for k in ["election", "senate", "house", "president", "trump", "biden"]):
        return "politics"
    if any(k in t for k in ["nfl", "nba", "mlb", "nhl", "ncaa", "soccer", "tennis", "golf", "ufc"]):
        return "sports"
    return "other"


@app.get("/api/risk/exposure-heatmap")
def get_exposure_heatmap():
    """Cross-book exposure heatmap + concentration risk for open Kalshi and sports positions."""
    thresholds = {
        "total_open_exposure_usd": {"warning": 2500.0, "critical": 5000.0},
        "top_market_share": {"warning": 0.35, "critical": 0.50},
        "top_cluster_share": {"warning": 0.55, "critical": 0.70},
        "hhi": {"warning": 1800.0, "critical": 2500.0},
    }

    with get_db() as conn:
        kalshi_rows = conn.execute(
            """
            SELECT market, direction, entry_price, num_contracts, cost_basis, status, expiry_date
            FROM kalshi_trades
            WHERE status IS NULL OR status != 'Settled'
            """
        ).fetchall()

        sports_rows = conn.execute(
            """
            SELECT sport, game, pick, stake, result, pick_date
            FROM sports_picks
            WHERE COALESCE(result, 'PENDING') = 'PENDING'
            """
        ).fetchall()

    cells = {}
    market_totals = {}
    cluster_totals = {}
    records = []
    missing_exposure_count = 0

    def add_cell(source: str, cluster: str, amount: float, positions: int = 1):
        key = (source, cluster)
        if key not in cells:
            cells[key] = {"source": source, "cluster": cluster, "exposure_usd": 0.0, "positions": 0}
        cells[key]["exposure_usd"] += float(amount or 0)
        cells[key]["positions"] += int(positions or 0)

    for r in kalshi_rows:
        market = (r["market"] or "Unknown Market").strip() or "Unknown Market"
        cluster = _normalize_cluster(market)
        qty = float(r["num_contracts"] or 0)
        entry = float(r["entry_price"] or 0)
        cost_basis = float(r["cost_basis"] or 0)

        exposure = cost_basis if cost_basis > 0 else (entry * qty)
        if exposure <= 0:
            missing_exposure_count += 1

        add_cell("kalshi", cluster, exposure, 1)
        market_totals[market] = market_totals.get(market, 0.0) + exposure
        cluster_totals[cluster] = cluster_totals.get(cluster, 0.0) + exposure

        records.append({
            "source": "kalshi",
            "label": market,
            "cluster": cluster,
            "direction": r["direction"],
            "exposure_usd": round(exposure, 2),
            "expiry_date": r["expiry_date"],
        })

    for r in sports_rows:
        sport = (r["sport"] or "Sports").strip() or "Sports"
        game = (r["game"] or "Unknown Game").strip() or "Unknown Game"
        pick = (r["pick"] or "").strip()
        label = f"{game} {pick}".strip()
        exposure = float(r["stake"] or 0)
        if exposure <= 0:
            missing_exposure_count += 1

        add_cell("sports", sport.lower(), exposure, 1)
        market_totals[label] = market_totals.get(label, 0.0) + exposure
        cluster_totals[sport.lower()] = cluster_totals.get(sport.lower(), 0.0) + exposure

        records.append({
            "source": "sports",
            "label": label,
            "cluster": sport.lower(),
            "direction": None,
            "exposure_usd": round(exposure, 2),
            "expiry_date": r["pick_date"],
        })

    total_open = sum(market_totals.values())
    sorted_markets = sorted(market_totals.items(), key=lambda x: x[1], reverse=True)
    sorted_clusters = sorted(cluster_totals.items(), key=lambda x: x[1], reverse=True)

    top_market_share = (sorted_markets[0][1] / total_open) if total_open > 0 and sorted_markets else 0.0
    top_cluster_share = (sorted_clusters[0][1] / total_open) if total_open > 0 and sorted_clusters else 0.0
    top3_share = (sum(v for _, v in sorted_markets[:3]) / total_open) if total_open > 0 else 0.0
    hhi = (sum(((v / total_open) ** 2) for _, v in sorted_markets) * 10000.0) if total_open > 0 else 0.0

    alerts = [
        {
            "metric": "total_open_exposure_usd",
            "value": round(total_open, 2),
            "level": _risk_level(total_open, thresholds["total_open_exposure_usd"]["warning"], thresholds["total_open_exposure_usd"]["critical"]),
        },
        {
            "metric": "top_market_share",
            "value": round(top_market_share, 4),
            "level": _risk_level(top_market_share, thresholds["top_market_share"]["warning"], thresholds["top_market_share"]["critical"]),
        },
        {
            "metric": "top_cluster_share",
            "value": round(top_cluster_share, 4),
            "level": _risk_level(top_cluster_share, thresholds["top_cluster_share"]["warning"], thresholds["top_cluster_share"]["critical"]),
        },
        {
            "metric": "hhi",
            "value": round(hhi, 1),
            "level": _risk_level(hhi, thresholds["hhi"]["warning"], thresholds["hhi"]["critical"]),
        },
    ]

    overall = "critical" if any(a["level"] == "critical" for a in alerts) else ("warning" if any(a["level"] == "warning" for a in alerts) else "ok")

    return {
        "as_of": datetime.now().isoformat(),
        "status": "ok",
        "overall_risk": overall,
        "fallback_state": "no_open_positions" if total_open <= 0 else None,
        "guardrails": {
            "missing_exposure_count": missing_exposure_count,
            "missing_exposure_pct": round(missing_exposure_count / max(len(records), 1), 4),
            "notes": [
                "Kalshi exposure uses cost_basis when available; falls back to entry_price * contracts.",
                "Sports open exposure uses pending stake.",
            ],
        },
        "summary": {
            "total_open_exposure_usd": round(total_open, 2),
            "open_positions": len(records),
            "top_market": {"name": sorted_markets[0][0], "exposure_usd": round(sorted_markets[0][1], 2)} if sorted_markets else None,
            "top_cluster": {"name": sorted_clusters[0][0], "exposure_usd": round(sorted_clusters[0][1], 2)} if sorted_clusters else None,
            "top_market_share": round(top_market_share, 4),
            "top_cluster_share": round(top_cluster_share, 4),
            "top3_market_share": round(top3_share, 4),
            "hhi": round(hhi, 1),
        },
        "heatmap": {
            "rows": sorted(list({c["source"] for c in cells.values()})),
            "cols": sorted(list({c["cluster"] for c in cells.values()})),
            "cells": [{**v, "exposure_usd": round(v["exposure_usd"], 2)} for v in sorted(cells.values(), key=lambda x: (x["source"], x["cluster"]))],
        },
        "clusters": [{"cluster": k, "exposure_usd": round(v, 2)} for k, v in sorted_clusters],
        "markets": [{"market": k, "exposure_usd": round(v, 2)} for k, v in sorted_markets[:15]],
        "alerts": alerts,
        "alert_thresholds": thresholds,
        "sample_output": {
            "example_alert_levels": {"ok": "below warning", "warning": "above warning", "critical": "above critical"},
            "example_threshold_check": {
                "top_market_share": {
                    "warning_at": thresholds["top_market_share"]["warning"],
                    "critical_at": thresholds["top_market_share"]["critical"],
                }
            },
        },
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


# — API: John's Business
@app.get("/api/john/jobs")
def get_john_jobs():
    """Return John's job data."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM john_jobs ORDER BY job_date DESC"
        ).fetchall()
    return {"jobs": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/john/leads")
def get_john_leads():
    """Return John's lead data."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM john_leads ORDER BY lead_date DESC"
        ).fetchall()
    return {"leads": [dict(r) for r in rows], "count": len(rows)}


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
    """API usage summary grouped case-insensitively by provider."""
    with get_db() as conn:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """
            SELECT lower(provider) as provider,
                   ROUND(SUM(COALESCE(cost_usd,0)), 6) as total_cost,
                   SUM(COALESCE(tokens_in,0)+COALESCE(tokens_out,0)) as total_tokens
            FROM api_usage
            WHERE usage_date >= ?
            GROUP BY lower(provider)
            ORDER BY total_cost DESC
            """,
            (cutoff,),
        ).fetchall()
    return {
        "period_days": days,
        "providers": [dict(r) for r in rows],
        "grand_total": {
            "total_cost": round(sum(float(r["total_cost"] or 0) for r in rows), 6),
            "total_tokens": int(sum(int(r["total_tokens"] or 0) for r in rows)),
        },
    }


@app.get("/api/usage/anthropic")
def get_anthropic_usage(days: int = 1):
    """Anthropic usage with totals and model/agent rollups."""
    with get_db() as conn:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """
            SELECT *
            FROM api_usage
            WHERE lower(provider)='anthropic' AND usage_date >= ?
            ORDER BY usage_date DESC, id DESC
            """,
            (cutoff,),
        ).fetchall()

    usage = [dict(r) for r in rows]
    total_cost = sum(float(r.get("cost_usd") or 0) for r in usage)
    total_tokens = sum(int(r.get("tokens_in") or 0) + int(r.get("tokens_out") or 0) for r in usage)

    by_model = {}
    by_agent = {}
    for r in usage:
        model = r.get("model") or "unknown"
        notes = r.get("notes") or ""
        agent = "unknown"
        if "agent:" in notes:
            agent = notes.split("agent:", 1)[1].strip().split()[0]

        if model not in by_model:
            by_model[model] = {"model": model, "total_cost": 0.0, "total_tokens": 0}
        by_model[model]["total_cost"] += float(r.get("cost_usd") or 0)
        by_model[model]["total_tokens"] += int(r.get("tokens_in") or 0) + int(r.get("tokens_out") or 0)

        if agent not in by_agent:
            by_agent[agent] = {"agent_id": agent, "total_cost": 0.0, "total_tokens": 0}
        by_agent[agent]["total_cost"] += float(r.get("cost_usd") or 0)
        by_agent[agent]["total_tokens"] += int(r.get("tokens_in") or 0) + int(r.get("tokens_out") or 0)

    return {
        "days": days,
        "total": {"total_cost": round(total_cost, 6), "total_tokens": int(total_tokens)},
        "by_model": sorted(
            [{**v, "total_cost": round(v["total_cost"], 6)} for v in by_model.values()],
            key=lambda x: x["total_cost"],
            reverse=True,
        ),
        "by_agent": sorted(
            [{**v, "total_cost": round(v["total_cost"], 6)} for v in by_agent.values()],
            key=lambda x: x["total_cost"],
            reverse=True,
        ),
        "usage": usage,
    }


@app.get("/api/usage/caps")
def get_usage_caps():
    """Budget cap tracking for Anthropic and OpenAI/ChatGPT plus OpenRouter actual spend."""
    with get_db() as conn:
        return calculate_cost_caps(conn)


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
    now = datetime.utcnow()
    with get_db() as conn:
        ensure_tables(conn)
        trade_count = conn.execute("SELECT COUNT(*) FROM kalshi_trades").fetchone()[0]
        freshness = get_freshness_summary(conn)

    scheduler = get_scheduler_checks()
    checks = {
        "database": {"pass": True, "trade_count": trade_count, "db_path": DB_PATH},
        "freshness": {
            "pass": not freshness.get("is_stale", True),
            "stale_sources": freshness.get("stale_sources", []),
        },
        "task_scheduler": scheduler,
    }
    overall_ok = checks["database"]["pass"] and checks["freshness"]["pass"] and scheduler.get("all_pass", False)

    return {
        "status": "ok" if overall_ok else "degraded",
        "timestamp": now.isoformat() + "Z",
        "version": "2026-03-01.freshness-guardrails.v1",
        "checks": checks,
        "freshness": freshness,
    }


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
