"""kappa of the ENTSO-E day-ahead intensity forecasts (descriptive, EXT4_PREREG.md section 5).
kappa = MAE of the day-ahead forecast for day D / mean within-day SD of realised intensity.
Usage: python scripts/entsoe_kappa.py DATA_ROOT FROM TO"""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)
import numpy as np, pandas as pd
from cwf.entsoe import TZ, build_vintages
root, lo, hi = sys.argv[1], pd.Timestamp(sys.argv[2], tz=TZ), pd.Timestamp(sys.argv[3], tz=TZ)
for z in ("DE_LU", "ES"):
    fc, act = build_vintages(root, z)
    h = (fc.window_utc - fc.capture_utc) / 3600
    t = pd.to_datetime(fc.window_utc, unit="s", utc=True).dt.tz_convert(TZ)
    m = (h >= 6) & (t >= lo) & (t < hi)
    e = np.abs(fc[m].forecast.to_numpy() - act.reindex(fc[m].window_utc).to_numpy())
    a = act[(pd.to_datetime(act.index, unit="s", utc=True).tz_convert(TZ) >= lo) & (pd.to_datetime(act.index, unit="s", utc=True).tz_convert(TZ) < hi)]
    days = pd.to_datetime(a.index, unit="s", utc=True).tz_convert(TZ).date
    sd = a.groupby(days).std().mean()
    print(f"{z}: MAE {np.nanmean(e):.1f} g/kWh, mean realised {a.mean():.0f}, within-day SD {sd:.1f}, kappa {np.nanmean(e)/sd:.2f}")
