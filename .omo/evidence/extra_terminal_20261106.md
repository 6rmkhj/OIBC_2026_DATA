# ExtraTrees terminal result

The sole preregistered candidate is rejected: primary-only alpha 0.02560833478817268 exceeds 0.02, but recent W worsens. No retuning or export occurred. Actual official-best remains untouched.

Primary W_pct 11.958095512329045 versus reference 11.959229078372204. Recent W_pct 11.006260068163833 versus reference 11.000952828788678.

Artifact base: analysis_outputs/renew_20261105/extra_wave/.

| Scenario | Invocation | Binary observable | Artifact |
|---|---|---|---|
| Released wave | python submission/score_push_renew/extra_run.py --run, through evidence/run_attempt01_launcher.ps1 | retained native handle exit0, EXTRA WAVE TERMINAL, six serial fits | run_attempt01.log; evidence/run_attempt01_start.json; evidence/run_attempt01_exit.json |
| Exact replay | same released command, extra_fit.py each primary/recent seed0/1/2 | all six bitwise_exact true, max_absolute_error0; 600 trees each | trials/{fold}/seed{seed}/replay.json; model.joblib; daylight_raw.parquet |
| Fixed decision | same released command | eligible false; reference_retained true; one primary alpha; no confirmation/test/export | results.json; comparisons/{fold}/metrics.json; predictions.parquet |
| Runtime, hashes, serial lifecycle | & analysis_outputs/renew_20261105/extra_wave/evidence/terminal_audit.ps1 | PASS; six nonoverlapping intervals; CPU/BLAS16, Arrow4, Normal32; all3628 protected hashes and six source hashes unchanged | evidence/terminal_audit.json; evidence/terminal_audit.log; preservation.json |
| Owned terminal cleanup | & analysis_outputs/renew_20261105/extra_wave/evidence/cleanup.ps1 | seven exact identities absent; tmp containment checked, reparse0, absent_after true | evidence/native_terminal_identities.json; evidence/terminal_cleanup.json; evidence/terminal_cleanup.log |

Controller PID44084 creation134383675258914110. No failed fits or reruns. Six real model fits, six native saved-model replays, zero real calibration fits. No frozen scientific source changes, dependencies or LSP installs. The additional scripts own launch, terminal auditing and cleanup only; their assertions passed on the actual completed wave.

All historical data was exposed; development improvement does not establish an official score. Root independent full verification remains separate and pending this handoff. Model files, logs, rejected results and immutable previous artifacts are preserved.
