$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\slowg\Downloads\OIBC_2026_DATA'
$temporaryRoot = 'C:\Users\slowg\AppData\Local\Temp'
$ownedPaths = @(
    'C:\Users\slowg\AppData\Local\Temp\oibc-renew-20261105.jM6rHVPE',
    'C:\Users\slowg\AppData\Local\Temp\ulw-20261105-renew.IzKQ4A1v.md'
)
$running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^python(w)?\.exe$' -and
    $_.CommandLine -match 'score_push_renew[\\/](extra_|incbound_|mono_|bound_|mlp_)'
})
if ($running.Count -ne 0) { throw 'Research process still active; no cleanup performed.' }
$receipts = @()
foreach ($ownedPath in $ownedPaths) {
    $absolute = [IO.Path]::GetFullPath($ownedPath)
    if (-not $absolute.StartsWith($temporaryRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Target outside the exact owned temporary namespace.'
    }
    $existed = Test-Path -LiteralPath $absolute
    $count = 0
    if ($existed) {
        $resolved = (Resolve-Path -LiteralPath $absolute).Path
        if ($resolved -ne $absolute) { throw 'Resolved target differs from expected path.' }
        $entry = Get-Item -LiteralPath $absolute -Force
        $entries = @($entry)
        if ($entry.PSIsContainer) { $entries += @(Get-ChildItem -LiteralPath $absolute -Force -Recurse) }
        foreach ($item in $entries) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point found.' }
            $itemPath = [IO.Path]::GetFullPath($item.FullName)
            if ($itemPath -ne $absolute -and -not $itemPath.StartsWith($absolute + '\', [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Child outside owned target.'
            }
        }
        $count = $entries.Count
        Remove-Item -LiteralPath $absolute -Recurse -Force
    }
    if (Test-Path -LiteralPath $absolute) { throw 'Owned temporary path still exists.' }
    $receipts += [pscustomobject]@{path=$absolute; existed_before=$existed; entries=$count; absent_after=$true; reparse_count=0; containment_checked=$true}
}
[pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o'); research_process_count=$running.Count; goal_status='paused_by_user'; targets=$receipts} |
    ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $workspace 'analysis_outputs\handoff_20261105\resource_cleanup.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $workspace 'analysis_outputs\handoff_20261105\resource_cleanup.json') -Raw
