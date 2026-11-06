# Final mechanistic GPU refinement wave

Status: TERMINAL. All 24 predefined fits completed, all 24 saved-model replays were exact, and all per-fit controllers plus `--finish` exited 0. None of the four variants passed the two-fold gate. The complete CPU reference remains selected; no confirmation, test, full-training or export stage was opened.

Use `analysis_outputs/score_push_gpu_20261104/environment/Scripts/python.exe submission/score_push_gpu_refine/gpu_run.py` with these sequential commands: `--prepare`; `--trial VARIANT FOLD SEED` for every predefined variant, both folds and seeds0/1/2; one `--compare VARIANT` after that variant's six trials; finally `--finish`. Each fit had a separate owning invocation. The new owned temp was `C:/Users/slowg/AppData/Local/Temp/oibc-gpu-refine-20261105.ZuTklfLr`; TMPDIR/TMP/TEMP and auxiliary caches pointed there, with PYTHONDONTWRITEBYTECODE=1. Worker leaves temp cleanup to the parent.

All paths below are relative to `analysis_outputs/score_push_gpu_refine_20261105/`.

| Criterion and exact scenario | Binary observable | Artifact |
|---|---|---|
| Freeze all hypotheses before model outcomes | Four variants, both folds and seeds0/1/2 declared; 24-fit budget; no seed0 screening or additional parameters | `protocol.json`, `sources/own/`, `sources/` |
| Correct zero-price input boundary before fitting | Original strict-positive check fails during preparation with zero model fits; root-approved revision keeps all six recent zero-SMP rows at exact zero weight | `evidence/prepare_attempt.log`, `prefit_amendment.json`, `sources/prefit_amendment/`, `evidence/prepare_revision1.log` |
| Same immutable GPU data and exact oracle coverage | 17568 primary and 13104 recent keys; y/SMP/k exactly equal original bounded oracles; k matches actual-hour11..15 | `data/*/oracle_check.json`, `data/*/labels.parquet`, `data_manifest.json` |
| Strict training cutoffs | Primary train<=2023Jun1; recent train<=2024Jun1; predicate-bounded feature, capacity and price reads; future generation labels never opened | `data/*/features.json`, `data/*/money.json`, `trials/*/*/seed*/config.json` |
| Exact monetary objective | Exact one-to-one group capacity join and many-to-one timestamp SMP join; positive training-only mean cost; finite nonnegative weights, positive aggregate mass; zero rows retained | `data/*/training_money.parquet`, `data/*/money.json`, `prefit_amendment.json` |
| Train-only masks and no price leakage | All models use station904 candidate columns with a training-only constant mask; energy/cf/y/SMP/k excluded from input names; prices and k used only for monetary weights | `trials/*/*/seed*/config.json` |
| Mean-before-clip and monetary algebra | Assert fixture distinguishes clipping individual seeds from clipping their mean; monetary weighted normalized error equals official kWh error up to the declared constant, including zero SMP | `evidence/arithmetic_self_check.json`, `sources/prefit_amendment/gpu_score.py` |
| Exactly 24 complete fitted models | Depth4/2000, depth8/2000, depth6/6000, monetary depth6/2000, each six fits; tree counts equal declared values; finite signed raw predictions | `trials/*/*/seed*/model.cbm`, `daylight_raw.parquet`, `convergence.json`, `full_params.json` |
| Exact saved-model replay | Every persisted model reloaded and array-equality predictions matched with maximum error0; negative raw counts preserved | `trials/*/*/seed*/replay.json` |
| Primary-only complement calibration | Exactly one scalar per three-seed variant, fitted primary only and transferred unchanged to recent; no cross-variant mixtures or seed choice | `comparisons/*/ensemble/decision.json`, `comparisons/*/ensemble/*/predictions.parquet` |
| Monthly and peak diagnostics | Target-day months use ts-1h; pure GPU, old incumbent, CPU reference and complete blend scored per month and peak | `comparisons/*/ensemble/*/diagnostics.csv`, `metrics.json` |
| Maximum authorized practical allocation | GPU0/VRAM90%, CatBoost GPU task type and thread_count16; CPU/BLAS16, Normal32, PyArrow4, one model fit at a time | `trials/*/*/seed*/runtime.json`, `full_params.json`, `gpu_samples.csv` |
| Durable execution and no duplicate live workers | Exact PID and process-creation identity tracked; saved model/raw hashes gate completed-fit reuse; real 30-second snapshots written during longer fits | `launch_checkpoint.json`, `controller_pid.json`, `worker_status.json`, `training_snapshot.cbsnapshot` where applicable |
| Authoritative terminal state | All 24 subprocess waits exit0; each owning fit invocation and final finish return0; exact original worker identities absent or terminated/reused | `trials/*/*/seed*/controller_receipt.json`, `controller_receipt.json`, `state.json`, `evidence/process_terminal.json` |
| Old scientific files unchanged | All412 protected input/source/model/candidate hashes equal prefit values; original failed preflight and original source snapshot retained | `preservation.json`, `protocol.json`, `prefit_amendment.json` |
| Source checks and reproducibility | Five Python files pass the no-excuse checker; explicit/full parameters, versions, source hashes, data hashes and output hashes retained | `evidence/source_check.log`, `artifact_hashes.json`, `sources/`, `trials/*/*/seed*/runtime.json` |

Final three-seed results (W%, lower is better):

| Variant | Primary-only alpha | Primary | Recent | Eligible |
|---|---:|---:|---:|---|
| CPU complete reference | - | 12.041603595410752 | 11.064366712650248 | retained |
| Shallow depth4/2000 | 0.22607612216898235 | 11.99090707657682 | 11.117182772170922 | no |
| Deep depth8/2000 | 0.23467002943549806 | 12.002405094220713 | 11.090418556028958 | no |
| Longer depth6/6000 | 0.15311289859638408 | 12.018119722490056 | 11.069843574910422 | no |
| Monetary depth6/2000 | 0.11679236895407659 | 12.015154638037908 | 11.163519399342077 | no |

Every variant improves the primary fold but regresses the recent fold. The declared both-fold requirement therefore rejects all four; no choice was made from the best individual seed or pure primary score.

Observed resources: summed fit/predict/replay time706.756seconds; maximum process working set1145143296bytes; maximum sampled GPU memory21065MiB and utilization60%. These are measured peaks, not a claim of constant/full utilization. All trials used one fit at a time. CatBoost retained its documented MAE metric-period message in fit logs; the fitted task type remainedGPU. GPU training is nondeterministic, so only saved-model replay is claimed exact.

Zero-price correction: recent training contains30728 group rows. SMP is zero for2024-02-10 12:00,2024-02-11 13:00 and2024-02-12 13:00 KST, producing six zero-weight group rows. They were retained. The recent training mean(capacity*SMP*k) is1186601.2270844749, strictly positive. No price flooring, row deletion or formula change occurred.

Code review: five modules own common resource/snapshot support, bounded monetary data preparation, one fit/replay, paired scoring and single-trial orchestration. Executable line counts are91,45,69,58,134 respectively. Existing numerical and controller patterns were reused; prior modules and the isolated environment were not modified. No new dependency or LSP installation was performed. Actual runs plus arithmetic/key/cutoff/replay assertions provide verification; static type checking remains unavailable by instruction.

This is adaptive, historically exposed development evidence, not pristine holdout or an official leaderboard result. Earlier CPU confirmation/cutoff regressions and the initial GPU rejection remain unchanged. No further family, confirmation evaluation, final export modification, upload or cleanup of shared temp was performed by this worker.
