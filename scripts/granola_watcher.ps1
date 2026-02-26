# granola_watcher.ps1
# Run by Windows Task Scheduler every 10 minutes
# Detects new Granola meeting notes and POSTs to OpenClaw gateway (zero token cost until notes found)

$GATEWAY_URL = "http://127.0.0.1:18789/hooks/wake"
$HOOK_TOKEN   = "granola-hook-cliff-2026"
$CACHE_FILE   = "C:\Users\chead\AppData\Roaming\Granola\cache-v3.json"
$LAST_SEEN_FILE = "C:\Users\chead\.openclaw\workspace\granola_last_seen.txt"

# Load last-seen timestamp (default: 15 min ago if first run)
$lastSeen = if (Test-Path $LAST_SEEN_FILE) {
    [datetime]::Parse((Get-Content $LAST_SEEN_FILE -Raw).Trim())
} else {
    (Get-Date).AddMinutes(-15)
}

try {
    $content = Get-Content $CACHE_FILE -Raw -ErrorAction Stop
    $outer = $content | ConvertFrom-Json
    $inner = $outer.cache | ConvertFrom-Json
    $docs   = $inner.state.documents
    $docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

    $newNotes = @()
    foreach ($id in $docIds) {
        $doc = $docs.$id
        if (-not $doc.updated_at) { continue }
        $updatedAt = [datetime]::Parse($doc.updated_at).ToLocalTime()
        $noteText  = if ($doc.notes_markdown) { $doc.notes_markdown } else { $doc.notes_plain }
        if ($updatedAt -gt $lastSeen -and $noteText -and $noteText.Trim().Length -gt 10) {
            $newNotes += "Meeting: $($doc.title)`nDate: $($doc.updated_at)`n`n$noteText"
        }
    }

    if ($newNotes.Count -gt 0) {
        $combined = $newNotes -join "`n`n---`n`n"
        $payload  = @{
            text = "GRANOLA_NEW_NOTES: New meeting notes detected. Read notes, extract all action items, execute what you can immediately (Excel, email, analysis), and WhatsApp Craig a summary of what was found and what you're doing.`n`n$combined"
            mode = "now"
        } | ConvertTo-Json -Depth 2

        $headers = @{
            "Authorization" = "Bearer $HOOK_TOKEN"
            "Content-Type"  = "application/json"
        }

        Invoke-RestMethod -Uri $GATEWAY_URL -Method POST -Headers $headers -Body $payload -ErrorAction Stop
        Write-Host "Fired wake event for $($newNotes.Count) new note(s)"
    } else {
        Write-Host "No new notes since $lastSeen"
    }

    # Update last-seen to now
    (Get-Date).ToString("o") | Set-Content $LAST_SEEN_FILE

} catch {
    Write-Error "Granola watcher error: $_"
}
