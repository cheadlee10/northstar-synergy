#!/usr/bin/env python3
"""
backfill_10days.py — Master historical expense backfill for NorthStar dashboard
Pulls all financial data from all sources for the last 10 days and populates dashboard.db
"""
import json, os, sqlite3, sys, argparse, urllib.request, urllib.error
from datetime import datetime, date, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"
AGENTS_DIR = r"C:\Users\chead\.openclaw\agents"
SCALPER_DB = r"C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db"
PICK_LOG = r"C:\Users\chead\.openclaw\workspace-scalper\pick_performance_log.jsonl"
JOHN_JOBS = r"C:\Users\chead\.openclaw\workspace-john\jobs.jsonl"
JOHN_LEADS = r"C:\Users\chead\.openclaw\workspace-john\leads.jsonl"

OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()

# Anthropic pricing
ANTHROPIC_PRICING = {
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku":    {"input": 0.25, "output": 1.25,  "cache_read": 0.03, "cache_write": 0.30},
    "claude-opus":     {"input": 15.0, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
}

def get_pricing(model: str) -> dict:
    m = (model or '').lower()
    if 'haiku' in m: return ANTHROPIC_PRICING['claude-haiku']
    if 'opus' in m: return ANTHROPIC_PRICING['claude-opus']
    return ANTHROPIC_PRICING['claude-sonnet-4']

def calc_cost(usage: dict, model: str) -> float:
    p = get_pricing(model)
    inp = (usage.get('input', 0) or 0) / 1_000_000 * p['input']
    out = (usage.get('output', 0) or 0) / 1_000_000 * p['output']
    cr = (usage.get('cacheRead', 0) or 0) / 1_000_000 * p['cache_read']
    cw = (usage.get('cacheWrite', 0) or 0) / 1_000_000 * p['cache_write']
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
        lead_date TEXT NOT NULL,
        source TEXT,
        client_name TEXT NOT NULL,
        service TEXT,
        estimated_value REAL DEFAULT 0,
        status TEXT DEFAULT 'new',
        notes TEXT,
        external_id TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        revenue_date TEXT NOT NULL,
        segment TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL
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
    """)
    conn.commit()

def backfill_openrouter(conn, verbose=False) -> int:
    if not OPENROUTER_KEY or not OPENROUTER_KEY.startswith('sk-or'):
        print(f"[!] OpenRouter: No API key")
        return 0
    data, code = http_get('https://openrouter.ai/api/v1/auth/key',
        {'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'})
    if code != 200:
        print(f"[!] OpenRouter API {code}")
        return 0
    d = data.get('data', {})
    today_str = str(date.today())
    daily_cost = round((d.get('usage_daily') or 0) / 1000, 6)
    cur = conn.execute("SELECT id FROM api_usage WHERE usage_date=? AND provider='OpenRouter' AND model='aggregate'", (today_str,))
    if cur.fetchone():
        if verbose: print(f"  [*] OpenRouter: today already logged")
        return 0
    conn.execute("INSERT INTO api_usage (usage_date,provider,model,cost_usd,notes) VALUES (?,?,?,?,?)",
        (today_str, 'OpenRouter', 'aggregate', daily_cost, f"OR daily=${daily_cost}"))
    conn.commit()
    if verbose: print(f"  [+] OpenRouter: ${daily_cost}")
    return 1

def backfill_anthropic(conn, verbose=False) -> int:
    """Parse all session logs for Anthropic costs."""
    daily = {}
    for root, dirs, files in os.walk(AGENTS_DIR):
        for fname in files:
            if not fname.endswith('.jsonl') or 'lock' in fname: continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or '"usage"' not in line: continue
                        try: rec = json.loads(line)
                        except: continue
                        msg = rec.get('message', {})
                        if msg.get('role') != 'assistant': continue
                        if 'anthropic' not in (msg.get('provider', '') or '').lower(): continue
                        usage = msg.get('usage', {})
                        if not usage: continue
                        ts = rec.get('timestamp', '')
                        if not ts: continue
                        day = ts[:10]
                        model = msg.get('model', 'unknown')
                        key = (day, model)
                        if key not in daily:
                            daily[key] = {'input': 0, 'output': 0, 'cache_read': 0, 'cache_write': 0}
                        daily[key]['input']       += usage.get('input', 0) or 0
                        daily[key]['output']      += usage.get('output', 0) or 0
                        daily[key]['cache_read']  += usage.get('cacheRead', 0) or 0
                        daily[key]['cache_write'] += usage.get('cacheWrite', 0) or 0
            except: continue
    
    synced = 0
    for (day, model), u in daily.items():
        cost = calc_cost(u, model)
        cur = conn.execute("SELECT id FROM api_usage WHERE usage_date=? AND provider='Anthropic' AND model=?", (day, model))
        if cur.fetchone(): continue
        conn.execute("INSERT INTO api_usage (usage_date,provider,model,tokens_in,tokens_out,cost_usd,notes) VALUES (?,?,?,?,?,?,?)",
            (day, 'Anthropic', model, u['input'], u['output'], cost, f"cr={u['cache_read']} cw={u['cache_write']}"))
        synced += 1
    conn.commit()
    if verbose and synced > 0: print(f"  [+] Anthropic: {synced} days")
    return synced

def backfill_kalshi(conn, verbose=False) -> int:
    """Backfill Kalshi P&L snapshots from scalper_v8.db."""
    if not os.path.exists(SCALPER_DB):
        print(f"[!] Kalshi: scalper_v8.db not found")
        return 0
    src = sqlite3.connect(SCALPER_DB)
    src.row_factory = sqlite3.Row
    synced = 0
    try:
        rows = src.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp").fetchall()
        for r in rows:
            try:
                conn.execute("""INSERT OR IGNORE INTO kalshi_snapshots
                    (snapshot_ts,snap_date,balance_cents,daily_pnl_cents,total_pnl_cents,
                     open_positions,total_orders,total_fills,win_count,loss_count,
                     total_fees_cents,weather_pnl_cents,crypto_pnl_cents,econ_pnl_cents,
                     mm_pnl_cents,lip_rewards_cents)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r['timestamp'], (r['timestamp'] or '')[:10],
                     r['balance_cents'] or 0, r['daily_pnl_cents'] or 0,
                     r['total_pnl_cents'] or 0, r['open_positions'] or 0,
                     r['total_orders'] or 0, r['total_fills'] or 0,
                     r['win_count'] or 0, r['loss_count'] or 0,
                     r['total_fees_cents'] or 0, r['weather_pnl_cents'] or 0,
                     r['crypto_pnl_cents'] or 0, r['econ_pnl_cents'] or 0,
                     r['mm_pnl_cents'] or 0, r['lip_rewards_cents'] or 0))
                if conn.execute("SELECT changes()").fetchone()[0]: synced += 1
            except: pass
        conn.commit()
    finally:
        src.close()
    if verbose and synced > 0: print(f"  [+] Kalshi: {synced} snapshots")
    return synced

