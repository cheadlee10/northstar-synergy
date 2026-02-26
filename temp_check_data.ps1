$env:PYTHONIOENCODING='utf-8'

# Check dashboard server
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:8765/api/summary" -TimeoutSec 5
    Write-Host "DASHBOARD: RUNNING"
    Write-Host $resp.Content.Substring(0, [Math]::Min(500, $resp.Content.Length))
} catch {
    Write-Host "DASHBOARD: DOWN - $($_.Exception.Message)"
}

# Check Scalper data sources
$scalperDir = "C:\Users\chead\.openclaw\workspace-scalper"

Write-Host "`n=== SCALPER DATA SOURCES ==="

if (Test-Path "$scalperDir\scalper_v8.db") {
    $f = Get-Item "$scalperDir\scalper_v8.db"
    Write-Host "scalper_v8.db: $($f.Length) bytes, modified $($f.LastWriteTime)"
} else { Write-Host "scalper_v8.db: NOT FOUND" }

if (Test-Path "$scalperDir\trade_log.jsonl") {
    $count = (Get-Content "$scalperDir\trade_log.jsonl" | Measure-Object).Count
    Write-Host "trade_log.jsonl: $count lines"
} else { Write-Host "trade_log.jsonl: NOT FOUND" }

if (Test-Path "$scalperDir\business_ledger.jsonl") {
    $count = (Get-Content "$scalperDir\business_ledger.jsonl" | Measure-Object).Count
    Write-Host "business_ledger.jsonl: $count lines"
    Get-Content "$scalperDir\business_ledger.jsonl" -TotalCount 5
} else { Write-Host "business_ledger.jsonl: NOT FOUND" }

if (Test-Path "$scalperDir\trade_log.csv") {
    $count = (Get-Content "$scalperDir\trade_log.csv" | Measure-Object).Count
    Write-Host "trade_log.csv: $count lines"
} else { Write-Host "trade_log.csv: NOT FOUND" }

if (Test-Path "$scalperDir\portfolio_snapshot.json") {
    Write-Host "portfolio_snapshot.json:"
    Get-Content "$scalperDir\portfolio_snapshot.json" -TotalCount 3
} else { Write-Host "portfolio_snapshot.json: NOT FOUND" }

# Check northstar.db tables
Write-Host "`n=== NORTHSTAR DB TABLES ==="
$dbPath = "C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"
if (Test-Path $dbPath) {
    Write-Host "northstar.db exists: $((Get-Item $dbPath).Length) bytes"
} else {
    Write-Host "northstar.db: NOT FOUND"
}

# Check if auto_populate task is registered
Write-Host "`n=== TASK SCHEDULER ==="
try {
    $tasks = Get-ScheduledTask -TaskPath "\OpenClaw\" -ErrorAction SilentlyContinue
    foreach ($t in $tasks) {
        Write-Host "$($t.TaskName): $($t.State)"
    }
} catch {
    Write-Host "No OpenClaw tasks found"
}
