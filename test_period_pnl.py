import sqlite3

db = sqlite3.connect('C:\\Users\\chead\\.openclaw\\workspace\\dashboard\\data\\northstar.db')
cur = db.cursor()

# Get starting balance
cur.execute('SELECT balance_cents FROM kalshi_snapshots ORDER BY snapshot_ts ASC LIMIT 1')
starting_bal = cur.fetchone()[0]
print(f'Starting balance: ${starting_bal/100:.2f}')

# Get last snapshot of each day to see daily P&L
print('\n=== DAILY P&L (balance at end of day) ===')
cur.execute('''
    SELECT snap_date, 
           MAX(balance_cents) end_of_day_bal,
           LAG(MAX(balance_cents)) OVER (ORDER BY snap_date) prev_day_bal
    FROM kalshi_snapshots
    GROUP BY snap_date
    ORDER BY snap_date ASC
''')
for row in cur.fetchall():
    date, eod_bal, prev_bal = row[0], row[1]/100, (row[2]/100 if row[2] else starting_bal/100)
    daily_pnl = eod_bal - prev_bal
    print(f'  {date}: ${eod_bal:.2f} (Δ ${daily_pnl:+.2f})')

# Test the period queries
print('\n=== PERIOD QUERIES (current code) ===')
PERIOD_SQL = {
    'today': "date(snap_date) = date('now','localtime')",
    'week': "date(snap_date) >= date('now','localtime','-7 days')",
    'month': "strftime('%Y-%m',snap_date) = strftime('%Y-%m','now','localtime')",
    'all': '1=1',
}

for period, cond in PERIOD_SQL.items():
    cur.execute(f"SELECT balance_cents FROM kalshi_snapshots WHERE {cond} ORDER BY snapshot_ts DESC LIMIT 1")
    result = cur.fetchone()
    current_bal = result[0]/100 if result else 0
    pnl = current_bal - starting_bal/100
    print(f'  {period}: current=${current_bal:.2f}, calc_pnl=${pnl:.2f}')

print('\n=== WHAT IT SHOULD BE (period start vs end balance) ===')
# For each period, find the first snapshot and the last snapshot
for period, cond in PERIOD_SQL.items():
    cur.execute(f"SELECT balance_cents FROM kalshi_snapshots WHERE {cond} ORDER BY snapshot_ts ASC LIMIT 1")
    first = cur.fetchone()
    cur.execute(f"SELECT balance_cents FROM kalshi_snapshots WHERE {cond} ORDER BY snapshot_ts DESC LIMIT 1")
    last = cur.fetchone()
    
    start_bal = first[0]/100 if first else 0
    end_bal = last[0]/100 if last else 0
    period_pnl = end_bal - start_bal
    print(f'  {period}: start=${start_bal:.2f}, end=${end_bal:.2f}, pnl=${period_pnl:.2f}')

db.close()
