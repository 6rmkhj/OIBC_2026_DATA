# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# Run: python submission/score_push/check_features.py
"""Independent numerical fixtures for new weather aggregation/context boundaries."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen model interface
from features import cyclic_wind, revisions, trajectory, weighted_weather


def main() -> None:
    ts = pd.Timestamp("2024-01-01 10:00", tz="Asia/Seoul")
    rows = pd.DataFrame({"ts": [ts]*2, "grp": ["G1"]*2, "capacity_kw": [1., 3.], "wa_cloud": [20., 80.], "wa_temp": [np.nan, 10.], "empty": [np.nan]*2, "wa_wind_dir": [350., 10.]})
    transformed = cyclic_wind(rows, "wa")
    names = ["wa_cloud", "wa_temp", "empty", "wa_wind_sin", "wa_wind_cos"]
    result = weighted_weather(transformed, names)
    assert result.wa_cloud.iloc[0] == 65 and result.wa_temp.iloc[0] == 10
    assert np.isnan(result["empty"].iloc[0])
    assert np.isclose(result.wa_wind_cos.iloc[0], np.cos(np.deg2rad(10)))
    assert np.isclose(result.wa_wind_sin.iloc[0], .5*np.sin(np.deg2rad(10)))
    perturbed = transformed.assign(energy=[1e9, -1e9], cf=[-999, 999], y=[np.nan, 1e20])
    pd.testing.assert_frame_equal(result, weighted_weather(perturbed, names))
    early = result.assign(wa_cloud=25.)
    assert revisions(result, early, ["wa_cloud"]).rev_wa_cloud.iloc[0] == 40
    assert revisions(result, early.assign(wa_cloud=np.nan), ["wa_cloud"]).rev_wa_cloud.isna().all()
    try:
        revisions(result, early.assign(ts=ts+pd.Timedelta(hours=1)), ["wa_cloud"])
    except AssertionError as error:
        assert str(error) == "Round group keys differ"
    else:
        raise AssertionError("Mismatched round keys accepted")
    times = pd.to_datetime(["2024-01-01 22:00", "2024-01-01 23:00", "2024-01-02 00:00", "2024-01-02 01:00", "2024-01-02 03:00", "2024-01-02 05:00"]).tz_localize("Asia/Seoul")
    context = trajectory(pd.DataFrame({"ts": times, "grp": "G1", "wa_cloud": [1, 2, 4, 8, 16, 32], "wb_cloud": 0., "wb_uv_idx": 0.}))
    assert context["traj_wa_cloud_+2"].iloc[2] == -3
    assert np.isnan(context["traj_wa_cloud_+2"].iloc[3])
    assert np.isnan(context["traj_wa_cloud_+2"].iloc[5])
    print("PASS weighted means, circular wind, missing values, label perturbation, revisions, midnight/gap isolation", flush=True)


if __name__ == "__main__":
    main()
