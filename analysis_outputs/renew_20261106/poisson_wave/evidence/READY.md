# Poisson PREPARED

One fixed Poisson LightGBM complement is prepared, with zero actual model fits or native predictions. Await root independent verification and explicit six-fit release. No prior wave, candidate, model or reference was changed.

Protocol SHA256: e16d56b2de93c10ea1845d9934ac454892ddf2fb7d7bdd2dd6ee159aaed32a27
Prepared manifest SHA256: 50de3310428c91fa392486a72635aae3997bca3c705eb8b78dc6f649d044bd13

Paths below are relative to analysis_outputs/renew_20261106/poisson_wave/.

| Scenario | Invocation | Binary observable | Evidence |
|---|---|---|---|
| Source rules | python C:/Users/slowg/.codex/plugins/cache/sisyphuslabs/omo/5.1.60/skills/programming/scripts/python/check-no-excuse-rules.py submission/score_push_renew/poisson_common.py submission/score_push_renew/poisson_prepare.py submission/score_push_renew/poisson_math.py submission/score_push_renew/poisson_fit.py submission/score_push_renew/poisson_score.py submission/score_push_renew/poisson_run.py | exit0, no violations in6 files | evidence/programming_check.log |
| Frozen preparation | python submission/score_push_renew/poisson_run.py --prepare | exit0, POISSON PREFIT READY; both exact TRAIN masks/scalars; raw inputs byte identical | prepare_attempt01.log; evidence/read_receipts.json; prepared_manifest.json |
| Nine synthetic checks | same preparation command calls poisson_math.self_check() | passed, zero fits; includes zero-target Poisson identity, weights, once-only inverse, signed-mean/clip/weather/night | evidence/selfchecks.json |
| Fixture sensitivity | python -c imports poisson_math, runs self_check, temporarily substitutes squared-normalizer weights and second-exp inverse, requires AssertionError for each, restores and reruns | two regression failures caught; baseline restored PASS; production source untouched | evidence/mutation_selfcheck.log |
| Resource/lifecycle | & analysis_outputs/renew_20261106/poisson_wave/evidence/prepare_attempt01_launcher.ps1 | retained native handle exit0; PID48560 creation134383687917462854 absent; Normal32, all four native pools16, Arrow4 | evidence/prepare_attempt01_start.json; evidence/prepare_attempt01_exit.json; evidence/prefit_checks.json |
| Inputs/source/protection | preparation rehashes all protected files; terminal PowerShell SHA256 comparison of each prepared entry and original/snapshot own source | 3813 protected files unchanged;20 prepared artifacts and6 source pairs exact; release/trials/model absent; stderr0bytes | preservation.json; protocol.json; evidence/prefit_seal_checks.json |
| Safe cleanup | & analysis_outputs/renew_20261106/poisson_wave/evidence/prefit_cleanup.ps1 | exact owned process absent; containment/reparse0; tmp absent | evidence/prefit_cleanup.json; evidence/prefit_cleanup.log |

Both raw matrices contain904 station candidates, TRAIN-only masks460/790; primary train/eval21086/9642 and recent30728/7015. Target finite/nonnegative with positive sum. Weights and inverse are byte-identical copied mono transforms after exact independent reconstruction. Labels and five-column application inputs match official-best WEATHER-only temperature_then_snow; no hour/cloud features enter application.

Installed LightGBM4.7.0 native DLL and basic.py/sklearn.py/engine.py hashes are pinned in evidence/environment.json. Context7 source provenance is evidence/poisson_source_reference.json; moving-main links are explicitly not commit-pinned. Models use the native exp-linked response and multiply inverse_kwh once.

Self-review: six small modules own protocol/resources, numerical math, input preparation, one native fit, orchestration and scoring respectively. Existing helper interfaces reused; no new dependencies, abstraction layer, test-only production seam or untyped escape added. LSP installation remains declined. No preparation failures or retries. Continuous nonnegative quasi-loss does not assert integer-count outcomes; all history is exposed and no performance claim is made before fits.
