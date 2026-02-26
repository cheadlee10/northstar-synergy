#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'

try:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 80)
    print("SCALPER V8 DATABASE — LIVE ACCOUNT STATE")
    print("=" * 80)
    
    # Latest PnL snapshot
    print("\n[1] PnL Snapshots (Latest 5)")
    c.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 5")
    for row in c.fetchall():
        d = dict(row)
        print(f"  {d.get('timestamp')} | Balance: ${(d.get('balance') or 0)/100:.2f} | Total P&L: ${(d.get('total_pnl') or 0)/100:.2f}")
    
    # Daily summary
    print("\n[2] Daily Summary (Latest 5 days)")
    c.execute("SELECT * FROM daily_summary ORDER BY date DESC LIMIT 5")
    for row in c.fetchall():
        d = dict(row)
        print(f"  {d.get('date')} | Balance: ${(d.get('end_balance') or 0)/100:.2f} | P&L: ${(d.get('daily_pnl') or 0)/100:.2f}")
    
    # Orders
    print("\n[3] Orders (Latest 10)")
    c.execute("""
        SELECT COUNT(*) total, 
               SUM(CASE WHEN filled > 0 THEN 1 ELSE 0 END) filled,
               SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) cancelled,
               SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) pending
        FROM orders
    """)
    counts = dict(c.fetchone() or {})
    print(f"  Total: {counts.get('total')} | Filled: {counts.get('filled')} | Pending: {counts.get('pending')} | Cancelled: {counts.get('cancelled')}")
    
    # Fills (realized trades)
    print("\n[4] Fills (Trades Realized)")
    c.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN result_cents > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN result_cents < 0 THEN 1 ELSE 0 END) as losses,
               SUM(result_cents) as total_result_cents
        FROM fills
    """)
    fills = dict(c.fetchone() or {})
    total_result = (fills.get('total_result_cents') or 0) / 100
    print(f"  Trades: {fills.get('total')} | Wins: {fills.get('wins')} | Losses: {fills.get('losses')} | Total P&L: ${total_result:.2f}")
    
    # Current positions
    print("\n[5] Current Positions (Open)")
    c.execute("SELECT COUNT(*) FROM positions WHERE quantity != 0")
    open_pos = c.fetchone()[0]
    print(f"  Open: {open_pos}")
    
    # Get latest balance
    c.execute("SELECT balance FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
    result = c.fetchone()
    current_balance = (result[0] if result else 0) / 100
    
    print("\n" + "=" * 80)
    print(f"CURRENT ACCOUNT STATE: ${current_balance:.2f}")
    print("=" * 80)
    
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
