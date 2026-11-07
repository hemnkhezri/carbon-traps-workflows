"""Exploratory (Deep Review item M1): coverage of the alpha = 0.9 single-window thresholds when the decision error is
taken over a task's duration, as the schedulers use them. For durations of k half-hour windows, e is the difference of
k-window means; horizon = capture lag + later start + duration/2 (DiffGate.threshold). Same submissions and vintages
as gate_coverage.py (GB confirmatory, seeds 10-14). Also reports the number of calibration errors per bin."""
import json
import numpy as np, pandas as pd
from cwf.data import CIData, load_national
from cwf import gate as G
CFG = json.load(open("confirm_config.json"))
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", CFG["months"])
CI = CIData(fc, act)
t0s = pd.read_csv("results/confirm.csv", usecols=["t0"]).t0.unique()
# count calibration errors per bin by wrapping np.quantile
counts = []
_q = np.quantile
def q_count(e, a, *args, **kw):
    if not args and not kw: counts.append(len(e))
    return _q(e, a, *args, **kw)
G.np.quantile = q_count
res = {k: [] for k in (1, 2, 4, 8, 16)}
for t0 in t0s:
    g = G.calibrate(CI, int(t0), 0.9)
    F = CI.vintage(int(t0), 94); A = CI.actual(int(t0), 94)
    if g is None or F is None or A is None:
        continue
    for k in res:
        cF = np.concatenate([[0], np.cumsum(F)]); cA = np.concatenate([[0], np.cumsum(A)])
        mF = (cF[k:] - cF[:-k]) / k; mA = (cA[k:] - cA[:-k]) / k   # mean over windows i..i+k-1
        n = len(mF)
        for L in range(1, n):
            dF = mF[:-L] - mF[L:]; dA = mA[:-L] - mA[L:]
            hor = (g.cap_lag_min + 30 * np.arange(L, n) + 15 * k) / 60.0
            li = G._bin(L * 0.5, G.LAG_EDGES_H)
            hi = np.clip(np.searchsorted(G.HOR_EDGES_H, hor, side="right") - 1, 0, len(G.HOR_EDGES_H) - 2)
            q = g.q[li, hi]
            for e in (dF - dA, dA - dF):
                res[k].append(np.c_[e <= q, np.full(len(e), t0)])
counts = np.array(counts)
print("calibration errors per bin: min", counts.min(), " median", int(np.median(counts)), " bins", len(counts))
for k, v in res.items():
    v = np.concatenate(v)
    per = pd.Series(v[:, 0]).groupby(v[:, 1]).mean()
    print(f"duration {k*0.5:4.1f} h: coverage {v[:,0].mean():.3f}  (pairs {len(v)}; per-submission 10th pct {per.quantile(0.1):.3f})")
