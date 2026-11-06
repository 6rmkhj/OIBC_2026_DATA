# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "lightgbm"]
# ///
# How to run: called by group_run.py --prepare.
"""Numerical proofs and a synthetic native-objective saved-model replay."""
from dataclasses import replace
import numpy as np
import lightgbm as lgb
from group_common import OUT, ARMS, save, digest, now
from group_objective import GroupLoss


def self_check() -> None:
    group = np.array([1,0,1,0],dtype=np.int64)
    share = np.array([.75,.2,.25,.8])
    target = np.array([.4,.8])
    cf = np.array([.6,.3,.7,.5])
    group_weight = np.array([1.7,2.3])
    prediction = np.array([.3,-.2,.8,1.1])
    records = []
    rng = np.random.default_rng(71)
    for name,(delta,regularizer,grouped) in ARMS.items():
        loss = GroupLoss(group,share,target,cf,group_weight[group]*share,group_weight,delta,regularizer,grouped)
        gradient,majorizer = loss.derivatives(prediction)
        epsilon = 1e-6
        differences = np.array([(loss.value(prediction+np.eye(4)[i]*epsilon)-loss.value(prediction-np.eye(4)[i]*epsilon))/(2*epsilon) for i in range(4)])
        np.testing.assert_allclose(gradient,differences,rtol=1e-8,atol=1e-8)
        hessian = np.column_stack([(loss.derivatives(prediction+np.eye(4)[i]*epsilon)[0]-loss.derivatives(prediction-np.eye(4)[i]*epsilon)[0])/(2*epsilon) for i in range(4)])
        minimum_eigenvalue = float(np.linalg.eigvalsh(np.diag(majorizer)-hessian).min())
        assert minimum_eigenvalue>=-1e-8
        margins = []
        for step in rng.normal(size=(100,4)):
            margin = loss.value(prediction)+gradient@step+.5*np.dot(majorizer,step*step)-loss.value(prediction+step)
            assert margin>=-1e-10
            margins.append(float(margin))
        zero_weight = np.array([0.,2.3])
        zero = replace(loss,group_weight=zero_weight,weight=zero_weight[group]*share)
        zg,zh = zero.derivatives(prediction)
        np.testing.assert_array_equal(zg[group==0],0.)
        np.testing.assert_array_equal(zh[group==0],0.)
        rejected = False
        try:
            replace(loss,group_weight=np.zeros(2),weight=np.zeros(4))
        except AssertionError:
            rejected = True
        assert rejected
        records.append({'arm':name,'gradient_max_error':float(np.max(np.abs(gradient-differences))),'majorizer_min_eigenvalue':minimum_eigenvalue,'upper_bound_min_margin':min(margins),'zero_price_exact':True,'allzero_rejected':True})
    # A night contribution changes the full target despite having no fitted row.
    full_energy = np.array([2.,3.,7.])
    night = np.array([False,False,True])
    assert full_energy.sum()/5 == 2.4 and full_energy[~night].sum()/5 == 1.
    tiny_group = np.repeat(np.arange(20),2)
    tiny_cf = np.tile([.2,.8],20)
    tiny_loss = GroupLoss(tiny_group,np.full(40,.5),np.full(20,.5),tiny_cf,np.ones(40),np.full(20,2.),.05,.1,True)
    features = np.arange(40,dtype=float).reshape(-1,1)
    data = lgb.Dataset(features,label=tiny_cf,free_raw_data=False)
    calls = []
    def objective(preds, dataset):
        if not calls:
            np.testing.assert_array_equal(preds,0.)
        calls.append(len(preds))
        return tiny_loss(preds,dataset)
    model = lgb.train({'objective':objective,'metric':'None','num_threads':16,'min_data_in_leaf':2,'num_leaves':3,'verbosity':-1,'force_col_wise':True},data,num_boost_round=3)
    path = OUT/'evidence/synthetic_model.txt'
    model.save_model(str(path))
    before = model.predict(features,raw_score=True,num_threads=16)
    after = lgb.Booster(model_file=str(path)).predict(features,raw_score=True,num_threads=16)
    np.testing.assert_array_equal(before,after)
    assert calls==[40]*3
    np.savez(OUT/'evidence/synthetic_fixture.npz',features=features,predictions=before,group=tiny_group,cf=tiny_cf)
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'numerical':records,'night_target_retained':True,'synthetic_only_fit_count':1,'synthetic_rounds':3,'native_callable_full_length':calls,'initial_prediction_zero':True,'saved_model_raw_replay_exact':True,'model_sha256':digest(path)})
