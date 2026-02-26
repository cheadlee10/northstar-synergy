$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\chead\.openclaw\workspace\dashboard\start_dashboard.ps1"'

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName 'NorthstarDashboard' `
    -TaskPath '\OpenClaw\' `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Starts Northstar Synergy P&L dashboard + Cloudflare tunnel on login' `
    -RunLevel Limited `
    -Force

Write-Host 'NorthstarDashboard task registered.'
