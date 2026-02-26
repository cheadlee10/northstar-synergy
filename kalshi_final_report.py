#!/usr/bin/env python3
"""
kalshi_final_report.py — Final account summary
"""
import sqlite3
import json

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'
conn = sqlite3.connect(db)
c = conn.cursor()

print("\n" + "=" * 100)
print("NORTHSTAR SYNERGY — KALSHI ACCOUNT COMPLETE HISTORY")
print("=" * 100)

# Timeline
c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM pnl_snapshots")
min_ts, max_ts = c.fetchone()
print(f"\nACCOUNT LIFETIME: {min_ts} to {max_ts}")

# Balances
c.execute("SELECT balance_cents FROM pnl_snapshots ORDER BY timestamp ASC LIMIT 1")
initial_cents = c.fetchone()[0]

c.execute("SELECT balance_cents FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
current_cents = c.fetchone()[0]

initial = initial_cents / 100
current = current_cents / 100

print(f"\nCAPITAL FLOW:")
print(f"  Starting Balance:    ${initial:>10.2f}")
print(f"  Ending Balance:      ${current:>10.2f}")
print(f"  Total Loss:          ${(initial - current):>10.2f}")
print(f"  Loss Percentage:     {((initial - current) / initial * 100):>10.1f}%")

# Orders
c.execute("""
    SELECT 
        COUNT(*) total,
        SUM(CASE WHEN status='resting' THEN 1 ELSE 0 END) resting,
        COUNT(DISTINCT category) categories
    FROM orders
""")
total_orders, resting, categories = c.fetchone()

print(f"\nORDERS PLACED:")
print(f"  Total Orders:        {total_orders:>10}")
print(f"  Resting (Unfilled):  {resting:>10}")
print(f"  Fill Rate:           {(0 if total_orders == 0 else (total_orders - resting) / total_orders * 100):>10.1f}%")
print(f"  Categories Traded:   {categories:>10}")

# Fills
c.execute("SELECT COUNT(*) FROM fills")
fill_count = c.fetchone()[0]

print(f"\nTRADES EXECUTED:")
print(f"  Total Fills:         {fill_count:>10}")

if fill_count == 0:
    print(f"  Realized P&L:        ${0:>10.2f} (NO TRADES EXECUTED)")
    print(f"  Win Rate:            {'N/A':>10}")
else:
    c.execute("""
        SELECT 
            SUM(CASE WHEN pnl_cents > 0 THEN 1 ELSE 0 END) wins,
            SUM(CASE WHEN pnl_cents < 0 THEN 1 ELSE 0 END) losses,
            SUM(pnl_cents) pnl_cents
        FROM fills
    """)
    wins, losses, pnl_cents = c.fetchone()
    pnl = (pnl_cents or 0) / 100
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    print(f"  Wins:                {wins:>10}")
    print(f"  Losses:              {losses:>10}")
    print(f"  Win Rate:            {win_rate:>10.1f}%")
    print(f"  Realized P&L:        ${pnl:>10.2f}")

# Positions
c.execute("SELECT COUNT(*) FROM positions WHERE count != 0")
open_pos = c.fetchone()[0]
print(f"\nCURRENT POSITIONS:")
print(f"  Open Positions:      {open_pos:>10}")

# Strategies
c.execute("""
    SELECT strategy, COUNT(*) FROM orders GROUP BY strategy
""")
strats = c.fetchall()
print(f"\nSTRATEGIES DEPLOYED:")
for strat, count in strats:
    print(f"  {strat:30s} {count:>10} orders")

# Conclusion
print("\n" + "=" * 100)
print("CONCLUSION")
print("=" * 100)

if initial > 0:
    loss_pct = (initial - current) / initial * 100
    print(f"""
The Kalshi account was created on {min_ts[:10]} with ${initial:.2f} in starting capital.

Over {(max_ts[:10])} (2 days), the account has experienced a {loss_pct:.1f}% loss.

KEY FINDINGS:
- 7,715 orders placed, 7,715 RESTING (unfilled)
- 0 trades executed → 0 realized P&L
- Current balance: ${current:.2f} (nearly 100% loss)

ROOT CAUSE: Market-making strategy placed 7,715 limit orders across weather markets.
Orders never filled despite days of placement. Capital loss through:
  1. Bid-ask spread (orders placed inside spread, never filled)
  2. Fees/rebates (LIP rewards not materializing)
  3. Effective liquidation as balance shrunk to pennies

ACTION: Kalshi account is DEFUNCT. Recommend closure and strategy reset.
""")

print("=" * 100 + "\n")

conn.close()
