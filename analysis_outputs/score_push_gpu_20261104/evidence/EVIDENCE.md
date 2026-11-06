# Bounded GPU CatBoost development family

Status: TERMINAL, eight authorized fits completed; all trial controllers and the owning invocation exited 0. Final selection rejected the three-seed GPU ensemble and retained the complete CPU reference. No confirmation, test, full-training or export stage was opened.

Invocation: `analysis_outputs/score_push_gpu_20261104/environment/Scripts/python.exe submission/score_push_gpu/gpu_run.py` from the workspace root. Environment used task-owned TMPDIR, PYTHONDONTWRITEBYTECODE=1, CPU/BLAS thread variables16. Runtime set Windows Normal priority, PyArrow4, GPU device0 with gpu_ram_part0.9, and one fit at a time. The isolated environment remains available for reproduction.

All artifact paths below are relative to `analysis_outputs/score_push_gpu_20261104/`.

| Criterion and exact scenario | Binary observable | Artifact |
|---|---|---|
| Freeze two recipes and bounded selection before fitting | Immutable protocol records four initial fits and at most four follow-ups, exact parameters and source/input SHA256 | `protocol.json`, `sources/`, `sources/own/` |
| Predicate-bound training and evaluation | Primary train<=2023Jun1; recent train<=2024Jun1; evaluation max2024Jun1/2025Mar1; source reads use Parquet predicates | `data/primary/features.json`, `data/recent/features.json`, `data_manifest.json`, `sources/own/gpu_data.py` |
| Exact development keysets and labels | 17568 primary and 13104 recent keys; outer one-to-one oracle merge succeeds; y/SMP/k exactly equal; k=3 at actual timestamp11..15 | `data/*/labels.parquet`, `data/*/features.json` |
| Target-free features and train-only missingness | 100 rich features, 904 station candidates; energy/cf/y/SMP/k excluded; station constant mask fitted only on training; numeric NaN handled natively as Min | `trials/*/*/seed*/config.json` |
| GPU fit resource allocation | Actual CatBoost task_typeGPU, thread_count16, device0; Normal priority32; BLAS16 and PyArrow4; GPU samples show RTX5090 activity | `trials/*/*/seed*/runtime.json`, `gpu_samples.csv`, `full_params.json` |
| Durable independent trials | Before-launch checkpoint; PID plus creation FILETIME; trial-owned CatBoost snapshot and training directory; completed model/raw hashes checked before skipping | `launch_checkpoint.json`, `worker_status.json`, `controller_pid.json`, `training_info/`, `training_snapshot.cbsnapshot` where a fit crossed the snapshot interval |
| Eight complete saved models and exact replay | Each model has2000 trees, finite signed raw output and exact array-equality saved-model replay; all eight replay errors0 | `trials/*/*/seed*/model.cbm`, `daylight_raw.parquet`, `replay.json`, `convergence.json` |
| No silent NaN averaging or early clipping | Every seed raw is finite; NumPy arithmetic mean across the exact daylight keys precedes nonnegative clipping; zero fill only outside those cached daylight keys | `sources/own/gpu_score.py`, `comparisons/*/*/*/predictions.parquet` |
| Primary-only scalar blend transfer | Three scalar calibrations total: two screens and the sole qualifying ensemble; each primary alpha transferred unchanged to recent | `comparisons/*/*/decision.json`, `progress.json`, `results.json` |
| Conditional follow-up gate | Rich CF screen rejected; station-normalized screen qualifies and alone receives seeds1/2 on both folds; final recent regression rejects ensemble | `results.json` |
| Monthly regressions and sample coverage | Right-closed target-day months use ts-1h; per-month and peak scores saved for GPU pure, CPU reference, blend and old incumbent | `comparisons/*/*/*/diagnostics.csv`, `metrics.json` |
| Preserve old scientific artifacts | All189 protected files retain their prefit SHA256; old delivered candidate unchanged | `preservation.json`, `protocol.json` |
| Source check and terminal processes | No violations in five files; all eight subprocess waits completed with exit0 and owning invocation returned exit0 | `evidence/source_check.log`, `trials/*/*/seed*/controller_receipt.json`, `controller_receipt.json` |
| Reproducibility | Every model saves explicit and complete CatBoost parameters, software versions, input hashes, model hash and raw prediction hash | `full_params.json`, `config.json`, `runtime.json`, `artifact_hashes.json` |

Results (W%, lower is better):

| Recipe | Primary alpha | Primary | Recent | Decision |
|---|---:|---:|---:|---|
| Complete CPU reference | - | 12.041603595410752 | 11.064366712650248 | retained |
| Rich CF GPU, seed0 complement | 0.06231365480541814 | 12.037505458243876 | 11.069621016866257 | recent regression; no follow-up |
| Station-normalized GPU, seed0 complement | 0.16074393847436044 | 12.011914909214648 | 11.055528879794092 | qualified for one follow-up |
| Station-normalized GPU, seeds0/1/2 complement | 0.18701860274942764 | 12.010372736377645 | 11.067682421633243 | recent regression; rejected |

The three-seed blend regresses in five of twelve primary months (2023Jun/Aug/Sep,2024Apr/May) and five of nine recent months (2024Aug/Sep/Oct/Nov,2025Feb). Exact monthly values are in the diagnostics files. Both folds preserve all full-hour group keys, including night hours.

Measured peak GPU memory was21065MiB and maximum sampled GPU utilization45%; these are observed values, not a claim of constant/full utilization. Maximum process working set was1129553920bytes. Summed fit/predict/replay time across eight model workers was157.408seconds. Every fit used one GPU worker, CPU16/BLAS16/Normal priority. CatBoost reports that MAE metric calculation is not implemented on GPU and defaults its metric period to5; the fitted learner task type remainedGPU. Training history and logs retain this message.

Versions: Python3.12.10, CatBoost1.2.10, NumPy2.5.4, pandas3.1.0, PyArrow26.0.0. GPU training is nondeterministic; retraining is not claimed bit-exact. Saved-model replay was exact for all eight models.

Code review: five modules independently own shared paths/resource receipts, bounded data preparation, one fit/replay, paired scoring, and family orchestration. Their executable line counts are82,55,63,42,119 respectively. Frozen numerical helpers were reused and hashed. No new dependency was installed by this worker. LSP/type-checker installation was skipped per instruction; source checks and actual execution are recorded.

This is exploratory, adaptively selected historical development evidence, not pristine holdout or an official leaderboard result. Original CPU confirmation regression and the post-hoc fresh-cutoff slight regression remain valid adverse evidence. No additional seeds, combined-variant simplex, hyperparameter grid, confirmation fitting, final export change or upload was performed.
