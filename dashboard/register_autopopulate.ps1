$action = New-ScheduledTaskAction `
    -Execute 'python' `
    -Argument '"C:\Users\chead\.openclaw\workspace\dashboard\auto_populate.py"' `
    -WorkingDirectory 'C:\Users\chead\.openclaw\workspace\dashboard'

$trigger = New-ScheduledTaskTrigger `
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -Once `
    -At (Get-Date)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 3) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName 'NorthstarAutoPopulate' `
    -TaskPath '\OpenClaw\' `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Auto-populates Northstar P&L dashboard: OpenRouter API, Anthropic session logs, Kalshi DB, sports picks, John jobs — every 15 min' `
    -RunLevel Limited `
    -Force

Write-Host 'NorthstarAutoPopulate task registered — runs every 15 minutes.'
