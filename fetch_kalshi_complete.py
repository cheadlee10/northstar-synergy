#!/usr/bin/env python3
"""
Fetch complete Kalshi financial history using Scalper's KalshiClient.
Uses available API methods: balance, positions, orders, fills.
"""
import sys
import os
import json
import asyncio
import sqlite3
from datetime import datetime

# Load Scalper .env
env_file = r"C:\Users\chead\.openclaw\workspace-scalper\.env"
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

# Add Scalper to path
sys.path.insert(0, r'C:\Users\chead\.openclaw\workspace-scalper')

import config
from kalshi_api import KalshiClient

async def fetch_complete_history():
    """Fetch complete financial history from Kalshi API"""
    client = KalshiClient()
    
    try:
        print("[Kalshi] Fetching portfolio...")
        
        # Get balance
        balance = await client.get_balance()
        print(f"  Balance: {balance}¢ = ${balance/100:.2f}")
        
        # Get all positions
        print("[Kalshi] Fetching all positions...")
        positions = await client.get_positions()
        print(f"  Found {len(positions)} open positions")
        
        # Calculate P&L from positions
        total_pnl_cents = 0
        winning_positions = 0
        losing_positions = 0
        
        for pos in positions:
            pnl = int(pos.get('pnl_cents', 0) or 0)
            total_pnl_cents += pnl
            if pnl > 0:
                winning_positions += 1
            elif pnl < 0:
                losing_positions += 1
        
        print(f"    Winning: {winning_positions}, Losing: {losing_positions}")
        print(f"    Position P&L: ${total_pnl_cents/100:.2f}")
        
        # Get all orders (all statuses)
        print("[Kalshi] Fetching resting orders...")
        resting_orders = await client.get_orders(status="resting")
        print(f"  Found {len(resting_orders)} resting orders")
        
        print("[Kalshi] Fetching canceled orders...")
        canceled_orders = await client.get_orders(status="canceled")
        print(f"  Found {len(canceled_orders)} canceled orders")
        
        # Get all fills
        print("[Kalshi] Fetching fills (last 100)...")
        fills = await client.get_fills(limit=100)
        print(f"  Found {len(fills)} fills")
        
        # Calculate fill P&L
        fill_pnl_cents = 0
        for fill in fills:
            fill_pnl = int(fill.get('pnl_cents', 0) or 0)
            fill_pnl_cents += fill_pnl
        
        print(f"    Fill P&L: ${fill_pnl_cents/100:.2f}")
        
        total_orders = len(resting_orders) + len(canceled_orders)
        
        print(f"\n[LIVE SUMMARY]")
        print(f"  Account balance: ${balance/100:.2f}")
        print(f"  Open positions: {len(positions)}")
        print(f"  Total orders placed: {total_orders}")
        print(f"  Total fills: {len(fills)}")
        print(f"  Position P&L: ${total_pnl_cents/100:.2f}")
        print(f"  Fill P&L: ${fill_pnl_cents/100:.2f}")
        
        result = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "balance_cents": balance,
            "balance_usd": balance / 100,
            "positions": {
                "count": len(positions),
                "winning": winning_positions,
                "losing": losing_positions,
                "pnl_cents": total_pnl_cents,
                "pnl_usd": total_pnl_cents / 100,
                "details": positions
            },
            "orders": {
                "resting": len(resting_orders),
                "canceled": len(canceled_orders),
                "total": total_orders,
                "resting_details": resting_orders,
                "canceled_details": canceled_orders
            },
            "fills": {
                "count": len(fills),
                "pnl_cents": fill_pnl_cents,
                "pnl_usd": fill_pnl_cents / 100,
                "details": fills
            }
        }
        
        await client.close()
        return result
    
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

async def sync_to_dashboard_db(history):
    """Insert Kalshi data into dashboard DB"""
    if history.get('status') != 'ok':
        print(f"[Error] Cannot sync: {history.get('error')}")
        return
    
    db_path = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    snap_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    balance = history['balance_cents']
    pos_pnl = history['positions']['pnl_cents']
    fill_pnl = history['fills']['pnl_cents']
    total_pnl = pos_pnl + fill_pnl
    
    try:
        c.execute("""
            INSERT INTO kalshi_snapshots (
                snapshot_ts, snap_date, balance_cents, total_pnl_cents,
                open_positions, total_orders, total_fills, win_count, loss_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, snap_date, balance, total_pnl,
              history['positions']['count'], 
              history['orders']['total'],
              history['fills']['count'],
              history['positions']['winning'],
              history['positions']['losing']))
        
        conn.commit()
        print(f"\n[Dashboard] Snapshot saved: {ts}")
    except Exception as e:
        print(f"[Dashboard Error] {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"[Kalshi] Using API key: {os.environ.get('KALSHI_API_KEY_ID', 'NOT SET')[:8]}...")
    print(f"[Kalshi] Environment: {os.environ.get('KALSHI_ENV', 'production')}")
    print(f"[Kalshi] Base URL: {config.KALSHI_BASE_URL}\n")
    
    history = asyncio.run(fetch_complete_history())
    
    # Save raw history
    output_file = r"C:\Users\chead\.openclaw\workspace\kalshi_live_complete.json"
    with open(output_file, 'w') as f:
        json.dump(history, f, indent=2, default=str)
    print(f"\n[File] Saved to: {output_file}")
    
    # Sync to dashboard
    if history['status'] == 'ok':
        asyncio.run(sync_to_dashboard_db(history))
