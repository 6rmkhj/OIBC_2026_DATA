$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA'
$out = Join-Path $root 'analysis_outputs\renew_20261106\poisson_wave'
Set-Location -LiteralPath $root
$env:PYTHONDONTWRITEBYTECODE = '1'
foreach ($name in @('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')) { Set-Item -LiteralPath "Env:$name" -Value '16' }
$stdout = Join-Path $out 'prepare_attempt01.log'
$stderr = Join-Path $out 'prepare_attempt01.error.log'
if ((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr)) { throw 'Unique log collision' }
$worker = Start-Process -FilePath 'C:\Users\slowg\AppData\Local\Programs\Python\Python312\python.exe' -ArgumentList @('submission/score_push_renew/poisson_run.py','--prepare') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$nativeHandle = $worker.Handle
$worker.PriorityClass = 'Normal'
$creation = $worker.StartTime.ToUniversalTime().ToFileTimeUtc()
@{pid=$worker.Id; creation_filetime=$creation; native_handle_retained_before_wait=$true; command='python submission/score_push_renew/poisson_run.py --prepare'; stdout=$stdout; stderr=$stderr; utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'evidence\prepare_attempt01_start.json') -Encoding utf8
$worker.WaitForExit()
$code = $worker.ExitCode
if ($null -eq $code) { throw 'Native exit code unavailable despite retained handle' }
$live = @(Get-Process -Id $worker.Id -ErrorAction SilentlyContinue)
$exact = $false
if ($live.Count) { $exact = ($live[0].StartTime.ToUniversalTime().ToFileTimeUtc() -eq $creation) }
if ($exact) { throw 'Exact preparation worker still present' }
@{pid=$worker.Id; creation_filetime=$creation; exit_code=$code; has_exited=$worker.HasExited; exact_worker_absent=$true; native_handle_retained_before_wait=$true; utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'evidence\prepare_attempt01_exit.json') -Encoding utf8
Write-Output "PREPARE_EXIT=$code"
