# Paired recent/direct and site-family execution

Primary: train ts <= 2023-06-01, evaluation 2023-06-01 < ts <= 2024-06-01. Recent: train ts <= 2024-06-01, evaluation 2024-06-01 < ts <= 2025-03-01. All timestamps Asia/Seoul, right-closed. March-May 2025 confirmation and test data remain closed. Data projections filter at Parquet read time; evaluation site frames contain no energy/cf/y columns.

## Measured results

| Recipe | Primary W_pct | Recent W_pct |
| --- | ---: | ---: |
| Current incumbent | 12.695950144 | 11.639886825 |
| Richer direct + original bottom-up, primary-only alpha .7642694482340047 | 12.622155809 | 11.536044344 |
| Site identity L1 + richer direct, primary-only alpha .9290728092455098 | 12.700542882 | 11.533470916 |
| Site identity L2 + richer direct, primary-only alpha .9443141067550673 | 12.704080564 | 11.533991858 |
| Haurwitz-normalized site L1 + richer direct, primary-only alpha .9343589013822885 | 12.698487075 | 11.517144862 |

Richer direct improves both development folds. Its recent score at unchanged incumbent alpha is 11.556766833. January-February 2025 improves from 9.828125003 to 9.686786374 with the primary-selected alpha.

All three new site models regress on primary, even after their own primary-only blend optimization; none qualifies for extra seeds. Six single-seed site fits completed, with explicit seed0. The best paired site screen, normalized L1, trades a primary regression against recent improvement and does not outperform the richer-direct/original-bottom-up recipe on the equal-fold relative-loss ranking. No new leaderboard score is claimed.

Full pure-site and fixed-alpha results are in `../screen_scores.json`; all six site/direct primary-calibration pairs are in `../all_primary_calibrations.json`. The old-direct pairs isolate site changes, while richer-direct pairs evaluate combined recipes. Every pair has raw prediction Parquet, score and monthly diagnostics.

## Exact scenarios, invocations, binary observables and artifacts

Paths in this table are relative to `analysis_outputs/score_push_20261104/` unless explicitly source paths.

| Scenario / invocation | Binary observable | Artifact |
| --- | --- | --- |
| `python submission/score_push/recent.py` | PASS exit0, recent direct predictions exactly equal filtered frozen incumbent; all-hour forecasts exactly equal old candidate; W_pct matches independent oracle within1e-10 | `recent/run.stdout.log`, `recent/manifest.json`, `recent/incumbent/predictions.parquet` |
| Same recent invocation | PASS three-seed richer-direct fit and both predeclared fixed alphas, without recent alpha fitting | `recent/results.json`, `recent/rich_fixed_alpha/`, `recent/rich_primary_alpha/` |
| `python submission/score_push/site_wave.py` | PASS exit0, three variants on two folds, six sequential seed0 fits, finite full observed-site predictions with exact night zeros | `site_wave/run.stdout.log`, `site_wave/protocol.json`, `site_wave/*/*/seed0/` |
| `python submission/score_push/site_calibrate.py` | PASS exit0, all six site/direct primary-only coefficients transferred unchanged to recent; no additional seed qualified | `site_wave/calibration.stdout.log`, `site_wave/all_primary_calibrations.json`, `site_wave/calibration_summary.json` |
| `python submission/score_push/verify_site_wave.py` | PASS exact site/group keys, finite predictions, cutoff boundaries, target-free selected features, all scores recomputed with frozen metric | `site_wave/evidence/verification.json`, `site_wave/evidence/verification.stdout.log` |
| Same verification invocation | PASS fixed metadata category mapping and real unseen-history rows:325491 primary,268861 recent per variant; all predictions finite | `site_wave/evidence/verification.json`, `site_wave/*/*/seed0/site_predictions.parquet` |
| Same verification invocation | PASS hand-calculated Haurwitz values and weighted-normalized-L1 equivalence; wrong Haurwitz coefficient mutant fails, original restored and passes | `site_wave/evidence/verification.stdout.log` |
| Same verification invocation | PASS input/output/source snapshot SHA256 pins and unchanged first-family inputs | `recent/manifest.json`, `site_wave/manifest.json`, `site_wave/evidence/verification.json`, source snapshot hash files |
| Model resource receipts and saved booster parameters | PASS Windows BelowNormal16384, modelthreads2,OMP2,BLAS1,PyArrow2, one fit at a time; all12 saved group/site model files declare num_threads2 | `recent/*/runtime.json`, `site_wave/*/*/seed0/runtime.json`, `site_wave/evidence/model_thread_parameters.log` |
| `python .../programming/scripts/python/check-no-excuse-rules.py submission/score_push/{wave_common,recent,site_features,site_wave,site_calibrate,verify_site_wave}.py` (six explicit arguments in actual invocation) | PASS no violations in six files | `site_wave/source_audit.log` |

Observed peak working set: recent direct/weather process4,231,487,488 bytes; site process2,110,742,528 bytes. Site fit times ranged20.453–192.297 seconds. Each main process ended with exit0; stderr logs are empty. No detached fit processes were launched in this wave.

Reusable caches: `recent/cache/` holds compact richer group features through the authorized recent boundary; `site_wave/cache/{primary,recent}/` holds projected site training/evaluation frames and fixed direct/label tables. Reusable code separates site features, chronological model execution, primary-only calibration and no-fit verification. First-family caches, executed sources, journals and trials were not modified.

Not performed: extra seeds because no variant met the paired gate, March-May confirmation, new dependencies, LSP/typechecker installation, neural models, full-data refit or submission export. Both development folds informed recipe comparison; historical outer exposure remains disclosed in the root protocol.
