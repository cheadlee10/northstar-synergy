---
name: dashboard-doctor
description: Diagnose and fix NorthStar Synergy dashboard issues. Use when dashboard is down (502, timeout, connection refused), data is stale (>30 min old), or Cloudflare tunnel is not responding. Includes health checks, auto-restart, and data sync recovery.
---

# Dashboard Doctor — Auto-Diagnosis & Recovery

Fixes dashboard connectivity, data sync, and tunnel issues without manual intervention.

## Quick Diagnosis (Run This First)

```bash
# Check if Flask app is running on 8765
Invoke-WebRequest -Uri "http://localhost:8765" -ErrorAction SilentlyContinue

# Check Cloudflare tunnel status
Get-Process cloudflared -ErrorAction SilentlyContinue

# Check if database is locked
Get-Item C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db

# Check last sync time
Get-Content C:\Users\chead\.openclaw\workspace\dashboard\last_sync.txt
```

## Common Issues & Fixes

### Issue 1: Flask App Down (Connection Refused)
**Symptom:** `Unable to connect to the remote server` on localhost:8765
**Fix:**
```bash
# 1. Kill any existing Python process on 8765
Get-Process python | Stop-Process -Force

# 2. Restart dashboard app
cd C:\Users\chead\.openclaw\workspace\dashboard
python app.py &
```

### Issue 2: Cloudflare Tunnel Down (502 Bad Gateway)
**Symptom:** 502 error on https://chronic-slope-condo-justify.trycloudflare.com/
**Fix:**
```bash
# 1. Check if cloudflared process is running
Get-Process cloudflared

# 2. If not running, restart:
Get-Process cloudflared | Stop-Process -Force
Start-Process "C:\Users\chead\AppData\Local\Programs\cloudflared\cloudflared.exe" -ArgumentList "tunnel run" -WindowStyle Hidden

# 3. Verify tunnel reconnected
Start-Sleep -Seconds 3
Invoke-WebRequest -Uri "https://chronic-slope-condo-justify.trycloudflare.com/api/summary" -ErrorAction SilentlyContinue
```

### Issue 3: Database Locked (auto_populate.py blocked)
**Symptom:** Dashboard data is stale (>30 min old)
**Fix:**
```bash
# 1. Check if sync process is stuck
Get-Process python | Where-Object {$_.ProcessName -like "*auto_populate*"}

# 2. Kill stuck process
Get-Process python | Stop-Process -Force

# 3. Run manual sync
python C:\Users\chead\.openclaw\workspace\dashboard\auto_populate.py

# 4. Verify data updated
Get-Item C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db | Select-Object -ExpandProperty LastWriteTime
```

### Issue 4: Data Out of Sync (Scalper DB ≠ Dashboard DB)
**Symptom:** P&L on dashboard doesn't match V8 database
**Fix:**
```bash
# Run full sync from all sources
python C:\Users\chead\.openclaw\workspace\dashboard\sync_from_scalper_db.py
python C:\Users\chead\.openclaw\workspace\dashboard\sync_kalshi_live.py
python C:\Users\chead\.openclaw\workspace\dashboard\auto_populate.py
```

## Automated Health Check Script

Run this daily (via Task Scheduler) to catch issues before they're critical:

