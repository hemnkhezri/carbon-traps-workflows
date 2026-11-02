"""Platform-sensitivity analysis, fixed before the run (EXT2_PREREG.md).
Usage: python analyse_hetero.py HETERO_CSV [HOMOGENEOUS_EXTENSION_CSV]
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


print("== Sanity checks")
print("rows", len(d), " jobs", d.groupby(["region", "seed", "wf", "T", "t0"]).ngroups, " (planned 1600)")
sg = d[d.sched.str.contains("SG") | (d.sched == "Shift")]
print("nominal misses (safeguarded + Shift)", int(sg.miss.sum()))
for s in ["CA-List+SG", "CA-LS+SG", "CWM+SG"]:
    print(f"oracle trap rate {s}: {100*d[(d.sched==s)&(d.regime=='oracle')].trap.mean():.2f}% (must be 0)")
if "cwm_status" in d:
    print("CWM replaced by HEFT:", d.cwm_status.value_counts().to_dict())

bt = Boot(d)
sel = lambda s, r, fs: bt.df[(bt.df.sched == s) & (bt.df.regime == r) & (bt.df.f.isin(fs))]
print("\n== Hypotheses (pooled)")
r = bt.ratio(sel("CA-LS+SG", "issued", F_SLACK), sel("CA-LS+SG", "oracle", F_SLACK), "saving")
print(f"G1 R = {fmt(r, 1)} -> {r[2] < 0.75}")
tr = [bt.mean(sel("CA-LS+SG", "issued", [f]), "trap1") for f in F_ALL]
print("G2 traps: " + "; ".join(f"{f}: {fmt(t)}" for f, t in zip(F_ALL, tr)) + f" -> {all(t[1] > 0.02 for t in tr)}")
td = bt.diff(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "trap1")
rr = bt.ratio(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "saving")
print(f"G3 trap diff = {fmt(td)}; retention = {fmt(rr, 1)} -> {(td[2] < 0) and (rr[1] >= 0.5)}")
rn = bt.ratio(sel("CWM+SG", "issued", F_SLACK), sel("CWM+SG", "oracle", F_SLACK), "native_saving")
print(f"G4 R_native(CWM+SG) = {fmt(rn, 1)} -> {rn[2] < 0.75}")
md = [bt.diff(sel("CA-LS+SG", "issued", [f]), sel("CA-LS+SG", "issued", [f]), "miss_rt", "heft_miss_rt") for f in F_ALL]
print("G5 miss - HEFT miss: " + "; ".join(f"{f}: {fmt(m)}" for f, m in zip(F_ALL, md)) + f" -> {all(m[1] > 0.10 for m in md)}")

print("\n== Descriptive (means, %)")
for col in ["saving", "native_saving", "trap1"]:
    print(f"\n-- {col}")
    print(d.pivot_table(index=["sched", "regime"], columns="region", values=col, aggfunc="mean").mul(100).round(2).to_string())
print("\n-- fast-machine share (%)")
print(d.groupby(["sched", "regime"]).fast_share.mean().mul(100).round(1).to_string())
print("\n-- miss_rt % (issued) by f")
print(d[d.regime == "issued"].pivot_table(index="sched", columns="f", values="miss_rt", aggfunc="mean").mul(100).round(1).to_string())
if len(sys.argv) > 2:
    h = pd.read_csv(sys.argv[2]); h = h[h.seed == 30]
    print("\n-- homogeneous (extension, seed 30) vs heterogeneous: mean emission saving %")
    a = h.groupby(["sched", "regime"]).saving.mean().mul(100).rename("homog")
    b = d.groupby(["sched", "regime"]).saving.mean().mul(100).rename("hetero")
    print(pd.concat([a, b], axis=1).round(2).dropna(how="all").to_string())
