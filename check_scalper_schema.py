#!/usr/bin/env python3
import sqlite3

db = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db'

conn = sqlite3.connect(db)
c = conn.cursor()

tables = ['pnl_snapshots', 'fills', 'orders', 'positions', 'daily_summary']

for table in tables:
    print(f"\n[{table}]")
    c.execute(f"PRAGMA table_info({table})")
    cols = c.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    
    # Show one row
    c.execute(f"SELECT * FROM {table} LIMIT 1")
    row = c.fetchone()
    if row:
        print(f"  Sample: {row}")
    else:
        print(f"  (empty)")

conn.close()
