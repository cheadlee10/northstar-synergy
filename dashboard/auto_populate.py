"""
auto_populate.py — Northstar Synergy dashboard auto-population
Pulls ALL data automatically — no manual entry ever.

Sources:
  1. OpenRouter API        → API credits used (daily/weekly/monthly)
  2. OpenClaw session logs → Anthropic token usage + cost calculation
  3. Kalshi Live API       → Live balance, positions, orders, fills
  4. pick_performance_log  → Sports picks results
  5. workspace-john/jobs   → John's business jobs
  6. workspace-john/leads  → John's sales pipeline

Run via: python auto_populate.py
Registered in Task Scheduler as NorthstarAutoPopulate (every 15 min)
"""
import json, os, sqlite3, urllib.request, urllib.error, glob, datetime, uuid, traceback
from datetime import datetime as dt, date

# ── Config ────────────────────────────────────────────────────────────────────
DASHBOARD_DB  = os.environ.get("DASHBOARD_DB", os.path.join(os.path.dirname(__file__), "data", "northstar.db"))
AGENTS_DIR    = r"C:\Users\chead\.openclaw\agents"
SCALPER_DB    = r"C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db"
PICK_LOG      = r"C:\Users\chead\.openclaw\workspace-scalper\pick_performance_log.jsonl"
JOHN_JOBS     = r"C:\Users\chead\.openclaw\workspace-john\jobs.jsonl"
JOHN_LEADS    = r"C:\Users\chead\.openclaw\workspace-john\leads.jsonl"

# API keys from environment
OR_KEY  = (os.environ.get('OPENROUTER_API_KEY') or '').strip()
if not OR_KEY or OR_KEY.startswith('sk-ant'):  # fallback to user env
    import subprocess
    try:
        result = subprocess.run(['powershell','-Command',
            '[System.Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY","User")'],
            capture_output=True, text=True, timeout=5)
        OR_KEY = result.stdout.strip()
    except: pass

ANT_KEY = (os.environ.get('ANTHROPIC_API_KEY') or '').strip()

