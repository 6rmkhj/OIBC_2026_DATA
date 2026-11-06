# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Exact daylight coverage aggregation, retaining station/model lineage."""
from cloud_common import ROOT, OUT, RAW, DATA, FOLDS, PROVIDERS, CUTOFFS, save, digest, block_indices, expected_cutoffs
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen profile semantics

def cloud_mean(rows: pd.DataFrame) -> pd.Series:
    available = rows.p_cloud.notna()
    weighted = rows.assign(weighted=rows.p_cloud*rows.capacity_kw,available_capacity=rows.capacity_kw.where(available))
    totals = weighted.groupby(['ts','grp'])[['weighted','available_capacity']].sum(min_count=1)
    return totals.weighted/totals.available_capacity

def station_predictions(provider: str, cutoff: pd.Timestamp, evaluation: bool) -> pd.DataFrame:
    station = f'{provider}_station'
    if evaluation:
        result = pd.read_parquet(OUT/'auxiliary'/provider/cutoff.strftime('%Y-%m-%d')/'predictions.parquet')
        assert result.model_cutoff.eq(cutoff).all() and result.ts.gt(cutoff).all()
        return result
    first = pd.Timestamp(CUTOFFS[0],tz='Asia/Seoul')
    warmup = pd.read_parquet(OUT/'data'/f'{provider}_forecast.parquet',columns=[station,'ts',f'base_{provider}_cloud'],filters=[('ts','<=',first)])
    warmup = warmup.rename(columns={f'base_{provider}_cloud':'p_cloud'}).assign(model_cutoff=pd.NaT,warmup=1)
    warmup['p_cloud'] = warmup.p_cloud.clip(0,100)
    warmup['model_cutoff'] = pd.Series(pd.NaT,index=warmup.index,dtype='datetime64[ns, Asia/Seoul]')
    blocks = [warmup]
    for index,date in enumerate(CUTOFFS):
        start = pd.Timestamp(date,tz='Asia/Seoul')
        if start>=cutoff:
            break
        end = min(pd.Timestamp(CUTOFFS[index+1],tz='Asia/Seoul'),cutoff)
        part = pd.read_parquet(OUT/'auxiliary'/provider/date/'predictions.parquet',filters=[('ts','<=',end)]).drop(columns='p_raw')
        assert (block_indices(part.ts)==index).all()
        blocks.append(part)
    result = pd.concat(blocks,ignore_index=True)
    assert not result.duplicated([station,'ts']).any()
    assert result.ts.le(cutoff).all()
    return result

def aggregate() -> None:
    from profile_features import profile
    protocol = json.loads((OUT/'protocol.json').read_text())
    sites = pd.read_csv(RAW/'sites.csv')
    assignment = json.loads((ROOT/protocol['assignment_source']).read_text())
    for fold in FOLDS:
        spec = json.loads((DATA/fold/'features.json').read_text())
        cutoff = pd.Timestamp(spec['cutoff'])
        for kind in ('train','evaluation'):
            destination = OUT/'data'/fold
            destination.mkdir(exist_ok=True)
            keys = pd.read_parquet(DATA/fold/f'{kind}.parquet',columns=['ts','grp'])
            rows = pd.read_parquet(ROOT/protocol['night_source'],columns=['site_id','ts','night','capacity_kw'],filters=[('ts','>=',keys.ts.min()),('ts','<=',keys.ts.max()),('night','==',False)])
            rows['grp'] = rows.site_id.map(assignment)
            rows = rows.merge(keys,on=['ts','grp'],how='inner',validate='many_to_one').merge(sites[['site_id','wa_station','wb_station']],on='site_id',validate='many_to_one')
            assert not rows.duplicated(['site_id','ts']).any()
            result = keys.copy()
            lineage = []
            for provider in PROVIDERS:
                station = f'{provider}_station'
                predictions = station_predictions(provider,cutoff,kind=='evaluation')
                needed = rows[[station,'ts']].drop_duplicates()
                used = needed.merge(predictions,on=[station,'ts'],how='left',validate='one_to_one',indicator=True)
                assert used._merge.eq('both').all()
                pd.testing.assert_series_equal(pd.to_datetime(used.model_cutoff).reset_index(drop=True).astype('datetime64[ns, Asia/Seoul]'),expected_cutoffs(used.ts,cutoff,kind=='evaluation'),check_names=False)
                used.drop(columns='_merge').to_parquet(destination/f'{kind}_{provider}_lineage.parquet',index=False)
                enriched = rows.merge(used.drop(columns='_merge'),on=[station,'ts'],how='left',validate='many_to_one')
                assert enriched.warmup.notna().all()
                levels = sorted(sites[station].unique())
                wide = profile(enriched,station,['p_cloud'],levels,f'aux_{provider}')
                contributions = [f'aux_{provider}_{level}_p_cloud' for level in levels]
                weighted = cloud_mean(enriched)
                wide = wide.merge(weighted.rename(f'aux_{provider}_mean').reset_index(),on=['ts','grp'],validate='one_to_one')
                flags = enriched.groupby(['ts','grp'],as_index=False).warmup.max().rename(columns={'warmup':f'aux_{provider}_warmup'})
                result = result.merge(wide[['ts','grp',*contributions,f'aux_{provider}_mean']],on=['ts','grp'],how='left',validate='one_to_one').merge(flags,on=['ts','grp'],how='left',validate='one_to_one')
                lineage.append({'provider':provider,'rows':len(used),'sha256':digest(destination/f'{kind}_{provider}_lineage.parquet')})
            pd.testing.assert_frame_equal(result[['ts','grp']],keys)
            result.to_parquet(destination/f'{kind}_features.parquet',index=False)
            save(destination/f'{kind}_lineage.json',{'rows':len(result),'features':list(result.columns[2:]),'station_lineage':lineage,'feature_sha256':digest(destination/f'{kind}_features.parquet'),'coverage_columns':['site_id','ts','night','capacity_kw']})

