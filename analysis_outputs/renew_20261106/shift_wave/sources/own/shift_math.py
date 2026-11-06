# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: shift_run.py --prepare runs synthetic checks without any model fit.
"""Train-only domain preprocessing, held-day folds and bounded density weights."""
import json
from typing import TypedDict
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing frozen key/calibration contracts
from shift_common import OUT,DOMAIN_COLUMNS

class Preprocessor(TypedDict):
    columns: list[str]
    median: list[float]
    mean: list[float]
    scale: list[float]
    training_rows: int
    clip: list[float]

def domain_matrix(frame: pd.DataFrame) -> np.ndarray:
    assert list(frame)==DOMAIN_COLUMNS
    values = frame.to_numpy(dtype=np.float64)
    assert not np.isinf(values).any()
    return values

def preprocess(train: np.ndarray, future: np.ndarray) -> tuple[np.ndarray,np.ndarray,Preprocessor]:
    assert train.ndim==future.ndim==2 and train.shape[1]==future.shape[1]==len(DOMAIN_COLUMNS)
    assert np.isfinite(train).any(axis=0).all() and not np.isinf(train).any() and not np.isinf(future).any()
    median = np.nanmedian(train,axis=0)
    imputed = np.where(np.isnan(train),median,train)
    mean = imputed.mean(axis=0)
    scale = imputed.std(axis=0,ddof=0)
    scale[scale==0] = 1.
    source = np.clip((imputed-mean)/scale,-8.,8.)
    target = np.clip((np.where(np.isnan(future),median,future)-mean)/scale,-8.,8.)
    assert np.isfinite(source).all() and np.isfinite(target).all()
    return source,target,{'columns':DOMAIN_COLUMNS,'median':median.tolist(),'mean':mean.tolist(),'scale':scale.tolist(),'training_rows':len(train),'clip':[-8.,8.]}

def day_folds(keys: pd.DataFrame) -> pd.DataFrame:
    assert list(keys)==['ts','grp'] and not keys.duplicated(['ts','grp']).any()
    ordinal = keys.ts.dt.tz_convert('Asia/Seoul').dt.date.map(lambda day:day.toordinal()).to_numpy(dtype=np.int64)
    return keys.assign(date_ordinal=ordinal,domain_fold=ordinal%3)

def density_weights(logit: np.ndarray, base: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    assert logit.shape==base.shape and np.isfinite(logit).all() and np.isfinite(base).all() and (base>0).all()
    ratio = np.exp(logit)
    modifier = np.sqrt(np.clip(ratio,.25,4.))
    weight = base*modifier*base.sum(dtype=np.float64)/(base*modifier).sum(dtype=np.float64)
    assert np.isfinite(ratio).all() and np.isfinite(weight).all() and (weight>0).all()
    np.testing.assert_allclose(weight.sum(dtype=np.float64),base.sum(dtype=np.float64),rtol=2e-15,atol=1e-12)
    return ratio,modifier,weight

def component(frame: pd.DataFrame, predictions: np.ndarray) -> pd.DataFrame:
    from cal_math import Calibration,Factor,apply
    assert list(frame)==['ts','grp','wa_temp','extra_wa_snow','static_capacity']
    assert predictions.shape==(3,len(frame)) and np.isfinite(predictions).all()
    original = json.loads((OUT/'original_weather_coefficients.json').read_text(encoding='utf-8'))['factors']
    fitted = Calibration(tuple(Factor(**r) for r in original['temperature']),Factor(**original['snow']),Factor(**original['conditional_snow']))
    mean = np.mean(predictions,axis=0,dtype=np.float64)
    clipped = np.clip(mean,0,frame.static_capacity.to_numpy(dtype=np.float64))
    weather = apply(frame.assign(p_reference=clipped),fitted,'temperature_then_snow').p.to_numpy()
    return frame.assign(signed_seed_mean=mean,p_component=clipped,p_weather=weather,p_new=weather)



def self_check() -> list[str]:
    base = np.array([1.,2.,3.])
    ratio,modifier,weight = density_weights(np.zeros(3),base)
    np.testing.assert_array_equal(ratio,np.ones(3))
    np.testing.assert_array_equal(modifier,np.ones(3))
    np.testing.assert_allclose(weight,base,rtol=1e-15)
    ratio,modifier,weight = density_weights(np.array([-20.,0.,20.]),base)
    np.testing.assert_array_equal(modifier,[.5,1.,2.])
    np.testing.assert_allclose(weight,np.array([.5,2.,6.])*6/8.5,rtol=1e-15)
    assert abs(weight.sum()-6)<1e-14
    train = np.tile(np.array([0.,2.,np.nan,4.])[:,None],(1,len(DOMAIN_COLUMNS)))
    train[:,-1] = 7.
    future = np.vstack([np.full(len(DOMAIN_COLUMNS),100.),np.full(len(DOMAIN_COLUMNS),np.nan)])
    source,target,stats = preprocess(train,future)
    np.testing.assert_allclose(source[:,0],[-np.sqrt(2),0,0,np.sqrt(2)],rtol=1e-15)
    assert stats['median'][0]==stats['mean'][0]==2. and stats['scale'][-1]==1.
    np.testing.assert_array_equal(target[0],np.full(len(DOMAIN_COLUMNS),8.))
    np.testing.assert_array_equal(target[1],np.zeros(len(DOMAIN_COLUMNS)))
    _,_,altered = preprocess(train,np.full_like(future,-1000.))
    assert stats==altered
    keys = pd.DataFrame({'ts':pd.date_range('2024-01-01 00:00',periods=6,freq='12h',tz='Asia/Seoul'),'grp':['A','B']*3})
    folds = day_folds(keys)
    assert folds.groupby('date_ordinal').domain_fold.nunique().eq(1).all()
    assert set(folds.domain_fold)=={0,1,2}
    for split in (0,1,2):
        assert set(folds.loc[folds.domain_fold==split,'date_ordinal']).isdisjoint(folds.loc[folds.domain_fold!=split,'date_ordinal'])
    raw = pd.DataFrame(train,columns=DOMAIN_COLUMNS)
    np.testing.assert_array_equal(domain_matrix(raw),train)
    rejected = False
    try:
        domain_matrix(raw.assign(cf=99.,y=99.,smp=99.,k=99.))
    except AssertionError:
        rejected = True
    assert rejected
    frame = pd.DataFrame({'ts':pd.date_range('2024-01-01 10:00',periods=3,freq='h',tz='Asia/Seoul'),'grp':['G1']*3,'wa_temp':[10.,10.,np.nan],'extra_wa_snow':[0.,0.,0.],'static_capacity':[100.]*3})
    predictions = np.array([[-12.,150.,0.],[9.,180.,0.],[9.,120.,0.]])
    result = component(frame,predictions)
    assert result.p_component.tolist()==[2.,100.,0.] and result.p_new.iloc[-1]==0.
    return ['equal_odds_identity','log_odds_clip_sqrt','base_mass_preserved','train_only_median_mean_population_std','constant_std_one','standardized_clip8','future_cannot_change_preprocessor','same_KSTday_group_partition','held_source_dates_disjoint','domain_label_whitelist','signed_mean_before_clip_weather_night']
