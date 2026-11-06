# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by refresh_run.py; self_check uses synthetic rows only.
"""The unchanged weather, hour and cloud fitting/application sequence."""
from dataclasses import dataclass
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing scalar-stage APIs
import cal_math
import hour_math
import sky_math
from refresh_common import COLUMNS

@dataclass(frozen=True,slots=True)
class Pipeline:
    weather: cal_math.Calibration
    hour: hour_math.HourFactors
    cloud: sky_math.CloudFactors

def decode(factors: dict) -> Pipeline:
    weather = factors['weather']
    return Pipeline(cal_math.Calibration(tuple(cal_math.Factor(**r) for r in weather['temperature']),cal_math.Factor(**weather['snow']),cal_math.Factor(**weather['conditional_snow'])),hour_math.HourFactors(tuple(cal_math.Factor(**r) for r in factors['hour']['hours'])),sky_math.CloudFactors(tuple(cal_math.Factor(**r) for r in factors['cloud']['clouds'])))

def apply_pipeline(inputs: pd.DataFrame, fitted: Pipeline) -> pd.DataFrame:
    assert list(inputs)==COLUMNS,'Application accepts no labels'
    assert isinstance(inputs.ts.dtype,pd.DatetimeTZDtype) and inputs.ts.notna().all()
    result = inputs.copy()
    result['p_weather'] = cal_math.apply(inputs,fitted.weather,'temperature_then_snow').p.to_numpy()
    hour_input = inputs.assign(p_reference=result.p_weather)
    result['p_hour'] = hour_math.apply(hour_input,fitted.hour).p.to_numpy()
    cloud_input = inputs.assign(p_reference=result.p_hour)
    result['p_cloud'] = sky_math.apply(cloud_input,fitted.cloud).p.to_numpy()
    result['p'] = result.p_cloud
    return result

def fit_pipeline(train: pd.DataFrame) -> Pipeline:
    assert isinstance(train.ts.dtype,pd.DatetimeTZDtype) and train.ts.notna().all()
    local = train.copy()
    local['ts'] = local.ts.dt.tz_convert('Asia/Seoul')
    weather = cal_math.fit(local)
    weather_p = cal_math.apply(local,weather,'temperature_then_snow').p
    for_hour = local.assign(p_reference=weather_p)
    hour = hour_math.fit(for_hour)
    hour_p = hour_math.apply(for_hour,hour).p
    cloud = sky_math.fit(local.assign(p_reference=hour_p))
    return Pipeline(weather,hour,cloud)

def self_check() -> list[str]:
    def factor(value: float):
        return cal_math.Factor(value,value,150,25,100.,True)
    weather = cal_math.Calibration(tuple(factor(1.1) for _ in range(5)),factor(1.1),factor(1.1))
    pipeline = Pipeline(weather,hour_math.HourFactors(tuple(factor(1.1) for _ in range(5))),sky_math.CloudFactors(tuple(factor(1.1) for _ in range(4))))
    inputs = pd.DataFrame({'ts':pd.date_range('2024-01-01',periods=4,tz='Asia/Seoul'),'grp':['a']*4,'p_reference':[100.,0.,100.,100.],'wa_temp':[20.]*4,'extra_wa_snow':[1.]*4,'wb_cloud':[30.,30.,np.nan,100.00000000000001],'static_capacity':[300.]*4})[COLUMNS]
    actual = apply_pipeline(inputs,pipeline)
    np.testing.assert_allclose(actual.p,[100*1.075*1.05*1.05,0.,100*1.075*1.05,100*1.075*1.05*1.05],rtol=0,atol=1e-12)
    lower_hour = hour_math.HourFactors(tuple(factor(.85) for _ in range(5)))
    clip_pipeline = Pipeline(weather,lower_hour,sky_math.CloudFactors(tuple(factor(1.15) for _ in range(4))))
    clipped = apply_pipeline(inputs.assign(static_capacity=103.),clip_pipeline)
    np.testing.assert_allclose(clipped.iloc[0][['p_weather','p_hour','p_cloud']].to_numpy(dtype=float),[103.,103*.925,103*.925*1.075],rtol=0,atol=1e-12)
    rejected = False
    try:
        apply_pipeline(inputs.assign(y=999.,smp=np.inf,k=-1.),pipeline)
    except AssertionError:
        rejected = True
    assert rejected
    training = pd.concat([inputs.iloc[[0]].assign(ts=pd.Timestamp('2024-01-01',tz='Asia/Seoul')+pd.Timedelta(hours=i),y=110.,smp=2.,k=3.,extra_wa_snow=0.) for i in range(24*30)],ignore_index=True)
    fitted = fit_pipeline(training)
    assert len(fitted.weather.temperature)==5 and len(fitted.hour.hours)==5 and len(fitted.cloud.clouds)==4
    assert not fitted.weather.snow.supported and not fitted.weather.conditional_snow.supported
    assert fitted.weather.temperature[3].factor==1.1
    assert np.isfinite(apply_pipeline(training[COLUMNS],fitted).p).all()
    return ['fullweatherhourcloudsequence','boundedweatherproductthenhalfshrink','intermediatecapacityclipbeforelaterstages','missingcloudidentity','finiteabove100retained','nightzero','applicationrejectslabels','synthetic16scalarpipeline','unusedsnowonlyretained']
