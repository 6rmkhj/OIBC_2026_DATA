# Read-only monotone feasibility review

Recommendation: treat the next candidate only as coordinate monotone regularization, not a globally physical cloud response. With all existing features held fixed, redundant cloud inputs cannot be ruled out; they are demonstrably present. Do not claim physical consistency from a direct-only constraint experiment.

## Compatibility and matched recipe

Installed package is LightGBM 4.7.0. Native DLL SHA256: 7e366d2e49cd061aac3ab21676b2f99b0c7a758dc3e888d4b23812af1b7d301c. `inspection.json` records the exact DLL path and native byte offsets: 0x3165c0 rejects monotone constraints for an objective (format string contains %s); 0x31be88 explicitly rejects regression_l1 with linear trees; 0x31bfd0 says intermediate/advanced constraints revert to basic with feature fraction !=1. Static strings alone do not prove which objective reaches the generic monotone rejection. Root owns the separate native L1/fair compatibility probe; this worker ran zero fits.

Use constant leaves (`linear_tree=false`) and basic monotone constraints. Current colsample_bytree=.8 should remain unchanged; do not change it to 1 just to select a different constraint method. LightGBM documentation also warns that linear-tree monotonic constraints cover split selection but not leaf linear models: https://github.com/lightgbm-org/LightGBM/blob/main/docs/Parameters.rst .

Root has separately recorded native regression_l1 rejection and fair support in analysis_outputs/renew_20261105/monotone_compatibility.json (synthetic-only,20 trees,max coordinate increase0). This worker inspected that artifact, but did not rerun its probe. Compare ONE constrained fair candidate with a matched unconstrained fair control, explicitly same fair_c=.1 as the root probe. Do not attribute a fair-vs-L1 improvement to monotonicity. The old normalized-weighted-L1 loss has a cancellation equivalence that fair does not retain.

Keep the existing normalized station recipe: exact same ordered training-only mask, full development train rows/cutoffs, y=cf/normalizer(cosz), weight=normalizer(cosz)*exp2(-age_days/180), inverse=normalizer(cosz)*capacity_kw. Root has selected the existing180day weighting recipe for BOTH matched arms. Use 400 estimators, learning_rate .03, num_leaves63, min_child_samples50, subsample .8, subsample_freq1, colsample_bytree .8, seed sentinel None for seed0 and integers1/2, CPU16/Arrow4/Normal, serial workers. Use identical180day recency weighting in both arms; no window change. Use the same three-seed aggregation, clipping/night handling, frozen calibration, and primary-only blend/scoring on both arms. The only differences between matched arms must be the constraint vector. Do not use the historic L1 score as the matched control.

Recipe source: submission/score_push/profile_models.py:23 (training mask), :31 (parameters), :33 (normalizer/weights); submission/score_push_renew/temporal_common.py:20 (CPU16 counterpart); submission/score_push_renew/temporal_fit.py:31 (cutoff), :39 (mask), :40 (scale), :43 (normalizer times temporal weights), :51 (seed sentinel); submission/score_push/site_features.py:19 (Haurwitz floor .05).

## Exact mapping

Recomputed `nunique(dropna=True)>1` from feature-only TRAIN columns, and exact ordered equality to saved station masks passed. Primary: 904 candidates, 460 selected, 21086 rows. Recent: 904 candidates, 790 selected, 30728 rows.

The FINAL recommended vector is fully enumerated for all1250 selected fold/features in recommended_constraint_vector.csv. Name-based rule after each fold mask:
- -1 on wa_cloud, wb_cloud and exact wa_station_WA*_wa_cloud / wb_station_WB*_wb_cloud names.
- +1 on toaa, toab and exact wa_station_WA*_toaa / wb_station_WB*_toab names.
- 0 on everything else, explicitly every csa/csb field.
Primary vector460:62 negatives,62 positives,336 zeros. Recent vector790:117 negatives,117 positives,556 zeros. Control vectors are all0. No additional candidate is proposed.

Direct cloud indices are0 and6; current toaa/toab indices25 and26 in both folds. Selected station clouds are primary28WA+32WB, recent53WA+62WB; matching selected TOA-attenuation contributions have the same counts. inspection.json has every selected name in exact order. cloud_feature_mapping.csv is the diagnostic inventory (including two preliminary mapping alternatives), not the final protocol; use recommended_constraint_vector.csv for the sole recommended pair.

Schema source: submission/score_push_gpu/gpu_data.py:28-38 (100 rich +804 station candidates); submission/score_push/profile_features.py:15 (station channels), :23-34 (capacity-weighted contribution and names), :39 (mask), :109 (float32 cast).

## Demonstrated proxy and missing-value risks

* Station cloud sums duplicate provider aggregate clouds to float32 precision. On training rows maximum absolute difference is primary WA2.66e-5/WB2.76e-5 and recent WA3.37e-5/WB3.02e-5. This rules out the preliminary two-aggregate-only mapping as a strong physical interpretation. The final recommendation constrains these station cloud contributions too, but leaves other routes unconstrained.
* Both masks retain `r10_wa_cloud`46, `rev_wa_cloud`52, `r10_wb_cloud`66, `rev_wb_cloud`75, cloud ramps79/80, daylight means85/87, standard deviations86/88, leads93/94. Revisions equal late-minus-early; ramps current-minus-prior; leads next-minus-current. A physical cloud perturbation therefore moves several coordinates with different signs, while daily std has no fixed sign. See submission/score_push/features.py:39-45 and :94; submission/autoresearch/train.py:57-80.
* `csa`23, `csb`24, `toaa`25, `toab`26, `cdis`28, `phys_humidity_clear`76 and `phys_uv_clear`78 remain, plus station csa/csb/toaa/toab contributions. csa=cosz*clip(1-cloud/100), toaa=toa*clip(1-cloud/100), analogous WB, and cdis=abs(WA-WB), whose sign is not fixed. See submission/make_submission.py:83-85 and submission/score_push/run.py:103-105. Cloud attenuation times TOA is nonnegative because TOA clips cosz at0 (make_submission.py:80), supporting the recommended +1 coordinate sign. csa/csb instead multiply raw cosz, which can be negative during an hour classified daylight from interval endpoints (make_submission.py:75-84). Thus csa/csb and their station versions remain0. Ramps/leads of toaa/toab also remain0. Do not assign blanket -1 or +1 to derived fields.
* Direct cloud TRAIN NaNs are0 in both folds, but station-cloud NaNs occur on70 WA rows and101 WB rows in both folds. Absent station bucket is0, present-but-all-missing isNaN, partial sums are not renormalized (profile_features.py:19-34, :118). Thus zero includes absence and clear sky, while NaN is a distinct branch condition. Finite-coordinate monotonicity must not be generalized across a missing-to-observed transition or changes in station capacity shares.

No fit, objective compatibility test, prediction test, source edit, prior-wave edit, dependency installation, feature removal, freeze, or implementation was performed by this worker. Validation was feature-only inspection; performance and end-to-end monotonicity remain untested.

Evidence criteria: native binary inspection => version/hash/exact strings captured in inspection.json; recomputed train-only masks => verified_train_only_mask_equals_saved=true per fold; feature mapping => cloud_feature_mapping.csv; source references above => direct reads. No claim of native L1/fair success is made by this artifact.
