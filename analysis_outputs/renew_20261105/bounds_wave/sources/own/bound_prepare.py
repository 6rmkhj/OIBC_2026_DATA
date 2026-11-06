# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: called by bound_run.py before inference.
"""Exact selected-feature TRAIN min/max bounds; TRAIN clipping is identity."""
import json
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- per-feature bound provenance table
from bound_common import MLP,OUT,FOLDS,save,digest,now

def training_range(train: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    assert train.dtype==np.dtype('float64') and np.isfinite(train).all() and train.ndim==2
    return train.min(axis=0),train.max(axis=0)

def self_check() -> list[str]:
    train = np.array([[0.,2.,7.],[1.,3.,7.],[2.,4.,7.]],dtype=np.float64)
    lower,upper = training_range(train)
    np.testing.assert_array_equal(lower,[0.,2.,7.])
    np.testing.assert_array_equal(upper,[2.,4.,7.])
    np.testing.assert_array_equal(np.clip(train,lower,upper).view(np.uint64),train.view(np.uint64))
    future = np.array([[-1.,3.,9.],[3.,9.,7.],[.5,2.5,7.]])
    np.testing.assert_array_equal(np.clip(future,lower,upper),[[0.,3.,7.],[2.,4.,7.],[.5,2.5,7.]])
    before = train.copy()
    np.clip(future*1e20,lower,upper)
    np.testing.assert_array_equal(train,before)
    np.testing.assert_array_equal(training_range(train)[0],lower)
    np.testing.assert_array_equal(training_range(train)[1],upper)
    return ['exactTRAINminmax','TRAINclippingbitidentity','finitefloat64','futureoutliersclipperfeature','inrangeunchanged','degeneraterangeidentity','futurecannotchangebounds']

def prepare() -> None:
    receipts = []
    for fold in FOLDS:
        source = MLP/'data'/fold
        train = np.load(source/'x_train.npy',mmap_mode='r',allow_pickle=False)
        future = np.load(source/'x_evaluation.npy',mmap_mode='r',allow_pickle=False)
        mask = json.loads((source/'feature_mask.json').read_text(encoding='utf-8'))
        names = mask['selected_columns']
        assert train.shape[1]==future.shape[1]==len(names)
        assert future.dtype==np.dtype('float64') and np.isfinite(future).all()
        lower,upper = training_range(train)
        identity = np.clip(train,lower,upper)
        assert np.array_equal(identity.view(np.uint64),train.view(np.uint64))
        del identity
        below = future<lower
        above = future>upper
        changed = below|above
        bounded = np.clip(future,lower,upper)
        assert bounded.dtype==np.dtype('float64') and np.isfinite(bounded).all()
        assert np.array_equal(bounded[~changed],future[~changed])
        assert (bounded>=lower).all() and (bounded<=upper).all()
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        table = pd.DataFrame({'feature_index':np.arange(len(names)),'feature':names,'lower':lower,'upper':upper,'below_count':below.sum(axis=0),'above_count':above.sum(axis=0),'clipped_count':changed.sum(axis=0)})
        table.to_parquet(directory/'bounds.parquet',index=False)
        np.save(directory/'x_evaluation_bounded.npy',bounded,allow_pickle=False)
        for name in ('labels.parquet','coverage.parquet','application_inputs.parquet'):
            shutil.copyfile(source/name,directory/name)
        record = {'fold':fold,'created_utc':now(),'source_train_sha256':digest(source/'x_train.npy'),'source_evaluation_sha256':digest(source/'x_evaluation.npy'),'feature_mask_sha256':digest(source/'feature_mask.json'),'bounded_matrix_sha256':digest(directory/'x_evaluation_bounded.npy'),'bounds_sha256':digest(directory/'bounds.parquet'),'train_rows':len(train),'evaluation_rows':len(future),'features':len(names),'dtype':'float64','train_identity_exact':True,'train_identity_bitwise':True,'changed_rows':int(changed.any(axis=1).sum()),'changed_entries':int(changed.sum()),'max_abs_original_evaluation':float(np.abs(future).max()),'max_abs_train':float(np.abs(train).max()),'new_model_fits':0,'bounds_read_labels':False}
        save(directory/'bounds_receipt.json',record)
        receipts.append(record)
    save(OUT/'evidence/bounds_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
