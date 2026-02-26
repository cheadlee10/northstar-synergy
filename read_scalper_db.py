#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'

try:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]
    print(f"[OK] Tables found: {', '.join(tables)}")
    
    # Get latest Kalshi balance
    if 'kalshi_snapshots' in tables:
        c.execute("""
            SELECT * FROM kalshi_snapshots 
            ORDER BY snapshot_ts DESC LIMIT 1
        """)
        latest = dict(c.fetchone() or {})
        if latest:
            print(f"\n[Kalshi Latest Snapshot]")
            print(f"  Timestamp: {latest.get('snapshot_ts')}")
            print(f"  Balance: ${(latest.get('balance_cents') or 0)/100:.2f}")
            print(f"  Total P&L: ${(latest.get('total_pnl_cents') or 0)/100:.2f}")
            print(f"  Daily P&L: ${(latest.get('daily_pnl_cents') or 0)/100:.2f}")
            print(f"  Open Positions: {latest.get('open_positions')}")
            print(f"  Wins: {latest.get('win_count')}, Losses: {latest.get('loss_count')}")
    
    # Get order history
    if 'kalshi_orders' in tables:
        c.execute("SELECT COUNT(*) FROM kalshi_orders")
        count = c.fetchone()[0]
        print(f"\n[Kalshi Orders] {count} total orders")
    
    conn.close()
    print("\n[OK] Database read successful")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
