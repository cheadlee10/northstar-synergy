"""
sync_history.py — one-time full historical import from all Scalper logs into dashboard DB.
Pulls: business_ledger.jsonl, trade_log.jsonl, trade_log.csv, session_log.jsonl, 
       engine_log.jsonl, pick_performance_log.jsonl
"""
import json, csv, sqlite3, os, re
from datetime import datetime, date

DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"
BASE = r"C:\Users\chead\.openclaw\workspace-scalper"

def run():
    conn = sqlite3.connect(DASHBOARD_DB)
    
    # Ensure tables exist
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS kalshi_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_ts TEXT NOT NULL,
        trade_date TEXT NOT NULL,
        ticker TEXT NOT NULL,
        category TEXT,
        direction TEXT,
        side TEXT,
        price_cents INTEGER,
        quantity INTEGER,
        order_id TEXT,
        is_maker INTEGER,
        pnl REAL DEFAULT 0,
        session_pnl REAL DEFAULT 0,
        source TEXT,
        UNIQUE(order_id, trade_ts)
    );
    CREATE TABLE IF NOT EXISTS business_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT NOT NULL,
        entry_time TEXT,
        entry_type TEXT NOT NULL,
        category TEXT,
        agent TEXT,
        amount REAL NOT NULL,
        description TEXT,
        source TEXT,
        UNIQUE(entry_date, entry_type, category, amount, description)
    );
    """)
    conn.commit()

    results = {}

    # ── 1. BUSINESS LEDGER ─────────────────────────────────────────────────────
    path = os.path.join(BASE, "business_ledger.jsonl")
    n = 0
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: rec = json.loads(line)
                except: continue
                desc = rec.get('desc') or rec.get('description','')
                try:
                    conn.execute("""INSERT OR IGNORE INTO business_ledger
                        (entry_date,entry_time,entry_type,category,agent,amount,description,source)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (rec.get('date',''), rec.get('time',''),
                         rec.get('type',''), rec.get('category',''),
                         rec.get('agent',''), float(rec.get('amount',0)),
                         desc, rec.get('source','')))
                    if conn.execute("SELECT changes()").fetchone()[0]: n += 1
                except: pass
        conn.commit()
        # Also mirror into revenue/expenses tables for the P&L statement
        cur = conn.execute("SELECT * FROM business_ledger")
        for r in cur.fetchall():
            if len(r) == 9:
                _id, edate, etime, etype, cat, agent, amt, desc, src = r
            else:
                continue # Skip if schema mismatch
            
            if etype == 'revenue':
                seg = 'Kalshi' if 'settlement' in (cat or '') or 'scalper' in (cat or '').lower() else 'Other'
                try:
                    conn.execute("""INSERT OR IGNORE INTO revenue (revenue_date,segment,description,amount)
                        SELECT ?,?,?,? WHERE NOT EXISTS (
                            SELECT 1 FROM revenue WHERE revenue_date=? AND description=? AND amount=?)""",
                        (edate, seg, desc, amt, edate, desc, amt))
                except: pass
            elif etype == 'expense':
                seg = 'AI / Tech' if 'api' in (cat or '').lower() or 'subscription' in (cat or '').lower() else 'Kalshi' if 'trading' in (cat or '').lower() or 'fee' in (cat or '').lower() else 'Operations'
                try:
                    conn.execute("""INSERT OR IGNORE INTO expenses (expense_date,segment,description,amount,category)
                        SELECT ?,?,?,?,? WHERE NOT EXISTS (
                            SELECT 1 FROM expenses WHERE expense_date=? AND description=? AND amount=?)""",
                        (edate, seg, desc, amt, cat, edate, desc, amt))
                except: pass
        conn.commit()
    results['business_ledger'] = n

    # ── 2. TRADE LOG (JSONL — fills with details) ──────────────────────────────
    path = os.path.join(BASE, "trade_log.jsonl")
    n = 0
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: rec = json.loads(line)
                except: continue
                ts = rec.get('timestamp','')
                ticker = rec.get('ticker','')
                # Parse category from ticker
                cat = 'weather' if 'KXHIGH' in ticker or 'KXLOW' in ticker or 'KXBOS' in ticker else 'sports' if 'KXNBA' in ticker or 'KXNCAA' in ticker or 'KXNFL' in ticker else 'other'
                try:
                    conn.execute("""INSERT OR IGNORE INTO kalshi_trades
                        (trade_ts,trade_date,ticker,category,direction,side,price_cents,quantity,order_id,is_maker,source)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (ts, ts[:10], ticker, cat,
                         rec.get('side',''), rec.get('side',''),
                         int(float(rec.get('yes_price',0))*100),
                         rec.get('count',0), rec.get('order_id',''),
                         1 if rec.get('is_maker') else 0, 'trade_log.jsonl'))
                    if conn.execute("SELECT changes()").fetchone()[0]: n += 1
                except: pass
        conn.commit()
    results['trade_log_jsonl'] = n

    # ── 3. TRADE LOG (CSV) ──────────────────────────────────────────────────────
    path = os.path.join(BASE, "trade_log.csv")
    n = 0
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for rec in reader:
                ts = rec.get('timestamp','')
                ticker = rec.get('ticker','')
                cat = 'weather' if 'KXHIGH' in ticker or 'KXLOW' in ticker or 'KXBOS' in ticker else 'sports' if 'KXNBA' in ticker else 'other'
                try:
                    conn.execute("""INSERT OR IGNORE INTO kalshi_trades
                        (trade_ts,trade_date,ticker,category,direction,side,price_cents,quantity,order_id,is_maker,source)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (ts, ts[:10], ticker, cat,
                         rec.get('direction',''), rec.get('direction',''),
                         int(rec.get('price_cents',0)),
                         int(rec.get('quantity',0)), rec.get('order_id',''),
                         0, 'trade_log.csv'))
                    if conn.execute("SELECT changes()").fetchone()[0]: n += 1
                except: pass
        conn.commit()
    results['trade_log_csv'] = n

    # ── 4. SESSION LOG (fills with P&L) ─────────────────────────────────────────
    path = os.path.join(BASE, "session_log.jsonl")
    n = 0
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: rec = json.loads(line)
                except: continue
                if rec.get('event') != 'fill': continue
                ts = rec.get('ts','')
                ticker = rec.get('ticker','')
                cat = 'weather' if 'KXHIGH' in ticker or 'KXLOW' in ticker or 'KXBOS' in ticker else 'sports' if 'KXNBA' in ticker else 'other'
                try:
                    conn.execute("""INSERT OR IGNORE INTO kalshi_trades
                        (trade_ts,trade_date,ticker,category,direction,side,price_cents,quantity,order_id,is_maker,pnl,session_pnl,source)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (ts, ts[:10], ticker, cat,
                         rec.get('side',''), rec.get('side',''),
                         int(float(rec.get('price',0))*100),
                         rec.get('size',0), '',
                         0, float(rec.get('pnl',0)), float(rec.get('session_pnl',0)),
                         'session_log.jsonl'))
                    if conn.execute("SELECT changes()").fetchone()[0]: n += 1
                except: pass
        conn.commit()
    results['session_log'] = n

    # ── Summary ─────────────────────────────────────────────────────────────────
    for t in ['kalshi_trades','business_ledger','revenue','expenses']:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        results[f'total_{t}'] = cnt
    
    conn.close()
    return results

if __name__ == '__main__':
    r = run()
    for k,v in r.items():
        print(f"  {k}: {v}")
