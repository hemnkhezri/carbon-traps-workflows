"""Exploratory: forecast error relative to intraday CI variability, per grid (used in Fig. 7).
MAE of 0-47 h forecasts; SD of actual CI within each vintage's 0-47 h span, averaged over vintages.
GB vintages subsampled to one every 6 h (00/06/12/18 UTC) to match CarbonCast's daily-issue scale."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import numpy as np
from cwf.carboncast import load_carboncast
from cwf.data import load_national

def stats(fc, act, hmax=47):
    h = (fc.window_utc - fc.capture_utc) / 3600
    f = fc[(h >= 0) & (h < hmax)].copy(); f["a"] = f.window_utc.map(act); f = f.dropna()
    f = f.drop_duplicates(["capture_utc", "window_utc"], keep="last")
    mae = (f.forecast - f.a).abs().mean(); sd = f.groupby("capture_utc").a.std().mean()
    return mae, sd, mae / sd

for R in ["CISO", "DE", "ERCO", "PJM"]:
    print(R, [round(x, 2) for x in stats(*load_carboncast("/home/claude/carbonfirst_CarbonCast", R))])
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", ["2026-07", "2026-08", "2026-09", "2026-10"])
fc = fc[(fc.capture_utc % 21600) == 0]
print("GB", [round(x, 2) for x in stats(fc, act)])
