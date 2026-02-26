#!/usr/bin/env pwsh
# Deploy dashboard + Cloudflare tunnel

$ErrorActionPreference = 'SilentlyContinue'

Write-Host "[*] Starting Northstar Dashboard..." -ForegroundColor Cyan

# Kill existing Python instances on port 8765
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object {
    taskkill /PID $_.OwningProcess /F 2>$null
}

# Start FastAPI server in background
Write-Host "[*] Starting FastAPI on localhost:8765..." -ForegroundColor Gray
Start-Process python -ArgumentList @(
    'C:\Users\chead\.openclaw\workspace\dashboard\app.py'
) -WorkingDirectory 'C:\Users\chead\.openclaw\workspace\dashboard' -NoNewWindow

# Wait for server to start
Start-Sleep -Seconds 3

# Check if port 8765 is listening
$listening = netstat -ano 2>$null | Select-String "8765.*LISTENING"
if ($listening) {
    Write-Host "[OK] Dashboard running on localhost:8765" -ForegroundColor Green
} else {
    Write-Host "[!] Dashboard failed to start" -ForegroundColor Red
    exit 1
}

# Start Cloudflare tunnel
Write-Host "[*] Setting up Cloudflare Tunnel..." -ForegroundColor Gray
if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $tunnel = Start-Process cloudflared -ArgumentList @(
        'tunnel', 'run',
        '--url', 'http://localhost:8765',
        '--name', 'northstar-dashboard'
    ) -PassThru -NoNewWindow
    Write-Host "[OK] Cloudflare tunnel started (PID: $($tunnel.Id))" -ForegroundColor Green
    Write-Host "[INFO] Check CloudFlare dashboard for public URL" -ForegroundColor Yellow
} else {
    Write-Host "[!] cloudflared CLI not installed" -ForegroundColor Yellow
    Write-Host "[INFO] Dashboard available locally at: http://localhost:8765" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dashboard is live!" -ForegroundColor Green
Write-Host "Local:  http://localhost:8765" -ForegroundColor Cyan
Write-Host "Public: (via Cloudflare tunnel)" -ForegroundColor Cyan
