# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: gpu_run.py --prepare before any fit.
"""Reuse frozen fold matrices and join strictly training-only monetary weights."""
from gpu_common import ROOT, OLD, PRIOR, OUT, FOLDS, save, digest
import json
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve immutable GPU matrix ordering


def prepare() -> None:
    protocol=json.loads((OUT/'protocol.json').read_text())
    price_path=ROOT/protocol['price_source']
    for fold in FOLDS:
        directory=OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        for source in (PRIOR/'data'/fold).glob('*'):
            if source.is_file():
                shutil.copyfile(source,directory/source.name)
        features=json.loads((directory/'features.json').read_text())
        cutoff=pd.Timestamp(features['cutoff'])
        train=pd.read_parquet(directory/'train.parquet',columns=['ts','grp'],filters=[('ts','<=',cutoff)])
        source=OLD/('cache/train.parquet' if fold=='primary' else 'recent/cache/train.parquet')
        capacity=pd.read_parquet(source,columns=['ts','grp','capacity_kw'],filters=[('ts','<=',cutoff)])
        prices=pd.read_parquet(price_path,columns=['ts','smp','k'],filters=[('ts','<=',cutoff)])
        np.testing.assert_array_equal(prices.k,np.where(prices.ts.dt.hour.between(11,15),3,1))
        money=train.merge(capacity,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert money._merge.eq('both').all() and len(money)==len(train)
        money=money.drop(columns='_merge').merge(prices,on='ts',how='left',validate='many_to_one')
        money=train.merge(money,on=['ts','grp'],how='left',validate='one_to_one')
        assert np.isfinite(money[['capacity_kw','smp','k']]).all().all() and money.ts.max()<=cutoff
        assert money[['capacity_kw','smp','k']].gt(0).all().all()
        cost=money.capacity_kw*money.smp*money.k
        mean=float(cost.mean())
        money['normalized_cost']=cost/mean
        money.to_parquet(directory/'training_money.parquet',index=False)
        save(directory/'money.json',{'source':str(source.relative_to(ROOT)),'price_source':str(price_path.relative_to(ROOT)),'price_sha256':digest(price_path),'capacity_sha256':digest(source),'read_filter':[['ts','<=',str(cutoff)]],'rows':len(money),'train_max':str(money.ts.max()),'train_only_mean_capacity_smp_k':mean,'normalized_min':float(money.normalized_cost.min()),'normalized_max':float(money.normalized_cost.max()),'raw_k_matches_actual_hour':True,'feature_matrix_receives_no_price_or_target_columns':True})
        labels=pd.read_parquet(directory/'labels.parquet')
        oracle_path=ROOT/'analysis_outputs/autoresearch_20261103'/('cache/selection_labels.parquet' if fold=='primary' else 'final/outer_predictions.parquet')
        end=pd.Timestamp('2024-06-01' if fold=='primary' else '2025-03-01',tz='Asia/Seoul')
        oracle=pd.read_parquet(oracle_path,columns=['ts','grp','y','smp','k'],filters=[('ts','>',cutoff),('ts','<=',end)])
        aligned=labels.merge(oracle,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True,suffixes=('','_oracle'))
        assert aligned._merge.eq('both').all() and len(aligned)==(17568 if fold=='primary' else 13104)
        for name in ('y','smp','k'):
            np.testing.assert_array_equal(aligned[name],aligned[name+'_oracle'])
        np.testing.assert_array_equal(labels.k,np.where(labels.ts.dt.hour.between(11,15),3,1))
        assert cutoff<labels.ts.min() and labels.ts.max()<=end
        save(directory/'oracle_check.json',{'passed':True,'keys':len(labels),'source':str(oracle_path.relative_to(ROOT)),'sha256':digest(oracle_path),'filter_start':str(cutoff),'filter_end':str(end)})
