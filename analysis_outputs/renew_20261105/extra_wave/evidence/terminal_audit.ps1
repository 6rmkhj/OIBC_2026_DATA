$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA'
$out = Join-Path $root 'analysis_outputs/renew_20261105/extra_wave'
$records = @()
foreach ($fold in @('primary','recent')) {
    foreach ($seed in @(0,1,2)) {
        $dir = Join-Path $out "trials/$fold/seed$seed"
        $status = Get-Content "$dir/worker_status.json" -Raw | ConvertFrom-Json
        $runtime = Get-Content "$dir/runtime.json" -Raw | ConvertFrom-Json
        $replay = Get-Content "$dir/replay.json" -Raw | ConvertFrom-Json
        $receipt = Get-Content "$dir/controller_receipt.json" -Raw | ConvertFrom-Json
        $config = Get-Content "$dir/config.json" -Raw | ConvertFrom-Json
        if ($status.state -ne 'complete' -or $status.new_model_fits -ne 1 -or $runtime.new_model_fits -ne 1) { throw 'Fit incomplete' }
        if ($receipt.exit_code -ne 0 -or -not $receipt.exact_worker_absent) { throw 'Worker exit failure' }
        if (-not $replay.passed -or -not $replay.bitwise_exact -or $replay.max_absolute_error -ne 0 -or $replay.saved_n_jobs -ne 1) { throw 'Replay failure' }
        if ($config.fit_parameters.n_jobs -ne 16 -or $config.inference_parameters.n_jobs -ne 1 -or $config.fit_parameters.n_estimators -ne 600) { throw 'Fit config failure' }
        if ($runtime.priority_class -ne 32 -or $runtime.pyarrow_cpu -ne 4 -or $runtime.pyarrow_io -ne 4) { throw 'Resource failure' }
        if (@($runtime.threadpools | Where-Object { $_.num_threads -ne 16 }).Count) { throw 'Threadpool failure' }
        if ((Get-FileHash "$dir/model.joblib").Hash.ToLowerInvariant() -ne $replay.model_sha256 -or (Get-FileHash "$dir/daylight_raw.parquet").Hash.ToLowerInvariant() -ne $replay.raw_sha256) { throw 'Model/raw hash mismatch' }
        $records += @{fold=$fold;seed=$seed;pid=$receipt.identity.pid;creation_filetime=$receipt.identity.creation_filetime;started_utc=$receipt.started_utc;finished_utc=$receipt.finished_utc;fit_seconds=$runtime.fit_seconds;peak_bytes=$runtime.peak_working_set_bytes;warnings=$runtime.warnings;exact_replay=$true}
    }
}
$intervals = @($records | Sort-Object started_utc)
for ($i=1; $i -lt $intervals.Count; $i++) { if ([DateTime]$intervals[$i-1].finished_utc -gt [DateTime]$intervals[$i].started_utc) { throw 'Overlapping worker intervals' } }
$controller = Get-Content "$out/evidence/run_attempt01_exit.json" -Raw | ConvertFrom-Json
if ($controller.exit_code -ne 0 -or -not $controller.has_exited -or -not $controller.native_handle_retained_before_wait) { throw 'Controller exit failure' }
if ((Get-Item "$out/run_attempt01.error.log").Length -ne 0) { throw 'Controller stderr not empty' }
$protocol = Get-Content "$out/protocol.json" -Raw | ConvertFrom-Json
foreach ($item in $protocol.protected_sha256.PSObject.Properties) { if ((Get-FileHash -LiteralPath (Join-Path $root $item.Name)).Hash.ToLowerInvariant() -ne $item.Value) { throw "Protected mismatch: $($item.Name)" } }
foreach ($item in $protocol.own_sources.PSObject.Properties) { if ((Get-FileHash -LiteralPath (Join-Path $root $item.Value.original)).Hash.ToLowerInvariant() -ne $item.Value.sha256) { throw 'Frozen source changed' } }
$results = Get-Content "$out/results.json" -Raw | ConvertFrom-Json
if ($results.real_model_fit_count -ne 6 -or $results.real_calibration_fit_count -ne 0 -or $results.confirmation_loaded -or $results.test_loaded -or $results.exported) { throw 'Scope failure' }
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');real_model_fits=6;native_replays=6;serial_intervals=6;records=$records;protected_files=@($protocol.protected_sha256.PSObject.Properties).Count;frozen_sources_unchanged=$true;stderr_bytes=0;eligible=$results.eligible} | ConvertTo-Json -Depth 8 | Set-Content "$out/evidence/terminal_audit.json" -Encoding utf8
Write-Output 'TERMINAL AUDIT PASS: six serial fits, six exact replays, resources and protected hashes'
