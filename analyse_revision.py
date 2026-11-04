"""Analysis of the revision robustness study (EXT3_PREREG.md, Q1-Q4, Q6). Cluster bootstrap over calendar days.
Usage: python analyse_revision.py A_CSV[,A_CSV2] [B_CSV[,B_CSV2]] [CONFIRM_CSV]"""
import sys

import numpy as np
import pandas as pd

B = 2000
A = pd.concat([pd.read_csv(p) for p in sys.argv[1].split(",")])
Bd = pd.concat([pd.read_csv(p) for p in sys.argv[2].split(",")]) if len(sys.argv) > 2 and sys.argv[2] else None
F = sorted(A.f.unique()); FS = [f for f in F if f >= 1.5]


def boot_fn(df):
    df = df.copy(); df["day"] = pd.to_datetime(df.t0, unit="s").dt.floor("D")
    keys = df[["day"]].drop_duplicates().reset_index(drop=True); keys["c"] = np.arange(len(keys))
    df = df.merge(keys, on="day"); n = len(keys)
    rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(B)]
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
    return df, stat, n


df, stat, n = boot_fn(A)
sel = lambda s, r, fs=F: df[(df.sched == s) & (df.regime == r) & (df.f.isin(fs))]
fm = lambda t, k=100, d=2: f"{k*t[0]:.{d}f} [{k*t[1]:.{d}f}, {k*t[2]:.{d}f}]"
print(f"== Sanity: rows {len(A)}, jobs {A.groupby(['seed','wf','T','t0']).ngroups}, days {n}")
sg = A[A.sched.str.contains(r"\+SG|Shift|RH-", regex=True)]
print("nominal misses (safeguarded, Shift, RH):", int(sg.miss.sum()))
print("oracle trap rate of safeguarded variants:", round(100 * A[(A.regime == 'oracle') & A.sched.str.contains('SG')].trap.mean(), 3), "%")
if len(sys.argv) > 3:
    C = pd.read_csv(sys.argv[3]); C = C[(C.sched == "CA-LS+SG") & C.seed.isin(A.seed.unique())]
    ref = A[A.sched == "CA-LS+SG"].merge(C, on=["seed", "wf", "T", "f", "t0", "regime"], suffixes=("", "_c"))
    print("reference CA-LS+SG vs confirmatory: rows matched", len(ref), " max |saving diff|", float((ref.saving - ref.saving_c).abs().max()))

print("\n== Q1 Re-planning (issued; R relative to static CA-LS+SG oracle, f >= 1.5)")
for s in ("CA-LS+SG", "RH-CA-LS+SG", "CA-LS+SG+Gate[diff0.9]", "RH-CA-LS+SG+Gate", "Shift", "RH-Shift", "Shift+Gate", "RH-Shift+Gate"):
    ref = "Shift" if "Shift" in s else "CA-LS+SG"
    r = stat(sel(s, "issued", FS), "saving", sel(ref, "oracle", FS), "saving", "ratio")
    t = stat(sel(s, "issued"), "trap1")
    print(f"{s:24s} R = {fm(r, 1)}   trap1 = {fm(t, 100, 1)}%   saving = {100*sel(s,'issued',FS).saving.mean():.2f}%")
r = stat(sel("RH-CA-LS+SG", "issued", FS), "saving", sel("CA-LS+SG", "oracle", FS), "saving", "ratio")
t = stat(sel("RH-CA-LS+SG", "issued"), "trap1")
print("Q1 reading:", "A (open-loop artefact)" if (r[2] >= 0.9 and t[2] < 0.02) else "B (re-planning does not remove the loss)")
print("mean re-plans per run:", round(A[A.sched == "RH-CA-LS+SG"].n_replans.mean(), 1))

print("\n== Q2 Executor (issued): miss - HEFT miss, pp")
ok = True
for f in F:
    a = stat(sel("CA-LS+SG", "issued", [f]), "miss_rt", sel("CA-LS+SG", "issued", [f]), "heft_miss_rt", "diff")
    b = stat(sel("CA-LS+SG", "issued", [f]), "miss_rr", sel("CA-LS+SG", "issued", [f]), "heft_miss_rr", "diff")
    ok &= b[1] > 0.10
    print(f"f={f}: static executor {fm(a, 100, 1)}; reactive executor {fm(b, 100, 1)}")
print("Q2 reading:", "robust to executor" if ok else "executor-dependent")

print("\n== Q3 Saving vs deadline misses (issued, all f): saving %, miss static %, miss reactive %, trap1 %")
for s in ("CA-LS+SG", "CA-LS+SG+Res75", "CA-LS+SG+Res50", "CA-LS+SG+Gate[diff0.9]", "Shift", "Shift+Gate"):
    x = sel(s, "issued")
    print(f"{s:24s} {100*x.saving.mean():6.2f} {100*x.miss_rt.mean():7.1f} {100*x.miss_rr.mean():7.1f} {100*x.trap1.mean():6.1f}")
h = sel("CA-LS+SG", "issued"); print(f"{'HEFT':24s} {0:6.2f} {100*h.heft_miss_rt.mean():7.1f} {100*h.heft_miss_rr.mean():7.1f} {0:6.1f}")
for s in ("CA-LS+SG+Res75", "CA-LS+SG+Res50"):
    r = stat(sel(s, "issued", FS), "saving", sel(s, "oracle", FS), "saving", "ratio")
    print(f"{s}: R (own oracle) = {fm(r, 1)}")

print("\n== Q4 Gate alternatives (issued, all f): saving, trap1, paired differences vs diff0.9")
g0 = "CA-LS+SG+Gate[diff0.9]"
for g in ("diff0.5", "diff0.8", "diff0.9", "diff0.95", "const", "level", "lagcap6"):
    s = f"CA-LS+SG+Gate[{g}]"
    sv = stat(sel(s, "issued"), "saving"); tr = stat(sel(s, "issued"), "trap1")
    ds = stat(sel(s, "issued"), "saving", sel(g0, "issued"), "saving", "diff")
    dt = stat(sel(s, "issued"), "trap1", sel(g0, "issued"), "trap1", "diff")
    dom = ds[1] > 0 and dt[2] < 0
    print(f"{g:9s} saving {fm(sv)}%  trap1 {fm(tr, 100, 1)}%  d_saving {fm(ds)} pp  d_trap {fm(dt, 100, 1)} pp  miss_rt {100*sel(s,'issued').miss_rt.mean():.1f}%{'  DOMINATES diff0.9' if dom else ''}")
x = sel("CA-LS+SG", "issued"); print(f"no gate   saving {100*x.saving.mean():.2f}%  trap1 {100*x.trap1.mean():.1f}%")

if Bd is not None:
    print("\n== Q6 Official tools with budget fraction (GB): mean saving % oracle / issued, R (f >= 1.5), trap1 issued %")
    for s in sorted(Bd.sched.unique()):
        x = Bd[Bd.sched == s]; o = x[(x.regime == "oracle") & x.f.isin(FS)].saving.mean(); i = x[(x.regime == "issued") & x.f.isin(FS)].saving.mean()
        print(f"{s:20s} {100*x[x.regime=='oracle'].saving.mean():6.2f} / {100*x[x.regime=='issued'].saving.mean():6.2f}   R {i/o if o else float('nan'):.2f}   trap1 {100*x[x.regime=='issued'].trap1.mean():.1f}")
