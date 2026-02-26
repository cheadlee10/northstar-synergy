#!/usr/bin/env python3
import sqlite3

print('[SOURCE CHECK: scalper_v8.db]')
try:
    src = sqlite3.connect(r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db')
    src.row_factory = sqlite3.Row
    
    # Get latest
    latest = src.execute('SELECT timestamp, balance_cents, total_pnl_cents, daily_pnl_cents, weather_pnl_cents FROM pnl_snapshots ORDER BY timestamp DESC LIMIT 1').fetchone()
    if latest:
        d = dict(latest)
        print(f"  Latest: {d['timestamp']}")
        print(f"    balance: ${d['balance_cents']/100:.2f}")
        print(f"    total_pnl: ${d['total_pnl_cents']/100:.2f}")
        print(f"    daily_pnl: ${d['daily_pnl_cents']/100:.2f}")
        print(f"    weather_pnl: ${d['weather_pnl_cents']/100:.2f}")
    else:
        print("  No snapshots found!")
    
    # Check count
    count = src.execute('SELECT COUNT(*) FROM pnl_snapshots').fetchone()[0]
    print(f"\n  Total snapshots: {count}")
    
    # Check for non-zero P&L
    nonzero = src.execute('SELECT COUNT(*) FROM pnl_snapshots WHERE total_pnl_cents != 0').fetchone()[0]
    print(f"  Non-zero P&L records: {nonzero}")
    
    src.close()
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
