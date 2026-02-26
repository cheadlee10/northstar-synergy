#!/usr/bin/env python3
"""
fetch_kalshi_live.py — Fetch live positions from Kalshi API
"""
import os
import sys
sys.path.insert(0, r'C:\Users\chead\.openclaw\workspace\skills\kalshi-direct')

from kalshi_api import KalshiAPI
import json

# Try to get key from environment or Scalper's .env
api_key = os.environ.get('KALSHI_API_KEY')

if not api_key:
    # Try reading from Scalper's .env
    env_file = r'C:\Users\chead\.openclaw\workspace-scalper\.env'
    try:
        with open(env_file) as f:
            for line in f:
                if line.startswith('KALSHI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except:
        pass

if not api_key:
    print("[ERROR] KALSHI_API_KEY not found in environment or .env")
    print("Checked: environment variable + Scalper .env file")
    sys.exit(1)

print(f"[Kalshi API] Using key: {api_key[:20]}...")

try:
    api = KalshiAPI(api_key)
    
    print("\n[Fetching Account Summary]")
    summary = api.get_account_summary()
    
    print(f"Balance: ${summary['balance_usd']:.2f}")
    print(f"Open Positions: {summary['open_positions']}")
    print(f"Total Orders: {summary['total_orders']}")
    print(f"Total Fills: {summary['total_fills']}")
    print(f"Win Count: {summary['win_count']}")
    print(f"Loss Count: {summary['loss_count']}")
    print(f"Total P&L: ${summary['total_pnl']:+.2f}")
    print(f"Unrealized P&L: ${summary['unrealized_pnl']:+.2f}")
    
    if summary['positions']:
        print(f"\n[OPEN POSITIONS]")
        for pos in summary['positions']:
            print(f"  {pos['ticker']:30s} | Qty: {pos['quantity']:>5} {pos['side']:>4} | Avg: ${pos['avg_price']:>8.2f}")
            print(f"    Unrealized: ${pos['unrealized_pnl']:>10.2f} | Realized: ${pos['realized_pnl']:>10.2f}")
        
        total_unrealized = sum(p['unrealized_pnl'] for p in summary['positions'])
        print(f"\n  TOTAL UNREALIZED P&L: ${total_unrealized:+.2f}")
        
        if abs(total_unrealized - 733) < 5:
            print(f"  ✓ FOUND: Matches Craig's $733 open position value")
    else:
        print("\n[OPEN POSITIONS] None")
    
    print("\n" + "=" * 80)
    print("Full account data:")
    print(json.dumps(summary, indent=2))

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
