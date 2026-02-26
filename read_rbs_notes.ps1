$content = Get-Content 'C:\Users\chead\AppData\Roaming\Granola\cache-v3.json' -Raw
$outer = $content | ConvertFrom-Json
$inner = $outer.cache | ConvertFrom-Json
$state = $inner.state
$docs = $state.documents
$docIds = $docs | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

foreach ($id in $docIds) {
    $doc = $docs.$id
    if ($doc.title -like '*RBS*' -or $doc.title -like '*rbs*') {
        Write-Host "=== $($doc.title) ==="
        Write-Host "Updated: $($doc.updated_at)"
        if ($doc.notes_markdown) { Write-Host $doc.notes_markdown }
        elseif ($doc.notes_plain) { Write-Host $doc.notes_plain }
        else { Write-Host "(no notes)" }
        Write-Host ""
    }
}
