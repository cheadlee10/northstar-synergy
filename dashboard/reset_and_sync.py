import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('data/northstar.db')
cursor = conn.cursor()

# DELETE ALL kalshi trades
cursor.execute("DELETE FROM kalshi_trades")
print("Cleared all Kalshi trades")

# Now parse ACTUAL trade_log.jsonl and calculate P&L properly
trade_log = Path('C:/Users/chead/.openclaw/workspace-scalper/trade_log.jsonl')

if not trade_log.exists():
    print(f"ERROR: Trade log not found at {trade_log}")
    conn.close()
    exit(1)

# Parse all trades
trades = []
with open(trade_log) as f:
    for line in f:
        try:
            trade = json.loads(line.strip())
            trades.append(trade)
        except:
            continue

print(f"Parsed {len(trades)} trades from log")

# Group by ticker and match buys with sells
from collections import defaultdict
by_ticker = defaultdict(lambda: {'buys': [], 'sells': []})

for t in trades:
    ticker = t.get('ticker', '')
    side = t.get('side', '')
    if side == 'buy':
        by_ticker[ticker]['buys'].append(t)
    elif side == 'sell':
        by_ticker[ticker]['sells'].append(t)

# Calculate completed trades (where both buy and sell exist)
completed = 0
total_pnl = 0

for ticker, data in by_ticker.items():
    buys = sorted(data['buys'], key=lambda x: x.get('timestamp', ''))
    sells = sorted(data['sells'], key=lambda x: x.get('timestamp', ''))
    
    for buy in buys:
        buy_price = buy.get('yes_price', 0)
        buy_qty = buy.get('count', 0)
        
        for sell in sells[:]:
            sell_price = sell.get('yes_price', 0)
            sell_qty = sell.get('count', 0)
            
            if buy_qty <= 0:
                break
                
            matched = min(buy_qty, sell_qty)
            if matched <= 0:
                continue
            
            # Calculate P&L
            pnl = (sell_price - buy_price) * matched
            fees = matched * 0.007 * 2  # $0.007 per contract per side
            net_pnl = pnl - fees
            
            cursor.execute("""
                INSERT INTO kalshi_trades 
                (trade_date, contract_id, market, direction, entry_price, exit_price,
                 num_contracts, status, fees, pnl_realized, cost_basis)
                VALUES (?, ?, ?, 'YES', ?, ?, ?, 'Settled', ?, ?, ?)
            """, (
                buy.get('timestamp'),
                ticker,
                ticker.split('-')[0] if '-' in ticker else ticker,
                buy_price,
                sell_price,
                int(matched),
                fees,
                net_pnl,
                buy_price * matched
            ))
            
            completed += 1
            total_pnl += net_pnl
            
            buy_qty -= matched
            sell['count'] = sell_qty - matched
            if sell['count'] <= 0:
                sells.remove(sell)

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*), SUM(pnl_realized) FROM kalshi_trades")
count, pnl = cursor.fetchone()

print(f"\n=== RESULT ===")
print(f"Completed trades: {completed}")
print(f"Total P&L: ${total_pnl:,.2f}")
print(f"DB rows: {count} | DB P&L: ${pnl or 0:,.2f}")

conn.close()
