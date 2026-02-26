$ErrorActionPreference = 'Stop'

# Ensure Python environment vars are set
$env:ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY  # inherited if set
$or_key = [System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','User')
if ($or_key) { $env:OPENROUTER_API_KEY = $or_key }

Write-Host "[*] Auto-populating NorthStar dashboard..." -ForegroundColor Cyan
Write-Host "    Sources: OpenRouter, Anthropic, Kalshi, Sports, John" -ForegroundColor Gray

python C:\Users\chead\.openclaw\workspace\dashboard\auto_populate.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dashboard populated successfully" -ForegroundColor Green
    Write-Host "     View at: http://localhost:8765 or via Cloudflare tunnel URL" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Auto-populate returned error code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
