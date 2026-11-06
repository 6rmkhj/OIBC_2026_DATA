# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib"]
# ///
# How to run: incbound_run.py --prepare; no model loads, inference, fits or scoring.
"""Feature-only original preprocessing and exact TRAIN-range bounds."""
import json
import shutil
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact original preprocessing frame dtype/order
from incbound_common import OUT,DATA,MODELS,RENEW,FOLDS,digest,save
from incbound_math import training_range

def prepare() -> None:
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        names = json.loads((DATA/fold/'features.json').read_text(encoding='utf-8'))['rich']
        assert len(names)==len(set(names))==100 and not {'ts','grp','cf','energy','y','smp','k'} & set(names)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp',*names])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*names])
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        preprocessing_hashes,target_scaler_hashes = [],[]
        train_matrices,future_matrices = [],[]
        for seed in (0,1,2):
            source = MODELS/fold/'mlp_cf'/f'seed{seed}'
            config = json.loads((source/'config.json').read_text(encoding='utf-8'))
            runtime = json.loads((source/'runtime.json').read_text(encoding='utf-8'))
            assert config['features']==names and config['normalization'] is False and config['variant']=='mlp_cf'
            assert config['training_rows']==len(train) and config['prediction_rows']==len(evaluation)
            assert runtime['model_n_jobs']==1 and runtime['environment']['OPENBLAS_NUM_THREADS']=='1'
            preprocessing_hashes.append(digest(source/'input_preprocessing.joblib'))
            target_scaler_hashes.append(digest(source/'target_scaler.joblib'))
            preprocessor = joblib.load(source/'input_preprocessing.joblib')
            before = joblib.hash(preprocessor)
            train_matrices.append(preprocessor.transform(train[names]))
            future_matrices.append(preprocessor.transform(evaluation[names]))
            assert joblib.hash(preprocessor)==before
        assert len(set(preprocessing_hashes))==len(set(target_scaler_hashes))==1
        x_train,future = train_matrices[0],future_matrices[0]
        for value in train_matrices[1:]:
            np.testing.assert_array_equal(value,x_train)
        for value in future_matrices[1:]:
            np.testing.assert_array_equal(value,future)
        assert future.dtype==x_train.dtype==np.dtype('float64') and np.isfinite(future).all()
        lower,upper = training_range(x_train)
        assert np.all(lower<upper),'No training-constant dimensions expected'
        bounded = np.clip(future,lower,upper)
        below,above = future<lower,future>upper
        assert np.array_equal(bounded[~(below|above)].view(np.uint64),future[~(below|above)].view(np.uint64))
        expected = (263,273) if fold=='primary' else (43,60)
        assert (int((below|above).any(axis=1).sum()),int((below|above).sum()))==expected
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        train.to_parquet(directory/'projected_train.parquet',index=False)
        evaluation.to_parquet(directory/'projected_evaluation.parquet',index=False)
        save(directory/'features.json',{'rich':names,'train_rows':len(train),'evaluation_rows':len(evaluation),'cutoff':str(cutoff),'end':str(end),'original_preprocessing_sha256':preprocessing_hashes[0],'original_target_scaler_sha256':target_scaler_hashes[0]})
        for name,value in (('x_train',x_train),('x_evaluation_original',future),('x_evaluation_bounded',bounded)):
            np.save(directory/f'{name}.npy',value,allow_pickle=False)
        pd.DataFrame({'feature_index':range(len(names)),'feature':names,'lower':lower,'upper':upper,'below_count':below.sum(axis=0),'above_count':above.sum(axis=0),'clipped_count':(below|above).sum(axis=0)}).to_parquet(directory/'bounds.parquet',index=False)
        evaluation[['ts','grp','capacity_kw']].to_parquet(directory/'evaluation_transform.parquet',index=False)
        for name in ('labels.parquet','coverage.parquet','application_inputs.parquet'):
            source = RENEW/'mlp_wave/data'/fold/name
            shutil.copyfile(source,directory/name)
            assert digest(source)==digest(directory/name)
        receipt = {'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'features':len(names),'changed_rows':expected[0],'changed_entries':expected[1],'train_clip_bitwise_identity':True,'in_range_eval_bitwise_preserved':True,'three_preprocessors_identical_bytes_and_outputs':True,'three_target_scalers_identical_bytes':True,'preprocessor_objects_unchanged':True,'train_projection':list(train),'evaluation_projection':list(evaluation),'generation_labels_read':False,'model_loads':0,'model_inferences':0,'real_model_fits':0,'source_train_sha256':digest(DATA/fold/'train.parquet'),'source_evaluation_sha256':digest(DATA/fold/'evaluation.parquet'),'bounds_sha256':digest(directory/'bounds.parquet'),'bounded_matrix_sha256':digest(directory/'x_evaluation_bounded.npy'),'original_matrix_sha256':digest(directory/'x_evaluation_original.npy')}
        save(directory/'bounds_receipt.json',receipt)
        receipts.append(receipt)
    save(OUT/'evidence/read_receipts.json',receipts)
