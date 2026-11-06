# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called only after released six workers complete their twelve inferences.
"""One fixed accepted-component substitution, without any weight or alpha fit."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact original mean and complete scoring keys
from incbound_common import OUT,FOLDS,REFERENCE,save
from incbound_math import ensemble,substitute,stages

def compare():
    from final_metrics import metrics
    weight = json.loads((OUT/'lineage.json').read_text(encoding='utf-8'))['effective_mlp_weight']
    scores = {}
    for fold in FOLDS:
        data = OUT/'data'/fold
        lineage = pd.read_parquet(data/'lineage.parquet')
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        labels = pd.read_parquet(data/'labels.parquet')
        coverage = pd.read_parquet(data/'coverage.parquet')
        keys = lineage[['ts','grp']]
        pd.testing.assert_frame_equal(keys,labels[['ts','grp']])
        pd.testing.assert_frame_equal(keys,inputs[['ts','grp']])
        np.testing.assert_array_equal(lineage.p_sky_reference,labels.p_reference)
        covered = keys.merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        old_raws,bounded_raws = [],[]
        for seed in (0,1,2):
            directory = OUT/'trials'/fold/f'seed{seed}'
            proof = json.loads((directory/'replay.json').read_text(encoding='utf-8'))
            assert proof['original_full_exact'] and proof['native_model_inferences']==2 and proof['new_model_fits']==0
            for filename,container in (('original_raw.parquet',old_raws),('bounded_raw.parquet',bounded_raws)):
                raw = pd.read_parquet(directory/filename)
                joined = covered.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
                assert joined.p_raw.isna().eq(joined.night).all() and int(joined.p_raw.notna().sum())==len(raw)
                container.append(raw)
        old = ensemble(keys,old_raws)
        np.testing.assert_array_equal(old,lineage.p_old_mlp)
        original_stages = stages(inputs,lineage.p_raw_temporal.to_numpy())
        for actual,reference in (('p_weather','p_weather_reference'),('p_hour','p_hour_reference'),('p','p_sky_reference')):
            np.testing.assert_array_equal(original_stages[actual],lineage[reference])
        bounded = ensemble(keys,bounded_raws)
        delta = bounded-lineage.p_old_mlp.to_numpy()
        raw_candidate = substitute(lineage.p_raw_temporal.to_numpy(),delta,weight)
        candidate = stages(inputs,raw_candidate)
        candidate['p_old_mlp'] = lineage.p_old_mlp.to_numpy()
        candidate['p_bounded_mlp'] = bounded
        candidate['mlp_delta'] = delta
        candidate['p_raw_temporal'] = lineage.p_raw_temporal.to_numpy()
        frame = labels.merge(candidate,on=['ts','grp'],sort=False,validate='one_to_one')
        assert frame.loc[covered.night,'p'].eq(0).all()
        directory = OUT/'comparisons'/fold
        directory.mkdir(parents=True)
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference')}
        assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
        save(directory/'metrics.json',scores[fold])
    both = all(scores[f]['p']['W']<scores[f]['p_reference']['W'] for f in FOLDS)
    return {'arm':'incumbent_rich_mlp_train_range','effective_mlp_weight':weight,'scores':scores,'both_folds_improve':both,'eligible':both,'seeds':[0,1,2],'new_alpha_fits':0,'new_weight_fits':0,'new_calibration_fits':0}
