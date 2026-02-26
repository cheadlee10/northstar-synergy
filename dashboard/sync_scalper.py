"""
sync_scalper.py — pulls live data from scalper_v8.db and pick_performance_log.jsonl
into the Northstar dashboard DB. Run standalone or imported.
"""
import sqlite3, json, os
from datetime import datetime, date

SCALPER_DB   = r"C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db"
PICK_LOG     = r"C:\Users\chead\.openclaw\workspace-scalper\pick_performance_log.jsonl"
ENGINE_LOG   = r"C:\Users\chead\.openclaw\workspace-scalper\engine_log.jsonl"
JOHN_JOBS    = r"C:\Users\chead\.openclaw\workspace-john\jobs.jsonl"
JOHN_LEADS   = r"C:\Users\chead\.openclaw\workspace-john\leads.jsonl"
DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS kalshi_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_ts TEXT NOT NULL,
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
    lip_rewards_cents INTEGER DEFAULT 0,
    UNIQUE(snapshot_ts)
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
"""

def sync():
    os.makedirs(os.path.dirname(DASHBOARD_DB), exist_ok=True)
    dash = sqlite3.connect(DASHBOARD_DB)
    dash.executescript(EXTRA_SCHEMA)
    dash.commit()
    
    results = {"kalshi_snapshots": 0, "sports_picks": 0, "errors": []}

    # ── KALSHI SNAPSHOTS ──────────────────────────────────────────────
    if os.path.exists(SCALPER_DB):
        try:
            src = sqlite3.connect(SCALPER_DB)
            src.row_factory = sqlite3.Row
            cur = src.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp")
            rows = cur.fetchall()
            src.close()
            for r in rows:
                ts = r["timestamp"]
                snap_date = ts[:10] if ts else str(date.today())
                try:
                    dash.execute("""
                        INSERT OR IGNORE INTO kalshi_snapshots
                        (snapshot_ts, snap_date, balance_cents, daily_pnl_cents, total_pnl_cents,
                         open_positions, total_orders, total_fills, win_count, loss_count,
                         total_fees_cents, weather_pnl_cents, crypto_pnl_cents, econ_pnl_cents,
                         mm_pnl_cents, lip_rewards_cents)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (ts, snap_date,
                          r["balance_cents"] or 0, r["daily_pnl_cents"] or 0, r["total_pnl_cents"] or 0,
                          r["open_positions"] or 0, r["total_orders"] or 0, r["total_fills"] or 0,
                          r["win_count"] or 0, r["loss_count"] or 0, r["total_fees_cents"] or 0,
                          r["weather_pnl_cents"] or 0, r["crypto_pnl_cents"] or 0,
                          r["econ_pnl_cents"] or 0, r["mm_pnl_cents"] or 0, r["lip_rewards_cents"] or 0))
                    if dash.execute("SELECT changes()").fetchone()[0]:
                        results["kalshi_snapshots"] += 1
                except Exception as e:
                    pass
            dash.commit()
        except Exception as e:
            results["errors"].append(f"kalshi_snapshots: {e}")

    # ── SPORTS PICKS ──────────────────────────────────────────────────
    if os.path.exists(PICK_LOG):
        try:
            with open(PICK_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except:
                        continue
                    game = rec.get("game", "")
                    pick = rec.get("pick", "")
                    pick_date = rec.get("date", str(date.today()))
                    ml = rec.get("ml", 0)
                    # compute implied P&L from ML and result
                    result = rec.get("result", "PENDING")
                    stake = float(rec.get("stake", 10))  # default $10 if not set
                    pl = 0.0
                    if result == "WIN":
                        if ml and ml > 0:
                            pl = stake * (ml / 100)
                        elif ml and ml < 0:
                            pl = stake * (100 / abs(ml))
                    elif result == "LOSS":
                        pl = -stake
                    try:
                        dash.execute("""
                            INSERT OR IGNORE INTO sports_picks
                            (pick_date, sport, game, pick, ml, open_ml, edge_val, model_prob,
                             framing_type, edge_bucket, confidence, result, stake, profit_loss)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (pick_date, rec.get("sport",""), game, pick,
                              rec.get("ml"), rec.get("open_ml"),
                              rec.get("edge_val"), rec.get("model_prob"),
                              rec.get("framing_type"), rec.get("edge_bucket"),
                              rec.get("confidence"), result, stake, pl))
                        if dash.execute("SELECT changes()").fetchone()[0]:
                            results["sports_picks"] += 1
                    except Exception as e:
                        pass
            dash.commit()
        except Exception as e:
            results["errors"].append(f"sports_picks: {e}")

    # ── JOHN JOBS ─────────────────────────────────────────────────────────
    results["john_jobs"] = 0
    results["john_leads"] = 0
    if os.path.exists(JOHN_JOBS):
        try:
            with open(JOHN_JOBS, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try: rec = json.loads(line)
                    except: continue
                    ext_id = rec.get("id", "")
                    # Check if already in DB by notes field containing the ID
                    cur = dash.execute("SELECT id FROM john_jobs WHERE notes LIKE ?", (f"%{ext_id}%",))
                    if cur.fetchone(): continue
                    notes = rec.get("notes","")
                    if ext_id: notes = f"[jid:{ext_id}] {notes}".strip()
                    dash.execute("""
                        INSERT INTO john_jobs (job_date,client_name,job_description,status,invoice_amount,paid,paid_date,notes)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (rec.get("date", str(date.today())),
                          rec.get("client","Unknown"),
                          rec.get("service",""),
                          rec.get("status","quoted"),
                          float(rec.get("amount",0)),
                          1 if rec.get("paid") else 0,
                          rec.get("paid_date"),
                          notes))
                    results["john_jobs"] += 1
            dash.commit()
        except Exception as e:
            results["errors"].append(f"john_jobs: {e}")

    # ── JOHN LEADS ────────────────────────────────────────────────────────
    if os.path.exists(JOHN_LEADS):
        try:
            dash.execute("""CREATE TABLE IF NOT EXISTS john_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT (datetime('now')),
                lead_date TEXT NOT NULL, source TEXT, client_name TEXT NOT NULL,
                service TEXT, estimated_value REAL DEFAULT 0, status TEXT DEFAULT 'new',
                notes TEXT, external_id TEXT UNIQUE)""")
            with open(JOHN_LEADS, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try: rec = json.loads(line)
                    except: continue
                    ext_id = rec.get("id","")
                    try:
                        dash.execute("""
                            INSERT OR IGNORE INTO john_leads
                            (lead_date,source,client_name,service,estimated_value,status,notes,external_id)
                            VALUES (?,?,?,?,?,?,?,?)
                        """, (rec.get("date", str(date.today())),
                              rec.get("source",""),
                              rec.get("client","Unknown"),
                              rec.get("service",""),
                              float(rec.get("estimated_value",0)),
                              rec.get("status","new"),
                              rec.get("notes",""),
                              ext_id or None))
                        if dash.execute("SELECT changes()").fetchone()[0]:
                            results["john_leads"] += 1
                    except: pass
            dash.commit()
        except Exception as e:
            results["errors"].append(f"john_leads: {e}")

    dash.close()
    return results

if __name__ == "__main__":
    r = sync()
    print(f"Synced: {r['kalshi_snapshots']} Kalshi snapshots, {r['sports_picks']} sports picks, {r.get('john_jobs',0)} John jobs, {r.get('john_leads',0)} leads")
    if r["errors"]: print("Errors:", r["errors"])
