$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\slowg\Downloads\OIBC_2026_DATA'
$target = [IO.Path]::GetFullPath((Join-Path $workspace 'tmp\pdfs\oibc_handoff_20261105'))
$parent = [IO.Path]::GetFullPath((Join-Path $workspace 'tmp\pdfs'))
if (-not $target.StartsWith($parent + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup target outside PDF temporary directory.' }
$manifestPath = Join-Path $workspace 'analysis_outputs\handoff_20261105\handoff_manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$pdfPath = Join-Path $workspace $manifest.pdf
if ((Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.sha256) { throw 'PDF changed after visual review.' }
if ((Resolve-Path -LiteralPath $target).Path -ne $target) { throw 'Resolved cleanup path differs.' }
$entries = @((Get-Item -LiteralPath $target -Force)) + @(Get-ChildItem -LiteralPath $target -Force -Recurse)
foreach ($entry in $entries) {
    if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point found.' }
    $itemPath = [IO.Path]::GetFullPath($entry.FullName)
    if ($itemPath -ne $target -and -not $itemPath.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Child outside target.' }
}
Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) { throw 'PDF temporary directory still exists.' }
$receipt = [pscustomobject]@{
    utc = [DateTime]::UtcNow.ToString('o')
    pdf_sha256 = $manifest.sha256
    pages_reviewed = @(1, 2, 3, 4, 5, 6)
    tool = 'tools.view_image on Poppler 120 DPI page renders'
    visual_result = 'PASS: legible Korean text, tables, code, page numbers; no clipping or overlap'
    temporary_directory = $target
    absent_after = $true
    containment_checked = $true
    reparse_count = 0
    entries_removed = $entries.Count
}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $workspace 'analysis_outputs\handoff_20261105\visual_qa.json') -Encoding UTF8
$receipt | ConvertTo-Json -Depth 4
