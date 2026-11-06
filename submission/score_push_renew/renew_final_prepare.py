# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: called by renew_final_run.py --prepare; no fitting or confirmation scoring.
"""Read-only reconstruction of cutoff-specific final matrices and night coverage."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen final_build contract
import pyarrow.parquet as pq
from renew_final_common import ROOT,OUT,OLD,CPU,RENEW,CUTOFFS,save,digest,decay_multiplier


def prepare() -> None:
    from final_build import enrich
    from site_features import normalizer
    from profile_features import column_mask
    base = [n for n in pq.ParquetFile(OLD/'outer_features.parquet').schema_arrow.names if n not in ('cf','energy','y','smp','k')]
    records = []
    for split,cutoff_text in CUTOFFS.items():
        cutoff = pd.Timestamp(cutoff_text,tz='Asia/Seoul')
        train = pd.read_parquet(OLD/'full_train.parquet',columns=[*base,'cf'],filters=[('ts','<=',cutoff)])
        weather = pd.read_parquet(CPU/'final/cache/train_weather.parquet',filters=[('ts','<=',cutoff)])
        stations = pd.read_parquet(CPU/'final/cache/train_stations.parquet',filters=[('ts','<=',cutoff)])
        train,rich,candidates = enrich(train,weather,stations)
        assert train.ts.max()<=cutoff and not train.duplicated(['ts','grp']).any()
        assert not {'energy','y','smp','k'} & set(train)
        names = column_mask(train,candidates)
        assert len(candidates)==904 and not {'cf','energy','y','smp','k','ts','grp'} & set(names)
        scale = normalizer(train.cosz.to_numpy())
        age = (cutoff-train.ts).dt.total_seconds().to_numpy()/86400
        decay = decay_multiplier(age,180)
        weights = train[['ts','grp']].assign(normalizer=scale,age_days=age,decay=decay,sample_weight=scale*decay,target=train.cf.to_numpy()/scale)
        assert np.isfinite(weights.iloc[:,2:].to_numpy()).all() and weights.age_days.ge(0).all()
        assert abs(weights.decay.mean()-1)<1e-12
        directory = OUT/'data'/split
        directory.mkdir(parents=True,exist_ok=True)
        train.to_parquet(directory/'train.parquet',index=False)
        weights.to_parquet(directory/'weights.parquet',index=False)
        save(directory/'features.json',{'cutoff':str(cutoff),'rich':rich,'candidates':candidates,'features':names,'train_rows':len(train),'max_train_ts':str(train.ts.max()),'mask_source':'TRAIN ONLY'})
        records.append({'kind':'training','split':split,'source':'autoresearch final full_train','projection':[*base,'cf'],'filter':['ts','<=',str(cutoff)],'rows':len(train),'max_target_ts':str(train.ts.max()),'selected_features':len(names)})
    ranges = {'recent':('2024-06-01','2025-03-01'),'march_may':('2025-03-01','2025-06-01'),'test':('2025-06-01',None)}
    protocol = json.loads((OUT/'protocol.json').read_text())
    assignment = json.loads((ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json').read_text())
    for split,(start_text,end_text) in ranges.items():
        start = pd.Timestamp(start_text,tz='Asia/Seoul')
        filters = [('ts','>',start)]
        if end_text:
            filters.append(('ts','<=',pd.Timestamp(end_text,tz='Asia/Seoul')))
        is_test = split=='test'
        side = 'test' if is_test else 'train'
        source = OLD/('test_features.parquet' if is_test else 'outer_features.parquet')
        frame = pd.read_parquet(source,columns=base,filters=filters)
        weather = pd.read_parquet(CPU/'final/cache'/f'{side}_weather.parquet',filters=filters)
        stations = pd.read_parquet(CPU/'final/cache'/f'{side}_stations.parquet',filters=filters)
        frame,rich,candidates = enrich(frame,weather,stations)
        assert not {'cf','energy','y','smp','k'} & set(frame)
        assert not frame.duplicated(['ts','grp']).any() and start<frame.ts.min()
        base_path = CPU/'final'/('test_predictions.parquet' if is_test else 'outer_predictions.parquet')
        cpu = pd.read_parquet(base_path,columns=['ts','grp','p_candidate'],filters=filters).rename(columns={'p_candidate':'p_cpu'})
        rows = pd.read_parquet(ROOT/protocol['night_cache']/f'feat_{side}.parquet',columns=['ts','site_id','night'],filters=filters)
        rows['grp'] = rows.site_id.map(assignment)
        assert rows.grp.notna().all() and not rows.duplicated(['ts','site_id']).any()
        coverage = rows.groupby(['ts','grp'],as_index=False).night.all()
        coverage = cpu[['ts','grp']].merge(coverage,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert coverage._merge.eq('both').all()
        expected = coverage.loc[~coverage.night,['ts','grp']].sort_values(['ts','grp']).reset_index(drop=True)
        pd.testing.assert_frame_equal(frame[['ts','grp']].sort_values(['ts','grp']).reset_index(drop=True),expected)
        night_check = cpu.merge(coverage[['ts','grp','night']],on=['ts','grp'],validate='one_to_one')
        assert night_check.loc[night_check.night,'p_cpu'].eq(0).all()
        directory = OUT/'data'/split
        directory.mkdir(parents=True,exist_ok=True)
        frame.to_parquet(directory/'evaluation.parquet',index=False)
        cpu.to_parquet(directory/'cpu_base.parquet',index=False)
        coverage.drop(columns='_merge').to_parquet(directory/'coverage.parquet',index=False)
        records.append({'kind':'evaluation','split':split,'source':str(source.relative_to(ROOT)),'projection':base,'filters':[(k,op,str(value)) for k,op,value in filters],'daylight_rows':len(frame),'full_rows':len(cpu),'target_columns_read':False,'night_zero_exact':True})
    rebuilt = pd.read_parquet(OUT/'data/march_may/evaluation.parquet')
    existing = pd.read_parquet(CPU/'deployment_check/evaluation_features.parquet')
    pd.testing.assert_frame_equal(rebuilt[existing.columns],existing)
    fresh = pd.read_parquet(CPU/'deployment_check/frozen_predictions.parquet',columns=['ts','grp','p_candidate']).rename(columns={'p_candidate':'p_cpu'})
    pd.testing.assert_frame_equal(fresh[['ts','grp']],pd.read_parquet(OUT/'data/march_may/cpu_base.parquet',columns=['ts','grp']))
    fresh.to_parquet(OUT/'data/latest/cpu_base.parquet',index=False)
    save(OUT/'evidence/read_receipts.json',records)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
