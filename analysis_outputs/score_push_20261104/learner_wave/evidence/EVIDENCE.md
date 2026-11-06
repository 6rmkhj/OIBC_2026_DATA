# Group learner-diversity family

The best paired development recipe averages three standard-CF MLP seeds and blends that member with the complete richer-direct/original-bottom-up reference. The new-member weight0.24368782387197704 was chosen only on primary and transferred unchanged to recent.

| Complete recipe | Primary W_pct | Recent W_pct |
| --- | ---: | ---: |
| Richer reference | 12.622155809 | 11.536044344 |
| Normalized group LGBM complement, weight .5241801091278886 | 12.357346864 | 11.378859806 |
| Standard-CF MLP seed0 complement, weight .20541863021636464 | 12.380962049 | 11.478763812 |
| Normalized-CF MLP complement, weight .17664950166758472 | 12.483238556 | 11.428834008 |
| RBF Nystroem/LinearSVR complement, weight .1225716703781049 | 12.542757264 | 11.484402513 |
| Standard-CF MLP seeds0/1/2 complement, weight .24368782387197704 | **12.321940729** | **11.317671544** |

The permitted single followup averaged two additional seeds for standard-CF MLP. Total16 fits:6 normalized LGBM,6 standard-CF MLP,2 normalized-CF MLP,2 kernel. No grid, iteration extension or dependency installation was performed. All four learners' direct blends with old bottom-up were also evaluated; those were weaker than blending into the complete richer reference. Full pure/member/blended results are in `results.json`, `scores.json`, and each recipe's `score.json`/`diagnostics.csv`.

Primary remains train<=2023-06-01/eval through2024-06-01; recent remains train<=2024-06-01/eval through2025-03-01, all Asia/Seoul and right-closed. March-May confirmation and test data remain closed. These are adaptively selected development scores, not leaderboard claims.

## Exact verification scenarios

All artifact paths below are relative to `analysis_outputs/score_push_20261104/learner_wave/`.

| Scenario / invocation | Binary observable | Artifact |
| --- | --- | --- |
| `python submission/score_push/learner_wave.py` | PASS exit0, exactly four screened families plus one permitted seed followup;16 sequential fits | `run.stdout.log`, `protocol.json`, `results.json`, `evidence/owned_exit.json` |
| Same invocation, reference baseline gates | PASS reconstructed reference scores12.622155808512135/11.536044344428209, same17568/13104 evaluation keys | `{primary,recent}/reference.parquet`, `results.json` |
| Same invocation, two blend paths | PASS10 primary-only analytical calibrations, all transferred unchanged to recent; calibration model fits0 | `scores.json`, `{primary,recent}/*/{screen,ensemble}/{old_bottom_up,richer_reference}/predictions.parquet` |
| `python submission/score_push/learner_verify.py` | PASS all16 saved models replay their signed daylight predictions; every model/config/preprocessor/runtime artifact fingerprinted | `evidence/verification.json`, `evidence/verification.stdout.log`, `{primary,recent}/*/seed*/` model artifacts |
| Same verification invocation | PASS fitted imputer/scaler parameters equal train-only refits; target scaler equals training target moments; entirely NaN evaluation rows stay finite | `evidence/verification.json`, `{primary,recent}/*/seed*/input_preprocessing.joblib`, `{primary,recent}/*/seed*/target_scaler.joblib` |
| Same verification invocation | PASS deliberate preprocessing leakage mutant fails; original fixture passes; hand-computed normalized group CF-L1 and CF-MSE equivalence passes including standardized-target constant | `evidence/verification.stdout.log` |
| Same verification invocation | PASS30 scored artifacts have exact evaluation keys, finite nonnegative predictions and recomputed unchanged metric;10 primary alpha pairs independently reapplied | `evidence/verification.json` |
| Same verification invocation | PASS all compact input, output and executed source snapshot hashes rechecked | `manifest.json`, `sources/hashes.json`, `evidence/verification.json` |
| Runtime/convergence receipts | PASS Windows BelowNormal16384, model CPUs<=2,BLAS1,OMP2,PyArrow2,one fit at a time; peak working set757280768bytes;0 warnings | `{primary,recent}/*/seed*/runtime.json`, `{primary,recent}/*/seed*/convergence.json`, `evidence/verification.json` |
| `python .../programming/scripts/python/check-no-excuse-rules.py submission/score_push/learner_models.py submission/score_push/learner_wave.py submission/score_push/learner_verify.py` | PASS no violations in3files | `source_audit.log` |

MLPs stopped in101–198 iterations, below max400. Kernel SVR converged in739/760 iterations, below max10000. No convergence warnings were suppressed or encountered. Both owned synchronous processes exited0 and no owned process remains; stderr logs are empty.

## Pure-member artifacts for subsequent no-refit diversity analysis

For each `fold` in `primary`, `recent`:

- `fold/lgb_normalized/screen/pure/predictions.parquet`: `p_new` is the three-seed normalized group LGBM member.
- `fold/mlp_cf/ensemble/pure/predictions.parquet`: `p_new` is the three-seed standard-CF MLP member.
- Both files contain `p_reference` (complete richer reference), `p_bu_old`, `p_dir_reference`, `y`, `smp`, `k`, `ts`, `grp`.
- Current best complete forecast: `fold/mlp_cf/ensemble/richer_reference/predictions.parquet`, column `p`.
- Other pure members: `fold/mlp_normalized/screen/pure/predictions.parquet` and `fold/kernel_l1/screen/pure/predictions.parquet`.

Align by(ts,grp). These artifacts suffice for residual comparisons or a separately authorized primary-only three-way blend without refitting. No such new blend was performed in this family.

Not performed: confirmation/test access, full-data refit, export, new libraries, GPU, or LSP/typechecker installation. Source responsibilities are bounded learner implementations, paired chronology/blending, and no-fit verification; prior experiment artifacts remain untouched.
