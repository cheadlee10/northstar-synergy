#!/usr/bin/env python3
"""
sync_from_scalper_db.py — Copy real Kalshi data from Scalper's DB to Dashboard
"""
import sqlite3
from datetime import datetime

SCALPER_DB = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'
DASHBOARD_DB = r'C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db'

def sync():
    scalper = sqlite3.connect(SCALPER_DB)
    scalper.row_factory = sqlite3.Row
    sc = scalper.cursor()
    
    dashboard = sqlite3.connect(DASHBOARD_DB)
    dc = dashboard.cursor()
    
    print("[Sync] Reading Scalper Kalshi snapshots...")
    
    # Get all snapshots from Scalper
    sc.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp")
    snapshots = [dict(row) for row in sc.fetchall()]
    
    print(f"[Sync] Found {len(snapshots)} Scalper snapshots")
    
    # Copy to dashboard
    inserted = 0
    for snap in snapshots:
        try:
            dc.execute("""
                INSERT OR REPLACE INTO kalshi_snapshots (
                    snapshot_ts, snap_date, balance_cents, daily_pnl_cents, total_pnl_cents,
                    open_positions, total_orders, total_fills, win_count, loss_count,
                    total_fees_cents, weather_pnl_cents, crypto_pnl_cents, econ_pnl_cents,
                    mm_pnl_cents, lip_rewards_cents
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snap['timestamp'],
                snap['timestamp'][:10],  # snap_date
                snap['balance_cents'],
                snap['daily_pnl_cents'],
                snap['total_pnl_cents'],
                snap['open_positions'],
                snap['total_orders'],
                snap['total_fills'],
                snap['win_count'],
                snap['loss_count'],
                snap['total_fees_cents'],
                snap['weather_pnl_cents'],
                snap['crypto_pnl_cents'],
                snap['econ_pnl_cents'],
                snap['mm_pnl_cents'],
                snap['lip_rewards_cents']
            ))
            inserted += 1
        except Exception as e:
            print(f"[Sync] Error inserting {snap['timestamp']}: {e}")
    
    dashboard.commit()
    
    print(f"[Sync] Inserted {inserted} snapshots into dashboard")
    
    # Get latest for summary
    sc.execute("SELECT * FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1")
    latest = dict(sc.fetchone() or {})
    
    print("\n" + "=" * 80)
    print("DASHBOARD NOW SHOWS:")
    print("=" * 80)
    print(f"Balance: ${(latest.get('balance_cents') or 0)/100:.2f}")
    print(f"Total P&L: ${(latest.get('total_pnl_cents') or 0)/100:.2f}")
    print(f"Daily P&L: ${(latest.get('daily_pnl_cents') or 0)/100:.2f}")
    print(f"Open Orders: {latest.get('total_orders')}")
    print(f"Wins: {latest.get('win_count')} | Losses: {latest.get('loss_count')}")
    
    scalper.close()
    dashboard.close()
    
    return {
        "status": "ok",
        "synced": inserted,
        "balance_usd": (latest.get('balance_cents') or 0) / 100,
        "pnl_usd": (latest.get('total_pnl_cents') or 0) / 100
    }

if __name__ == "__main__":
    result = sync()
    import json
    print("\nResult:", json.dumps(result, indent=2))
