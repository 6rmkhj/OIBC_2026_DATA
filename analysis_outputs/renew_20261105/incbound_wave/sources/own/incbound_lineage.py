# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: incbound_run.py --prepare; reads stored predictions, never models or labels.
"""Exact accepted MLP/refinement/profile/temporal/sky lineage from stored values."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact original stored ensemble and key semantics
from threadpoolctl import threadpool_limits
from incbound_common import ROOT,OUT,OLD,RENEW,MODELS,FOLDS,digest,save
from incbound_math import ensemble,stages,substitute

def prepare_lineage() -> None:
    recipe = json.loads((OLD/'refinement_wave/chosen_recipe.json').read_text(encoding='utf-8'))
    profile = json.loads((OLD/'profile_wave/selected_recipe.json').read_text(encoding='utf-8'))
    temporal = json.loads((RENEW/'recency_wave/results.json').read_text(encoding='utf-8'))['selected']
    assert recipe['id']=='leaves63_trees400_ensemble' and recipe['members']==['p_reference','norm','mlp']
    assert profile['profile']['id']=='stations_lgb' and profile['profile']['stage']=='ensemble'
    assert temporal['variant']=='decay180' and temporal['seeds']==[0,1,2]
    assert profile['base_recipe_sha256']==digest(OLD/'refinement_wave/chosen_recipe.json')
    member = recipe['member_artifacts_relative_to_score_push_output']['mlp']
    assert member=={'path_pattern':'learner_wave/{fold}/mlp_cf/ensemble/pure/predictions.parquet','column':'p_new'}
    mlp_weight = recipe['weights_primary_only'][recipe['members'].index('mlp')]
    station_alpha = profile['profile']['alpha_primary_only']
    temporal_alpha = temporal['alpha_primary_only']
    effective_weight = (1-temporal_alpha)*(1-station_alpha)*mlp_weight
    receipts = []
    for fold in FOLDS:
        data = OUT/'data'/fold
        old = pd.read_parquet(MODELS/fold/'mlp_cf/ensemble/pure/predictions.parquet',columns=['ts','grp','p_new'])
        keys = old[['ts','grp']]
        raws = [pd.read_parquet(MODELS/fold/'mlp_cf'/f'seed{s}/daylight_raw.parquet',columns=['ts','grp','p_raw']) for s in (0,1,2)]
        np.testing.assert_array_equal(ensemble(keys,raws),old.p_new)
        refine = pd.read_parquet(OLD/'refinement_wave'/fold/f"recipes/{recipe['id']}/predictions.parquet",columns=['ts','grp',*recipe['members'],'p'])
        pd.testing.assert_frame_equal(refine[['ts','grp']],keys)
        np.testing.assert_array_equal(refine.mlp,old.p_new)
        with threadpool_limits(limits=1,user_api='blas'):
            refined = refine[recipe['members']].to_numpy()@np.array(recipe['weights_primary_only'])
        np.testing.assert_array_equal(refined,refine.p)
        prof = pd.read_parquet(ROOT/profile['prediction_paths'][fold],columns=['ts','grp','p_reference','p_new','alpha','p'])
        pd.testing.assert_frame_equal(prof[['ts','grp']],keys)
        np.testing.assert_array_equal(prof.p_reference,refine.p)
        assert prof.alpha.eq(station_alpha).all()
        np.testing.assert_array_equal((1-station_alpha)*prof.p_reference+station_alpha*prof.p_new,prof.p)
        raw = pd.read_parquet(RENEW/'recency_wave/comparisons/decay180/ensemble'/fold/'predictions.parquet',columns=['ts','grp','p_reference','p_new','alpha','p'])
        pd.testing.assert_frame_equal(raw[['ts','grp']],keys)
        np.testing.assert_array_equal(raw.p_reference,prof.p)
        assert raw.alpha.eq(temporal_alpha).all()
        np.testing.assert_array_equal((1-temporal_alpha)*raw.p_reference+temporal_alpha*raw.p_new,raw.p)
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        pd.testing.assert_frame_equal(inputs[['ts','grp']],keys)
        original = stages(inputs,raw.p.to_numpy())
        expected = {}
        for wave,arm,column in (('calibration_wave','temperature_then_snow','p_weather'),('hour_wave','hour_bias','p_hour'),('sky_wave','cloud_bias','p')):
            frame = pd.read_parquet(RENEW/wave/'comparisons'/arm/fold/'predictions.parquet',columns=['ts','grp','p'])
            pd.testing.assert_frame_equal(frame[['ts','grp']],keys)
            np.testing.assert_array_equal(original[column],frame.p)
            expected[column] = frame.p.to_numpy()
        coverage = pd.read_parquet(data/'coverage.parquet')
        covered = keys.merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        assert covered.night.notna().all() and old.loc[covered.night,'p_new'].eq(0).all() and raw.loc[covered.night,'p'].eq(0).all()
        zero = substitute(raw.p.to_numpy(),np.zeros(len(raw)),effective_weight)
        assert np.array_equal(zero.view(np.uint64),raw.p.to_numpy().view(np.uint64))
        keys.assign(p_old_mlp=old.p_new.to_numpy(),p_raw_temporal=raw.p.to_numpy(),p_weather_reference=expected['p_weather'],p_hour_reference=expected['p_hour'],p_sky_reference=expected['p']).to_parquet(data/'lineage.parquet',index=False)
        receipts.append({'fold':fold,'rows':len(keys),'stored_signed_seed_ensemble_exact':True,'refinement_matrix_product_exact':True,'profile_equation_exact':True,'temporal_equation_exact':True,'all_stage_replay_exact':True,'zero_delta_raw_bits_preserved':True,'generation_labels_read':False,'model_loads':0,'model_inferences':0,'model_fits':0})
    save(OUT/'lineage.json',{'mlp_weight_in_refinement':mlp_weight,'station_alpha':station_alpha,'temporal_alpha':temporal_alpha,'effective_mlp_weight':effective_weight,'source_recipe':str((OLD/'refinement_wave/chosen_recipe.json').relative_to(ROOT)),'source_profile':str((OLD/'profile_wave/selected_recipe.json').relative_to(ROOT)),'source_temporal':str((RENEW/'recency_wave/results.json').relative_to(ROOT)),'formula':'(1-temporal_alpha)*(1-station_alpha)*mlp_weight_in_refinement','refinement_arithmetic_blas_threads':1,'folds':receipts})
