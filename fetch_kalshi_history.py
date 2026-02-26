#!/usr/bin/env python3
"""
Fetch complete Kalshi financial history using Scalper's KalshiClient.
Pull everything: balance history, all trades, all fills, P&L breakdown.
"""
import sys
import os
import json
import asyncio
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

async def fetch_full_history():
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
        print(f"  Found {len(positions)} positions")
        
        # Get all markets (paginated)
        print("[Kalshi] Fetching all markets...")
        markets_data = await client.get_markets(limit=200)
        all_markets = markets_data.get('markets', [])
        print(f"  Found {len(all_markets)} markets")
        
        # Get order history
        print("[Kalshi] Fetching order history...")
        orders = await client.get_order_history()
        print(f"  Found {len(orders)} orders")
        
        # Get fills
        print("[Kalshi] Fetching fills...")
        fills = await client.get_fills()
        print(f"  Found {len(fills)} fills")
        
        # Calculate total P&L from positions
        total_pnl = 0
        for pos in positions:
            pnl = int(pos.get('pnl_cents', 0))
            total_pnl += pnl
        
        print(f"\n[Summary]")
        print(f"  Total P&L: ${total_pnl/100:.2f}")
        print(f"  Total positions: {len(positions)}")
        print(f"  Total orders: {len(orders)}")
        print(f"  Total fills: {len(fills)}")
        
        result = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "balance_cents": balance,
            "balance_usd": balance / 100,
            "positions_count": len(positions),
            "orders_count": len(orders),
            "fills_count": len(fills),
            "total_pnl_usd": total_pnl / 100,
            "positions": positions,
            "orders": orders,
            "fills": fills,
            "markets": all_markets
        }
        
        await client.close()
        return result
    
    except Exception as e:
        print(f"[Error] {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print(f"[Kalshi] Using API key: {os.environ.get('KALSHI_API_KEY_ID', 'NOT SET')[:8]}...")
    print(f"[Kalshi] Environment: {os.environ.get('KALSHI_ENV', 'production')}")
    print(f"[Kalshi] Base URL: {config.KALSHI_BASE_URL}")
    
    result = asyncio.run(fetch_full_history())
    
    # Save to file
    output_file = r"C:\Users\chead\.openclaw\workspace\kalshi_full_history.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n[File] Saved to: {output_file}")
    
    if result['status'] == 'ok':
        print(f"\n[Summary]")
        print(f"  Balance: ${result['balance_usd']:.2f}")
        print(f"  Total P&L: ${result['total_pnl_usd']:.2f}")
        print(f"  Positions: {result['positions_count']}")
        print(f"  Orders: {result['orders_count']}")
        print(f"  Fills: {result['fills_count']}")
