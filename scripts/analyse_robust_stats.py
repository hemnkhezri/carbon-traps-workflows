"""Robustness of the statistical conclusions (requested by internal review; post hoc, reported as such).
1. Cluster bootstrap over calendar days and over ISO weeks instead of submission times.
2. Holm correction across the hypotheses of each study (bootstrap one-sided p-values).
3. R per f, absolute loss (pp), emission-weighted ratio.
4. Trap-threshold sensitivity (0, 1, 2, 5%) and expected excess emission per run.
Usage: python analyse_robust_stats.py confirm|extension
"""
import sys

import numpy as np
import pandas as pd

B = 2000
study = sys.argv[1]
d = pd.read_csv("results/confirm.csv" if study == "confirm" else "results/extension.csv")
if "region" not in d:
    d["region"] = "GB"
d["day"] = pd.to_datetime(d.t0, unit="s").dt.floor("D")
d["week"] = pd.to_datetime(d.t0, unit="s").dt.isocalendar().week.astype(int)
d["ex"] = (d.carbon_kg / d.heft_carbon_kg - 1).clip(lower=0) if "carbon_kg" in d else np.nan


def boot(df, unit):
    keys = df[["region", unit]].drop_duplicates().reset_index(drop=True); keys["c"] = np.arange(len(keys))
    df = df.merge(keys, on=["region", unit]); n = len(keys)
    rng = np.random.default_rng(2026)
    idx = [rng.integers(0, n, n) for _ in range(B)]
    def sums(sub, col):
        g = sub.groupby("c")[col].agg(["sum", "count"]); s = np.zeros(n); k = np.zeros(n)
        s[g.index] = g["sum"].to_numpy(float); k[g.index] = g["count"].to_numpy(float); return s, k
    def stat(sub_a, col_a, sub_b=None, col_b=None, kind="mean"):
        s1, k1 = sums(sub_a, col_a)
        if kind == "mean":
            f = lambda b: s1[b].sum() / k1[b].sum()
        else:
            s2, k2 = sums(sub_b, col_b)
            f = (lambda b: (s1[b].sum() / k1[b].sum()) / (s2[b].sum() / k2[b].sum())) if kind == "ratio" else \
                (lambda b: s1[b].sum() / k1[b].sum() - s2[b].sum() / k2[b].sum())
        allb = np.arange(n); est = f(allb); bs = np.array([f(b) for b in idx])
        return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5), bs
    return df, stat, n


F = sorted(d.f.unique()); FS = [f for f in F if f >= 1.5]
sel = lambda df, s, r, fs: df[(df.sched == s) & (df.regime == r) & (df.f.isin(fs))]
print(f"== {study}: rows {len(d)}; distinct submission times {d.groupby(['region','t0']).ngroups}; "
      f"days {d.groupby(['region','day']).ngroups}; weeks {d.groupby(['region','week']).ngroups}")
print("rows per job and sched x regime combinations per f:",
      d.groupby(['region', 'seed', 'wf', 'T', 't0', 'f']).size().iloc[0],
      sorted(d.groupby(['sched', 'regime']).size().index.tolist()))