# Anthropic pricing per million tokens (claude-sonnet-4-x range)
ANTHROPIC_PRICING = {
    "claude-sonnet-4":  {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku":     {"input": 0.25, "output": 1.25,  "cache_read": 0.03, "cache_write": 0.30},
    "claude-opus":      {"input": 15.0, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
    "default":          {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
}

def get_pricing(model: str) -> dict:
    m = (model or '').lower()
    if 'haiku' in m:  return ANTHROPIC_PRICING['claude-haiku']
    if 'opus' in m:   return ANTHROPIC_PRICING['claude-opus']
    return ANTHROPIC_PRICING['claude-sonnet-4']

def calc_cost(usage: dict, model: str) -> float:
    p = get_pricing(model)
    inp   = (usage.get('input',0) or 0) / 1_000_000 * p['input']
    out   = (usage.get('output',0) or 0) / 1_000_000 * p['output']
    cr    = (usage.get('cacheRead',0) or 0) / 1_000_000 * p['cache_read']
    cw    = (usage.get('cacheWrite',0) or 0) / 1_000_000 * p['cache_write']
    return round(inp + out + cr + cw, 6)

def http_get(url, headers):
    try:
        req = urllib.request.Request(url, headers=headers)
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code
    except Exception as ex:
        return {"error": str(ex)}, 0

def init_db(conn):
    conn.executescript("""
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
        sport TEXT, game TEXT NOT NULL, pick TEXT,
        ml INTEGER, open_ml INTEGER,
        edge_val REAL, model_prob REAL,
        framing_type TEXT, edge_bucket TEXT, confidence TEXT,
        result TEXT DEFAULT 'PENDING',
        stake REAL DEFAULT 0, profit_loss REAL DEFAULT 0,
        UNIQUE(pick_date, game, pick)
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
    CREATE TABLE IF NOT EXISTS john_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        lead_date TEXT NOT NULL, source TEXT, client_name TEXT NOT NULL,
        service TEXT, estimated_value REAL DEFAULT 0, status TEXT DEFAULT 'new',
        notes TEXT, external_id TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        revenue_date TEXT NOT NULL, segment TEXT NOT NULL,
        description TEXT NOT NULL, amount REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        expense_date TEXT NOT NULL, segment TEXT NOT NULL,
        description TEXT NOT NULL, amount REAL NOT NULL, category TEXT
    );
    CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        bet_date TEXT NOT NULL, sport TEXT NOT NULL, game TEXT NOT NULL,
        book TEXT DEFAULT 'Kalshi', bet_type TEXT DEFAULT 'ML',
        stake REAL NOT NULL, odds TEXT, odds_decimal REAL,
        result TEXT DEFAULT 'PENDING', profit_loss REAL DEFAULT 0,
        edge_pct REAL, notes TEXT
    );
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
    );
    """)
    conn.commit()

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1: OPENROUTER API
# ══════════════════════════════════════════════════════════════════════════════
def sync_openrouter(conn) -> dict:
    if not OR_KEY or not OR_KEY.startswith('sk-or'):
        return {"synced": 0, "error": "No OpenRouter key"}
    data, code = http_get('https://openrouter.ai/api/v1/auth/key',
        {'Authorization': f'Bearer {OR_KEY}', 'Content-Type': 'application/json'})
    if code != 200:
        return {"synced": 0, "error": f"OR API {code}: {data}"}
    d = data.get('data', {})
    today_str = str(date.today())
    # Store today's usage as a daily snapshot
    # Check if we already have today's OR entry
    cur = conn.execute("SELECT id, cost_usd FROM api_usage WHERE usage_date=? AND provider='OpenRouter' AND model='aggregate'", (today_str,))
    existing = cur.fetchone()
    daily_cost = round((d.get('usage_daily') or 0) / 1000, 6)  # OR uses credits (millicents)
    if existing:
        conn.execute("UPDATE api_usage SET cost_usd=?, notes=? WHERE id=?",
            (daily_cost, f"OR aggregate: total_lifetime=${d.get('usage',0):.2f}", existing[0]))
    else:
        conn.execute("INSERT INTO api_usage (usage_date,provider,model,cost_usd,notes) VALUES (?,?,?,?,?)",
            (today_str, 'OpenRouter', 'aggregate', daily_cost,
             f"OR aggregate: total_lifetime=${d.get('usage',0):.2f} weekly=${d.get('usage_weekly',0):.2f}"))
    conn.commit()
    return {"synced": 1, "daily_usd": daily_cost, "monthly_usd": round((d.get('usage_monthly') or 0)/1000, 4)}

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2: OPENCLAW SESSION LOGS → ANTHROPIC COSTS
# ══════════════════════════════════════════════════════════════════════════════
def sync_anthropic_from_logs(conn) -> dict:
    """Parse all OpenClaw session JSONL files for Anthropic usage data."""
    # Get last processed timestamp
    cur = conn.execute("SELECT MAX(notes) FROM api_usage WHERE provider='Anthropic' AND model != 'aggregate'")
    row = cur.fetchone()
    last_ts = ""  # process everything; dedup by (date, model, tokens_in, tokens_out)
    
    # Group by date+model → accumulate tokens
    daily = {}  # key=(date, model) → {input, output, cache_read, cache_write}
    
    for root, dirs, files in os.walk(AGENTS_DIR):
        for fname in files:
            if not fname.endswith('.jsonl') or 'lock' in fname:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or '"usage"' not in line:
                            continue
                        try:
                            rec = json.loads(line)
                        except:
                            continue
                        msg = rec.get('message', {})
                        if msg.get('role') != 'assistant':
                            continue
                        provider = msg.get('provider', '')
                        if 'anthropic' not in provider.lower():
                            continue
                        usage = msg.get('usage', {})
                        if not usage:
                            continue
                        ts = rec.get('timestamp', '')
                        if not ts:
                            continue
                        day = ts[:10]
                        model = msg.get('model', 'unknown')
                        key = (day, model)
                        if key not in daily:
                            daily[key] = {'input': 0, 'output': 0, 'cache_read': 0, 'cache_write': 0}
                        daily[key]['input']       += usage.get('input', 0) or 0
                        daily[key]['output']      += usage.get('output', 0) or 0
                        daily[key]['cache_read']  += usage.get('cacheRead', 0) or 0
                        daily[key]['cache_write'] += usage.get('cacheWrite', 0) or 0
            except:
                continue
    
    # Upsert into api_usage (replace existing anthropic entries for each day/model)
    synced = 0
    for (day, model), u in daily.items():
        cost = calc_cost(u, model)
        # Check if exists
        cur = conn.execute("SELECT id FROM api_usage WHERE usage_date=? AND provider='Anthropic' AND model=?", (day, model))
        existing = cur.fetchone()
        if existing:
            conn.execute("UPDATE api_usage SET tokens_in=?, tokens_out=?, cost_usd=? WHERE id=?",
                (u['input'], u['output'], cost, existing[0]))
        else:
            conn.execute("INSERT INTO api_usage (usage_date,provider,model,tokens_in,tokens_out,cost_usd,notes) VALUES (?,?,?,?,?,?,?)",
                (day, 'Anthropic', model, u['input'], u['output'], cost,
                 f"cache_r={u['cache_read']} cache_w={u['cache_write']}"))
            synced += 1
    conn.commit()
    return {"synced": synced, "days_processed": len(daily)}

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3: KALSHI (LIVE API via Scalper's KalshiClient)
# ══════════════════════════════════════════════════════════════════════════════
def sync_kalshi(conn) -> dict:
    # Sync Kalshi data directly from live API using Scalper credentials.
    """Sync Kalshi data directly from live API using Scalper's credentials."""
    import asyncio
    import sys
    
    # Load Scalper environment
    scalper_env_path = r"C:\Users\chead\.openclaw\workspace-scalper\.env"
    if os.path.exists(scalper_env_path):
        with open(scalper_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()
    
    # Add Scalper to path
    scalper_path = r'C:\Users\chead\.openclaw\workspace-scalper'
    if scalper_path not in sys.path:
        sys.path.insert(0, scalper_path)
    
    try:
        import config
        from kalshi_api import KalshiClient
        
        async def fetch_kalshi():
            client = KalshiClient()
            try:
                # Get live data
                balance = await client.get_balance()
                positions = await client.get_positions()
                resting_orders = await client.get_orders(status="resting")
                canceled_orders = await client.get_orders(status="canceled")
                fills = await client.get_fills(limit=100)
                
                # Calculate P&L
                pos_pnl = sum(int(p.get('pnl_cents', 0) or 0) for p in positions)
                fill_pnl = sum(int(f.get('pnl_cents', 0) or 0) for f in fills)
                total_pnl = pos_pnl + fill_pnl
                
                wins = len([p for p in positions if int(p.get('pnl_cents', 0) or 0) > 0])
                losses = len([p for p in positions if int(p.get('pnl_cents', 0) or 0) < 0])
                
                return {
                    "status": "ok",
                    "balance": balance,
                    "positions": len(positions),
                    "orders": len(resting_orders) + len(canceled_orders),
                    "fills": len(fills),
                    "total_pnl": total_pnl,
                    "wins": wins,
                    "losses": losses
                }
            finally:
                await client.close()
        
        # Run async fetch
        result = asyncio.run(fetch_kalshi())
        
        if result['status'] != 'ok':
            return {"synced": 0, "error": result.get('error'), "source": "kalshi_live_api"}
        
        # Insert snapshot
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        snap_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        
        conn.execute("""
            INSERT INTO kalshi_snapshots (
                snapshot_ts, snap_date, balance_cents, total_pnl_cents,
                open_positions, total_orders, total_fills, win_count, loss_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, snap_date, result['balance'], result['total_pnl'],
              result['positions'], result['orders'], result['fills'],
              result['wins'], result['losses']))
        
        conn.commit()
        
        return {
            "synced": 1,
            "source": "kalshi_live_api",
            "balance_usd": result['balance'] / 100,
            "pnl_usd": result['total_pnl'] / 100,
            "timestamp": ts
        }
    
    except Exception as e:
        return {"synced": 0, "error": str(e), "source": "kalshi_live_api"}

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 4: SPORTS PICKS
# ══════════════════════════════════════════════════════════════════════════════
def sync_sports_picks(conn) -> dict:
    if not os.path.exists(PICK_LOG):
        return {"synced": 0}
    synced = 0
    with open(PICK_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except: continue
            result = rec.get('result', 'PENDING')
            stake = float(rec.get('stake', 10) or 10)
            ml = rec.get('ml', 0)
            pl = 0.0
            if result == 'WIN':
                pl = stake * (ml/100) if ml and ml > 0 else stake * (100/abs(ml)) if ml and ml < 0 else stake
            elif result == 'LOSS':
                pl = -stake
            try:
                conn.execute("""INSERT OR IGNORE INTO sports_picks
                    (pick_date,sport,game,pick,ml,open_ml,edge_val,model_prob,
                     framing_type,edge_bucket,confidence,result,stake,profit_loss)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rec.get('date', str(date.today())), rec.get('sport',''),
                     rec.get('game',''), rec.get('pick',''),
                     rec.get('ml'), rec.get('open_ml'),
                     rec.get('edge_val'), rec.get('model_prob'),
                     rec.get('framing_type'), rec.get('edge_bucket'),
                     rec.get('confidence'), result, stake, pl))
                if conn.execute("SELECT changes()").fetchone()[0]: synced += 1
            except: pass
    conn.commit()
    return {"synced": synced}

# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 5: JOHN'S JOBS + LEADS
# ══════════════════════════════════════════════════════════════════════════════
def sync_john(conn) -> dict:
    jobs_synced = leads_synced = 0
    for fpath, table, sync_fn in [
        (JOHN_JOBS, 'john_jobs', _sync_john_jobs),
        (JOHN_LEADS, 'john_leads', _sync_john_leads),
    ]:
        if os.path.exists(fpath):
            try:
                n = sync_fn(conn, fpath)
                if table == 'john_jobs': jobs_synced = n
                else: leads_synced = n
            except Exception as e:
                pass
    return {"jobs": jobs_synced, "leads": leads_synced}

def _sync_john_jobs(conn, fpath):
    n = 0
    with open(fpath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except: continue
            ext_id = rec.get('id', '')
            cur = conn.execute("SELECT id FROM john_jobs WHERE notes LIKE ?", (f'%[jid:{ext_id}]%',))
            if cur.fetchone(): continue
            notes = f"[jid:{ext_id}] {rec.get('notes','')}".strip() if ext_id else rec.get('notes','')
            conn.execute("""INSERT INTO john_jobs (job_date,client_name,job_description,status,invoice_amount,paid,paid_date,notes)
                VALUES (?,?,?,?,?,?,?,?)""",
                (rec.get('date', str(date.today())), rec.get('client','Unknown'),
                 rec.get('service',''), rec.get('status','quoted'),
                 float(rec.get('amount',0)), 1 if rec.get('paid') else 0,
                 rec.get('paid_date'), notes))
            n += 1
    conn.commit()
    return n

def _sync_john_leads(conn, fpath):
    n = 0
    with open(fpath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except: continue
            try:
                conn.execute("""INSERT OR IGNORE INTO john_leads
                    (lead_date,source,client_name,service,estimated_value,status,notes,external_id)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (rec.get('date', str(date.today())), rec.get('source',''),
                     rec.get('client','Unknown'), rec.get('service',''),
                     float(rec.get('estimated_value',0)), rec.get('status','new'),
                     rec.get('notes',''), rec.get('id') or None))
                if conn.execute("SELECT changes()").fetchone()[0]: n += 1
            except: pass
    conn.commit()
    return n

# ══════════════════════════════════════════════════════════════════════════════
# MASTER SYNC
# ══════════════════════════════════════════════════════════════════════════════
def _extract_records_synced(result: dict) -> int:
    if not isinstance(result, dict):
        return 0
    total = 0
    for key in ("synced", "jobs", "leads"):
        val = result.get(key)
        if isinstance(val, int):
            total += val
    return total


def _run_source_with_audit(conn, run_id: str, source: str, fn):
    started = datetime.datetime.utcnow().isoformat() + "Z"
    conn.execute(
        """
        INSERT INTO sync_run_audit (run_id, source, started_at, status)
        VALUES (?, ?, ?, 'running')
        """,
        (run_id, source, started),
    )
    audit_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()

    try:
        result = fn(conn)
        status = "success"
        error_message = None
    except Exception as e:
        result = {"error": str(e), "traceback": traceback.format_exc(limit=2)}
        status = "error"
        error_message = str(e)

    completed = datetime.datetime.utcnow().isoformat() + "Z"
    records_synced = _extract_records_synced(result)
    conn.execute(
        """
        UPDATE sync_run_audit
        SET completed_at=?, status=?, records_synced=?, error_message=?, details_json=?
        WHERE id=?
        """,
        (
            completed,
            status,
            records_synced,
            error_message,
            json.dumps(result, default=str)[:4000],
            audit_id,
        ),
    )
    conn.commit()
    return result


def run_all() -> dict:
    os.makedirs(os.path.dirname(DASHBOARD_DB), exist_ok=True)
    conn = sqlite3.connect(DASHBOARD_DB)
    init_db(conn)
    run_id = datetime.datetime.utcnow().strftime("run-%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:8]
    results = {"run_id": run_id}
    results['openrouter'] = _run_source_with_audit(conn, run_id, 'openrouter', sync_openrouter)
    results['anthropic'] = _run_source_with_audit(conn, run_id, 'anthropic', sync_anthropic_from_logs)
    results['kalshi'] = _run_source_with_audit(conn, run_id, 'kalshi', sync_kalshi)
    results['sports_picks'] = _run_source_with_audit(conn, run_id, 'sports_picks', sync_sports_picks)
    results['john'] = _run_source_with_audit(conn, run_id, 'john', sync_john)
    conn.close()
    return results

if __name__ == '__main__':
    print(f"[{dt.now().strftime('%H:%M:%S')}] Northstar auto-populate starting...")
    r = run_all()
    for src, res in r.items():
        print(f"  {src}: {res}")
    print(f"[{dt.now().strftime('%H:%M:%S')}] Done.")
