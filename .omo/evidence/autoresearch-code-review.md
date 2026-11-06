# Autoresearch code review

codeQualityStatus: WATCH
recommendation: APPROVE

Scope: submission/autoresearch/{prepare,evaluate,train,common,run}.py. Bounded read-only implementation audit; report is the only written artifact. No git repository/diff or notepad was provided. Files were reviewed as new implementation, including connected make_submission.py grouping/features. The requested ulw-loop status command returned ULW_LOOP_SUBCOMMAND_UNKNOWN; fallback report location used.

## CRITICAL
None.

## HIGH
1. `submission/autoresearch/evaluate.py:47` applies the overall-score positive-denominator assertion to every calendar-month diagnostic. The selection ends inclusively at 2024-06-01 midnight. Its June diagnostic has 2 rows and zero weighted generation, so every valid baseline evaluation aborts before saving the overall score. Evidence: `analysis_outputs/autoresearch_20261103/wave.log` traceback; independent read of selection_labels.parquet confirmed June `(2, 0.0)` while all other months have positive denominators. Keep positive-denominator enforcement for the overall objective; represent undefined diagnostic W_pct as null (or explicitly omit this empty-energy diagnostic). Add a zero-energy-slice check. Baseline exact reproduction remains pending this fix.

## MEDIUM
1. `submission/autoresearch/run.py:97` limits concurrency within one invocation only; separate runner invocations can exceed the four-training-thread budget and race the shared best.json/results.tsv. Operate exactly one coordinator; if multiple launches are supported, add a single-instance guard.
2. `submission/autoresearch/evaluate.py:42` checks fixed hashes before reading/scoring but not after scoring. Thus a concurrent input edit during the evaluation window is not detected before recording success. Recheck before publishing results if the stated boundary requires after-scoring integrity verification.

## LOW
- `submission/autoresearch/common.py:22`: save_json value is untyped; structured score/result dictionaries are only partially typed. This falls short of the programming skill's strict typing preference, but does not establish a runtime defect.

## Resolved during audit
The original run.py record() allowed scoring exceptions to escape before journaling, losing the trial record and interrupting parallel result collection. The current file catches AssertionError/ValueError/KeyError/OSError, writes error.json, and journals crash results. This covers the observed failure. No runtime fault injection was performed after the edit.

## Verified boundaries
- Official objective is sum(smp*k*abs(group_prediction-group_energy)); W_pct divides by sum(smp*k*group_energy). Independent hand-computed self-check passed with W=800.
- Prediction schema, uniqueness, coverage, finite and nonnegative constraints have meaningful malformed-input self-checks; self-check passed.
- Selection feature preparation removes energy/cf before aggregation; model feature list excludes targets. Training reads only ts/grp from selection labels to preserve full output keys, not selection target values.
- CF training weights capacity*smp*k correctly convert absolute CF residual to the weighted group-kWh objective; exp2(-age/recency_days) implements the specified half-life.
- Default direct configuration matches historical GROUP hyperparameters apart from intended n_jobs reduction. Exact numeric baseline has not yet been proven.
- Preparation predicates exclude outer rows. No outer evaluation path exists in these five files. Historical outer score must not be described as pristine.
- Cache and fixed-source hashes passed independent verify_frozen() at review time. Snapshot train.py is the actual subprocess argv path, not merely an archival copy. Config/source hashes and frozen manifest digest are retained.
- Runner uses two worker threads and each fit n_jobs=2, with OMP=2 and BLAS/MKL/NUMEXPR=1 in child environment. Separate trial directories isolate output. subprocess.run(timeout=600) kills/reaps the direct process; training code starts no child processes. Runner writes journal from main thread only within that invocation.
- Source feature builder uses round 17 with round 10 fallback. This preserves historical forecast selection. Actual prev-day issue timestamps are absent from cached features and were not independently proven by this audit.

## Skill perspective
Loaded programming SKILL.md plus Python README and remove-ai-slops SKILL.md. Applied overfit/slop and maintainability review: no deletion-only tests, prose pins, implementation-constant mirrors, test-only production seams, unnecessary normalization, or needless extraction found. The scoring/malformed-input self-check tests independent behavior. Existing pandas interface intentionally preserves original numerics; a library migration would add scope and numeric risk. Strict typing gap noted LOW above. Production boundary checks are justified by experiment integrity, not redundant internal validation.

## Evidence and limitations
Inspected analysis_outputs/autoresearch_20261103/{wave.log,cache/manifest.json,trials/baseline/invocation.json} and artifact inventory, plus analysis_outputs/award_run/provenance.json. Executed evaluate.py --self-check and lightweight frozen-hash/monthly-denominator checks. No training, installs, heavy resource checks, LSP, or outer evaluation. Files were being edited concurrently; this report describes the bounded snapshot inspected and needs follow-up for the HIGH fix.

## Bounded delta re-review — final disposition

Prior HIGH blocker RESOLVED. No remaining blocker in the requested delta scope. Earlier findings above are historical; MEDIUM operating limitations were not reopened.

- evaluate.py now assigns each hourly interval to the month of `ts - 1 hour`. This correctly includes the June 1 midnight endpoint in May and removes the spurious June-only diagnostic without changing the overall metric or excluding rows.
- Independently recomputed denominators from selection_labels.parquet using that expression: exactly 12 monthly groups, every denominator positive. Existing baseline diagnostics.csv contains those 12 months plus the two halves, with finite scores.
- Independently read results.tsv: exactly 9 successful trial rows; successful baseline W_pct equals 13.210225898116454 exactly as parsed. baseline/score.json agrees; wave.log contains all nine completed results.
- Failed-trial journaling: current record() catches the observed assertion failure, records an error artifact and exit_code=1, then reaches the shared CSV/result write. results.tsv retains the earlier baseline crash row with exit_code=1, followed by the successful run. The original baseline error.json is no longer present in the current trial directory; historical error-detail retention was not independently established. This does not prevent the central failed-trial journal check from passing.
- Frozen-source/cache verification passed again. No training was launched.

