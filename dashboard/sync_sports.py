import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('data/northstar.db')
cursor = conn.cursor()

# Clear sports picks
cursor.execute("DELETE FROM sports_picks")
print("Cleared sports_picks")

# Parse real picks from log
picks_log = Path('C:/Users/chead/.openclaw/workspace-scalper/pick_performance_log.jsonl')

if not picks_log.exists():
    print(f"Picks log not found: {picks_log}")
    conn.close()
    exit(1)

total_pnl = 0
added = 0

with open(picks_log) as f:
    for line_num, line in enumerate(f, 1):
        try:
            pick = json.loads(line.strip())
            
            result = pick.get('result', 'PENDING')
            ml = pick.get('ml', 0)
            
            # Calculate P&L
            if result == 'WIN':
                if ml > 0:
                    profit = (ml / 100) * 100
                else:
                    profit = (100 / abs(ml)) * 100
            elif result == 'LOSS':
                profit = -100
            else:
                profit = None
            
            cursor.execute("""
                INSERT INTO sports_picks 
                (pick_date, sport, game, pick, ml, open_ml, edge_val, model_prob,
                 confidence, result, stake, profit_loss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 100, ?)
            """, (
                pick.get('date'),
                pick.get('sport'),
                pick.get('game'),
                pick.get('pick'),
                ml,
                pick.get('open_ml'),
                pick.get('edge_val'),
                pick.get('model_prob'),
                pick.get('confidence', 'MEDIUM'),
                result,
                profit
            ))
            
            added += 1
            if profit is not None:
                total_pnl += profit
                
        except Exception as e:
            print(f"Error on line {line_num}: {e}")
            continue

conn.commit()

# Verify
cursor.execute("SELECT result, COUNT(*), SUM(profit_loss) FROM sports_picks WHERE result IN ('WIN', 'LOSS') GROUP BY result")
results = cursor.fetchall()

print(f"\nAdded {added} picks")
print(f"Total settled P&L: ${total_pnl:,.2f}")
print("\nBreakdown:")
for r in results:
    print(f"  {r[0]}: {r[1]} picks | ${r[2]:,.2f}")

conn.close()
