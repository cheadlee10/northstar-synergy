$json = Get-Content 'C:\Users\chead\.openclaw\openclaw.json' -Raw | ConvertFrom-Json
$json.agents.list[1].model = 'anthropic/claude-sonnet-4.6'
$out = $json | ConvertTo-Json -Depth 20
Set-Content -Path 'C:\Users\chead\.openclaw\openclaw.json' -Value $out -Encoding UTF8
Write-Output ("Scalper model now: " + $json.agents.list[1].model)
