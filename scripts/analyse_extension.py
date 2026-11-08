"""Extension analysis, fixed before the extension run (EXT_PREREG.md).
Cluster bootstrap over (region, submission) clusters, 2000 resamples, seed 2026.
Usage: python analyse_extension.py RESULTS_CSV
"""
import sys

import numpy as np
import pandas as pd

B = 2000
d = pd.read_csv(sys.argv[1])
F_ALL = sorted(d.f.unique())
F_SLACK = [f for f in F_ALL if f >= 1.5]


class Boot:
    def __init__(self, df):
        self.df = df
        keys = df[["region", "t0"]].drop_duplicates().reset_index(drop=True)
        keys["c"] = np.arange(len(keys))
        self.df = df.merge(keys, on=["region", "t0"])
        self.n = len(keys)
        rng = np.random.default_rng(2026)
        self.boot = [rng.integers(0, self.n, self.n) for _ in range(B)]

    def sums(self, sub, col):
        g = sub.groupby("c")[col].agg(["sum", "count"])
        s = np.zeros(self.n); k = np.zeros(self.n)
        s[g.index] = g["sum"].to_numpy(float); k[g.index] = g["count"].to_numpy(float)
        return s, k

    @staticmethod
    def pct(bs):
        bs = np.asarray(bs, float); bs = bs[np.isfinite(bs)]
        return np.percentile(bs, 2.5), np.percentile(bs, 97.5)

    def mean(self, sub, col):
        s, k = self.sums(sub, col)
        with np.errstate(invalid="ignore", divide="ignore"):
            bs = [s[b].sum() / k[b].sum() for b in self.boot]
        return (s.sum() / k.sum(), *self.pct(bs))

    def ratio(self, a, b_, col):
        s1, k1 = self.sums(a, col); s2, k2 = self.sums(b_, col)
        with np.errstate(invalid="ignore", divide="ignore"):
            bs = [(s1[b].sum() / k1[b].sum()) / (s2[b].sum() / k2[b].sum()) for b in self.boot]
        return ((s1.sum() / k1.sum()) / (s2.sum() / k2.sum()), *self.pct(bs))

    def diff(self, a, b_, col1, col2=None):
        col2 = col2 or col1
        s1, k1 = self.sums(a, col1); s2, k2 = self.sums(b_, col2)
        with np.errstate(invalid="ignore", divide="ignore"):
            bs = [s1[b].sum() / k1[b].sum() - s2[b].sum() / k2[b].sum() for b in self.boot]
        return (s1.sum() / k1.sum() - s2.sum() / k2.sum(), *self.pct(bs))


def fmt(t, k=100):
    return f"{k*t[0]:.2f} [{k*t[1]:.2f}, {k*t[2]:.2f}]"


def hypotheses(df, label):
    bt = Boot(df)
    sel = lambda s, r, fs: bt.df[(bt.df.sched == s) & (bt.df.regime == r) & (bt.df.f.isin(fs))]
    out = {}
    r = bt.ratio(sel("CA-LS+SG", "issued", F_SLACK), sel("CA-LS+SG", "oracle", F_SLACK), "saving")
    out["E1"] = r[2] < 0.75
    print(f"[{label}] E1 R = {fmt(r, 1)} -> {out['E1']}")
    tr = [bt.mean(sel("CA-LS+SG", "issued", [f]), "trap1") for f in F_ALL]
    out["E2"] = all(t[1] > 0.02 for t in tr)
    print(f"[{label}] E2 traps: " + "; ".join(f"{f}: {fmt(t)}" for f, t in zip(F_ALL, tr)) + f" -> {out['E2']}")
    td = bt.diff(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "trap1")
    rr = bt.ratio(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "saving")
    out["E3"] = (td[2] < 0) and (rr[1] >= 0.5)
    print(f"[{label}] E3 trap diff = {fmt(td)}; retention = {fmt(rr, 1)} -> {out['E3']}")
    md = [bt.diff(sel("CA-LS+SG", "issued", [f]), sel("CA-LS+SG", "issued", [f]), "miss_rt", "heft_miss_rt") for f in F_ALL]
    e4a = all(m[1] > 0.10 for m in md)
    gd = bt.diff(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "miss_rt")
    e4b = gd[2] < 0
    out["E4"] = e4a and e4b
    print(f"[{label}] E4a miss - HEFT miss: " + "; ".join(f"{f}: {fmt(m)}" for f, m in zip(F_ALL, md)) + f" -> {e4a}")
    print(f"[{label}] E4b gated - ungated miss = {fmt(gd)} -> {e4b}")
    return out


print("== Sanity checks")
print("rows", len(d), " jobs", d.groupby(["region", "seed", "wf", "T", "t0"]).ngroups, " (planned 4800)")
print("nominal misses", int(d.miss.sum()))
for s in ["CA-List+SG", "CA-LS+SG", "CaWoSched+SG", "CWM+SG"]:
    print(f"oracle trap rate {s}: {100*d[(d.sched==s)&(d.regime=='oracle')].trap.mean():.2f}% (must be 0)")

print("\n== Primary (pooled over regions)")
res = hypotheses(d, "pooled")
print("SUMMARY", res)

print("\n== Secondary (per region)")
for reg in sorted(d.region.unique()):
    hypotheses(d[d.region == reg], reg)

print("\n== Descriptive: mean emission saving % and native-objective saving % (oracle vs issued)")
for col in ["saving", "native_saving"]:
    t = d[d.sched.isin(["CA-LS+SG", "CaWoSched+SG", "CWM+SG", "Shift"])].pivot_table(
        index=["sched", "region"], columns="regime", values=col, aggfunc="mean").mul(100).round(2)
    print(f"\n-- {col}"); print(t.to_string())
print("\n-- trap1 % issued by scheduler and region")
print(d[d.regime == "issued"].pivot_table(index="sched", columns="region", values="trap1", aggfunc="mean").mul(100).round(2).to_string())
print("\n-- deadline misses with runtime noise, issued, by scheduler and f")
print(d[d.regime == "issued"].groupby(["sched", "f"]).agg(miss_rt=("miss_rt", "mean"), heft=("heft_miss_rt", "mean")).mul(100).round(2).to_string())
