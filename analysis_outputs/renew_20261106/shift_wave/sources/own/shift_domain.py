# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: released shift_run.py serially launches shift_domain.py FOLD SPLIT.
"""One balanced domain classifier and held-source-only density predictions."""
import json
import sys
import time
import warnings
from pathlib import Path
from shift_common import OUT,FOLDS,DOMAIN_PARAMS,environment,install_frozen,require_release,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    require_release()
    import joblib
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen held-source keys and sidecars
    import sklearn
    from sklearn.linear_model import LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits,threadpool_info
    expected = json.loads((OUT/'evidence/environment.json').read_text())
    assert sklearn.__version__==expected['sklearn_version']
    for path,sha in expected['installed_sources_sha256'].items():
        assert digest(Path(path))==sha
    fold,split_text = sys.argv[1:]
    assert fold in FOLDS and split_text in ('0','1','2')
    split = int(split_text)
    directory = OUT/'domain_trials'/fold/f'split{split}'
    assert directory.is_dir() and not (directory/'classifier.joblib').exists(),'No repeated fit'
    with threadpool_limits(limits=16):
        assert all(p['num_threads']==16 for p in threadpool_info())
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data = OUT/'data'/fold
        source = np.load(data/'domain_train_matrix.npy',allow_pickle=False)
        target = np.load(data/'domain_evaluation_matrix.npy',allow_pickle=False)
        partitions = pd.read_parquet(data/'domain_fold.parquet')
        preprocessor = json.loads((data/'preprocessing.json').read_text())
        held = partitions.domain_fold.eq(split).to_numpy()
        assert held.any() and (~held).any()
        assert set(partitions.loc[held,'date_ordinal']).isdisjoint(partitions.loc[~held,'date_ordinal'])
        x = np.concatenate([source[~held],target])
        y = np.concatenate([np.zeros(int((~held).sum()),dtype=np.int64),np.ones(len(target),dtype=np.int64)])
        save(directory/'config.json',{'fold':fold,'split':split,'parameters':DOMAIN_PARAMS,'domain_columns':preprocessor['columns'],'source_fit_rows':int((~held).sum()),'held_source_rows':int(held.sum()),'future_fit_rows':len(target),'domain_priors':'balanced class weights','prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'input_sha256':{name:digest(data/name) for name in ('domain_train_matrix.npy','domain_evaluation_matrix.npy','domain_fold.parquet','preprocessing.json')},'generation_labels_accessed':False,'future_energy_accessed':False})
        started = time.monotonic()
        classifier = LogisticRegression(**DOMAIN_PARAMS)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            classifier.fit(x,y)
        warning_records = [{'category':w.category.__name__,'message':str(w.message)} for w in caught]
        for warning in caught:
            warnings.showwarning(warning.message,warning.category,warning.filename,warning.lineno)
        save(directory/'convergence.json',{'warnings':warning_records,'n_iter':classifier.n_iter_.tolist(),'max_iter':1000,'retuned':False})
        assert not any(issubclass(w.category,ConvergenceWarning) for w in caught),'No convergence retry or retuning'
        assert classifier.classes_.tolist()==[0,1]
        logit = classifier.decision_function(source[held])
        assert np.isfinite(logit).all()
        joblib.dump({'classifier':classifier,'preprocessing':preprocessor},directory/'classifier.joblib')
        saved = joblib.load(directory/'classifier.joblib')
        replay = saved['classifier'].decision_function(source[held])
        assert np.array_equal(logit.view(np.uint64),replay.view(np.uint64)) and saved['preprocessing']==preprocessor
        partitions.loc[held,['ts','grp','domain_fold']].assign(row_index=np.flatnonzero(held),logit=logit)[['row_index','ts','grp','domain_fold','logit']].to_parquet(directory/'oof.parquet',index=False)
        save(directory/'replay.json',{'passed':True,'bitwise_exact':True,'held_rows':len(logit),'classifier_sha256':digest(directory/'classifier.joblib'),'oof_sha256':digest(directory/'oof.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'new_model_fits':1,'new_domain_fits':1,'new_generation_fits':0,'warnings':warning_records})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'classifier_sha256':digest(directory/'classifier.joblib'),'new_model_fits':1,'new_domain_fits':1})
        print('SHIFT DOMAIN COMPLETE',fold,split,flush=True)

def combine_weights() -> None:
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact ordered OOF-to-generation-key join
    from shift_math import density_weights
    for fold in FOLDS:
        data = OUT/'data'/fold
        partitions = pd.read_parquet(data/'domain_fold.parquet')
        oof = pd.concat([pd.read_parquet(OUT/'domain_trials'/fold/f'split{k}'/'oof.parquet') for k in (0,1,2)],ignore_index=True).sort_values('row_index').reset_index(drop=True)
        np.testing.assert_array_equal(oof.row_index,np.arange(len(partitions)))
        pd.testing.assert_frame_equal(oof[['ts','grp','domain_fold']],partitions[['ts','grp','domain_fold']],check_exact=True)
        base = pd.read_parquet(data/'training_transform.parquet')
        pd.testing.assert_frame_equal(base[['ts','grp']],partitions[['ts','grp']],check_exact=True)
        ratio,modifier,weight = density_weights(oof.logit.to_numpy(),base.sample_weight.to_numpy())
        oof.assign(ratio=ratio,modifier=modifier,base_weight=base.sample_weight.to_numpy(),sample_weight=weight).to_parquet(data/'domain_weights.parquet',index=False)
    files = [p for p in (OUT/'domain_trials').rglob('*') if p.is_file()]
    files += [OUT/'data'/fold/'domain_weights.parquet' for fold in FOLDS]
    save(OUT/'weights_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in files})

if __name__=='__main__':
    main()