def backfill_sports_picks(conn, verbose=False) -> int:
    """Backfill sports picks."""
    if not os.path.exists(PICK_LOG): return 0
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
    if verbose and synced > 0: print(f"  [+] Sports picks: {synced} picks")
    return synced

def backfill_john(conn, verbose=False) -> dict:
    """Backfill John's jobs and leads."""
    jobs = leads = 0
    # Jobs
    if os.path.exists(JOHN_JOBS):
        with open(JOHN_JOBS, 'r', encoding='utf-8') as f:
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
                jobs += 1
        conn.commit()
    # Leads
    if os.path.exists(JOHN_LEADS):
        with open(JOHN_LEADS, 'r', encoding='utf-8') as f:
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
                    if conn.execute("SELECT changes()").fetchone()[0]: leads += 1
                except: pass
        conn.commit()
    if verbose and (jobs + leads) > 0: print(f"  [+] John: {jobs} jobs, {leads} leads")
    return {"jobs": jobs, "leads": leads}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=10)
    parser.add_argument('--full', action='store_true', help='Backfill all available data')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(DASHBOARD_DB), exist_ok=True)
    conn = sqlite3.connect(DASHBOARD_DB)
    init_db(conn)
    
    print(f"[*] NorthStar Financial Backfill")
    print(f"    DB: {DASHBOARD_DB}")
    print()
    
    results = {}
    results['openrouter'] = backfill_openrouter(conn, args.verbose)
    results['anthropic'] = backfill_anthropic(conn, args.verbose)
    results['kalshi'] = backfill_kalshi(conn, args.verbose)
    results['sports_picks'] = backfill_sports_picks(conn, args.verbose)
    results['john'] = backfill_john(conn, args.verbose)
    
    conn.close()
    
    print()
    print("[SUMMARY]")
    for src, res in results.items():
        if isinstance(res, dict):
            print(f"  {src}: {res}")
        else:
            print(f"  {src}: {res} rows")
    
    total = sum(r if isinstance(r, int) else sum(r.values()) for r in results.values())
    print()
    print(f"[OK] Total: {total} records backfilled")
    print(f"     View at: http://localhost:8765")

if __name__ == '__main__':
    main()
