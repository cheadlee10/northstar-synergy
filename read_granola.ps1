$content = Get-Content "C:\Users\chead\AppData\Roaming\Granola\cache-v3.json" -Raw
$outer = $content | ConvertFrom-Json
$inner = $outer.cache | ConvertFrom-Json
$state = $inner.state

# Get all documents
$docs = $state.documents
$docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

Write-Host "=== MEETINGS ($($docIds.Count) total) ==="
foreach ($id in $docIds) {
    $doc = $docs.$id
    Write-Host "`n--- $($doc.title) ---"
    Write-Host "ID: $id"
    Write-Host "Created: $($doc.created_at)"
    Write-Host "Updated: $($doc.updated_at)"
    
    # Try to get note content
    if ($doc.notes) {
        Write-Host "Notes: $($doc.notes | ConvertTo-Json -Depth 3 -Compress | Select-Object -First 1)"
    }
    if ($doc.notes_plain) {
        Write-Host "Notes (plain): $($doc.notes_plain.Substring(0, [Math]::Min(500, $doc.notes_plain.Length)))"
    }
    # Show all properties
    $doc | Get-Member -MemberType NoteProperty | ForEach-Object { 
        $val = $doc.$($_.Name)
        if ($val -and $val -ne "" -and $_.Name -notmatch "^(id|user_id)$") {
            $str = "$val"
            Write-Host "  [$($_.Name)]: $($str.Substring(0, [Math]::Min(200, $str.Length)))"
        }
    }
}
