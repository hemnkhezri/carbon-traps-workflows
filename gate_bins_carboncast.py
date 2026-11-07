"""Exploratory (Deep Review item M3): calibration of the gate on daily 96-h CarbonCast vintages.
For every submission of the generality extension (seeds 30-32) and the platform study (seed 30): number of vintages
used, errors per populated bin, bins that fell back to the largest quantile, vintage age at t0, and the latest
horizon (from capture) that a plan can reach."""
import numpy as np, pandas as pd
from cwf.data import CIData
from cwf.carboncast import load_carboncast
from cwf import gate as G
_q = np.quantile; counts = []
def qc(e, a, *args, **kw):
    if not args and not kw: counts.append(len(e))
    return _q(e, a, *args, **kw)
G.np.quantile = qc
d = pd.read_csv("results/extension.csv", usecols=["region", "t0", "D"])
out = []
for reg, g in d.groupby("region"):
    fc, act = load_carboncast("/home/claude/carbonfirst_CarbonCast", reg)
    CI = CIData(fc, act)
    Dmax = g.D.max()
    for t0 in g.t0.unique():
        counts.clear()
        caps = CI.captures[(CI.captures >= t0 - 7 * 86400) & (CI.captures <= t0 - 49 * 3600)]
        gate = G.calibrate(CI, int(t0), 0.9)
        nfill = int(len(G.LAG_EDGES_H) - 1) * int(len(G.HOR_EDGES_H) - 1) - len(counts)
        out.append(dict(region=reg, t0=t0, n_vint=len(caps), min_n=min(counts), med_n=np.median(counts),
                        n_fill=nfill, age_h=gate.cap_lag_min / 60, max_hor_h=gate.cap_lag_min / 60 + Dmax / 60))
o = pd.DataFrame(out)
print(o.groupby("region").agg(subs=("t0", "size"), vint_min=("n_vint", "min"), vint_max=("n_vint", "max"),
      min_n=("min_n", "min"), med_n=("med_n", "median"), fill_max=("n_fill", "max"), age_min=("age_h", "min"),
      age_max=("age_h", "max"), max_hor=("max_hor_h", "max"), share_hor_gt48=("max_hor_h", lambda x: (x > 48).mean())).round(2).to_string())
print("D max (h):", round(d.D.max() / 60, 2))
