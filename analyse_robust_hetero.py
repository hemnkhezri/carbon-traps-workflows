"""Post-hoc robustness of the platform-study verdicts (Deep Review item M5), as analyse_robust_stats.py:
cluster bootstrap over region x submission, region x calendar day and region x ISO week; one-sided bootstrap p-values
(intersection-union for composite hypotheses); Holm over G1-G5 at a one-sided family level of 0.025."""
import numpy as np
import pandas as pd

B = 2000
d = pd.read_csv("results/hetero.csv")
d["day"] = pd.to_datetime(d.t0, unit="s").dt.floor("D")
d["week"] = pd.to_datetime(d.t0, unit="s").dt.isocalendar().week.astype(int)
F = sorted(d.f.unique()); FS = [f for f in F if f >= 1.5]
for unit in ("t0", "day", "week"):
    keys = d[["region", unit]].drop_duplicates().reset_index(drop=True); keys["c"] = np.arange(len(keys))
    df = d.merge(keys, on=["region", unit]); n = len(keys)
    rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(B)]
    sel = lambda s, r, fs: df[(df.sched == s) & (df.regime == r) & (df.f.isin(fs))]
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
        with np.errstate(invalid="ignore", divide="ignore"):
            bs = np.array([f(i) for i in idx])
        bs = bs[np.isfinite(bs)]
        return f(np.arange(n)), np.percentile(bs, 2.5), np.percentile(bs, 97.5), bs
    pv = {}
    r = stat(sel("CA-LS+SG", "issued", FS), "saving", sel("CA-LS+SG", "oracle", FS), "saving", "ratio")
    pv["G1"] = np.mean(r[3] >= 0.75)
    tr = [stat(sel("CA-LS+SG", "issued", [f]), "trap1") for f in F]
    pv["G2"] = max(np.mean(t[3] <= 0.02) for t in tr)
    td = stat(sel("CA-LS+SG+Gate", "issued", F), "trap1", sel("CA-LS+SG", "issued", F), "trap1", "diff")
    rr = stat(sel("CA-LS+SG+Gate", "issued", F), "saving", sel("CA-LS+SG", "issued", F), "saving", "ratio")
    pv["G3"] = max(np.mean(td[3] >= 0), np.mean(rr[3] < 0.5))
    rn = stat(sel("CWM+SG", "issued", FS), "native_saving", sel("CWM+SG", "oracle", FS), "native_saving", "ratio")
    pv["G4"] = np.mean(rn[3] >= 0.75)
    md = [stat(sel("CA-LS+SG", "issued", [f]), "miss_rt", sel("CA-LS+SG", "issued", [f]), "heft_miss_rt", "diff") for f in F]
    pv["G5"] = max(np.mean(m[3] <= 0.10) for m in md)
    print(f"\n-- cluster unit: region x {unit} (n = {n})")
    print(f"G1 R = {r[0]:.3f} [{r[1]:.3f}, {r[2]:.3f}]")
    print("G2 traps: " + "; ".join(f"{f}: {100*t[0]:.1f} [{100*t[1]:.1f}, {100*t[2]:.1f}]" for f, t in zip(F, tr)))
    print(f"G3 trap diff {100*td[0]:.2f} [{100*td[1]:.2f}, {100*td[2]:.2f}] pp; retention {rr[0]:.2f} [{rr[1]:.2f}, {rr[2]:.2f}]")
    print(f"G4 R native = {rn[0]:.2f} [{rn[1]:.2f}, {rn[2]:.2f}]")
    print("G5 miss gap: " + "; ".join(f"{f}: {100*m[0]:.1f} [{100*m[1]:.1f}, {100*m[2]:.1f}]" for f, m in zip(F, md)))
    keys_ = sorted(pv, key=pv.get); m = len(keys_); out = []
    for i, k in enumerate(keys_):
        adj = min(1.0, max((m - j) * pv[keys_[j]] for j in range(i + 1)))
        out.append(f"{k}: p={pv[k]:.4f}, Holm={adj:.4f} -> {'supported' if adj < 0.025 else 'not supported'}")
    print("Holm (one-sided, family alpha 0.025): " + " | ".join(out))
