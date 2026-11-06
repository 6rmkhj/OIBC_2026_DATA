# Fixed-recipe deployment-cutoff diagnostic

Status: completed through recovery controller exit 0. Original controller was interrupted; its exit code is unknown and is never represented as success.

Original invocation: `python submission/score_push/deployment_run.py` with PYTHONDONTWRITEBYTECODE=1, task-owned TMPDIR, one fit, LightGBM 2 threads, BLAS 1, PyArrow 2 and BelowNormal priority. Recovery invocation: `python submission/score_push/deployment_resume.py` with the same owned temp and no bytecode. User-authorized resource amendment uses one fit, LightGBM 16 threads, BLAS 16, PyArrow 4 and Normal priority.

All paths below are relative to `analysis_outputs/score_push_20261104/deployment_check/`.

| Criterion and exact scenario | Binary observable | Captured artifact |
|---|---|---|
| Freeze recipes, cutoff and source bytes before fitting | Protocol created exclusively; snapshot imports check source SHA256 | `protocol.json`, `sources/`, `input_hashes.json` |
| Same March 1 cutoff for both arms and shared fresh bottom-up | Both use predicate-filtered training labels; site train maxima <= cutoff; no reused full-June bottom-up | `site_train_counts.json`, `features.json`, `models/*/config.json`, `resume/models/station/*/config.json` |
| Predict without March-May labels | Target-free feature projections; predictions persisted and hashed before evaluation-label read | `evaluation_features.parquet`, `frozen_predictions.parquet`, `prediction_freeze.json` |
| Recover only unfinished work after genuine process loss | OpenProcess PID31788 returns NULL / error87; preserve 269 completed scientific fits and partial station mask; fit only three station seeds | `evidence/process_probe.json`, `resource_amendment.json`, `resume/controller_receipt.json` |
| Execute original and recovery controllers | Recovery exit0 in synchronous owning tool and receipt; original exit explicitly null | `run.log`, `resume/run.log`, `resume/controller_receipt.json` |
| Saved-model replay for all 272 scientific models | All saved raw predictions finite and allclose at stated tolerances; BU reconstructed exactly including float32 storage; negative raw seed counts retained | `replay.json`, `models/*/daylight_raw.parquet`, `resume/models/station/*/daylight_raw.parquet`, `bottom_up_site.parquet` |
| Train-only station constant mask | Recomputed mask exactly equals original pre-interruption train-only mask | `models/station/seed0/feature_mask.json`, `resume/models/station/*/feature_mask.json` |
| Fixed mixtures, nonnegative components and common 4416 keys | Complete one-to-one outer key merge; identical y/SMP/k/site_count to original oracle; no component NaN skipping | `components.parquet`, `paired_predictions.parquet` |
| Original and fresh paired loss, months and peak hours | Peak k matches actual timestamp hours11..15; target months use ts-1h; all metric assertions pass | `metrics.json`, `diagnostics.csv` |
| Paired daily bootstrap | Seed20261104, 2000 replicates, 92 daily blocks; saved daily inputs and every replicate | `bootstrap.json`, `bootstrap_daily_*.parquet`, `bootstrap_replicates_*.parquet` |
| Resource limits and actual allocation | All fits sequential; original receipts BelowNormal/2/BLAS1; recovered model params and threadpool reports Normal/16/BLAS16 | `models/*/runtime.json`, `resume/models/station/*/runtime.json`, `resume/runtime.json`, `resource_amendment.json` |
| GPU capability check on actual NVIDIA device | NVIDIA CUDA platform0/device0 identified; installed LightGBM explicitly rejects GPU learner build | `resume/gpu_capability.json`, `resume/run.log` |
| Preserve protected scientific files and all completed raw/models | Original protected hash map and recovery preexisting model/raw hash map both identical after completion | `preservation.json`, `protocol.json`, `resource_amendment.json` |
| Source quality check | No violations across six new Python modules | `evidence/final_source_check.log` |

Fresh-cutoff W: incumbent 467123277.22488314; candidate 467559229.70844895. W%: 9.43777524221884 versus 9.446583241641658, a candidate regression of 0.008807999422818 percentage points. Paired bootstrap W% difference 95% interval [-0.40194614109042687, 0.3770645226918446].

Original-cutoff W%: 9.576119223065254 versus 9.848506521192688. Its adverse result is retained. This is a post-hoc training-cutoff diagnostic using historically exposed data, not pristine holdout or official leaderboard evidence. No recipe, coefficient, composition or delivered final export was changed.

The GPU runtime field `gpu_synthetic_capability_fits: 1` records one attempted capability call; the call failed before fitting because GPU support is absent. Zero GPU models were successfully trained. The three actual resumed station fits used CPU 16 threads and their saved-model replays passed.

Actual fitted counts: five pooled bottom-up models, 252 site models and 15 group models, totaling 272. PV011 has only 746 daylight training rows and correctly uses pooled fallback under the frozen 1000-row eligibility rule. Original peak working set was 1704796160 bytes; resumed peak was 1223761920 bytes. Resumed station fit-and-replay times were 13.125, 13.453 and 13.390 seconds; resumed controller workload took 61.219 seconds.

Code review: the six modules separately own original orchestration, fixed fitting, paired reporting, recovery orchestration, saved-model replay and GPU device discovery. Existing frozen numerical interfaces were reused. There are no new dependencies or test-only production seams. Operational assertions cover replay, train-only masking, keys, weights, finite values and preservation. LSP/type checker was not installed, per instruction. No upload, final-export refit, further tuning or speculative model search was performed.