for unit in ("t0", "day", "week"):
    df, stat, n = boot(d, unit)
    print(f"\n-- cluster unit: {unit} (n = {n})")
    pv = {}
    r = stat(sel(df, "CA-LS+SG", "issued", FS), "saving", sel(df, "CA-LS+SG", "oracle", FS), "saving", "ratio")
    pv["H1"] = np.mean(r[3] >= 0.75); print(f"H1/E1 R = {r[0]:.3f} [{r[1]:.3f}, {r[2]:.3f}]  p = {pv['H1']:.4f}")
    tr = [stat(sel(df, "CA-LS+SG", "issued", [f]), "trap1") for f in F]
    pv["H2"] = max(np.mean(t[3] <= 0.02) for t in tr)
    print("H2/E2 traps: " + "; ".join(f"{f}: {100*t[0]:.1f} [{100*t[1]:.1f}, {100*t[2]:.1f}]" for f, t in zip(F, tr)) + f"  p = {pv['H2']:.4f}")
    if study == "confirm":
        h3 = stat(sel(df, "CA-LS+SG", "synthetic", FS), "saving", sel(df, "CA-LS+SG", "issued", FS), "saving", "diff")
        pv["H3"] = np.mean(h3[3] <= 0); print(f"H3 diff = {100*h3[0]:.2f} [{100*h3[1]:.2f}, {100*h3[2]:.2f}] pp  p = {pv['H3']:.4f}")
    g = stat(sel(df, "CA-LS+SG+Gate", "issued", F), "trap1", sel(df, "CA-LS+SG", "issued", F), "trap1", "diff")
    rr = stat(sel(df, "CA-LS+SG+Gate", "issued", F), "saving", sel(df, "CA-LS+SG", "issued", F), "saving", "ratio")
    pv["H4"] = max(np.mean(g[3] >= 0), np.mean(rr[3] < 0.5))
    print(f"H4/E3 trap diff = {100*g[0]:.2f} [{100*g[1]:.2f}, {100*g[2]:.2f}] pp; retention {rr[0]:.2f} [{rr[1]:.2f}, {rr[2]:.2f}]  p = {pv['H4']:.4f}")
    if study == "extension":  # E4 (added after review): misses vs HEFT under runtime noise, and the gate's effect
        e4 = [stat(sel(df, "CA-LS+SG", "issued", [f]), "miss_rt", sel(df, "CA-LS+SG", "issued", [f]), "heft_miss_rt", "diff") for f in F]
        e4g = stat(sel(df, "CA-LS+SG+Gate", "issued", F), "miss_rt", sel(df, "CA-LS+SG", "issued", F), "miss_rt", "diff")
        pv["E4"] = max(max(np.mean(t[3] <= 0.10) for t in e4), np.mean(e4g[3] >= 0))
        print("E4 miss gap: " + "; ".join(f"{f}: {100*t[0]:.1f} [{100*t[1]:.1f}, {100*t[2]:.1f}]" for f, t in zip(F, e4))
              + f"; gated - ungated {100*e4g[0]:.1f} [{100*e4g[1]:.1f}, {100*e4g[2]:.1f}]  p = {pv['E4']:.4f}")
    if study == "confirm":
        for s in ("CA-List+SG", "CaWoSched+SG"):
            r5 = stat(sel(df, s, "issued", FS), "saving", sel(df, s, "oracle", FS), "saving", "ratio")
            t5 = [stat(sel(df, s, "issued", [f]), "trap1") for f in F]
            pv[f"H5 {s}"] = max(np.mean(r5[3] >= 0.75), max(np.mean(t[3] <= 0.02) for t in t5))
            print(f"H5 {s}: R = {r5[0]:.3f} [{r5[1]:.3f}, {r5[2]:.3f}]; min trap lower bound {100*min(t[1] for t in t5):.1f}%  p = {pv[f'H5 {s}']:.4f}")
    # Holm
    keys = sorted(pv, key=pv.get); m = len(keys); out = []
    for i, k in enumerate(keys):
        adj = min(1.0, max((m - j) * pv[keys[j]] for j in range(i + 1)))
        out.append(f"{k}: p={pv[k]:.4f}, Holm={adj:.4f} -> {'supported' if adj < 0.025 else 'not supported'}")
    print("Holm (one-sided, family alpha 0.025): " + " | ".join(out))

print("\n-- R per f, absolute loss and emission-weighted ratio (CA-LS+SG; cluster unit day)")
df, stat, n = boot(d, "day")
for f in F:
    r = stat(sel(df, "CA-LS+SG", "issued", [f]), "saving", sel(df, "CA-LS+SG", "oracle", [f]), "saving", "ratio")
    a = stat(sel(df, "CA-LS+SG", "oracle", [f]), "saving", sel(df, "CA-LS+SG", "issued", [f]), "saving", "diff")
    line = f"f={f}: R = {r[0]:.2f} [{r[1]:.2f}, {r[2]:.2f}]; loss = {100*a[0]:.2f} [{100*a[1]:.2f}, {100*a[2]:.2f}] pp"
    if "carbon_kg" in d:
        o = sel(d, "CA-LS+SG", "oracle", [f]); i = sel(d, "CA-LS+SG", "issued", [f])
        ew = (1 - i.carbon_kg.sum() / i.heft_carbon_kg.sum()) / (1 - o.carbon_kg.sum() / o.heft_carbon_kg.sum())
        line += f"; emission-weighted R = {ew:.2f}"
    print(line)
if "carbon_kg" in d:
    print("\n-- trap-threshold sensitivity, issued, all f (%), and expected excess emission per run (% of HEFT)")
    for s in sorted(d[d.regime == "issued"].sched.unique()):
        x = d[(d.sched == s) & (d.regime == "issued")]; ratio = x.carbon_kg / x.heft_carbon_kg
        print(f"{s:18s} >0%: {100*(ratio > 1 + 1e-9).mean():5.1f}  >1%: {100*(ratio > 1.01).mean():5.1f}  "
              f">2%: {100*(ratio > 1.02).mean():5.1f}  >5%: {100*(ratio > 1.05).mean():5.1f}  "
              f"E[excess] = {100*(ratio - 1).clip(lower=0).mean():.2f}%")
