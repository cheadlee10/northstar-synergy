#!/usr/bin/env python3
"""
monitor_v8_health.py — Monitor Scalper V8 engine health and live positions
Checks DB connectivity, position count, P&L, and suggests actions
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

db_path = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'
log_path = r'C:\Users\chead\.openclaw\workspace-scalper\logs\scalper_v8.log'

print("=" * 100)
print("SCALPER V8 ENGINE — HEALTH MONITOR")
print("=" * 100)

# Check if DB exists
if not Path(db_path).exists():
    print(f"\n✗ DATABASE NOT FOUND: {db_path}")
    print(f"  V8 engine may not have started yet.")
    print(f"  Action: Run launch_v8.ps1 from workspace-scalper/")
    exit(1)

print(f"\n✓ Database found: {db_path}")

# Connect
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get latest snapshot
print("\n[LATEST ACCOUNT STATE]")
c.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
latest_snap = dict(c.fetchone() or {})

if latest_snap:
    ts = latest_snap.get('timestamp')
    balance = (latest_snap.get('balance_cents') or 0) / 100
    pnl = (latest_snap.get('total_pnl_cents') or 0) / 100
    open_pos = latest_snap.get('open_positions')
    
    print(f"  Timestamp: {ts}")
    print(f"  Balance: ${balance:.2f}")
    print(f"  Total P&L: ${pnl:+.2f}")
    print(f"  Open Positions: {open_pos}")
    
    # Check freshness
    try:
        snap_time = datetime.fromisoformat(ts)
        now = datetime.utcnow()
        age = (now - snap_time).total_seconds()
        
        if age < 60:
            print(f"  Status: ✓ RUNNING (snapshot < 1 min old)")
        elif age < 300:
            print(f"  Status: ✓ RUNNING (snapshot {int(age)}s old)")
        elif age < 3600:
            print(f"  Status: ⚠ SLOW (snapshot {int(age/60)}m old)")
        else:
            print(f"  Status: ✗ STALLED (snapshot {int(age/3600)}h old)")
    except:
        pass
else:
    print(f"  No snapshots found. V8 may not have run.")

# Orders status
print("\n[ORDERS ANALYSIS]")
c.execute("""
    SELECT 
        COUNT(*) total,
        SUM(CASE WHEN status='resting' THEN 1 ELSE 0 END) resting,
        SUM(CASE WHEN status='FILLED' THEN 1 ELSE 0 END) filled,
        SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) cancelled
    FROM orders
""")
ord = dict(c.fetchone() or {})
print(f"  Total Orders Placed: {ord.get('total', 0)}")
print(f"  Resting (Unfilled): {ord.get('resting', 0)}")
print(f"  Filled: {ord.get('filled', 0)}")
print(f"  Cancelled: {ord.get('cancelled', 0)}")

if ord.get('total', 0) > 0 and ord.get('filled', 0) == 0:
    print(f"  ⚠ WARNING: {ord.get('total')} orders placed, 0 fills. Market-making not executing.")

# Fills (realized trades)
print("\n[EXECUTED TRADES]")
c.execute("SELECT COUNT(*) FROM fills")
fill_count = c.fetchone()[0]

if fill_count == 0:
    print(f"  Executed Trades: {fill_count}")
    print(f"  ⚠ WARNING: No trades executed. Orders are not filling.")
    print(f"  Possible issues:")
    print(f"    1. Limit orders are too far from midpoint")
    print(f"    2. Market liquidity is low")
    print(f"    3. Order strategy parameters need tuning")
else:
    c.execute("""
        SELECT 
            SUM(CASE WHEN pnl_cents > 0 THEN 1 ELSE 0 END) wins,
            SUM(CASE WHEN pnl_cents < 0 THEN 1 ELSE 0 END) losses,
            SUM(pnl_cents) pnl_cents
        FROM fills
    """)
    f = dict(c.fetchone())
    pnl = (f.get('pnl_cents') or 0) / 100
    print(f"  Executed Trades: {fill_count}")
    print(f"  Wins: {f.get('wins', 0)} | Losses: {f.get('losses', 0)}")
    print(f"  Realized P&L: ${pnl:+.2f}")

# Strategies
print("\n[STRATEGIES DEPLOYED]")
c.execute("""
    SELECT strategy, COUNT(*) FROM orders GROUP BY strategy
""")
strats = c.fetchall()
for row in strats:
    print(f"  {row[0]:30s} {row[1]:>6} orders")

# Positions
print("\n[OPEN POSITIONS]")
c.execute("SELECT COUNT(*) FROM positions WHERE count != 0")
open_pos = c.fetchone()[0]
print(f"  Open Positions (DB): {open_pos}")
print(f"  Craig's Report: $733 in open positions")

if open_pos == 0 and 733 > 0:
    print(f"  ⚠ SYNC ISSUE: Positions exist live ($733) but not in local DB")
    print(f"  Action: Positions may be cached in memory or Kalshi API")
    print(f"  Run: python fetch_v8_positions.py to export positions")

# Log file check
print("\n[RECENT LOG MESSAGES]")
try:
    with open(log_path, 'r', errors='ignore') as f:
        lines = f.readlines()[-20:]  # Last 20 lines
        for line in lines[-5:]:
            print(f"  {line.rstrip()}")
except FileNotFoundError:
    print(f"  ! Log file not found: {log_path}")

# Summary
print("\n" + "=" * 100)
print("RECOMMENDED ACTIONS")
print("=" * 100)

if not latest_snap:
    print("\n1. V8 ENGINE NOT RUNNING")
    print("   Run: workspace-scalper\\launch_v8.ps1")
elif ord.get('total', 0) == 0:
    print("\n1. NO ORDERS PLACED")
    print("   Check V8 logs for startup errors")
    print("   Verify market data sources are accessible (weather API, etc)")
elif ord.get('filled', 0) == 0:
    print("\n1. ORDERS NOT FILLING")
    print("   Options:")
    print("   a) Adjust MM parameters (spread, gamma, kappa) in .env")
    print("   b) Check if markets have sufficient liquidity")
    print("   c) Verify Kalshi API can accept orders")
elif fill_count > 0 and pnl < 0:
    print("\n1. LOSING MONEY")
    print("   Review strategy:") 
    print("   - Check MM parameter optimization")
    print("   - Review realized P&L breakdown by category")
    print("   - Consider disabling low-performing strategies")

if open_pos == 0 and 733 > 0:
    print("\n2. SYNC POSITIONS TO DASHBOARD")
    print("   Run: python fetch_v8_positions.py")
    print("   This will export live $733 positions to dashboard DB")

print("\n" + "=" * 100)

conn.close()
