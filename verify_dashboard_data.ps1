#!/usr/bin/env pwsh
# Verify dashboard database has all data

$db = "C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

if (-not (Test-Path $db)) {
    Write-Host "[!] Database not found: $db" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Checking $db..."

# Use Python to query
$py = @"
import sqlite3
db = sqlite3.connect(r'$db')

# Count tables
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"[*] Tables ({len(tables)}):")
for t in tables:
    count = db.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"    {t[0]}: {count} rows")

# Key counts
print("\n[CRITICAL] Data Check:")
k = db.execute("SELECT COUNT(*) FROM kalshi_snapshots").fetchone()[0]
a = db.execute("SELECT COUNT(*) FROM api_usage WHERE provider IN ('OpenRouter','Anthropic')").fetchone()[0]
r = db.execute("SELECT COUNT(*) FROM revenue").fetchone()[0]
e = db.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
j = db.execute("SELECT COUNT(*) FROM john_jobs").fetchone()[0]
b = db.execute("SELECT COUNT(*) FROM bets").fetchone()[0]

print(f"  Kalshi Snapshots: {k}")
print(f"  API Usage (OR+ANT): {a}")
print(f"  Revenue: {r}")
print(f"  Expenses: {e}")
print(f"  John Jobs: {j}")
print(f"  Bets: {b}")

if k > 0:
    latest = db.execute("SELECT snapshot_ts, balance_cents, total_pnl_cents FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 1").fetchone()
    print(f"\n  Latest Kalshi: {latest}")

db.close()
"@

python -c $py
