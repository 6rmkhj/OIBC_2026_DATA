$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA\analysis_outputs\renew_20261105\bounds_wave'
$target = [IO.Path]::GetFullPath((Join-Path $root 'tmp'))
$expected = $root + '\tmp'
if ($target -cne $expected -or -not $target.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup containment failure' }
$existed = Test-Path -LiteralPath $target
$reparseCount = 0
if ($existed) {
    $items = @((Get-Item -LiteralPath $target -Force)) + @(Get-ChildItem -LiteralPath $target -Force -Recurse)
    $reparseCount = @($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
    if ($reparseCount -ne 0) { throw 'Cleanup reparse point found' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
$absent = -not (Test-Path -LiteralPath $target)
if (-not $absent) { throw 'Cleanup target still exists' }
& "$root\evidence\check_native.ps1"
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');target=$target;containment_checked=$true;reparse_count=$reparseCount;existed_before=$existed;absent_after=$absent;native_identity_recheck='native_terminal_identities.json';preserved_all_other_paths=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$root\evidence\terminal_cleanup.json" -Encoding UTF8
Write-Output 'OWNED TMP CLEANUP PASS'
