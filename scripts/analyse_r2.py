"""Exploratory post-hoc analyses (EXT3_DEVIATIONS.md item 2). Cluster bootstrap over calendar days.
Usage: python analyse_r2.py results/rev/A_s10.csv,results/rev/A_s11.csv,results/rev/RH_s10s11.csv results/rev/R2_s10s11.csv"""
import sys

import numpy as np
import pandas as pd

A = pd.concat([pd.read_csv(p) for p in sys.argv[1].split(",")]).drop_duplicates(
    ["seed", "wf", "T", "f", "t0", "sched", "regime"], keep="last")
R2 = pd.read_csv(sys.argv[2])
d = pd.concat([A, R2])
d["day"] = pd.to_datetime(d.t0, unit="s").dt.floor("D")
days = np.sort(d.day.unique()); d["c"] = d.day.map({x: i for i, x in enumerate(days)}); n = len(days)
rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(2000)]
FS = [1.5, 2.0, 3.0]


def sums(sub, col):
    g = sub.groupby("c")[col].agg(["sum", "count"]); s = np.zeros(n); k = np.zeros(n)
    s[g.index] = g["sum"].to_numpy(float); k[g.index] = g["count"].to_numpy(float); return s, k


def stat(a, ca, b=None, cb=None, kind="mean"):
    s1, k1 = sums(a, ca)
    if kind == "mean":
        f = lambda i: s1[i].sum() / k1[i].sum()
    else:
        s2, k2 = sums(b, cb)
        f = (lambda i: (s1[i].sum() / k1[i].sum()) / (s2[i].sum() / k2[i].sum())) if kind == "ratio" else \
            (lambda i: s1[i].sum() / k1[i].sum() - s2[i].sum() / k2[i].sum())
    bs = np.array([f(i) for i in idx]); return f(np.arange(n)), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


sel = lambda s, r, fs=None: d[(d.sched == s) & (d.regime == r) & (d.f.isin(fs) if fs else True)]
fm = lambda t, k=100, dd=2: f"{k*t[0]:.{dd}f} [{k*t[1]:.{dd}f}, {k*t[2]:.{dd}f}]"
print("rows R2:", len(R2), "| days", n)
chk = sel("CA-LS+SG[corr]", "issued").set_index(["seed", "wf", "T", "f", "t0"]).saving
ref = sel("CA-LS+SG", "issued").set_index(["seed", "wf", "T", "f", "t0"]).saving.reindex(chk.index)
print("check: CA-LS+SG plans identical in R2 and A:", float((chk - ref).abs().max()))

print("\n(a) Re-planning: saving (f >= 1.5, %), and ratios")
for s, r in (("CA-LS+SG", "oracle"), ("RH-CA-LS+SG", "oracle"), ("CA-LS+SG", "issued"),
             ("RH-CA-LS+SG[stale]", "issued"), ("RH-CA-LS+SG", "issued")):
    print(f"  {s:20s} {r:7s} {fm(stat(sel(s, r, FS), 'saving'))}")
print("  R of RH vs RH oracle:", fm(stat(sel("RH-CA-LS+SG", "issued", FS), "saving", sel("RH-CA-LS+SG", "oracle", FS), "saving", "ratio"), 1))
print("  R of stale RH vs RH oracle:", fm(stat(sel("RH-CA-LS+SG[stale]", "issued", FS), "saving", sel("RH-CA-LS+SG", "oracle", FS), "saving", "ratio"), 1))
print("  R of static vs static oracle:", fm(stat(sel("CA-LS+SG", "issued", FS), "saving", sel("CA-LS+SG", "oracle", FS), "saving", "ratio"), 1))
print("  info gain (RH issued - stale RH), pp:", fm(stat(sel("RH-CA-LS+SG", "issued", FS), "saving", sel("RH-CA-LS+SG[stale]", "issued", FS), "saving", "diff")))
for s in ("CA-LS+SG", "RH-CA-LS+SG[stale]", "RH-CA-LS+SG"):
    print(f"  trap1 {s:20s} {fm(stat(sel(s, 'issued'), 'trap1'), 100, 1)}%")

print("\n(b) Quantile planner CA-LS+SG[Q0.9] vs CA-LS+SG and gate (issued, all f)")
for s in ("CA-LS+SG", "CA-LS+SG+Gate[diff0.9]", "CA-LS+SG[Q0.9]"):
    x = sel(s, "issued")
    print(f"  {s:24s} saving {fm(stat(x, 'saving'))}%  trap1 {fm(stat(x, 'trap1'), 100, 1)}%  miss_rt {100*x.miss_rt.mean():.1f}%")
print("  R (f>=1.5) of Q0.9 vs CA-LS oracle:", fm(stat(sel("CA-LS+SG[Q0.9]", "issued", FS), "saving", sel("CA-LS+SG", "oracle", FS), "saving", "ratio"), 1))
print("  d_saving Q0.9 - gate:", fm(stat(sel("CA-LS+SG[Q0.9]", "issued"), "saving", sel("CA-LS+SG+Gate[diff0.9]", "issued"), "saving", "diff")),
      " d_trap:", fm(stat(sel("CA-LS+SG[Q0.9]", "issued"), "trap1", sel("CA-LS+SG+Gate[diff0.9]", "issued"), "trap1", "diff"), 100, 1))

print("\n(c) Correlated runtime noise (static executor): miss %, and gap to HEFT (pp)")
for s in ("CA-LS+SG[corr]", "CA-LS+SG+Res75[corr]"):
    for f in sorted(d.f.unique()):
        x = sel(s, "issued", [f])
        print(f"  {s:22s} f={f}: miss {100*x.miss_corr.mean():5.1f}  HEFT {100*x.heft_miss_corr.mean():5.1f}  gap {fm(stat(x, 'miss_corr', x, 'heft_miss_corr', 'diff'), 100, 1)}")
    x = sel(s, "issued"); print(f"  {s:22s} all f: miss {100*x.miss_corr.mean():.1f}  HEFT {100*x.heft_miss_corr.mean():.1f}")
