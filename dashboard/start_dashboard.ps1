# start_dashboard.ps1 — starts FastAPI server + Cloudflare tunnel, posts public URL to Cliff

$DASHBOARD_DIR = "C:\Users\chead\.openclaw\workspace\dashboard"
$LOG = "$DASHBOARD_DIR\tunnel.log"
$HOOK_URL = "http://127.0.0.1:18789/hooks/wake"
$HOOK_TOKEN = "granola-hook-cliff-2026"

# Kill any existing instances
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -ErrorAction SilentlyContinue
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -ErrorAction SilentlyContinue
Start-Sleep 2

# Start FastAPI
Start-Process python -ArgumentList "$DASHBOARD_DIR\app.py" -WorkingDirectory $DASHBOARD_DIR -WindowStyle Hidden

# Wait for server
Start-Sleep 4

# Start cloudflared tunnel
if (Test-Path $LOG) { Remove-Item $LOG }
Start-Process "$DASHBOARD_DIR\cloudflared.exe" `
    -ArgumentList "tunnel --url http://localhost:8765" `
    -RedirectStandardError $LOG `
    -WindowStyle Hidden

# Wait for URL to appear
$url = $null
$tries = 0
while (-not $url -and $tries -lt 20) {
    Start-Sleep 2
    $tries++
    if (Test-Path $LOG) {
        $line = Get-Content $LOG | Select-String "trycloudflare.com"
        if ($line) {
            $url = ($line.Line -split "https://")[1].Split(" ")[0].Trim()
            $url = "https://$url"
        }
    }
}

if ($url) {
    # Alert Cliff via OpenClaw webhook
    $body = @{ text = "[Dashboard] Northstar Synergy dashboard is live at: $url"; mode = "now" } | ConvertTo-Json -Compress
    try {
        Invoke-RestMethod -Uri $HOOK_URL -Method POST `
            -Headers @{ "Authorization" = "Bearer $HOOK_TOKEN"; "Content-Type" = "application/json" } `
            -Body $body
    } catch {}
    Write-Host "Dashboard live: $url"
} else {
    Write-Host "Tunnel started but could not capture URL. Check $LOG"
}
