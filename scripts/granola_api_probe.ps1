# Probe Granola API for file upload capabilities
$token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InNzb19vaWRjX2tleV9wYWlyXzAxSlpKMFhCQktKUUZLV0tLMlRCMDM2UFNEIn0.eyJ3b3Jrb3NfaWQiOiJ1c2VyXzAxSzdGSzhQSjdDNURDMk5HNk5TQ0U2RjNGIiwiZXh0ZXJuYWxfaWQiOiJiMGEyOGVhYS00ZTE4LTRlZGYtYjU0MC1kZGEwYzk2YzdlNjciLCJpc3MiOiJodHRwczovL2F1dGguZ3Jhbm9sYS5haS91c2VyX21hbmFnZW1lbnQvY2xpZW50XzAxSlpKMFhCREFUOFBISldRWTA5WTBWRDYxIiwic3ViIjoidXNlcl8wMUs3Rks4UEo3QzVEQzJORzZOU0NFNkYzRiIsInNpZCI6InNlc3Npb25fMDFLSFZNWVc3WTVBNEsyVjlTMEhKV0M3QkIiLCJqdGkiOiIwMUtKNVJLTk01OUFHNzRLSzlSNjRTR0hGRCIsImV4cCI6MTc3MTg4OTE5MiwiaWF0IjoxNzcxODY3NTkyfQ.Mwui3ogIQEBBDZt2O_d2Da8tq3ej-2V2xcxQi3YXDzY-bWx7dnBctrAp31UiSGwu3guIzaDSMGvVjFEmF0j5rg3OAAQL3gGtHAuOUpRzENz1Msu0Enx-CJhGCnXfRssPqJmChanF15PfUsf9b41X-XDOmWz_1oSLZRVzMp1EC2Brhl606j-2nGGec06Up-kIzW9P77wTEG-iWVT4p-k2edLPAKxKuckO-karWarz_KH8ynpHHpy-tPHTAcASIadPsNphDAB-fnvaLzpGltXGWYw8mWqIeMZ1CZxCeUW_gUfvng79kHnKYq4vD4-2RcJ53rdSCsrJGClYMLyLQ0eqxFA"
$headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }

$endpoints = @(
    "https://api.granola.ai/v1/documents",
    "https://api.granola.ai/v1/upload",
    "https://api.granola.ai/v1/files",
    "https://api.granola.ai/v2/documents",
    "https://api.granola.ai/v2/upload",
    "https://app.granola.ai/api/upload",
    "https://api.granola.ai/v1"
)

foreach ($url in $endpoints) {
    try {
        $r = Invoke-WebRequest -Uri $url -Headers $headers -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "GET $url -> $($r.StatusCode): $($r.Content.Substring(0,[Math]::Min(200,$r.Content.Length)))"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        Write-Host "GET $url -> $code"
    }
}