```python
import subprocess
import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def health_check():
    """Check dashboard health and auto-fix common issues"""
    
    issues = []
    
    # 1. Check Flask app
    try:
        r = requests.get("http://localhost:8765", timeout=5)
        if r.status_code != 200:
            issues.append(f"Flask returned {r.status_code}")
    except:
        issues.append("Flask app unreachable (down or crashed)")
        # Auto-fix: restart
        subprocess.run(["pkill", "-f", "app.py"], capture_output=True)
        subprocess.Popen(["python", "C:/Users/chead/.openclaw/workspace/dashboard/app.py"])
    
    # 2. Check Cloudflare tunnel
    try:
        r = requests.get("https://chronic-slope-condo-justify.trycloudflare.com/api/summary", timeout=5)
        if r.status_code != 200:
            issues.append(f"Tunnel returned {r.status_code}")
    except:
        issues.append("Cloudflare tunnel down")
        # Auto-fix: restart tunnel
        subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
        subprocess.Popen(["cloudflared", "tunnel", "run"])
    
    # 3. Check database sync recency
    db_path = Path("C:/Users/chead/.openclaw/workspace/dashboard/data/northstar.db")
    if db_path.exists():
        age = (datetime.now() - datetime.fromtimestamp(db_path.stat().st_mtime)).total_seconds()
        if age > 1800:  # >30 min old
            issues.append(f"Database stale ({age/60:.0f} min old)")
            # Auto-fix: run sync
            subprocess.run(["python", "C:/Users/chead/.openclaw/workspace/dashboard/auto_populate.py"])
    
    # 4. Check Scalper DB sync
    try:
        scalper_db = sqlite3.connect("C:/Users/chead/.openclaw/workspace-scalper/scalper_v8.db")
        dashboard_db = sqlite3.connect("C:/Users/chead/.openclaw/workspace/dashboard/data/northstar.db")
        
        scalper_c = scalper_db.cursor()
        dashboard_c = dashboard_db.cursor()
        
        scalper_c.execute("SELECT MAX(timestamp) FROM pnl_snapshots")
        scalper_ts = scalper_c.fetchone()[0]
        
        dashboard_c.execute("SELECT MAX(snapshot_ts) FROM kalshi_snapshots")
        dashboard_ts = dashboard_c.fetchone()[0]
        
        if scalper_ts != dashboard_ts:
            issues.append(f"Kalshi data out of sync ({scalper_ts} vs {dashboard_ts})")
            # Auto-fix: sync
            subprocess.run(["python", "C:/Users/chead/.openclaw/workspace/dashboard/sync_from_scalper_db.py"])
    except Exception as e:
        issues.append(f"Sync check failed: {e}")
    
    # Report
    if issues:
        print(f"[Dashboard Doctor] Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"[Dashboard Doctor] ✓ All systems healthy")
        return True

if __name__ == "__main__":
    health_check()
```

## Integration with Monitoring

### Task Scheduler (Windows)
```powershell
$action = New-ScheduledTaskAction `
  -Execute "C:\Users\chead\AppData\Local\Programs\Python\Python312\python.exe" `
  -Argument "C:\Users\chead\.openclaw\workspace\skills\dashboard-doctor\health_check.py"

$trigger = New-ScheduledTaskTrigger -At 06:00:00 -RepeatInterval (New-TimeSpan -Hours 12)

Register-ScheduledTask `
  -TaskName "DashboardDoctor" `
  -Action $action `
  -Trigger $trigger
```

### OpenClaw Cron
```json
{
  "name": "DashboardDoctor",
  "schedule": {
    "kind": "cron",
    "expr": "0 */6 * * *",
    "tz": "America/Los_Angeles"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "Run dashboard health check: python C:\\Users\\chead\\.openclaw\\workspace\\skills\\dashboard-doctor\\health_check.py"
  },
  "sessionTarget": "main"
}
```

## When to Manually Intervene

- **Dashboard offline >30 min**: Restart manually (auto-restart may have failed)
- **Sync errors persist**: Check for SQL corruption (run PRAGMA integrity_check)
- **Tunnel repeatedly fails**: Check internet connection and Cloudflare account status
- **P&L discrepancies >5%**: Investigate data source (Scalper trades vs actual fills)

## Dashboard Doctor Commands

```bash
# Full health check
python C:\Users\chead\.openclaw\workspace\skills\dashboard-doctor\health_check.py

# Restart Flask only
pkill -f app.py && python C:\Users\chead\.openclaw\workspace\dashboard\app.py

# Restart Cloudflare tunnel only
pkill -f cloudflared && cloudflared tunnel run

# Full data resync
python C:\Users\chead\.openclaw\workspace\dashboard\auto_populate.py

# Check last sync status
Get-Item C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db | Select-Object LastWriteTime
```

## Cost
Zero — all diagnostics are local operations, no API calls.
