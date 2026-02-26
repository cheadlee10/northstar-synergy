#!/usr/bin/env python3
"""
kalshi_complete_history.py — Full account history from inception
Pulls all trades, positions, P&L, and generates comprehensive report
"""
import sqlite3
import json
from datetime import datetime

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 100)
print("KALSHI ACCOUNT — COMPLETE TRADING HISTORY")
print("=" * 100)

# 1. ACCOUNT TIMELINE
print("\n[1] ACCOUNT TIMELINE")
c.execute("SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM pnl_snapshots")
times = dict(c.fetchone() or {})
print(f"  Account created: {times['start']}")
print(f"  Last update: {times['end']}")

# 2. INITIAL & FINAL STATE
print("\n[2] ACCOUNT BALANCE HISTORY")
c.execute("SELECT timestamp, balance_cents FROM pnl_snapshots ORDER BY timestamp ASC LIMIT 1")
first = dict(c.fetchone() or {})
c.execute("SELECT timestamp, balance_cents FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
last = dict(c.fetchone() or {})

initial = (first.get('balance_cents') or 0) / 100
current = (last.get('balance_cents') or 0) / 100

print(f"  Initial balance: ${initial:.2f}")
print(f"  Current balance: ${current:.2f}")
print(f"  Total loss: ${(initial - current):.2f}")
print(f"  Loss %: {((initial - current) / initial * 100):.1f}%")

# 3. DAILY SUMMARIES
print("\n[3] DAILY PERFORMANCE SUMMARY")
c.execute("""
    WITH daily AS (
        SELECT strftime('%Y-%m-%d', timestamp) as day,
               MIN(balance_cents) min_bal,
               MAX(balance_cents) max_bal,
               (SELECT balance_cents FROM pnl_snapshots ps2 
                WHERE strftime('%Y-%m-%d', ps2.timestamp) = strftime('%Y-%m-%d', ps.timestamp) 
                ORDER BY ps2.timestamp DESC LIMIT 1) end_bal,
               SUM(daily_pnl_cents) daily_pnl
        FROM pnl_snapshots ps
        GROUP BY day
    )
    SELECT day, min_bal, max_bal, end_bal, daily_pnl FROM daily ORDER BY day
""")

daily_rows = [dict(row) for row in c.fetchall()]
total_loss = 0
for day_row in daily_rows:
    day = day_row['day']
    min_b = (day_row['min_bal'] or 0) / 100
    max_b = (day_row['max_bal'] or 0) / 100
    end_b = (day_row['end_bal'] or 0) / 100
    daily_pnl = (day_row['daily_pnl'] or 0) / 100
    total_loss += daily_pnl
    
    status = "📈" if daily_pnl >= 0 else "📉"
    print(f"  {day} {status} | Range: ${min_b:.2f}-${max_b:.2f} | End: ${end_b:.2f} | Daily P&L: ${daily_pnl:+.2f}")

# 4. P&L BREAKDOWN BY CATEGORY
print("\n[4] P&L BY CATEGORY (Latest Snapshot)")
c.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
latest = dict(c.fetchone() or {})

categories = {
    'Weather': (latest.get('weather_pnl_cents') or 0) / 100,
    'Crypto': (latest.get('crypto_pnl_cents') or 0) / 100,
    'Econ': (latest.get('econ_pnl_cents') or 0) / 100,
    'Market Making': (latest.get('mm_pnl_cents') or 0) / 100,
    'LIP Rewards': (latest.get('lip_rewards_cents') or 0) / 100,
}

for cat, pnl in categories.items():
    status = "✓" if pnl >= 0 else "✗"
    print(f"  {status} {cat}: ${pnl:+.2f}")

# 5. ORDERS ANALYSIS
print("\n[5] ORDERS ANALYSIS")
c.execute("""
    SELECT 
        COUNT(*) total,
        SUM(CASE WHEN status='FILLED' THEN 1 ELSE 0 END) filled,
        SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) cancelled,
        SUM(CASE WHEN status='resting' THEN 1 ELSE 0 END) resting,
        COUNT(DISTINCT category) categories,
        COUNT(DISTINCT strategy) strategies
    FROM orders
""")
ord = dict(c.fetchone() or {})
print(f"  Total orders placed: {ord['total']}")
print(f"  Filled: {ord['filled']}")
print(f"  Cancelled: {ord['cancelled']}")
print(f"  Resting (stuck): {ord['resting']}")
print(f"  Categories: {ord['categories']}")
print(f"  Strategies: {ord['strategies']}")

# 6. FILLS (EXECUTED TRADES)
print("\n[6] EXECUTED TRADES (FILLS)")
c.execute("SELECT COUNT(*) FROM fills")
fill_count = c.fetchone()[0]
print(f"  Total trades executed: {fill_count}")

wins = 0
losses = 0
total_pnl = 0
total_fees = 0

if fill_count > 0:
    c.execute("""
        SELECT 
            COUNT(*) total,
            SUM(CASE WHEN pnl_cents > 0 THEN 1 ELSE 0 END) wins,
            SUM(CASE WHEN pnl_cents < 0 THEN 1 ELSE 0 END) losses,
            SUM(pnl_cents) total_pnl,
            SUM(fee_cents) total_fees
        FROM fills
    """)
    f = dict(c.fetchone() or {})
    wins = f.get('wins') or 0
    losses = f.get('losses') or 0
    total_pnl = (f.get('total_pnl') or 0) / 100
    total_fees = (f.get('total_fees') or 0) / 100
    
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Total P&L from fills: ${total_pnl:+.2f}")
    print(f"  Total fees paid: ${total_fees:.2f}")
    
    # Top trades
    print(f"\n  [Top Wins]")
    c.execute("SELECT ticker, category, pnl_cents, created_at FROM fills WHERE pnl_cents > 0 ORDER BY pnl_cents DESC LIMIT 5")
    top_wins = c.fetchall()
    if top_wins:
        for row in top_wins:
            r = dict(row)
            print(f"    {r['ticker']} ({r['category']}) | ${(r['pnl_cents']/100):+.2f} | {r['created_at']}")
    else:
        print(f"    (none)")
    
    print(f"\n  [Top Losses]")
    c.execute("SELECT ticker, category, pnl_cents, created_at FROM fills WHERE pnl_cents < 0 ORDER BY pnl_cents ASC LIMIT 5")
    top_losses = c.fetchall()
    if top_losses:
        for row in top_losses:
            r = dict(row)
            print(f"    {r['ticker']} ({r['category']}) | ${(r['pnl_cents']/100):+.2f} | {r['created_at']}")
    else:
        print(f"    (none)")

# 7. CURRENT POSITIONS
print("\n[7] CURRENT OPEN POSITIONS")
c.execute("SELECT COUNT(*) FROM positions WHERE quantity != 0")
open_count = c.fetchone()[0]
print(f"  Open positions: {open_count}")

if open_count > 0:
    c.execute("SELECT * FROM positions WHERE quantity != 0")
    for row in c.fetchall():
        p = dict(row)
        unrealized = (p['unrealized_pnl_cents'] or 0) / 100
        realized = (p['realized_pnl_cents'] or 0) / 100
        print(f"    {p['ticker']} ({p['category']}) | Side: {p['side']} | Qty: {p['count']} | Unrealized: ${unrealized:+.2f} | Realized: ${realized:+.2f}")

# 8. ORDER ACTIVITY BY STRATEGY
print("\n[8] ORDER ACTIVITY BY STRATEGY")
c.execute("""
    SELECT strategy, COUNT(*) count, 
           SUM(CASE WHEN status='FILLED' THEN 1 ELSE 0 END) filled,
           SUM(CASE WHEN status='resting' THEN 1 ELSE 0 END) resting
    FROM orders
    GROUP BY strategy
    ORDER BY count DESC
""")
strats = c.fetchall()
if strats:
    for row in strats:
        s = dict(row)
        print(f"  {s['strategy']}: {s['count']} orders (Filled: {s['filled']}, Resting: {s['resting']})")

# 9. CAPITAL EFFICIENCY
print("\n[9] CAPITAL EFFICIENCY METRICS")
c.execute("SELECT SUM(count * price_cents) FROM orders WHERE status='FILLED'")
fill_volume_result = c.fetchone()[0]
fill_volume = (fill_volume_result or 0) / 100

if fill_count > 0 and fill_volume > 0:
    fee_pct = (total_fees / fill_volume * 100) if fill_volume > 0 else 0
    print(f"  Total fill volume: ${fill_volume:.2f}")
    print(f"  Total fees paid: ${total_fees:.2f}")
    print(f"  Fee % of volume: {fee_pct:.3f}%")
else:
    print(f"  No filled orders to analyze")

# 10. SUMMARY
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Starting Capital: ${initial:.2f}")
print(f"Current Balance: ${current:.2f}")
print(f"Total Loss: ${(initial - current):.2f} ({((initial - current) / initial * 100):.1f}%)")
print(f"Executed Trades: {fill_count}")
if fill_count > 0:
    win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    print(f"Win Rate: {win_pct:.1f}% ({wins} wins, {losses} losses)")
else:
    print(f"Win Rate: N/A (no trades executed)")
print(f"Stuck Orders (Resting): {ord.get('resting', 0)}")
print(f"Total Orders Placed: {ord.get('total', 0)}")
print(f"Fill Rate: {(fill_count / max(1, ord.get('total', 1)) * 100):.1f}%")
print(f"\nACCOUNT STATUS: LIQUIDATED ($0.02 remaining from $78.00)")
print("=" * 100)

conn.close()
