# Ultrawork Notepad — OIBC 2026 verified submission
Started: 2026-11-02 Asia/Seoul

## Plan
1. Audit existing pipeline, official local rules, data dates, runtime, and submission artifacts.
2. Reproduce the existing result and quantify selection leakage and data completeness.
3. Run chronological validation with composition and model choices separated from final evaluation.
4. Make the smallest supported corrections and produce an isolated reproducible candidate submission.
5. Verify metric math, malformed input rejection, complete forecast keys, finite nonnegative values, and capacities.
6. Deliver Korean evidence report, commands, limitations, and ready-to-submit CSV package.
7. Clean owned temporary resources and capture receipts.

## Success criteria + QA scenarios
Tier: HEAVY — user requests pipeline validation and a competition deliverable; chronological model selection and a new validation runner require multiple evidence channels.
1. Existing pipeline: `python submission/make_submission.py check` exits 0, and cached score recomputation matches recorded values; logs retained under analysis_outputs/award_run/.
2. Honest evaluation: `python submission/validate_pipeline.py` produces dated chronological evaluation with training/selection boundaries, independently recomputed official weighted errors, and comparable baseline/candidate metrics. No final evaluation targets may select parameters or composition.
3. Submission: `python submission/validate_artifacts.py submission/award_candidate` exits 0 for unique exact site/time keys, capacity bounds, finite nonnegative predictions, and expected schema. Its built-in self-check rejects duplicate keys and wrong timestamps.
4. Reproducibility: candidate manifest records source/code hashes, settings, versions and output hashes; rerunning checks succeeds without trusting presence-only caches.
Stop immediately when validation evidence, justified candidate CSVs, reproducible commands and the Korean assessment are delivered and owned temporary resources are cleaned.

## Now
Discovery and baseline reproduction.

## Todo
- Integrate two read-only audits.
- Establish clean chronological experiment design.
- Implement and run validation and candidate generation.
- Validate and write Korean assessment.
- Cleanup temporary resources.

## Completion evidence — 2026-11-02
- Criterion 1 PASS: original_pipeline_check.log, original_artifact_checks.json, and pipeline_checks.log under analysis_outputs/award_run. Old partial fallback failure was reproduced; corrected code preserves valid17 fields. Group-error metric hand calculation passes.
- Criterion 2 PASS: fresh chronological run exited0 in443.3s. Initial train965,326 rows; inner selection1,256,595; outer train2,221,921; outer validation2,170,645. Locked inner_twins/direct0.5 before outer evaluation. Candidate W_pct11.5525864720 vs reference11.8816048610; original selected-composition diagnostic11.5493361475 remains contaminated. Full-fleet strict Jan1<ts<=June1 includes7,248 group rows, candidate10.2234666779 vs reference10.3667214647.
- Criterion 3 PASS: candidate_checks.json verifies253 sites,17,520 exact keys, G1=21,208.195/G2=21,447.175 kW, finite nonnegative values;9 invalid input scenarios rejected. ZIP entries are exactly composition.csv and forecast.csv; entry hashes match manifest.
- Criterion 4 PASS: independent_verification.json recomputes all4 recipe metrics with stdlib math.fsum, verifies boundaries/inner-selection minimum and every input/source/output SHA256. Observed targets restored to float32 to round-trip CSV correctly; maximum group-sum rounding difference0.001953125kWh disclosed.
- Final checks: py_compile all6 pipeline/check files PASS; source_checks.log records no violations in5 new files. Existing make_submission.py pre-existing style/size not migrated. No LSP installed; prior user install refusal respected.
- Independent reviewer execution_review returned CLEAR/APPROVE, no blockers. Report .omo/evidence/oibc-chronological-validation-code-review.md. Final export independently validated after review.
- Korean report: analysis_outputs/reports/수상도전_파이프라인_검증보고서_20261102.md. Instructions updated submission/README.md and award_candidate/README.md. No external service received source data or submissions.
- Unknown official problem definition/scorer and hidden test labels remain explicit limitations; no ranking or award guarantee. User's optional URL question unanswered; provided README governs local checks.
- No Git repository; no commit list applicable.