Skill-perspective delta check: the one-hour adjustment follows the hourly interval contract rather than hard-coding a failing month; no unnecessary parsing, extraction, or implementation-mirroring test was introduced. Existing programming/remove-ai-slops review remains applicable.

Final codeQualityStatus: WATCH (prior nonblocking operating caveats retained)
Final recommendation: APPROVE
Final blockers: []

Skipped repeat review of previously approved areas, fault injection, training, and outer evaluation, as requested. Historical error.json retention remains unverified; centralized crash record is verified.

## Second-wave bounded review

Delta status: CLEAR. Recommendation: APPROVE. Blockers: []. Previous unrelated operating caveats remain unchanged.

Reviewed current train.py and all 10 saved w2 snapshots/configs/score artifacts. Every snapshot train.py SHA-256 matches snapshot.json. The explicit-zero w2_baseline remains preserved at W_pct 13.254413767810991; its snapshot uses random_state=seed. The corrected w2_baseline_default and remaining nine corrected snapshots map sentinel 0 to None with an explanatory comment; corrected baseline score is exactly 13.210225898116454.

Ramp inputs are existing forecast-derived columns only: wa_cloud, wb_cloud, wb_uv_idx, wa_temp, plus toaa/toab (deterministic forecast-cloud/solar-geometry products already in the base feature set). No observed weather, generation, or selection labels enter ramps. Grouping uses group and the day of ts minus one hour; the diff is emitted only for exactly one-hour adjacency. Independently exercised unsorted synthetic rows across groups, midnight and a two-hour gap: within-day midnight differences retained; cross-day/group/gap differences NaN; original row identity and target alignment preserved. Sorting is applied to each entire frame before X, target and weights are extracted, so no X/y misalignment is introduced.

Ensemble averages raw CF predictions across seeds, clips the mean nonnegative, then multiplies by aligned group capacity once. This is correct for an ensemble defined as mean CF followed by the existing nonnegative output boundary. Seed fits are sequential in the group loop, each n_jobs=2; runner concurrency remains unchanged. predict_frames receives label-free selection and returns timestamp/group keys, so caller ordering need not match the input frame ordering.

Rechecked frozen prepare/evaluate/common and cache hashes successfully. Skill-perspective check applied using already loaded programming/remove-ai-slops criteria: no unnecessary normalization/extraction, target-dependent features, brittle test pins, or needless abstraction introduced. Reusable predict_frames encapsulates the actual fit/predict path rather than a test-only seam.

No model fit, outer-data read, or production edit performed. Residual: target-day forecast issue-time provenance remains inherited from the frozen feature cache; this delta review establishes no stronger availability claim. Mean-then-clip is intentional and differs from averaging separately clipped seed predictions when individual seeds predict below zero.

## Third-wave context and spatial bounded review

Delta status: CLEAR. Recommendation: APPROVE. Blockers: []. Reviewed only stable trials/w3_context_seeds/train.py and submission/autoresearch_spatial.py, not the in-progress pooled candidate.

Context uses existing forecast/weather-derived fields, grouping by group plus the right-closed target day (ts minus one hour). Daily summaries never use targets; leads require exactly one-hour adjacency within that day/group. Whole-frame sorting preserves target/weight alignment. Independent unsorted synthetic check confirmed midnight inclusion, no cross-day/group lead, gap masking, daily mean values and row/target identity. Stable train snapshot SHA-256 matches snapshot.json. Participant README.md lines 9, 32 and 93 explicitly establish prior-day 17:00 prediction, right-closed hourly timestamps, and round 10/17 issuance on the previous day; therefore same-target-day forecast leads and summaries are available by the declared prediction time.

Spatial read_parquet projects site/time/night/capacity and five weather-derived columns only and filters ts <= selection cutoff; no energy/cf/observed-weather column is selected. Physical source-file hashing does not deserialize target values. Capacity-weighted variance is E_w[x^2] minus E_w[x]^2, clipped at zero for roundoff; each feature uses only its nonmissing positive-capacity weights. All-missing values produce NaN, not a falsely precise zero. Clear/overcast fractions use the same valid-weight denominator and strict thresholds.

Spatial self-check independently executed successfully, covering unequal capacities, missing/all-missing inputs, constant values, cloud boundaries, night-only groups and rejection of label-bearing frames. Inspected mutation_check.log showing that removing mean-square subtraction fails this independent arithmetic check. Independently verified builder/assignment/output hashes and exact ordered train/selection ts/grp key equality with frozen cache, reading only small output/key projections. Did not repeat raw aggregation or read outer data.

Skill perspective: no overfit/prose/removal-only tests or needless parsing/normalization identified. Projection and exact-column validation form a justified target-leakage boundary; missing-weight normalization is mathematically required. Remaining strict-typing/style caveats from prior report are unchanged and outside this delta.

Residual limitation: spatial summaries describe the supplied site/weather proxy and available daylight-site coverage, not independently observed full-fleet dispersion. This was already disclosed; no stronger coverage claim is established. No fits or production edits performed, and no second aggregation was started.
