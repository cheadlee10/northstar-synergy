$content = Get-Content "C:\Users\chead\AppData\Roaming\Granola\cache-v3.json" -Raw
$outer = $content | ConvertFrom-Json
$inner = $outer.cache | ConvertFrom-Json
$state = $inner.state
$docs = $state.documents
$docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

# Build list and sort by updated_at
$meetings = @()
foreach ($id in $docIds) {
    $doc = $docs.$id
    if ($doc.title -and $doc.updated_at) {
        $meetings += [PSCustomObject]@{
            id = $id
            title = $doc.title
            updated_at = $doc.updated_at
            created_at = $doc.created_at
            notes_plain = $doc.notes_plain
            notes_markdown = $doc.notes_markdown
        }
    }
}

$sorted = $meetings | Sort-Object updated_at -Descending | Select-Object -First 8

foreach ($m in $sorted) {
    Write-Host "=============================="
    Write-Host "TITLE: $($m.title)"
    Write-Host "DATE:  $($m.updated_at)"
    Write-Host "------------------------------"
    if ($m.notes_markdown) {
        Write-Host $m.notes_markdown.Substring(0, [Math]::Min(800, $m.notes_markdown.Length))
    } elseif ($m.notes_plain) {
        Write-Host $m.notes_plain.Substring(0, [Math]::Min(800, $m.notes_plain.Length))
    } else {
        Write-Host "(no notes content)"
    }
    Write-Host ""
}
