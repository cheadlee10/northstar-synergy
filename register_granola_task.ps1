$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\chead\.openclaw\workspace\granola_monitor.ps1"'

$trigger = New-ScheduledTaskTrigger `
    -RepetitionInterval (New-TimeSpan -Minutes 10) `
    -Once `
    -At (Get-Date)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName 'GranolaMonitor' `
    -TaskPath '\OpenClaw\' `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Checks Granola meeting notes every 10 min and alerts Cliff via webhook' `
    -RunLevel Limited `
    -Force

Write-Host 'GranolaMonitor task registered successfully.'
