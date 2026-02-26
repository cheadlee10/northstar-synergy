# granola_check.ps1
# Reads Granola cache, finds notes updated in last 20 minutes, outputs them
# Called by OpenClaw cron — if output is non-empty, a system event fires

$cutoff = (Get-Date).ToUniversalTime().AddMinutes(-20)
$cachePath = "C:\Users\chead\AppData\Roaming\Granola\cache-v3.json"

try {
    $content = Get-Content $cachePath -Raw -ErrorAction Stop
    $outer = $content | ConvertFrom-Json
    $inner = $outer.cache | ConvertFrom-Json
    $state = $inner.state
    $docs = $state.documents
    $docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

    $newNotes = @()
    foreach ($id in $docIds) {
        $doc = $docs.$id
        if (-not $doc.updated_at) { continue }
        $updatedAt = [datetime]::Parse($doc.updated_at).ToUniversalTime()
        if ($updatedAt -gt $cutoff -and ($doc.notes_markdown -or $doc.notes_plain)) {
            $noteText = if ($doc.notes_markdown) { $doc.notes_markdown } else { $doc.notes_plain }
            if ($noteText.Trim().Length -gt 10) {
                $newNotes += "=== $($doc.title) ($($doc.updated_at)) ===`n$noteText"
            }
        }
    }

    if ($newNotes.Count -gt 0) {
        Write-Output "NEW_GRANOLA_NOTES"
        Write-Output ($newNotes -join "`n`n")
    }
    # If nothing new, no output = cron stays silent
} catch {
    Write-Error "Granola read error: $_"
}
