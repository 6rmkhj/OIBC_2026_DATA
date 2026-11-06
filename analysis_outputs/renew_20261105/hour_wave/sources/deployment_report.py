# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by deployment_fit after prediction freeze.
"""Paired reporting after all diagnostic predictions are immutable."""
from wave_common import OUT, save_json
from final_build import OLD, MARCH, JUNE
from final_metrics import metrics
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve frozen score interface

DEST = OUT / "deployment_check"


def report(prediction: pd.DataFrame) -> None:
    """Open evaluation labels once; retain old-cutoff comparison explicitly."""
    labels = pd.read_parquet(OLD / "outer_predictions.parquet", columns=["ts","grp","y","smp","k","site_count"], filters=[("ts",">",MARCH),("ts","<=",JUNE)])
    frame = prediction.merge(labels,on=["ts","grp"],validate="one_to_one",how="outer",indicator=True)
    assert len(frame)==4416 and frame._merge.eq("both").all()
    frame = frame.drop(columns="_merge")
    assert not frame.duplicated(["ts","grp"]).any()
    assert np.isfinite(frame[["y","smp","k","p_previous","p_candidate"]]).all().all()
    np.testing.assert_array_equal(frame.k,np.where(frame.ts.dt.hour.between(11,15),3,1))
    frame.to_parquet(DEST / "paired_predictions.parquet",index=False)
    old = pd.read_parquet(OUT / "final/outer_predictions.parquet",filters=[("ts",">",MARCH),("ts","<=",JUNE)])
    comparison = frame.merge(old[["ts","grp","y","smp","k","site_count"]],on=["ts","grp"],validate="one_to_one",suffixes=("","_old"))
    for name in ("y","smp","k","site_count"):
        np.testing.assert_array_equal(comparison[name],comparison[name+"_old"])
    diagnostics = []
    scores = {}
    bootstrap = {}
    for cutoff, rows in (("original_2024Jun1",old),("fresh_2025Mar1",frame)):
        scores[cutoff] = {p:metrics(rows,p) for p in ("p_previous","p_candidate")}
        months = {month:values for month,values in rows.groupby((rows.ts-pd.Timedelta(hours=1)).dt.strftime("%Y-%m"))}
        for subset, values in {"all":rows,"peak_11_15":rows[rows.k.eq(3)],**months}.items():
            diagnostics.extend({"cutoff":cutoff,"subset":subset,"arm":p,**metrics(values,p)} for p in ("p_previous","p_candidate"))
        weight = rows.smp*rows.k
        daily = pd.DataFrame({"day":(rows.ts-pd.Timedelta(hours=1)).dt.floor("D"),"delta":weight*((rows.p_candidate-rows.y).abs()-(rows.p_previous-rows.y).abs()),"denominator":weight*rows.y}).groupby("day").sum()
        daily.to_parquet(DEST / f"bootstrap_daily_{cutoff}.parquet")
        ix = np.random.default_rng(20261104).integers(0,len(daily),size=(2000,len(daily)))
        delta = daily.delta.to_numpy()[ix].sum(axis=1)
        pct = 100*delta/daily.denominator.to_numpy()[ix].sum(axis=1)
        pd.DataFrame({"W_delta":delta,"W_pct_delta":pct}).to_parquet(DEST / f"bootstrap_replicates_{cutoff}.parquet",index=False)
        bootstrap[cutoff] = {"seed":20261104,"replicates":2000,"blocks":len(daily),"W_delta_95CI":np.quantile(delta,[.025,.975]).tolist(),"W_pct_delta_95CI":np.quantile(pct,[.025,.975]).tolist()}
    save_json(DEST / "metrics.json",scores)
    save_json(DEST / "bootstrap.json",bootstrap)
    pd.DataFrame(diagnostics).to_csv(DEST / "diagnostics.csv",index=False)
    print("METRICS",json.dumps(scores),flush=True)
