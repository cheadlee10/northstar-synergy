#!/usr/bin/env python3
"""
fetch_v8_positions.py — Export positions from V8 engine to dashboard
Craig reported $733 in open positions. This script finds and syncs them.
"""
import sqlite3
import json
from datetime import datetime

v8_db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'
dashboard_db = r'C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db'

print("=" * 80)
print("FETCH V8 POSITIONS → DASHBOARD SYNC")
print("=" * 80)

v8_conn = sqlite3.connect(v8_db)
v8_conn.row_factory = sqlite3.Row
v8_c = v8_conn.cursor()

# Get latest snapshot for reference
v8_c.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
latest = dict(v8_c.fetchone() or {})

print(f"\n[V8 Account State]")
print(f"  Balance: ${(latest.get('balance_cents', 0) or 0)/100:.2f}")
print(f"  Open Positions (recorded): {latest.get('open_positions', 0)}")
print(f"  Total Orders: {latest.get('total_orders', 0)}")

# Check positions table
print(f"\n[V8 Positions Table]")
v8_c.execute("SELECT COUNT(*) FROM positions WHERE count != 0")
pos_count = v8_c.fetchone()[0]
print(f"  Rows with open quantity: {pos_count}")

if pos_count > 0:
    v8_c.execute("SELECT ticker, side, count, unrealized_pnl_cents FROM positions WHERE count != 0")
    positions = [dict(row) for row in v8_c.fetchall()]
    
    total_unrealized = sum((row['unrealized_pnl_cents'] or 0) for row in positions)
    print(f"  Total unrealized P&L: ${total_unrealized/100:.2f}")
    
    for pos in positions:
        print(f"    {pos['ticker']:30s} | Qty: {pos['count']:>4} {pos['side']:>4} | Unrealized: ${(pos['unrealized_pnl_cents'] or 0)/100:>10.2f}")
    
    # Sync to dashboard
    print(f"\n[Syncing to Dashboard]")
    dashboard_conn = sqlite3.connect(dashboard_db)
    dashboard_c = dashboard_conn.cursor()
    
    synced = 0
    for pos in positions:
        try:
            dashboard_c.execute("""
                INSERT OR REPLACE INTO positions (
                    ticker, category, side, count, avg_price_cents, 
                    unrealized_pnl_cents, realized_pnl_cents, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pos['ticker'],
                'weather',  # Scalper is weather-focused
                pos['side'],
                pos['count'],
                0,  # Don't have avg_price_cents in this context
                pos['unrealized_pnl_cents'],
                0,
                datetime.utcnow().isoformat()
            ))
            synced += 1
        except Exception as e:
            print(f"    Error syncing {pos['ticker']}: {e}")
    
    dashboard_conn.commit()
    dashboard_conn.close()
    
    print(f"  ✓ Synced {synced} positions to dashboard")
    print(f"  Dashboard: {dashboard_db}")
    
else:
    print(f"  No open positions in V8 DB")
    print(f"  But Craig reports $733 live positions.")
    print(f"  Options:")
    print(f"    1. Positions may be in memory (V8 process, not yet persisted)")
    print(f"    2. Check if V8 is actively trading (see monitor_v8_health.py)")
    print(f"    3. Ask Craig for position details (ticker, qty, side)")

v8_conn.close()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
