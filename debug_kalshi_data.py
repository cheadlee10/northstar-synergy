import sqlite3

db = sqlite3.connect('C:\\Users\\chead\\.openclaw\\workspace\\dashboard\\data\\northstar.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print('=== KALSHI SNAPSHOTS TABLE ===')
cur.execute('SELECT COUNT(*) FROM kalshi_snapshots')
count = cur.fetchone()[0]
print(f'Total snapshots: {count}')

print('\n=== FIRST 5 SNAPSHOTS ===')
cur.execute('SELECT snapshot_ts, balance_cents, total_pnl_cents, total_fills, win_count, loss_count FROM kalshi_snapshots ORDER BY snapshot_ts ASC LIMIT 5')
for row in cur.fetchall():
    print(f'  {row[0]}: bal=${row[1]/100:.2f}, pnl=${row[2]/100:.2f}, fills={row[3]}, w={row[4]}, l={row[5]}')

print('\n=== LAST 5 SNAPSHOTS ===')
cur.execute('SELECT snapshot_ts, balance_cents, total_pnl_cents, total_fills, win_count, loss_count FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 5')
for row in cur.fetchall():
    print(f'  {row[0]}: bal=${row[1]/100:.2f}, pnl=${row[2]/100:.2f}, fills={row[3]}, w={row[4]}, l={row[5]}')

print('\n=== BALANCE RANGE BY DAY (first 10 days) ===')
cur.execute('''
    SELECT snap_date, 
           MIN(balance_cents) min_bal, 
           MAX(balance_cents) max_bal,
           COUNT(*) snapshots_per_day
    FROM kalshi_snapshots 
    GROUP BY snap_date 
    ORDER BY snap_date ASC 
    LIMIT 10
''')
for row in cur.fetchall():
    print(f'  {row[0]}: min=${row[1]/100:.2f}, max=${row[2]/100:.2f} ({row[3]} snapshots)')

print('\n=== STARTING AND ENDING BALANCE ===')
cur.execute('SELECT snapshot_ts, balance_cents FROM kalshi_snapshots ORDER BY snapshot_ts ASC LIMIT 1')
first = cur.fetchone()
start_bal = first[1] / 100 if first else 0
print(f'Starting: {first[0]} = ${start_bal:.2f}')

cur.execute('SELECT snapshot_ts, balance_cents FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 1')
last = cur.fetchone()
end_bal = last[1] / 100 if last else 0
print(f'Ending:   {last[0]} = ${end_bal:.2f}')
print(f'ACTUAL P&L: ${end_bal - start_bal:.2f}')

db.close()
