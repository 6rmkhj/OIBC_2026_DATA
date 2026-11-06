$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA\analysis_outputs\renew_20261105\incbound_wave'
$records = @()
foreach ($path in @(Get-ChildItem -LiteralPath "$root\evidence" -Filter 'prepare_attempt*_start.json')) {
    $identity = Get-Content -LiteralPath $path.FullName -Raw | ConvertFrom-Json
    $observed = Get-CimInstance Win32_Process -Filter ('ProcessId='+$identity.pid)
    $observedTime = $null
    if ($observed) { $observedTime = $observed.CreationDate.ToUniversalTime().ToFileTimeUtc() }
    if ($observedTime -eq $identity.creation_filetime) { throw ('Exact preparation identity still running: '+$identity.pid) }
    $records += @{pid=$identity.pid;creation_filetime=$identity.creation_filetime;exact_absent=$true;observed_creation_filetime=$observedTime}
}
if ($records.Count -ne 1) { throw 'Expected one preparation identity' }
$target = [IO.Path]::GetFullPath((Join-Path $root 'tmp'))
if ($target -cne ($root+'\tmp') -or -not $target.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup containment failure' }
$existed = Test-Path -LiteralPath $target
$reparseCount = 0
if ($existed) {
    $items = @((Get-Item -LiteralPath $root -Force),(Get-Item -LiteralPath $target -Force)) + @(Get-ChildItem -LiteralPath $target -Force -Recurse)
    $reparseCount = @($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
    if ($reparseCount -ne 0) { throw 'Cleanup reparse point found' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
$absent = -not (Test-Path -LiteralPath $target)
if (-not $absent) { throw 'Cleanup target still exists' }
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');records=$records;target=$target;containment_checked=$true;reparse_count=$reparseCount;existed_before=$existed;absent_after=$absent} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$root\evidence\prefit_cleanup.json" -Encoding UTF8
Write-Output 'PREFIT ONE IDENTITY ABSENT; OWNED TMP CLEANUP PASS'
