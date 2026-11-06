# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "catboost", "lightgbm", "threadpoolctl"]
# ///
"""Cloud-wave constants and frozen scientific/resource helpers."""
from pathlib import Path
import json
import sys
from typing import Final
from temporal_common import ROOT, DATA, PARAMS, FOLDS, decay_multiplier, signed_mean, ensure_terminal
import gpu_common
from gpu_common import digest, save, now, configure, resource, child_identity

OUT: Final = ROOT/'analysis_outputs/renew_20261105/cloud_wave'
RAW: Final = ROOT/'handover 2/01_participant_dataset'
TEMPORAL: Final = ROOT/'analysis_outputs/renew_20261105/recency_wave'
CUTOFFS: Final = ('2021-06-01','2021-12-01','2022-06-01','2022-12-01','2023-06-01','2023-12-01','2024-06-01')
ARMS: Final = ('means','profiles')
PROVIDERS: Final = ('wa','wb')
REFERENCE: Final = {'primary':12.033226215978063,'recent':11.059225184100658}
AUX_PARAMS: Final = {'loss_function':'MAE','depth':6,'iterations':1000,'learning_rate':.05,'l2_leaf_reg':3,'border_count':128,'boosting_type':'Plain','random_seed':0,'task_type':'GPU','devices':'0','thread_count':16,'gpu_ram_part':.9,'nan_mode':'Min','verbose':200,'allow_writing_files':True,'save_snapshot':True,'snapshot_interval':30}

def install_frozen() -> None:
    gpu_common.OUT = OUT
    sys.meta_path.insert(0,gpu_common.FrozenImports())
    protocol = json.loads((OUT/'protocol.json').read_text())
    records = protocol['own_sources'].copy()
    amendment = OUT/'source_amendment.json'
    if amendment.exists():
        change = json.loads(amendment.read_text())
        assert digest(OUT/'protocol.json')==change['original_protocol_sha256']
        records.update(change['own_sources'])
    for name,record in records.items():
        assert digest(ROOT/record['original']) == record['sha256']
        assert digest(OUT/record.get('snapshot','sources/own/'+name)) == record['sha256']

def block_indices(times):
    """Boundary timestamps belong to the preceding strict-forward block."""
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- existing scientific interfaces
    cutoffs = pd.DatetimeIndex(CUTOFFS,tz='Asia/Seoul')
    return np.searchsorted(cutoffs.asi8,pd.DatetimeIndex(times).asi8,side='left')-1

def observed(provider: str, cutoff: str):
    """Push the one-day embargo into the observation read itself."""
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- bounded parquet/helper interface
    upper = pd.Timestamp(cutoff,tz='Asia/Seoul')-pd.Timedelta(days=1)
    names = [f'{provider}_station','ts',f'{provider}_cloud']
    rows = pd.read_parquet(RAW/'train'/f'observed_{provider}.parquet',columns=names,filters=[('ts','<=',upper)])
    valid = valid_cloud(rows[names[-1]])
    receipt = {'read_columns':names,'read_filter_max':str(upper),'read_rows':len(rows),'invalid_excluded':int((~valid).sum()),'valid_rows':int(valid.sum()),'label_max':str(rows.loc[valid,'ts'].max()),'source_sha256':digest(RAW/'train'/f'observed_{provider}.parquet')}
    retained = rows.loc[valid].reset_index(drop=True)
    duplicated = retained.duplicated(names[:2],keep=False)
    receipt['duplicate_rows'] = int(duplicated.sum())
    receipt['duplicate_keys'] = len(retained.loc[duplicated,names[:2]].drop_duplicates())
    receipt['conflicting_keys'] = int((retained.loc[duplicated].groupby(names[:2])[names[-1]].nunique()>1).sum())
    return retained, receipt

def valid_cloud(values):
    import numpy as np
    return np.isfinite(values) & values.between(0,100)


def expected_cutoffs(times, cutoff, evaluation: bool):
    import pandas as pd  # noqa: PANDAS_OK -- exact timestamp lineage
    if evaluation:
        return pd.Series(cutoff,index=range(len(times)),dtype='datetime64[ns, Asia/Seoul]')
    indices = block_indices(times)
    return pd.Series([pd.NaT if index<0 else pd.Timestamp(CUTOFFS[index],tz='Asia/Seoul') for index in indices],dtype='datetime64[ns, Asia/Seoul]')


