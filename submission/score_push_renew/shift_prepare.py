# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: shift_run.py --prepare; no classifier or generation fits.
"""Verified generation copies and label-free train-only domain preprocessing."""
import inspect
import json
import shutil
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- unchanged frozen scientific data contracts
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import _logistic
from shift_common import OUT,SOURCE,FOLDS,DOMAIN_COLUMNS,GENERATION_FILES,save,digest
from shift_math import domain_matrix,preprocess,day_folds

def prepare() -> None:
    from site_features import normalizer
    assert json.loads((SOURCE/'independent_check.json').read_text())['status']=='PASS'
    for path,sha in json.loads((SOURCE/'terminal_manifest.json').read_text(encoding='utf-8-sig')).items():
        assert digest(SOURCE/path)==sha,path
    prior = json.loads((SOURCE/'evidence/environment.json').read_text())
    native = Path(lgb.__file__).parent/'bin/lib_lightgbm.dll'
    assert lgb.__version__==prior['lightgbm_version']=='4.7.0' and digest(native)==prior['native_sha256']
    assert sklearn.__version__=='1.9.1'
    installed = [Path(lgb.__file__).parent/name for name in ('basic.py','sklearn.py','engine.py')]+[Path(_logistic.__file__)]
    save(OUT/'evidence/environment.json',{'lightgbm_version':lgb.__version__,'native_library':str(native),'native_sha256':digest(native),'sklearn_version':sklearn.__version__,'classifier_signature':str(inspect.signature(LogisticRegression)),'installed_sources_sha256':{str(p):digest(p) for p in installed},'numpy_version':np.__version__,'domain_reference_sha256':digest(OUT/'evidence/domain_reference.txt'),'new_dependencies_installed':False,'real_domain_fits':0,'real_generation_fits':0})
    receipts = []
    for fold,(cutoff_text,_) in FOLDS.items():
        source = SOURCE/'data'/fold
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        for name in GENERATION_FILES:
            shutil.copyfile(source/name,directory/name)
            assert digest(source/name)==digest(directory/name)
        source_inputs = pd.read_parquet(source/'train.parquet',columns=DOMAIN_COLUMNS)
        future_inputs = pd.read_parquet(source/'evaluation.parquet',columns=DOMAIN_COLUMNS)
        train_values,future_values = domain_matrix(source_inputs),domain_matrix(future_inputs)
        train_matrix,future_matrix,preprocessor = preprocess(train_values,future_values)
        keys = pd.read_parquet(source/'train.parquet',columns=['ts','grp'])
        partitions = day_folds(keys)
        assert set(partitions.domain_fold)=={0,1,2}
        assert partitions.groupby('date_ordinal').domain_fold.nunique().eq(1).all()
        cutoff = pd.Timestamp(cutoff_text,tz='Asia/Seoul')
        evaluation_keys = pd.read_parquet(source/'evaluation.parquet',columns=['ts','grp'])
        assert keys.ts.max()<=cutoff<evaluation_keys.ts.min()
        scalar = pd.read_parquet(source/'train.parquet',columns=['ts','grp','cf','cosz'])
        transform = pd.read_parquet(source/'training_transform.parquet')
        pd.testing.assert_frame_equal(keys,transform[['ts','grp']],check_exact=True)
        n = normalizer(scalar.cosz.to_numpy())
        decay = np.exp2(-((cutoff-scalar.ts).dt.total_seconds().to_numpy()/86400)/180)
        np.testing.assert_array_equal(transform.target_normalized,scalar.cf.to_numpy()/n)
        np.testing.assert_array_equal(transform.sample_weight,n*(decay/decay.mean()))
        assert np.isfinite(transform.sample_weight).all() and transform.sample_weight.gt(0).all()
        source_inputs.to_parquet(directory/'domain_train_inputs.parquet',index=False)
        future_inputs.to_parquet(directory/'domain_evaluation_inputs.parquet',index=False)
        np.save(directory/'domain_train_matrix.npy',train_matrix,allow_pickle=False)
        np.save(directory/'domain_evaluation_matrix.npy',future_matrix,allow_pickle=False)
        save(directory/'preprocessing.json',preprocessor)
        partitions.to_parquet(directory/'domain_fold.parquet',index=False)
        receipts.append({'fold':fold,'train_rows':len(keys),'evaluation_rows':len(evaluation_keys),'domain_columns':DOMAIN_COLUMNS,'matrix_dtype':str(train_matrix.dtype),'train_shape':list(train_matrix.shape),'evaluation_shape':list(future_matrix.shape),'source_nan_count':int(np.isnan(train_values).sum()),'future_nan_count':int(np.isnan(future_values).sum()),'base_weight_sum':float(transform.sample_weight.sum()),'day_partition_rows':{str(k):int(partitions.domain_fold.eq(k).sum()) for k in (0,1,2)},'all8_generation_files_byte_identical':True,'target_base_weight_reconstructed_exact':True,'generation_labels_in_domain_inputs':False,'provided_future_covariates_transductive':True,'future_energy_accessed':False,'real_domain_fits':0,'real_generation_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
    for name in ('environment.json','domain_reference.txt','read_receipts.json','selfchecks.json'):
        manifest['evidence/'+name] = digest(OUT/'evidence'/name)
    save(OUT/'prepared_manifest.json',manifest)
