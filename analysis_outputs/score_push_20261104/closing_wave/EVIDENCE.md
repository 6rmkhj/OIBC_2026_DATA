# Closing no-fit check: adaptive search closed

Final decision: **retain the confirmed complete station-profile forecast**. The single three-member convex candidate improved primary but regressed on recent, failing the predeclared both-fold adoption gate.

| Forecast | Primary W_pct | Recent W_pct |
| --- | ---: | ---: |
| Confirmed station complete,retained | **12.041603595410752** | **11.064366712650248** |
| Closing convex candidate,rejected | 12.025368953638855 | 11.08568733620659 |

Candidate primary-only weights,ordered station/cell-LGB/cell-MLP: `[0.8870668127040238,0.07447445143507794,0.03845873586089831]`. The identical vector was applied to recent. Selected weights are `[1,0,0]`; no alternate weights or models were tried after rejection.

Exactly one sparse HiGHS optimization was performed,with explicitly forwarded threads2. No model training occurred. Solver status0/Optimal,weight sum1,minimum weight0.0384587,max primal residual1.11e-16,scaled dual gap−1.04e-17. Exact prediction loss was recomputed separately from the solver's slack objective; both are preserved in `weights/optimization.json`. The expected SciPy warning says the threads option is forwarded to HiGHS verbatim.

## Scenario / invocation / binary observable / artifact

All paths below are relative to `analysis_outputs/score_push_20261104/closing_wave/`.

| Scenario and invocation | Binary observable | Captured artifact |
| --- | --- | --- |
| `python submission/score_push/closing.py` | PASS exit0,one optimizer call,zero model fits,protocol frozen before candidate evaluation | `protocol.json`, `run.stdout.log`, `owned_exit.json` |
| Frozen parent loading within same invocation | PASS all six prediction files match parent final-manifest hashes;labels and keys identical across members | `input_manifest.json`, `verification.json` |
| Primary-only optimizer within same invocation | PASS fit matrix is exactly primary,17568rows through2024-06-01;nonnegative unit-sum weights;solver success/feasibility | `weights/primary_fit_matrix.parquet`, `weights/optimization.json` |
| Transfer and arithmetic replay within same invocation | PASS candidate weights unchanged on13104recent rows through2025-03-01;all six score artifacts independently recomputed;selected raw Parquets round-trip exactly | `{primary,recent}/{baseline,candidate,selected}/predictions.parquet`, `verification.json` |
| Night/zero preservation within same invocation | PASS all member forecasts are0 outside frozen daylight keys;candidate and selected forecasts preserve those0rows and all evaluation keys | `verification.json` |
| Fixed adoption gate | PASS candidate rejected for recent regression;station forecast retained without another optimization | `results.json`, `selected_recipe.json` |
| Native resources | PASS BelowNormal16384,HiGHS2,BLAS1,OMP2,PyArrow2,peak working set256573440bytes;owned process exited0 | `runtime.json`, `weights/solver_runtime.json`, `owned_exit.json` |
| Source audit on `submission/score_push/closing.py` | PASS no violations | `source_audit.log` |
| `python submission/score_push/closing.py --manifest`,run last | PASS final output and source fingerprint inventory | `final_manifest.json` |

## Selected output and member provenance

Selected complete raw forecasts are `primary/selected/predictions.parquet` and `recent/selected/predictions.parquet`,column `p`. Each also carries `ts`,`grp`,`y`,`smp`,`k`,`station`,`cell_lgb`,`cell_mlp`. Source member paths and source value columns are in `selected_recipe.json` and pinned by `input_manifest.json`.

The retained station source remains `profile_wave/{fold}/stations_lgb/ensemble/complement/predictions.parquet:p`. The rejected cell candidates are `profile_wave/{fold}/cells_lgb/screen/pure/predictions.parquet:p_new` and `profile_wave/{fold}/cells_mlp/screen/pure/predictions.parquet:p_new`.

**Hyperparameter/model/ensemble search ends here. No later tuning from confirmation is permitted.** The UTC closure timestamp is recorded in `selected_recipe.json`. Source/recipe freeze and authorization for confirmation/full refitting belong to the next root instruction. Confirmation,test data,training,full refit and submission were not accessed/performed in this check. Development scores do not establish a new leaderboard result.
