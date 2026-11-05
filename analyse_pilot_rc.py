"""Go/no-go analysis for the RC-CAS pilot (PILOT_RC_PREREG.md)."""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); d["day"] = pd.to_datetime(d.t0, unit="s").dt.floor("D")
days = np.sort(d.day.unique()); d["c"] = d.day.map({x: i for i, x in enumerate(days)}); n = len(days)
rng = np.random.default_rng(2026); idx = [rng.integers(0, n, n) for _ in range(2000)]
def m(sub, col):
    g = sub.groupby("c")[col].agg(["sum", "count"]); s = np.zeros(n); k = np.zeros(n)
    s[g.index] = g["sum"].astype(float); k[g.index] = g["count"]; return s, k
def diff(a, b, col):
    s1, k1 = m(a, col); s2, k2 = m(b, col); f = lambda i: s1[i].sum() / k1[i].sum() - s2[i].sum() / k2[i].sum()
    bs = [f(i) for i in idx]; return f(np.arange(n)), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
FS = d.f >= 1.5
print(f"rows {len(d)}, submissions {d.t0.nunique()}, days {n}, nominal misses {int(d.miss.sum())}")
o = d[(d.sched == 'CA-LS+SG[oracle]') & FS].saving.mean()
print(f"{'scheduler':22s} saving(f>=1.5)  R    trap1(all f)  scen_trap(mean)")
for s in sorted(d.sched.unique()):
    x = d[d.sched == s]
    print(f"{s:22s} {100*x[x.f>=1.5].saving.mean():7.2f}   {x[x.f>=1.5].saving.mean()/o:5.2f}  {100*x.trap1.mean():6.1f}   "
          f"{'' if 'scen_trap' not in x or x.scen_trap.isna().all() else round(100*x.scen_trap.mean(),1)}")
g = d[d.sched == "CA-LS+SG+Gate[0.9]"]; gt = g.trap1.mean(); gs = g[g.f >= 1.5].saving.mean()
s1 = d[d.sched == "RC-CAS[0.1]"].trap1.mean() <= 0.12 and d[d.sched == "RC-CAS[0.05]"].trap1.mean() <= 0.07
s2 = False
for a in ("0.05", "0.1", "0.2"):
    x = d[d.sched == f"RC-CAS[{a}]"]
    dd = diff(x[x.f >= 1.5], g[g.f >= 1.5], "saving")
    ok = x.trap1.mean() <= gt and dd[0] >= max(0.01, 0.1 * gs) and dd[1] > 0
    s2 |= ok
    print(f"RC-CAS[{a}] vs gate: d_saving {100*dd[0]:.2f} [{100*dd[1]:.2f}, {100*dd[2]:.2f}] pp; trap {100*x.trap1.mean():.1f} vs {100*gt:.1f}  -> {'meets S2' if ok else 'fails S2'}")
print("S1 validity:", s1, "| S2 usefulness:", s2, "| DECISION:", "GO" if (s1 and s2) else "NO-GO")
