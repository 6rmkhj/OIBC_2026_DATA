# Weather-only spatial-profile family: terminal evidence

Selected recipe: three-seed provider-station normalized-LGBM-L1, blended into the complete current refinement forecast. Primary-only new-member weight is **0.2808471620447986**, transferred unchanged to recent. Normalized LGBM uses63leaves,400trees,learning_rate.03,min_child_samples50,seedsNone/1/2 and the existing Haurwitz target/weight transformation.

| Recipe | Primary W_pct | Recent W_pct | Decision |
| --- | ---: | ---: | --- |
| Current refinement reference | 12.161987874 | 11.187337589 | Baseline |
| Cell normalized-LGB,seed0 complement | 12.114264422 | 11.178756807 | Qualified screen |
| Cell CF-MLP,seed0 complement | 12.122069591 | 11.183733598 | Qualified screen |
| Station normalized-LGB,seed0 complement | 12.058063071 | 11.090472007 | Best paired screen |
| Station CF-MLP,seed0 complement | 12.108092722 | 11.210209861 | Discarded: recent regression |
| Station normalized-LGB,seedsNone/1/2 complement | **12.041603595410752** | **11.064366712650248** | Adopted: both folds improve |

Exactly12 new model fits completed:8 screens and4 additional fits for the one qualifying station/tree variant. All pure scores and complement scores are saved. No further family, confirmation/test access, full refit or export occurred.

## Representation and missingness

Metadata enumeration includes11 fixed floor(latitude)/floor(longitude) cells,61 provider-A stations and73 provider-B stations. Profiles use exact existing daylight site-hour coverage with projected forecast/physics columns only. Energy,cf,y are never projected into the builder. The training feature-cache input is filtered at Parquet read to ts<=2025-03-01 and night=False. Metadata mappings use the provided sites table and unchanged deployed assignment.

For each group/hour,bucket share is bucket capacity/group capacity. Weather contribution is sum(capacity*weather)/group capacity. An absent bucket has share0 and contribution0. A present bucket whose channel is entirely missing has NaN contribution; partial missing values contribute only known terms without renormalization. Thus observed0,absent and all-missing states remain distinct in the stored representation. Cache values are float32; aggregation and share checks use float64 first.

Both learners drop columns with<=1 distinct nonmissing training value, including all-missing columns. Masks are fitted only on each training fold and persisted/replayed exactly; future stations cannot activate never-trained MLP input dimensions. MLP imputation,input scaling and target scaling remain training-only. Selected features never contain targets or score weights.

## Exact scenarios, invocations, binary observables and artifacts

Paths below are relative to `analysis_outputs/score_push_20261104/profile_wave/`.

| Scenario / invocation | Binary observable | Captured artifact |
| --- | --- | --- |
| `python submission/score_push/profile_wave.py`, checks before fits | PASS weighted contribution/share hand fixture; absent/all-missing/partial-missing distinction; duplicate-key rejection; label perturbation invariance; train-only mask; deliberately broken weighting fails | `prefit_checks.json`, `run.stdout.log`, executed `sources/profile_features.py` |
| Same runner, weather projection/build | PASS11/61/73 metadata groups; no energy/cf/y projection; exact daylight site coverage; stored profiles and source hashes | `cache/manifest.json`, `cache/cells.parquet`, `cache/stations.parquet`, `build_runtime.json` |
| Same runner, bounded paired screens/followup | PASS12 sequential fits,one permitted additional-seed variant,process exit0 | `protocol.json`, `results.json`, `run.stdout.log`, `evidence/owned_exit.json` |
| Primary-only analytic complement | PASS same alpha applied to both periods; pure and blended forecasts preserve17568/13104 full hourly keys | `results.json`, `{primary,recent}/*/{screen,ensemble}/{pure,complement}/predictions.parquet` |
| `python submission/score_push/profile_verify.py` | PASS all12 serialized model replays,saved masks equal train-only masks,MLP scalers match train-only refits | `evidence/verification.json`, `evidence/verification.stdout.log`, `{primary,recent}/*/seed*/feature_mask.json` |
| Same verification invocation | PASS exact keys and unchanged y/SMP/k labels,finite/nonnegative forecasts,fixed cutoffs and frozen metric recomputation | `evidence/verification.json`, `manifest.json` |
| Same verification invocation | PASS cache shares sum1 and all input/cache/output/executed-source hashes verify | `cache/manifest.json`, `sources/hashes.json`, `manifest.json`, `evidence/verification.json` |
| Runtime/convergence receipts | PASS BelowNormal16384,modelCPU<=2,BLAS1,OMP2,PyArrow2,one active fit;peakRSS1562943488bytes;0 warnings | `{primary,recent}/*/seed*/runtime.json`, `{primary,recent}/*/seed*/convergence.json`, `evidence/verification.json` |
| `python .../programming/scripts/python/check-no-excuse-rules.py` with the five profile modules | PASS no violations | `source_audit.log` |
| `python submission/score_push/profile_manifest.py`, run last | PASS completed artifacts,current sources and reused external dependency fingerprints | `final_manifest.json` |

Selected station ensemble monthly regressions:3of12 primary months and4of9 recent months. Largest regressions are +0.176255pp in August2023 and +0.154574pp in December2024. January-February2025 combined improves by0.123000pp. All variants' per-month deltas are in `evidence/monthly_comparison.csv`; these regressions limit generalization claims despite both aggregate windows improving.

## No-refit component paths and schema

For each `fold` in `primary`, `recent`:

- Chosen **complete** forecast: `fold/stations_lgb/ensemble/complement/predictions.parquet`, use column `p`.
- Cell-tree **pure** forecast: `fold/cells_lgb/screen/pure/predictions.parquet`, use column `p_new`.
- Cell-MLP **pure** forecast: `fold/cells_mlp/screen/pure/predictions.parquet`, use column `p_new`.

Common schema: `ts` timestamp[us,Asia/Seoul],`grp` string,`y` float32,`p_bu_old` float64,`smp` float64,`k` int64,`p_dir_reference` float64,`p_reference` float64,`p_new` float64,`p` float64. Complete complement files also have `alpha` float64. Here `p_reference` is the **pre-profile refinement** forecast; it is not the newly selected station-complete forecast. Align components by(ts,grp),and use the complete station file's `p` for any separately authorized no-fit check.

`selected_recipe.json` records the recursive base recipe hash,selected profile,primary alpha and exact complete prediction paths. No additional convex selection was performed in this stage.

Both owned processes exited0; no owned fit process remains. Not performed: March-May confirmation,test data,LSP/typechecker installation,new dependencies,GPU,full refit or submission. Development gains are not a new leaderboard result.
