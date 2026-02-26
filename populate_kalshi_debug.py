#!/usr/bin/env python3
"""Debug Kalshi sync — find out why snapshots aren't flowing."""
import os, sqlite3
from pathlib import Path

SCALPER_DB = r"C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db"
DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

print(f"[*] Checking Scalper DB: {SCALPER_DB}")
if not os.path.exists(SCALPER_DB):
    print(f"[!] SCALPER_DB DOES NOT EXIST")
    # List what's in workspace-scalper
    sp_dir = r"C:\Users\chead\.openclaw\workspace-scalper"
    if os.path.exists(sp_dir):
        print(f"[*] Contents of {sp_dir}:")
        for f in os.listdir(sp_dir):
            fp = os.path.join(sp_dir, f)
            size = os.path.getsize(fp) if os.path.isfile(fp) else "DIR"
            print(f"    {f}: {size}")
    exit(1)

print(f"[OK] Scalper DB exists: {os.path.getsize(SCALPER_DB)} bytes")

try:
    src = sqlite3.connect(SCALPER_DB)
    src.row_factory = sqlite3.Row
    
    # List tables
    cur = src.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"[*] Scalper tables: {tables}")
    
    # Check pnl_snapshots
    if 'pnl_snapshots' in tables:
        cur = src.execute("SELECT COUNT(*) FROM pnl_snapshots")
        count = cur.fetchone()[0]
        print(f"[*] pnl_snapshots rows: {count}")
        if count > 0:
            cur = src.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
            row = cur.fetchone()
            print(f"[*] Latest snapshot: {dict(row)}")
    else:
        print(f"[!] pnl_snapshots table NOT FOUND")
    
    src.close()
except Exception as e:
    print(f"[!] Error reading Scalper DB: {e}")
    exit(1)

# Now insert into dashboard
print(f"\n[*] Syncing to dashboard: {DASHBOARD_DB}")
try:
    src = sqlite3.connect(SCALPER_DB)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(DASHBOARD_DB)
    
    rows = src.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp").fetchall()
    synced = 0
    for r in rows:
        try:
            dst.execute("""INSERT OR IGNORE INTO kalshi_snapshots
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
            if dst.execute("SELECT changes()").fetchone()[0]:
                synced += 1
        except Exception as e:
            print(f"[!] Error inserting row: {e}")
    
    dst.commit()
    src.close()
    dst.close()
    print(f"[OK] Synced {synced} Kalshi snapshots to dashboard")
except Exception as e:
    print(f"[!] Error syncing: {e}")
    exit(1)
