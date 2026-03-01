import sqlite3
conn = sqlite3.connect('data/northstar.db')
cursor = conn.cursor()

# Calculate P&L for all settled trades that don't have it
cursor.execute("""
    SELECT rowid, entry_price, exit_price, num_contracts, fees
    FROM kalshi_trades 
    WHERE status='Settled' 
    AND pnl_realized IS NULL
    AND entry_price IS NOT NULL 
    AND exit_price IS NOT NULL
""")

rows = cursor.fetchall()
print(f'Calculating P&L for {len(rows)} trades...')

total_pnl = 0
for rowid, entry, exit_p, qty, fees in rows:
    pnl = (exit_p - entry) * qty - (fees or 0)
    cursor.execute("UPDATE kalshi_trades SET pnl_realized = ? WHERE rowid = ?", (pnl, rowid))
    total_pnl += pnl

conn.commit()

# Verify
cursor.execute("SELECT SUM(pnl_realized) FROM kalshi_trades WHERE status='Settled'")
new_total = cursor.fetchone()[0] or 0
print(f'Total calculated P&L: ${new_total:,.2f}')

conn.close()
