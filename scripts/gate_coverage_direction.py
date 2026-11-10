"""Exploratory (post hoc, Nov 2026), written in reply to a reviewer question: the coverage of scripts/gate_coverage.py
split by direction. Forward = deferral from the earlier window u to the later window v; backward = the reverse.
Original description: empirical coverage of the alpha = 0.9 difference-error bounds on the realised errors of
the vintage used at each confirmatory submission time (GB, seeds 10-14). For every pair of 30-min windows (u, v)
within 47 h of t0, both directions, e = (F(u) - F(v)) - (A(u) - A(v)); covered if e <= q[lag bin, horizon bin]."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import json
import numpy as np, pandas as pd
from cwf.data import CIData, WIN, load_national
from cwf.gate import calibrate, LAG_EDGES_H, HOR_EDGES_H
CFG = json.load(open("confirm_config.json"))
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", CFG["months"])
CI = CIData(fc, act)
t0s = pd.read_csv("results/confirm.csv", usecols=["t0"]).t0.unique()
rows = []
for t0 in t0s:
    g = calibrate(CI, int(t0), 0.9)
    F = CI.vintage(int(t0), 94); A = CI.actual(int(t0), 94)
    if g is None or F is None or A is None:
        continue
    for L in range(1, 94):
        lag_h = L * 0.5
        li = np.clip(np.searchsorted(LAG_EDGES_H, lag_h, side="right") - 1, 0, len(LAG_EDGES_H) - 2)
        dF = F[:-L] - F[L:]; dA = A[:-L] - A[L:]
        hor = (g.cap_lag_min + 30 * np.arange(L, 94)) / 60.0
        hi = np.clip(np.searchsorted(HOR_EDGES_H, hor, side="right") - 1, 0, len(HOR_EDGES_H) - 2)
        q = g.q[li, hi]
        for dirn, e in (("forward", dF - dA), ("backward", dA - dF)):
            rows.append(pd.DataFrame({"t0": t0, "dir": dirn, "lag": li, "hor": hi, "cov": e <= q, "e": e}))
d = pd.concat(rows)
for dirn, g in d.groupby("dir"):
    pt = g.groupby("t0")["cov"].mean()
    print(f"{dirn}: coverage {g['cov'].mean():.3f} (pairs {len(g)}); per-submission median {pt.median():.3f}, 10th pct {pt.quantile(0.1):.3f}; mean error {g['e'].mean():+.2f} gCO2/kWh")
f = d[d.dir == "forward"]
print("forward coverage by lag x horizon bin:")
print(f.pivot_table(index="lag", columns="hor", values="cov", aggfunc="mean").round(3).to_string())
print("forward mean error by lag x horizon bin:")
print(f.pivot_table(index="lag", columns="hor", values="e", aggfunc="mean").round(2).to_string())
