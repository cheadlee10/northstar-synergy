#!/usr/bin/env python3
"""
REAL Data Sync - Parse actual trade logs and calculate true P&L
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
SCALPER_DIR = Path('C:/Users/chead/.openclaw/workspace-scalper')
DASHBOARD_DB = Path('C:/Users/chead/.openclaw/workspace/dashboard/data/northstar.db')

def sync_kalshi_trades():
    """Parse trade_log.jsonl and calculate real P&L."""
    trade_log = SCALPER_DIR / 'trade_log.jsonl'
    
    if not trade_log.exists():
        print(f"Trade log not found: {trade_log}")
        return 0, 0
    
    conn = sqlite3.connect(DASHBOARD_DB)
    cursor = conn.cursor()
    
    # Clear existing fake data
    cursor.execute("DELETE FROM kalshi_trades WHERE pnl_realized IS NULL OR trade_date LIKE '%REPLACE%'")
    
    # Parse trade log
    trades_by_contract = {}
    with open(trade_log) as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                ticker = trade.get('ticker', '')
                
                if ticker not in trades_by_contract:
                    trades_by_contract[ticker] = []
                trades_by_contract[ticker].append(trade)
            except:
                continue
    
    # Calculate P&L for completed trades (pairs of buy/sell)
    total_pnl = 0
    trades_added = 0
    
    for ticker, trades in trades_by_contract.items():
        # Group by side
        buys = [t for t in trades if t.get('side') == 'buy']
        sells = [t for t in trades if t.get('side') == 'sell']
        
        # Match buys with sells to calculate P&L
        for buy in buys:
            buy_price = buy.get('yes_price', 0)
            buy_qty = buy.get('count', 0)
            
            # Find matching sell
            for sell in sells[:]:
                sell_price = sell.get('yes_price', 0)
                sell_qty = sell.get('count', 0)
                
                # Calculate matched quantity
                matched_qty = min(buy_qty, sell_qty)
                if matched_qty <= 0:
                    continue
                
                # P&L calculation
                pnl = (sell_price - buy_price) * matched_qty
                fees = matched_qty * 0.007 * 2  # $0.007 per contract per side
                net_pnl = pnl - fees
                
                # Determine market from ticker
                market = ticker.split('-')[0] if '-' in ticker else ticker
                
                # Insert completed trade
                cursor.execute("""
                    INSERT INTO kalshi_trades 
                    (trade_date, contract_id, market, direction, entry_price, exit_price,
                     num_contracts, status, fees, pnl_realized, cost_basis)
                    VALUES (?, ?, ?, 'YES', ?, ?, ?, 'Settled', ?, ?, ?)
                """, (
                    buy.get('timestamp', datetime.now().isoformat()),
                    ticker,
                    market,
                    buy_price,
                    sell_price,
                    matched_qty,
                    fees,
                    net_pnl,
                    buy_price * matched_qty
                ))
                
                total_pnl += net_pnl
                trades_added += 1
                
                # Update remaining quantities
                buy_qty -= matched_qty
                sell['count'] = sell_qty - matched_qty
                
                if sell['count'] <= 0:
                    sells.remove(sell)
                
                if buy_qty <= 0:
                    break
    
    conn.commit()
    conn.close()
    
    print(f"Kalshi: Added {trades_added} completed trades with ${total_pnl:,.2f} P&L")
    return trades_added, total_pnl

def sync_sports_picks():
    """Parse pick_performance_log.jsonl for real sports betting data."""
    picks_log = SCALPER_DIR / 'pick_performance_log.jsonl'
    
    if not picks_log.exists():
        print(f"Picks log not found: {picks_log}")
        return 0, 0
    
    conn = sqlite3.connect(DASHBOARD_DB)
    cursor = conn.cursor()
    
    # Clear existing sports data
    cursor.execute("DELETE FROM sports_picks")
    
    total_pnl = 0
    picks_added = 0
    
    with open(picks_log) as f:
        for line in f:
            try:
                pick = json.loads(line.strip())
                
                # Calculate P&L for settled picks (assume $100 unit bets)
                result = pick.get('result', 'PENDING')
                ml = pick.get('ml', 0)
                
                if result == 'WIN':
                    # Moneyline payout calculation
                    if ml > 0:
                        profit = (ml / 100) * 100  # +130 = $130 profit on $100 bet
                    else:
                        profit = (100 / abs(ml)) * 100  # -150 = $66.67 profit
                elif result == 'LOSS':
                    profit = -100  # Lost $100 stake
                else:
                    profit = 0  # Pending
                
                cursor.execute("""
                    INSERT INTO sports_picks 
                    (pick_date, sport, game, pick, ml, open_ml, edge_val, model_prob,
                     confidence, result, stake, profit_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 100, ?)
                """, (
                    pick.get('date'),
                    pick.get('sport'),
                    pick.get('game'),
                    pick.get('pick'),
                    ml,
                    pick.get('open_ml'),
                    pick.get('edge_val'),
                    pick.get('model_prob'),
                    pick.get('confidence', 'MEDIUM'),
                    result,
                    profit
                ))
                
                if result in ('WIN', 'LOSS'):
                    total_pnl += profit
                picks_added += 1
                
            except Exception as e:
                continue
    
    conn.commit()
    conn.close()
    
    print(f"Sports: Added {picks_added} picks with ${total_pnl:,.2f} P&L")
    return picks_added, total_pnl

def main():
    print("=" * 60)
    print("SYNCING REAL DATA FROM TRADE LOGS")
    print("=" * 60)
    
    kalshi_count, kalshi_pnl = sync_kalshi_trades()
    sports_count, sports_pnl = sync_sports_picks()
    
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Kalshi trades: {kalshi_count} | P&L: ${kalshi_pnl:,.2f}")
    print(f"Sports picks:  {sports_count} | P&L: ${sports_pnl:,.2f}")
    print(f"TOTAL P&L:     ${kalshi_pnl + sports_pnl:,.2f}")

if __name__ == "__main__":
    main()
