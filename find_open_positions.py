#!/usr/bin/env python3
"""
find_open_positions.py — Find all open positions with real P&L
"""
import sqlite3

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 100)
print("KALSHI OPEN POSITIONS — DETAILED AUDIT")
print("=" * 100)

# Check positions table schema
print("\n[POSITIONS TABLE SCHEMA]")
c.execute("PRAGMA table_info(positions)")
schema = c.fetchall()
for col in schema:
    print(f"  {col[1]} ({col[2]})")

# Get ALL positions (not just where count != 0)
print("\n[ALL POSITIONS IN TABLE]")
c.execute("SELECT COUNT(*) FROM positions")
total_pos = c.fetchone()[0]
print(f"Total rows: {total_pos}")

# Get summary
c.execute("""
    SELECT 
        COUNT(*) total,
        SUM(CASE WHEN count != 0 THEN 1 ELSE 0 END) open,
        SUM(unrealized_pnl_cents) unrealized_pnl,
        SUM(realized_pnl_cents) realized_pnl
    FROM positions
""")
summary = dict(c.fetchone())
unrealized = (summary.get('unrealized_pnl') or 0) / 100
realized = (summary.get('realized_pnl') or 0) / 100

print(f"Total rows: {summary['total']}")
print(f"Open positions: {summary['open']}")
print(f"Total unrealized P&L: ${unrealized:+.2f}")
print(f"Total realized P&L: ${realized:+.2f}")

# List ALL positions
print("\n[POSITION DETAILS]")
c.execute("SELECT * FROM positions ORDER BY ticker")
for row in c.fetchall():
    p = dict(row)
    qty = p.get('count') or 0
    unrealized = (p.get('unrealized_pnl_cents') or 0) / 100
    realized = (p.get('realized_pnl_cents') or 0) / 100
    
    if qty != 0 or unrealized != 0 or realized != 0:
        print(f"  {p['ticker']:30s} | Qty: {qty:>4} {p['side']:>4} | Avg Price: ${(p.get('avg_price_cents') or 0)/100:.2f}")
        print(f"    Unrealized: ${unrealized:>10.2f} | Realized: ${realized:>10.2f} | Updated: {p['updated_at']}")

# Sum up open positions with real values
print("\n[OPEN POSITIONS WITH VALUE]")
c.execute("""
    SELECT ticker, side, count, avg_price_cents, unrealized_pnl_cents, realized_pnl_cents
    FROM positions
    WHERE count != 0 OR unrealized_pnl_cents != 0 OR realized_pnl_cents != 0
    ORDER BY unrealized_pnl_cents DESC
""")

rows = c.fetchall()
if rows:
    total_unrealized = 0
    for row in rows:
        r = dict(row)
        qty = r['count']
        side = r['side']
        avg_price = (r['avg_price_cents'] or 0) / 100
        unrealized = (r['unrealized_pnl_cents'] or 0) / 100
        realized = (r['realized_pnl_cents'] or 0) / 100
        total_unrealized += unrealized
        
        print(f"  {r['ticker']:30s} | Qty: {qty:>4} {side:>4} | Avg: ${avg_price:>8.2f}")
        print(f"    Unrealized: ${unrealized:>10.2f} | Realized: ${realized:>10.2f}")
    
    print(f"\n  TOTAL UNREALIZED P&L: ${total_unrealized:>10.2f}")
    if abs(total_unrealized - 733) < 10:
        print(f"  ✓ MATCHES: $733 open position value found!")
else:
    print("  (no open positions with value)")

# Check orders for any pending
print("\n[PENDING ORDERS THAT MIGHT CREATE POSITIONS]")
c.execute("""
    SELECT COUNT(*) FROM orders WHERE status='resting'
""")
resting = c.fetchone()[0]
print(f"Resting orders: {resting}")

conn.close()
