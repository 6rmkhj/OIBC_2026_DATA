# Poisson terminal result

The sole fixed candidate is rejected: primary-only optimal alpha0, both_folds_improve false, eligible false. Reference predictions are retained exactly. No tuning, confirmation/test, full refit or export followed.

Mixed/reference W_pct: primary11.959229078372204, recent11.000952828788678. Pure Poisson weather-corrected component W_pct: primary13.0268753068244, recent13.334322872162243.

Paths below are relative to analysis_outputs/renew_20261106/poisson_wave/.

| Scenario | Invocation | Binary observable | Artifact |
|---|---|---|---|
| Released fixed wave | python submission/score_push_renew/poisson_run.py --run through evidence/run_attempt01_launcher.ps1 | native retained handle exit0; six serial model fits; POISSON WAVE TERMINAL | run_attempt01.log; evidence/run_attempt01_start.json; evidence/run_attempt01_exit.json |
| Native model replay | same command launches poisson_fit.py FOLD SEED for primary/recent, seeds0/1/2 | all six bitwise exact replays; maxerror0;400trees; actual seeds None/1/2 | trials/{fold}/seed{seed}/{config,convergence,replay,runtime,controller_receipt}.json; model.txt; daylight_raw.parquet |
| Fixed comparison | same released command | alpha0, eligible false, reference_retained true | results.json; comparisons/{fold}/metrics.json; predictions.parquet |
| Scope, resources, hashes and intervals | & analysis_outputs/renew_20261106/poisson_wave/evidence/terminal_audit.ps1 | PASS; six nonoverlapping intervals; Normal32/all native pools16/Arrow4;3813protected hashes and six frozen sources unchanged | evidence/terminal_audit.json; evidence/terminal_audit.log; preservation.json |
| Owned lifecycle and cleanup | & analysis_outputs/renew_20261106/poisson_wave/evidence/cleanup.ps1 | all seven exact identities absent; tmp containment/reparse0; tmp absent | evidence/native_terminal_identities.json; evidence/terminal_cleanup.json; evidence/terminal_cleanup.log |

Controller PID40860 creation134383692781306377; native exit0, stderr0bytes. Six actual fits, six saved-model native replays, zero calibration fits. No failed fits or retries. Native model predictions already apply the exponential link; inverse capacity applied once. No scientific source edits after freeze. Owned audit and cleanup scripts reuse the established lifecycle and passed against the completed wave.

All historical data is exposed; this is a development comparison, not an official score. Root independent full verification remains separate and pending handoff. Existing actual official-best and all prior waves/candidates remain unchanged. No next experiment is authorized by this assignment.
