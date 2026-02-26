# granola_monitor.ps1
# Checks Granola cache for new/updated meeting notes and POSTs to OpenClaw gateway.
# Designed for Windows Task Scheduler — runs every 10 minutes, zero token cost between fires.

$GATEWAY_URL   = "http://127.0.0.1:18789/hooks/wake"
$HOOK_TOKEN    = "granola-hook-cliff-2026"
$GRANOLA_CACHE = "$env:APPDATA\Granola\cache-v3.json"
$STATE_FILE    = "C:\Users\chead\.openclaw\workspace\granola_last_seen.json"

# --- Load last-seen state ---
if (Test-Path $STATE_FILE) {
    $state = Get-Content $STATE_FILE -Raw | ConvertFrom-Json
    $lastSeenStr = $state.last_seen
    $lastSeen = [datetime]::Parse($lastSeenStr, $null, [System.Globalization.DateTimeStyles]::RoundtripKind)
} else {
    # First run — look back 30 minutes so we catch anything recent
    $lastSeen = (Get-Date).ToUniversalTime().AddMinutes(-30)
    $lastSeenStr = $lastSeen.ToString("o")
}

# --- Parse Granola cache ---
try {
    $raw = Get-Content $GRANOLA_CACHE -Raw -Encoding UTF8
    $outer = $raw | ConvertFrom-Json
    $inner = $outer.cache | ConvertFrom-Json
    $docs = $inner.state.documents
} catch {
    Write-Host "[granola_monitor] ERROR reading Granola cache: $_"
    exit 1
}

# --- Find documents updated since last check ---
$docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
$newDocs = @()

foreach ($id in $docIds) {
    $doc = $docs.$id
    if (-not $doc.updated_at) { continue }

    try {
        $updatedAt = [datetime]::Parse($doc.updated_at, $null, [System.Globalization.DateTimeStyles]::RoundtripKind)
    } catch {
        continue
    }

    if ($updatedAt -gt $lastSeen) {
        $title = if ($doc.title) { $doc.title } else { "(Untitled)" }
        $notes = ""
        if ($doc.notes_markdown) {
            # Truncate to first 500 chars to keep alert concise
            $notes = $doc.notes_markdown.Substring(0, [Math]::Min(500, $doc.notes_markdown.Length))
        } elseif ($doc.notes_plain) {
            $notes = $doc.notes_plain.Substring(0, [Math]::Min(500, $doc.notes_plain.Length))
        }
        $newDocs += [PSCustomObject]@{
            Title     = $title
            UpdatedAt = $updatedAt
            Notes     = $notes
        }
    }
}

# --- If new docs found, fire alert ---
if ($newDocs.Count -gt 0) {
    # Sort newest first
    $newDocs = $newDocs | Sort-Object UpdatedAt -Descending

    $lines = @("[Granola] $($newDocs.Count) new/updated meeting note(s):")
    foreach ($d in $newDocs) {
        $ts = $d.UpdatedAt.ToLocalTime().ToString("h:mm tt")
        $lines += "- [$ts] $($d.Title)"
        if ($d.Notes -ne "") {
            # First meaningful line of notes as preview
            $preview = ($d.Notes -split "`n" | Where-Object { $_.Trim() -ne "" } | Select-Object -First 2) -join " / "
            if ($preview.Length -gt 200) { $preview = $preview.Substring(0, 200) + "..." }
            $lines += "  > $preview"
        }
    }

    $alertText = $lines -join "`n"

    $body = @{
        text = $alertText
        mode = "now"
    } | ConvertTo-Json -Compress

    try {
        $response = Invoke-RestMethod `
            -Uri $GATEWAY_URL `
            -Method POST `
            -Headers @{ "Authorization" = "Bearer $HOOK_TOKEN"; "Content-Type" = "application/json" } `
            -Body $body
        Write-Host "[granola_monitor] Alert sent for $($newDocs.Count) doc(s)."
    } catch {
        Write-Host "[granola_monitor] ERROR posting to gateway: $_"
        exit 1
    }
} else {
    Write-Host "[granola_monitor] No new Granola notes since $lastSeenStr"
}

# --- Update last-seen timestamp ---
$nowUtc = (Get-Date).ToUniversalTime().ToString("o")
@{ last_seen = $nowUtc } | ConvertTo-Json | Set-Content $STATE_FILE -Encoding UTF8
