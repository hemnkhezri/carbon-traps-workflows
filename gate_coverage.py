"""Q5 of EXT3_PREREG.md: empirical coverage of the alpha = 0.9 difference-error bounds on the realised errors of
the vintage used at each confirmatory submission time (GB, seeds 10-14). For every pair of 30-min windows (u, v)
within 47 h of t0, both directions, e = (F(u) - F(v)) - (A(u) - A(v)); covered if e <= q[lag bin, horizon bin]."""
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
        for e in (dF - dA, dA - dF):
            rows.append(pd.DataFrame({"t0": t0, "lag": li, "hor": hi, "cov": e <= q, "q": q, "abs_e": np.abs(e)}))
d = pd.concat(rows)
print("overall coverage (nominal 0.90):", round(d["cov"].mean(), 3), " pairs:", len(d), " submissions:", d.t0.nunique())
per_t0 = d.groupby("t0")["cov"].mean()
print("per-submission coverage: median", round(per_t0.median(), 3), " 10th pct", round(per_t0.quantile(0.1), 3))
lag_lab = [f"{LAG_EDGES_H[i]:g}-{LAG_EDGES_H[i+1]:.0f}h" for i in range(len(LAG_EDGES_H) - 1)]
hor_lab = [f"{HOR_EDGES_H[i]:g}-{HOR_EDGES_H[i+1]:.0f}h" for i in range(len(HOR_EDGES_H) - 1)]
t = d.pivot_table(index="lag", columns="hor", values="cov", aggfunc="mean").round(3)
t.index = [lag_lab[i] for i in t.index]; t.columns = [hor_lab[i] for i in t.columns]
print("coverage by lag (rows) x horizon (cols):"); print(t.to_string())
