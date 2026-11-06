# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called ONLY after root release by yield_run.py.
"""Fit each fold's site gains once and materialize shared train/eval transforms."""
from dataclasses import asdict
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- original site and group key contracts
from yield_common import OUT,FOLDS,save,digest,now,decay_multiplier
from yield_math import SiteGain,YieldFit,fit_gains,group_gains,haurwitz,normalizer


def materialize() -> None:
    release = json.loads((OUT/'release.json').read_text())
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    sites = pd.read_parquet(OUT/'data/sites.parquet')
    assignment = sites.set_index('site_id').grp
    records = []
    (OUT/'coefficients').mkdir(exist_ok=True)
    for fold in FOLDS:
        directory = OUT/'data'/fold
        train_site = pd.read_parquet(directory/'site_train.parquet')
        eval_site = pd.read_parquet(directory/'site_evaluation.parquet')
        spec = json.loads((directory/'features.json').read_text())
        cutoff = pd.Timestamp(spec['cutoff'])
        assert train_site.ts.max()<=cutoff<eval_site.ts.min()
        path = OUT/'coefficients'/f'{fold}.json'
        loaded = path.exists()
        if loaded:
            stored = json.loads(path.read_text())
            assert stored['source_sha256']==digest(directory/'site_train.parquet')
            fitted = YieldFit(stored['global_q90'],stored['clear_rows'],tuple(SiteGain(**r) for r in stored['sites']))
        else:
            fitted = fit_gains(train_site,sites.site_id.tolist())
            save(path,{**asdict(fitted),'cutoff':spec['cutoff'],'max_target_ts':str(train_site.ts.max()),'source':'data/'+fold+'/site_train.parquet','source_sha256':digest(directory/'site_train.parquet'),'quantile_method':'linear','training_only':True})
        for split,panel in [('train',train_site),('evaluation',eval_site)]:
            active = panel[['ts','site_id','capacity_kw']].copy()
            active['grp'] = active.site_id.astype(str).map(assignment)
            assert active.grp.notna().all()
            gains = group_gains(active,fitted)
            original = pd.read_parquet(directory/f'{split}_capacity.parquet')
            aligned = gains.merge(original,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True,suffixes=('','_original'))
            assert aligned._merge.eq('both').all()
            np.testing.assert_allclose(aligned.capacity_kw,aligned.capacity_kw_original,rtol=1e-12,atol=1e-8)
            gains.to_parquet(directory/f'{split}_group_gain.parquet',index=False)
            frame = pd.read_parquet(directory/f'{split}.parquet')
            transformed = frame[['ts','grp','cosz']].merge(gains[['ts','grp','group_gain']],on=['ts','grp'],how='left',sort=False,validate='one_to_one')
            pd.testing.assert_frame_equal(transformed[['ts','grp']],frame[['ts','grp']])
            assert transformed.group_gain.notna().all()
            transformed['physical_haurwitz'] = haurwitz(frame.cosz.to_numpy())
            transformed['new_normalizer'] = normalizer(frame.cosz.to_numpy(),transformed.group_gain.to_numpy())
            transformed = transformed.drop(columns='cosz')
            if split=='train':
                transformed['age_days'] = (cutoff-frame.ts).dt.total_seconds()/86400
                transformed['decay'] = decay_multiplier(transformed.age_days.to_numpy(),180)
                transformed['target'] = frame.cf/transformed.new_normalizer
                transformed['sample_weight'] = transformed.new_normalizer*transformed.decay
            assert np.isfinite(transformed.iloc[:,2:].to_numpy()).all() and transformed.new_normalizer.ge(.05).all()
            transformed.to_parquet(directory/('training_transform.parquet' if split=='train' else 'evaluation_transform.parquet'),index=False)
        records.append({'fold':fold,'loaded_existing_coefficients':loaded,'site_records':len(fitted.sites),'global_q90':fitted.global_q90,'clear_rows':fitted.clear_rows,'coefficient_sha256':digest(path)})
    save(OUT/'coefficient_fit_receipt.json',{'utc':now(),'records':records,'training_only':True,'shared_all_seeds':True})
    paths = list((OUT/'coefficients').glob('*.json'))+[OUT/'coefficient_fit_receipt.json']
    paths += [p for fold in FOLDS for p in (OUT/'data'/fold).glob('*') if p.name.endswith(('_group_gain.parquet','_transform.parquet'))]
    save(OUT/'transform_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in paths})
