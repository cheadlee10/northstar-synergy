#!/usr/bin/env python3
import sqlite3
from datetime import datetime

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print("SCALPER KALSHI ACCOUNT — REAL-TIME P&L")
print("=" * 80)

# Get latest snapshot
c.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
latest = dict(c.fetchone() or {})

if not latest:
    print("[ERROR] No snapshots found")
else:
    print(f"\n[CURRENT STATE] {latest.get('timestamp')}")
    print(f"  Balance: ${(latest.get('balance_cents') or 0)/100:.2f}")
    print(f"  Total P&L: ${(latest.get('total_pnl_cents') or 0)/100:.2f}")
    print(f"  Daily P&L: ${(latest.get('daily_pnl_cents') or 0)/100:.2f}")
    print(f"  Open Positions: {latest.get('open_positions')}")
    print(f"  Total Orders: {latest.get('total_orders')}")
    print(f"  Total Fills: {latest.get('total_fills')}")
    print(f"  Wins: {latest.get('win_count')} | Losses: {latest.get('loss_count')}")
    print(f"  Weather P&L: ${(latest.get('weather_pnl_cents') or 0)/100:.2f}")
    print(f"  Crypto P&L: ${(latest.get('crypto_pnl_cents') or 0)/100:.2f}")
    print(f"  Econ P&L: ${(latest.get('econ_pnl_cents') or 0)/100:.2f}")
    print(f"  MM P&L: ${(latest.get('mm_pnl_cents') or 0)/100:.2f}")

# Get all snapshots to see history
print("\n[HISTORY] Last 10 snapshots")
c.execute("SELECT timestamp, balance_cents, total_pnl_cents, daily_pnl_cents FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 10")
for row in c.fetchall():
    d = dict(row)
    print(f"  {d['timestamp']} | Balance: ${(d['balance_cents']/100):>8.2f} | Total: ${((d['total_pnl_cents'] or 0)/100):>8.2f}")

# Check fills
print("\n[FILLS]")
c.execute("SELECT COUNT(*) FROM fills")
fill_count = c.fetchone()[0]
print(f"  Total fills: {fill_count}")

if fill_count > 0:
    c.execute("""
        SELECT COUNT(*) total,
               SUM(CASE WHEN pnl_cents > 0 THEN 1 ELSE 0 END) wins,
               SUM(CASE WHEN pnl_cents < 0 THEN 1 ELSE 0 END) losses,
               SUM(pnl_cents) total_pnl
        FROM fills
    """)
    f = dict(c.fetchone())
    print(f"  Wins: {f.get('wins')} | Losses: {f.get('losses')} | Total P&L: ${(f.get('total_pnl') or 0)/100:.2f}")

# Check orders
print("\n[ORDERS]")
c.execute("""
    SELECT COUNT(*) total,
           SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) pending,
           SUM(CASE WHEN status='resting' THEN 1 ELSE 0 END) resting,
           SUM(CASE WHEN status='FILLED' THEN 1 ELSE 0 END) filled,
           SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) cancelled
    FROM orders
""")
o = dict(c.fetchone())
print(f"  Total: {o['total']} | Pending: {o['pending']} | Resting: {o['resting']} | Filled: {o['filled']} | Cancelled: {o['cancelled']}")

print("\n" + "=" * 80)

conn.close()
