"""ENTSO-E study analysis, fixed before the confirmatory run (EXT4_PREREG.md).
Cluster bootstrap, 2000 resamples, seed 2026. Primary clusters: (zone, submission).
Secondary: (zone, local day) and (zone, ISO week). One-sided bootstrap p-values with Holm (m = 5).
Usage: python scripts/analyse_entsoe.py RESULTS_CSV [RESULTS_CSV ...]
"""
import sys

import numpy as np
import pandas as pd

B = 2000
TZ = "Europe/Brussels"
d = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
loc = pd.to_datetime(d.t0, unit="s", utc=True).dt.tz_convert(TZ)
d["day"] = loc.dt.strftime("%Y-%m-%d")
d["week"] = loc.dt.strftime("%G-W%V")
d["season"] = loc.dt.month.map({12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
                                6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"})
F_ALL = sorted(d.f.unique())
F_SLACK = [f for f in F_ALL if f >= 1.5]


class Boot:
    def __init__(self, df, unit="t0"):
        keys = df[["region", unit]].drop_duplicates().reset_index(drop=True)
        keys["c"] = np.arange(len(keys))
        self.df = df.merge(keys, on=["region", unit])
        self.n = len(keys)
        rng = np.random.default_rng(2026)
        self.boot = [rng.integers(0, self.n, self.n) for _ in range(B)]

    def sums(self, sub, col):
        g = sub.groupby("c")[col].agg(["sum", "count"])
        s = np.zeros(self.n); k = np.zeros(self.n)
        s[g.index] = g["sum"].to_numpy(float); k[g.index] = g["count"].to_numpy(float)
        return s, k

    def stat(self, f, *parts):
        """f maps a list of (sum, count) means to a number; returns point and bootstrap replicates."""
        sk = [self.sums(sub, col) for sub, col in parts]
        with np.errstate(invalid="ignore", divide="ignore"):
            pt = f([s.sum() / k.sum() for s, k in sk])
            bs = np.array([f([s[b].sum() / k[b].sum() for s, k in sk]) for b in self.boot])
        return pt, bs[np.isfinite(bs)]


def ci(pt, bs, k=1):
    return f"{k*pt:.3f} [{k*np.percentile(bs, 2.5):.3f}, {k*np.percentile(bs, 97.5):.3f}]"


def hypotheses(df, label, unit="t0", verbose=True):
    bt = Boot(df, unit)
    sel = lambda s, r, fs, z=None: bt.df[(bt.df.sched == s) & (bt.df.regime == r) & (bt.df.f.isin(fs))
                                         & ((bt.df.region == z) if z else True)]
    ratio = lambda v: v[0] / v[1]
    diff = lambda v: v[0] - v[1]
    res, p = {}, {}
    # X1: forecasts lose part of the saving (upper bound of R < 1)
    pt, bs = bt.stat(ratio, (sel("CA-LS+SG", "issued", F_SLACK), "saving"), (sel("CA-LS+SG", "oracle", F_SLACK), "saving"))
    res["X1"] = np.percentile(bs, 97.5) < 1; p["X1"] = np.mean(bs >= 1)
    out = [f"X1 R = {ci(pt, bs)}"]
    # X2: trap1 lower bound > 2% at every f
    ps, txt, ok = [], [], True
    for f in F_ALL:
        pt, bs = bt.stat(lambda v: v[0], (sel("CA-LS+SG", "issued", [f]), "trap1"))
        ok &= np.percentile(bs, 2.5) > 0.02; ps.append(np.mean(bs <= 0.02)); txt.append(f"{f}: {ci(pt, bs, 100)}")
    res["X2"] = ok; p["X2"] = max(ps); out.append("X2 traps % " + "; ".join(txt))
    # X3: gate lowers traps and keeps at least half the saving
    pt1, bs1 = bt.stat(diff, (sel("CA-LS+SG+Gate", "issued", F_ALL), "trap1"), (sel("CA-LS+SG", "issued", F_ALL), "trap1"))
    pt2, bs2 = bt.stat(ratio, (sel("CA-LS+SG+Gate", "issued", F_ALL), "saving"), (sel("CA-LS+SG", "issued", F_ALL), "saving"))
    res["X3"] = np.percentile(bs1, 97.5) < 0 and np.percentile(bs2, 2.5) >= 0.5
    p["X3"] = max(np.mean(bs1 >= 0), np.mean(bs2 < 0.5))
    out.append(f"X3 trap diff pp = {ci(pt1, bs1, 100)}; retention = {ci(pt2, bs2)}")
    # X4: R higher on DE-LU (lower kappa) than on ES
    zs = sorted(df.region.unique())
    if {"DE_LU", "ES"} <= set(zs):
        pt, bs = bt.stat(lambda v: v[0] / v[1] - v[2] / v[3],
                         (sel("CA-LS+SG", "issued", F_SLACK, "DE_LU"), "saving"), (sel("CA-LS+SG", "oracle", F_SLACK, "DE_LU"), "saving"),
                         (sel("CA-LS+SG", "issued", F_SLACK, "ES"), "saving"), (sel("CA-LS+SG", "oracle", F_SLACK, "ES"), "saving"))
        res["X4"] = np.percentile(bs, 2.5) > 0; p["X4"] = np.mean(bs <= 0)
        out.append(f"X4 R(DE_LU) - R(ES) = {ci(pt, bs)}")
    # X5: runtime noise -> CA-LS misses exceed HEFT by > 10 pp at every f
    ps, txt, ok = [], [], True
    for f in F_ALL:
        s = sel("CA-LS+SG", "issued", [f])
        pt, bs = bt.stat(diff, (s, "miss_rt"), (s, "heft_miss_rt"))
        ok &= np.percentile(bs, 2.5) > 0.10; ps.append(np.mean(bs <= 0.10)); txt.append(f"{f}: {ci(pt, bs, 100)}")
    res["X5"] = ok; p["X5"] = max(ps); out.append("X5 miss - HEFT miss pp " + "; ".join(txt))
    if verbose:
        for o in out:
            print(f"[{label}] {o}")
    return res, p


def holm(p):
    k = sorted(p, key=p.get); m = len(k); adj, run = {}, 0
    for i, h in enumerate(k):
        run = max(run, min(1, (m - i) * p[h])); adj[h] = run
    return adj


print("== Sanity checks")
print("rows", len(d), " jobs", d.groupby(["region", "seed", "wf", "T", "t0"]).ngroups, " (planned 2400)")
print("submissions per zone", d.groupby("region").t0.nunique().to_dict())
print("nominal misses", int(d.miss.sum()))
for s in ["CA-List+SG", "CA-LS+SG", "CaWoSched+SG", "CWM+SG"]:
    print(f"oracle trap rate {s}: {100*d[(d.sched==s)&(d.regime=='oracle')].trap.mean():.2f}% (must be 0)")

print("\n== Primary (pooled over zones, clusters = zone x submission)")
res, p = hypotheses(d, "pooled")
adj = holm(p)
for h in res:
    print(f"{h}: criterion {'met' if res[h] else 'not met'}; one-sided p = {p[h]:.4f}; Holm p = {adj[h]:.4f}"
          f" -> {'Supported' if res[h] and adj[h] <= 0.025 else 'Not supported'}")

print("\n== Secondary: other clusterings")
for unit in ("day", "week"):
    r, pp = hypotheses(d, f"pooled/{unit}", unit)
    print(f"[{unit}] clusters={d[['region', unit]].drop_duplicates().shape[0]} criteria={r} Holm={ {h: round(v, 4) for h, v in holm(pp).items()} }")

print("\n== Secondary: per zone (X1-X3, X5)")
for z in sorted(d.region.unique()):
    hypotheses(d[d.region == z], z)

print("\n== Descriptive: by season (CA-LS+SG, f >= 1.5 for R; all f for traps)")
rows = []
for (z, s), g in d.groupby(["region", "season"]):
    a = g[(g.sched == "CA-LS+SG") & g.f.isin(F_SLACK)]
    R = a[a.regime == "issued"].saving.mean() / a[a.regime == "oracle"].saving.mean()
    b = g[(g.regime == "issued")]
    rows.append(dict(zone=z, season=s, n_sub=g.t0.nunique(), oracle_saving=100 * a[a.regime == "oracle"].saving.mean(), R=R,
                     trap1=100 * b[b.sched == "CA-LS+SG"].trap1.mean(), trap1_gate=100 * b[b.sched == "CA-LS+SG+Gate"].trap1.mean()))
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("\n== Descriptive: emission saving % and native saving % (oracle vs issued)")
for col in ["saving", "native_saving"]:
    t = d[d.sched.isin(["CA-LS+SG", "CA-LS+SG+Gate", "CaWoSched+SG", "CWM+SG", "Shift"])].pivot_table(
        index=["sched", "region"], columns="regime", values=col, aggfunc="mean").mul(100).round(2)
    print(f"\n-- {col}"); print(t.to_string())
print("\n-- trap1 % issued by scheduler and zone")
print(d[d.regime == "issued"].pivot_table(index="sched", columns="region", values="trap1", aggfunc="mean").mul(100).round(2).to_string())
print("\n-- deadline misses with runtime noise %, issued, by scheduler and f")
print(d[d.regime == "issued"].groupby(["sched", "f"]).agg(miss_rt=("miss_rt", "mean"), heft=("heft_miss_rt", "mean")).mul(100).round(2).to_string())
