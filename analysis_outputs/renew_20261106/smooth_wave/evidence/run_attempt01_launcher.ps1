$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\slowg\Downloads\OIBC_2026_DATA'
$out = Join-Path $workspace 'analysis_outputs\renew_20261106\smooth_wave'
$stdout = Join-Path $out 'run_attempt01.log'
$stderr = Join-Path $out 'run_attempt01.error.log'
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr)) { throw 'Unique log collision.' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
foreach ($name in @('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')) { Set-Item -LiteralPath "Env:$name" -Value '16' }
$worker = Start-Process -FilePath 'C:\Users\slowg\AppData\Local\Programs\Python\Python312\python.exe' -ArgumentList @('submission/score_push_renew/smooth_run.py') -WorkingDirectory $workspace -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$nativeHandle = $worker.Handle
$worker.PriorityClass = 'Normal'
$creation = $worker.StartTime.ToUniversalTime().ToFileTimeUtc()
@{pid=$worker.Id;creation_filetime=$creation;native_handle_retained_before_wait=$true;command='python submission/score_push_renew/smooth_run.py';utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'evidence\run_attempt01_start.json') -Encoding UTF8
$worker.WaitForExit()
$code = $worker.ExitCode
if ($null -eq $code) { throw 'Native exit code unavailable.' }
$live = @(Get-Process -Id $worker.Id -ErrorAction SilentlyContinue)
if ($live.Count -and $live[0].StartTime.ToUniversalTime().ToFileTimeUtc() -eq $creation) { throw 'Exact worker still present.' }
@{pid=$worker.Id;creation_filetime=$creation;exit_code=$code;has_exited=$worker.HasExited;exact_worker_absent=$true;native_handle_retained_before_wait=$true;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'evidence\run_attempt01_exit.json') -Encoding UTF8
$target = [IO.Path]::GetFullPath((Join-Path $out 'tmp'))
if ($target -ne ($out + '\tmp') -or -not $target.StartsWith($out + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup containment failure.' }
if (Test-Path -LiteralPath $target) {
    if ((Resolve-Path -LiteralPath $target).Path -ne $target) { throw 'Resolved target differs.' }
    $entries = @((Get-Item -LiteralPath $target -Force)) + @(Get-ChildItem -LiteralPath $target -Force -Recurse)
    foreach ($entry in $entries) {
        if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point found.' }
        $entryPath = [IO.Path]::GetFullPath($entry.FullName)
        if ($entryPath -ne $target -and -not $entryPath.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Child outside owned target.' }
    }
    Remove-Item -LiteralPath $target -Recurse -Force
}
if (Test-Path -LiteralPath $target) { throw 'Temporary directory still exists.' }
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');target=$target;absent_after=$true;reparse_count=0;containment_checked=$true;exact_worker_absent=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'evidence\terminal_cleanup.json') -Encoding UTF8
if ($code -ne 0) {
    Get-Content -LiteralPath $stderr -Tail 35
    throw "Smoothing process failed with exit $code."
}
$manifest = [ordered]@{}
foreach ($file in Get-ChildItem -LiteralPath $out -File -Recurse | Sort-Object FullName) {
    if ($file.Name -in @('controller.lock','terminal_manifest.json','independent_check.json')) { continue }
    $relative = $file.FullName.Substring($out.Length + 1).Replace('\','/')
    $manifest[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'terminal_manifest.json') -Encoding UTF8
Write-Output "SMOOTH_EXIT=$code"
Get-FileHash -LiteralPath (Join-Path $out 'terminal_manifest.json') -Algorithm SHA256 | Select-Object Hash
