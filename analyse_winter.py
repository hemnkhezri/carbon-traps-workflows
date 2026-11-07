"""Winter replication analysis (osf_registration/WINTER_REPLICATION_PREREG.md), W1-W5.
Usage: python analyse_winter.py CONFIRM_STYLE_CSV REVISION_A_CSV  (outputs of run_confirm.py and run_revision.py --part A)"""
import sys
import numpy as np, pandas as pd
C = pd.read_csv(sys.argv[1]); A = pd.read_csv(sys.argv[2])
d = pd.concat([C, A[A.sched == "CA-LS+SG+Res75"]], ignore_index=True)
B = 2000
for unit in ("t0", "day", "week"):
    x = d.copy(); ts = pd.to_datetime(x.t0, unit="s")
    x["u"] = x.t0 if unit == "t0" else (ts.dt.floor("D") if unit == "day" else ts.dt.isocalendar().week.astype(int))
    keys = {k: i for i, k in enumerate(sorted(x.u.unique()))}; x["c"] = x.u.map(keys); n = len(keys)
    rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(B)]
    def sk(s, col):
        g = s.groupby("c")[col].agg(["sum", "count"]); a = np.zeros(n); k = np.zeros(n)
        a[g.index] = g["sum"].astype(float); k[g.index] = g["count"]; return a, k
    def st(s1, c1, s2=None, c2=None, kind="mean"):
        a1, k1 = sk(s1, c1)
        if kind == "mean": f = lambda i: a1[i].sum() / k1[i].sum()
        else:
            a2, k2 = sk(s2, c2)
            f = (lambda i: (a1[i].sum() / k1[i].sum()) / (a2[i].sum() / k2[i].sum())) if kind == "ratio" else (lambda i: a1[i].sum() / k1[i].sum() - a2[i].sum() / k2[i].sum())
        bs = np.array([f(i) for i in idx]); return f(np.arange(n)), np.percentile(bs, 2.5), np.percentile(bs, 97.5), bs
    sel = lambda s, r, fs=None: x[(x.sched == s) & (x.regime == r) & (x.f.isin(fs) if fs is not None else True)]
    FS = [1.5, 2.0, 3.0]; F = sorted(x.f.unique()); p = {}
    w1 = st(sel("CA-LS+SG", "issued", FS), "saving", sel("CA-LS+SG", "oracle", FS), "saving", "ratio"); p["W1"] = np.mean(w1[3] >= 0.75)
    w2 = [st(sel("CA-LS+SG", "issued", [f]), "trap1") for f in F]; p["W2"] = max(np.mean(t[3] <= 0.02) for t in w2)
    g = st(sel("CA-LS+SG+Gate", "issued"), "trap1", sel("CA-LS+SG", "issued"), "trap1", "diff")
    gr = st(sel("CA-LS+SG+Gate", "issued"), "saving", sel("CA-LS+SG", "issued"), "saving", "ratio"); p["W3"] = max(np.mean(g[3] >= 0), np.mean(gr[3] < 0.5))
    r = sel("CA-LS+SG+Res75", "issued", FS)
    w4a = st(r, "miss_rt", r, "heft_miss_rt", "diff"); w4b = st(r, "saving", sel("CA-LS+SG", "issued", FS), "saving", "ratio")
    p["W4"] = max(np.mean(w4a[3] >= 0.05), np.mean(w4b[3] < 0.7))
    w5 = st(sel("Shift", "issued", FS), "saving", sel("CA-LS+SG", "issued", FS), "saving", "diff"); p["W5"] = max(np.mean(w5[3] >= 0.01), np.mean(w5[3] <= -0.01))
    print(f"-- cluster {unit} (n={n})")
    print(f"W1 R = {w1[0]:.3f} [{w1[1]:.3f}, {w1[2]:.3f}]")
    print("W2 traps: " + "; ".join(f"{f}: {100*t[0]:.1f} [{100*t[1]:.1f}, {100*t[2]:.1f}]" for f, t in zip(F, w2)))
    print(f"W3 trap diff {100*g[0]:.2f} [{100*g[1]:.2f}, {100*g[2]:.2f}] pp; retention {gr[0]:.2f} [{gr[1]:.2f}, {gr[2]:.2f}]")
    print(f"W4 miss gap {100*w4a[0]:.1f} [{100*w4a[1]:.1f}, {100*w4a[2]:.1f}] pp; saving ratio {w4b[0]:.2f} [{w4b[1]:.2f}, {w4b[2]:.2f}]")
    print(f"W5 Shift - CA-LS {100*w5[0]:.2f} [{100*w5[1]:.2f}, {100*w5[2]:.2f}] pp")
    ks = sorted(p, key=p.get); m = len(ks)
    print("Holm: " + " | ".join(f"{k}: p={p[k]:.4f} adj={min(1, max((m-j)*p[ks[j]] for j in range(i+1))):.4f} -> {'supported' if min(1, max((m-j)*p[ks[j]] for j in range(i+1))) < 0.025 else 'not supported'}" for i, k in enumerate(ks)))
