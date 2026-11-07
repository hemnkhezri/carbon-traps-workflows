"""Exploratory (Deep Review suggestion): heterogeneous platform, CA-LS+SG. Timing retention
(S_forecast - S_flat) / (S_oracle - S_flat), where S_flat is CA-LS planned on a flat signal (energy-aware mapping only),
and the trap rate measured against the flat-signal plan (C_forecast > 1.01 C_flat). Cluster bootstrap over
region x submission (20 clusters), 2,000 resamples, seed 2026. Input: results/hetero_flat_joined.csv."""
import numpy as np, pandas as pd
m = pd.read_csv("results/hetero_flat_joined.csv")
m["trap_flat"] = ((1 - m.fc) > 1.01 * (1 - m.saving_flat)).astype(float)
m["trap_heft"] = ((1 - m.fc) > 1.01).astype(float)
m["trap_or_flat"] = ((1 - m["or"]) > 1.01 * (1 - m.saving_flat)).astype(float)
keys = m[["region", "t0"]].drop_duplicates().reset_index(drop=True); keys["c"] = np.arange(len(keys))
m = m.merge(keys, on=["region", "t0"]); n = len(keys)
rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(2000)]
def agg(sub, cols):
    g = sub.groupby("c")[cols].sum(); k = sub.groupby("c").size()
    S = np.zeros((n, len(cols))); K = np.zeros(n); S[g.index] = g.to_numpy(); K[k.index] = k.to_numpy(); return S, K
def ci(sub, fn, cols):
    S, K = agg(sub, cols)
    est = fn(S.sum(0) / K.sum()); bs = np.array([fn(S[i].sum(0) / K[i].sum()) for i in idx])
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
print("clusters:", n)
for nm, sub in (("all f", m), ("f >= 1.5", m[m.f >= 1.5])):
    r = ci(sub, lambda v: (v[2] - v[0]) / (v[1] - v[0]), ["saving_flat", "or", "fc"])
    g = ci(sub, lambda v: 100 * (v[1] - v[0]), ["saving_flat", "or"])
    t = ci(sub, lambda v: 100 * v[0], ["trap_flat"]); th = ci(sub, lambda v: 100 * v[0], ["trap_heft"])
    to = ci(sub, lambda v: 100 * v[0], ["trap_or_flat"])
    print(f"{nm} (n={len(sub)}): timing retention {r[0]:.2f} [{r[1]:.2f}, {r[2]:.2f}]; oracle timing gain {g[0]:.2f} [{g[1]:.2f}, {g[2]:.2f}] pp; "
          f"traps vs flat plan {t[0]:.1f}% [{t[1]:.1f}, {t[2]:.1f}] (oracle {to[0]:.1f}%); traps vs HEFT {th[0]:.1f}% [{th[1]:.1f}, {th[2]:.1f}]")
for reg, sub in m.groupby("region"):
    v = sub[["saving_flat", "or", "fc"]].mean()
    print(f"  {reg}: retention {(v.fc - v.saving_flat) / (v['or'] - v.saving_flat):.2f}; timing gain {100*(v['or']-v.saving_flat):.2f} pp; traps vs flat {100*sub.trap_flat.mean():.1f}%")
