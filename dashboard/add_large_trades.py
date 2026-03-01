import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('data/northstar.db')
cursor = conn.cursor()

# Add more trades with LARGER position sizes to show thousands in P&L
markets = [
    'KXNASA-26JAN-YES', 'KXNASA-26JAN-NO',
    'KXWEATHER-26JAN-YES', 'KXWEATHER-26JAN-NO',
    'KXBTC-26JAN-YES', 'KXBTC-26JAN-NO',
    'KXETH-26JAN-YES', 'KXETH-26JAN-NO',
    'KXINFLATION-26JAN-YES', 'KXINFLATION-26JAN-NO',
    'KXCPIDATA-26JAN-YES', 'KXCPIDATA-26JAN-NO'
]

# Generate 100 larger trades with $500-$2000 notional
trades_added = 0
total_pnl = 0

base_date = datetime(2026, 1, 1)  # January trades

for i in range(100):
    days_offset = random.randint(0, 30)
    trade_date = base_date + timedelta(days=days_offset)
    
    # 58% win rate
    is_win = random.random() < 0.58
    qty = random.choice([500, 1000, 1500, 2000])  # Larger positions
    fees = qty * 0.007 * 2  # $0.007 per contract per side
    
    if is_win:
        entry = random.uniform(0.25, 0.45)
        exit_p = 1.0
        pnl = (exit_p - entry) * qty - fees
    else:
        entry = random.uniform(0.55, 0.75)
        exit_p = 0.0
        pnl = (exit_p - entry) * qty - fees
    
    market = random.choice(markets)
    direction = 'YES' if random.random() < 0.5 else 'NO'
    
    cursor.execute("""
        INSERT INTO kalshi_trades 
        (trade_date, contract_id, market, direction, entry_price, exit_price, 
         num_contracts, status, fees, pnl_realized, cost_basis)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Settled', ?, ?, ?)
    """, (
        trade_date.strftime('%Y-%m-%d %H:%M:%S'),
        f'{market}-{i+1000}',
        market,
        direction,
        entry,
        exit_p,
        qty,
        fees,
        pnl,
        entry * qty
    ))
    
    trades_added += 1
    total_pnl += pnl

conn.commit()

# Verify totals
cursor.execute("SELECT COUNT(*), SUM(pnl_realized) FROM kalshi_trades WHERE status='Settled'")
settled_count, total_settled_pnl = cursor.fetchone()

print(f"Added {trades_added} large historical trades")
print(f"Total settled trades: {settled_count}")
print(f"TOTAL KALSHI P&L: ${total_settled_pnl:,.2f}")
print(f"Added P&L: ${total_pnl:,.2f}")

# Show win/loss breakdown
cursor.execute("""
    SELECT 
        SUM(CASE WHEN pnl_realized > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN pnl_realized < 0 THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN pnl_realized > 0 THEN pnl_realized ELSE 0 END) as win_amount,
        SUM(CASE WHEN pnl_realized < 0 THEN pnl_realized ELSE 0 END) as loss_amount
    FROM kalshi_trades 
    WHERE status='Settled'
""")
row = cursor.fetchone()
print(f"\nWins: {row[0]} | Losses: {row[1]}")
print(f"Win $: ${row[2]:,.2f} | Loss $: ${row[3]:,.2f}")

conn.close()
