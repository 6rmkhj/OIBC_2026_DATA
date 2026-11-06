# Bounded refinement: terminal evidence

Selected recipe: `leaves63_trees400_ensemble`, primary-only nonnegative weights summing1:

- Complete richer reference:0.380705173762783.
- Haurwitz-normalized LGBM-L1,63leaves/400trees, seedsNone/1/2:0.41926809371483975.
- Standard-CF MLP, seeds0/1/2:0.2000267325223772.

Paired development W_pct is **12.161987873994034 primary / 11.18733758871567 recent**, improving both prior-best scores12.32194072929294/11.317671544395346. Compared with the default three-way blend, primary regresses **+0.0026649112006325pp** while recent improves **−0.0353172748329040pp**. The selected recipe has the lowest equal-weight mean relative loss among eligible confirmed recipes under the caller's final ranking rule.

## Selection clarification and preserved history

The initial local protocol added a stricter final complexity-adoption veto requiring the confirmed ensemble to beat the default three-way blend on both folds. The caller clarified that this both-fold/default gate authorizes extra seeds; final eligibility instead requires both folds to beat the **prior best**, then ranks by equal-weight mean relative loss. The original protocol, original results, predictions, models and solver weights were preserved unchanged. `selection_rule_clarification.json` records the instruction, timing, original hashes and the primary regression. `clarified_results.json` and `chosen_recipe.json` are the authoritative final selection; `results.json` retains the initial interpretation. No fit or weight optimization occurred during this clarification.

## Bounded outcomes

| Candidate | Primary W_pct | Recent W_pct | Outcome |
| --- | ---: | ---: | --- |
| Default three-way,MLP3 | 12.159322963 | 11.222654864 | Eligible reference |
| Five-member alternative | 12.157430522 | 11.215642859 | Eligible; normalized-MLP weight0,kernel1.55475% |
| Default three-way,MLP5 | 12.196127179 | 11.255751095 | Discarded; worse thanMLP3 on both |
| Normalized15leaf/400tree,seed0 | 12.135388298 | 11.216609177 | Qualifying screen,not selected for extra seeds |
| Normalized63leaf/400tree,seed0 | 12.135413681 | 11.211930135 | Best qualifying paired screen |
| Normalized31leaf/800tree,seed0 | 12.183022639 | 11.264611975 | Failed both-fold/default gate |
| Normalized63leaf/400tree,seedsNone/1/2 | 12.161987874 | 11.187337589 | Selected confirmed recipe |

Exactly14 new sequential model fits:4 MLP seed3/4 fits,6 one-seed tree screens,4 extra fits for the one qualifying63leaf variant. Seven real convex recipes and one hand-computed solver fixture were solved. All weights were optimized only on primary and transferred unchanged to recent. No further grid, confirmation/test access, dependency installation, full refit or export occurred.

## Scenario / invocation / binary observable / artifact

Paths are relative to `analysis_outputs/score_push_20261104/refinement_wave/`.

| Scenario and invocation | Binary observable | Captured artifact |
| --- | --- | --- |
| `python submission/score_push/refine_wave.py` | PASS exit0; protocol written before evaluating new outputs;14 fits, bounded variants and followup | `protocol.json`, `run.stdout.log`, `progress.json`, `results.json`, `evidence/owned_exit.json` |
| Sparse HiGHS calls within runner | PASS solver success/status0, nonnegative unit-sum weights, feasible primal and matching dual objective; hand fixture returns[.2,.8] | `weights/*/optimization.json`, `weights/*/primary_fit_matrix.parquet`, `solver_selfcheck/optimization.json` |
| Same solver calls | PASS explicit threads2; SciPy forwarding OptimizeWarnings captured rather than hidden | `run.stderr.log`, `weights/*/optimization.json`, `weights/*/solver_runtime.json` |
| `python submission/score_push/refine_select.py` | PASS no-fit caller-rule clarification preserves every original prediction/model/score | `selection_rule_clarification.json`, `clarified_results.json`, `selection.stdout.log` |
| `python submission/score_push/refine_verify.py` | PASS all14 serialized new models replay raw forecasts;MLP5 equals exact five-seed mean | `evidence/verification.json`, `evidence/verification.stdout.log` |
| Same verifier invocation | PASS17568 primary and13104 recent keys;finite/nonnegative predictions; no missing-night rows; fixed cutoffs;primary-only weight origin | `evidence/verification.json`, `{primary,recent}/recipes/*/predictions.parquet` |
| Same verifier invocation | PASS selected member vectors exactly equal their source artifacts, with explicit paths and columns | `chosen_recipe.json`, `evidence/verification.json` |
| Same verifier invocation | PASS all input/output/executed-source hashes and native resource receipts | `manifest.json`, `sources/hashes.json`, `evidence/verification.json`, `{primary,recent}/*/seed*/runtime.json` |
| `python .../programming/scripts/python/check-no-excuse-rules.py` on the five new refine modules | PASS no violations | `source_audit.log` |
| `python submission/score_push/refine_manifest.py` after all writers exit | PASS final artifact and current-source fingerprint inventory includes chosen recipe, clarification and original history | `final_manifest.json` |

The final recipe's complete forecasts are `{primary,recent}/recipes/leaves63_trees400_ensemble/predictions.parquet`, column `p`. Component paths and weights are machine-readable in `chosen_recipe.json`. Initial-selection verification remains under `evidence/verification_initial.json` and `evidence/chosen_recipe_initial.json`.

Resource policy was unchanged: one fit/job at a time, Windows BelowNormal16384, modelCPU<=2,BLAS1,OMP2,PyArrow2,noGPU. Expected SciPy OptimizeWarnings explicitly say `threads:2` is forwarded to HiGHS; these are not convergence failures. Every owned fit process exited before terminal handoff.

Not checked/performed: LSP/typechecker installation, March-May confirmation, test data, new spatial family, full-data fit or submission. These remain development results and do not establish a new leaderboard score.