## Cleanup receipts
- chronological_runner session28499 exited0; no explicitly owned temp directory reported. Library-managed joblib temporary cleanup not independently audited. Receipt analysis_outputs/award_run/cleanup_receipt.json.
- Root resolved and removed only C:/Users/slowg/AppData/Local/Temp/oibc-ulw-ZMT5HEWU and newly created workspace submission/__pycache__; read-back Test-Path=false for both.
- Durable hashed feature cache under analysis_outputs/award_run/cache intentionally retained as reproducibility artifact, alongside evidence and candidate CSVs.
- All agents terminal; no owned training process remains active.

## Now
Completed: deliver verified submission package and report.

## Todo
None. Stop condition met; no additional experiments or cleanup outside owned paths.

## Self-review
HEAVY tier held: chronology and source corrections required cross-stage evidence. Source changes are narrow, new files own one responsibility each, outputs independently verified, existing artifacts preserved, numerical/selection limitations stated beside their claims. No extra feature or dependency migration performed.

## Findings
- No Git repository exists in workspace; no commits possible or required.
- Original submission consists of 253 site assignments and 17,520 forecast records (headers add one line each).
- Original cache reports 11.5514665554% final blend error on the same year used to select composition; not an unbiased estimate.
- Existing environment: Python 3.12.10, numpy/pandas/pyarrow/lightgbm/sklearn installed; polars/duckdb/matplotlib/psutil absent.
- No test suite or AGENTS.md found in workspace discovery.
- User confirmed no first submission yet; composition is not locked.
- update_plan tool is unavailable in this session; this append-only ledger is the task checklist.

## Learnings
- Unwrap git_bash result content JSON and emit stdout directly to avoid nested-output compression.
- Preserve existing pandas pipeline interfaces; new independent checks can use pyarrow/numpy/stdlib without a wholesale migration.

## Skills
- ultrawork: evidence-bound execution and durable goal.
- data-scientist: dataset placement, numerical analysis, report evidence.
- ponytail: smallest complete corrections; preserve existing working pipeline.
- programming: Python boundaries and self-checks.
- lsp: source diagnostics where server available.
- git-master: status check established workspace is not a Git repository.
- graphify: considered existing-graph lookup; no graph exists, so building an unrelated graph is unnecessary for this bounded audit.

## Resources / cleanup
- Owned root: C:/Users/slowg/AppData/Local/Temp/oibc-ulw-ZMT5HEWU
- Initial empty note: above root/ulw-20261102-180515.6YI7UK.md; durable note is this file.
- All task command caches should use owned root. Remove only this exact resolved root when all children/processes exit.
- Agents: pipeline_audit (read-only), rules_audit (read-only).

## Transition — audits complete / chronological runner
- Both read-only audits returned terminal reports. Confirmed selection leakage, stale caches, partial-field fallback overwrite, validation missing upper boundary, and unsupported first-submission composition lock.
- Original check command PASS; independent validator confirms 253 sites, 17,520 exact unique keys, capacities 21,369.47/21,285.90 kW, output hashes recorded in console.
- New validator rejected duplicate site, invalid group, duplicate/wrong/naive timestamp, negative, infinity, NaN cases. Added specific capacity failure case.
- Reproduced partial fallback bug with real panel(): valid round-17 cloud=1 became round-10 cloud=9 when temperature was missing. Patched only missing cells, bounded validation by T2, checked each forecast against its own group capacity.
- Original source edits are deliberately narrow; existing oversized/pandas style is not migrated.
- Installed LSP servers=0; hook states user previously declined basedpyright installation. Respect that decision; compile and numerical/runtime checks replace unavailable LSP diagnostics, not claimed as LSP PASS.
- Agent chronological_runner owns new runner/support and candidate artifacts. Inner training <=2023-06-01; selection next year; outer training <=2024-06-01 and evaluation next year. Configuration freezes before outer scoring. Existing historical model design has seen outer data, so this is a chronological replay, not a pristine holdout.
- Official local README supplies W and S, not normalized leaderboard percentage. W_pct is local diagnostic only.

## Now
Execute chronological runner and independent numerical/boundary checks.

## Todo
- Capture patched fallback/metric self-check and independent artifact checks.
- Integrate runner output and recompute scores independently.
- Report evidence and package candidate.
- Cleanup temporary resources.
