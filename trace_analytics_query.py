import sqlite3

db = sqlite3.connect('C:\\Users\\chead\.openclaw\\workspace\\dashboard\\data\\northstar.db')
cur = db.cursor()

# Replicate EXACTLY what analytics.py is doing now
PERIOD_SQL = {
    'today': "date(snap_date) = date('now','localtime')",
    'week': "date(snap_date) >= date('now','localtime','-7 days')",
    'month': "strftime('%Y-%m',snap_date) = strftime('%Y-%m','now','localtime')",
}

for period, cond in PERIOD_SQL.items():
    print(f'\n=== {period.upper()} ===')
    print(f'Condition: {cond}')
    
    # First snapshot
    query1 = f"SELECT snapshot_ts, balance_cents FROM kalshi_snapshots WHERE {cond} ORDER BY snapshot_ts ASC LIMIT 1"
    print(f'First snapshot query: {query1}')
    cur.execute(query1)
    first = cur.fetchone()
    if first:
        print(f'  Result: {first[0]} = ${first[1]/100:.2f}')
    else:
        print(f'  Result: NONE')
    start_bal = first[1] if first else 0
    
    # Last snapshot
    query2 = f"SELECT snapshot_ts, balance_cents, total_fills, win_count, loss_count FROM kalshi_snapshots WHERE {cond} ORDER BY snapshot_ts DESC LIMIT 1"
    print(f'Last snapshot query: {query2}')
    cur.execute(query2)
    last = cur.fetchone()
    if last:
        print(f'  Result: {last[0]} = ${last[1]/100:.2f}')
    else:
        print(f'  Result: NONE')
    
    if last:
        end_bal = last[1]
        pnl = (end_bal - start_bal) / 100
        print(f'Calculation: ({end_bal} - {start_bal}) / 100 = {pnl:.2f}')

db.close()
