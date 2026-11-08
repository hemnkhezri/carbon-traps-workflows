"""Confirmatory analysis, fixed before the confirmatory run (CONFIRM_PREREG.md).

Uncertainty: cluster bootstrap over submission times t0 (all runs that share a
t0 share the same CI trace), 2000 resamples, percentile 95% intervals, rng seed 2026.
Usage: python analyse_confirm.py RESULTS_CSV
"""
import sys

import numpy as np
import pandas as pd

B = 2000
RNG = np.random.default_rng(2026)
d = pd.read_csv(sys.argv[1])
F_ALL = sorted(d.f.unique())
F_SLACK = [f for f in F_ALL if f >= 1.5]
t0s = np.sort(d.t0.unique())
idx = {t: i for i, t in enumerate(t0s)}
d["c"] = d.t0.map(idx)
BOOT = [RNG.integers(0, len(t0s), len(t0s)) for _ in range(B)]


def cluster_sums(sub, col):
    g = sub.groupby("c")[col].agg(["sum", "count"])
    s = np.zeros(len(t0s)); n = np.zeros(len(t0s))
    s[g.index] = g["sum"].to_numpy(float); n[g.index] = g["count"].to_numpy(float)
    return s, n


def pct(bs):
    bs = np.asarray(bs, float)
    bs = bs[np.isfinite(bs)]
    return np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def mean_ci(sub, col):
    s, n = cluster_sums(sub, col)
    est = s.sum() / n.sum()
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = [s[b].sum() / n[b].sum() for b in BOOT]
    return (est, *pct(bs))


def ratio_ci(num, den, col):
    s1, n1 = cluster_sums(num, col); s2, n2 = cluster_sums(den, col)
    est = (s1.sum() / n1.sum()) / (s2.sum() / n2.sum())
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = [(s1[b].sum() / n1[b].sum()) / (s2[b].sum() / n2[b].sum()) for b in BOOT]
    return (est, *pct(bs))


def diff_ci(a, b_, col):
    s1, n1 = cluster_sums(a, col); s2, n2 = cluster_sums(b_, col)
    est = s1.sum() / n1.sum() - s2.sum() / n2.sum()
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = [s1[b].sum() / n1[b].sum() - s2[b].sum() / n2[b].sum() for b in BOOT]
    return (est, *pct(bs))


def sel(sched, regime, fs):
    return d[(d.sched == sched) & (d.regime == regime) & (d.f.isin(fs))]


def fmt(t, pct=True):
    k = 100 if pct else 1
    return f"{k*t[0]:.2f} [{k*t[1]:.2f}, {k*t[2]:.2f}]"


print("== Sanity checks")
print("rows:", len(d), " submissions:", len(t0s), " jobs:", d.groupby(["seed", "wf", "T", "t0"]).ngroups)
print("nominal deadline misses (all schedulers):", int(d.miss.sum()))
for s in ["CA-List+SG", "CA-LS+SG", "CaWoSched+SG"]:
    print(f"oracle trap rate {s}: {100*sel(s, 'oracle', F_ALL).trap.mean():.2f}% (must be 0)")
print("share of runs where the safeguard kept HEFT:")
print((d.groupby(["sched", "regime"]).used_heft.mean() * 100).round(1).to_string())

res = {}
print("\n== H1: relative loss, CA-LS+SG, f >= 1.5 pooled. Supported if upper bound < 0.75")
r = ratio_ci(sel("CA-LS+SG", "issued", F_SLACK), sel("CA-LS+SG", "oracle", F_SLACK), "saving")
res["H1"] = r[2] < 0.75
print(f"R = issued/oracle mean saving = {fmt(r, False)} -> {'SUPPORTED' if res['H1'] else 'NOT supported'}")

print("\n== H2: trap rate (>1%), CA-LS+SG issued, every f. Supported if every lower bound > 2%")
ok = True
for f in F_ALL:
    t = mean_ci(sel("CA-LS+SG", "issued", [f]), "trap1")
    ok &= t[1] > 0.02
    print(f"f={f}: {fmt(t)}")
res["H2"] = ok
print("->", "SUPPORTED" if ok else "NOT supported")

print("\n== H3: synthetic i.i.d. noise overstates savings, CA-LS+SG, f >= 1.5. Supported if lower bound > 0")
t = diff_ci(sel("CA-LS+SG", "synthetic", F_SLACK), sel("CA-LS+SG", "issued", F_SLACK), "saving")
res["H3"] = t[1] > 0
print(f"synthetic - issued mean saving (pp) = {fmt(t)} -> {'SUPPORTED' if res['H3'] else 'NOT supported'}")

print("\n== H4: gate, CA-LS+SG issued, all f. Supported if trap diff upper < 0 AND retention lower >= 0.5")
td = diff_ci(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "trap1")
rr = ratio_ci(sel("CA-LS+SG+Gate", "issued", F_ALL), sel("CA-LS+SG", "issued", F_ALL), "saving")
res["H4"] = (td[2] < 0) and (rr[1] >= 0.5)
print(f"trap1 gated - ungated (pp) = {fmt(td)}; retention = {fmt(rr, False)} -> {'SUPPORTED' if res['H4'] else 'NOT supported'}")

print("\n== H5 (secondary): H1 and H2 criteria for CA-List+SG and CaWoSched+SG")
for s in ["CA-List+SG", "CaWoSched+SG"]:
    r = ratio_ci(sel(s, "issued", F_SLACK), sel(s, "oracle", F_SLACK), "saving")
    traps = [mean_ci(sel(s, "issued", [f]), "trap1") for f in F_ALL]
    h1, h2 = r[2] < 0.75, all(t[1] > 0.02 for t in traps)
    print(f"{s}: R = {fmt(r, False)} ({'H1 ok' if h1 else 'H1 no'}); traps by f: "
          + "; ".join(f"{f}: {fmt(t)}" for f, t in zip(F_ALL, traps)) + f" ({'H2 ok' if h2 else 'H2 no'})")

print("\n== Summary:", res)

print("\n== Exploratory: mean saving % by scheduler, regime, f")
print(d.pivot_table(index=["sched", "f"], columns="regime", values="saving", aggfunc="mean").mul(100).round(2).to_string())
print("\n== Exploratory: trap rate (>1%) %")
print(d.pivot_table(index=["sched", "f"], columns="regime", values="trap1", aggfunc="mean").mul(100).round(2).to_string())
print("\n== Exploratory: runtime variability (issued) - deadline misses % and saving %")
iss = d[d.regime == "issued"]
print(iss.groupby(["sched", "f"]).agg(miss_rt=("miss_rt", "mean"), heft_miss_rt=("heft_miss_rt", "mean"),
                                       saving_rt=("saving_rt", "mean"), trap1_rt=("trap1_rt", "mean")).mul(100).round(2).to_string())
print("\n== Exploratory: by makespan target (issued vs oracle mean saving %)")
print(d[d.sched.isin(["CA-LS+SG", "Shift", "CaWoSched+SG"])].pivot_table(
    index=["sched", "T", "f"], columns="regime", values="saving", aggfunc="mean").mul(100).round(2).to_string())
