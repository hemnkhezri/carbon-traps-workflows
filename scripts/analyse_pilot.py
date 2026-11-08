"""Apply the sealed stop rule (PREREG.md section 6) and the sanity checks (section 7)."""
import sys

import numpy as np
import pandas as pd

d = pd.read_csv(sys.argv[1])
FACT = [1.2, 1.5, 2.0]
heft = d[d.sched == "HEFT"]
ca = d[d.sched != "HEFT"].copy()
ca["saving"] = 1 - ca.carbon / ca.heft_carbon
ca["trap"] = ca.carbon > ca.heft_carbon * (1 + 1e-9)

print("== Sanity checks (section 7)")
n_jobs = d.groupby(["seed", "wf", "T", "t0"]).ngroups
print(f"completed jobs: {n_jobs} (planned 2400); rows {len(d)}")
print(f"HEFT deadline misses: {int(heft.miss.sum())}")
print(f"carbon-aware deadline misses: {int(ca.miss.sum())}")
ok = ca[(ca.sched == "CA-List") & (ca.regime == "oracle")].groupby("f").saving.median()
print("oracle median saving of CA-List by f:", (100 * ok).round(2).to_dict())
print("repair modes:", ca["mode"].value_counts().to_dict())

print("\n== Primary outcomes (issued regime, ungated)")
rows = []
for s in ["CA-List", "CA-LS"]:
    for f in FACT:
        g = ca[(ca.sched == s) & (ca.f == f)]
        med = {r: 100 * g[g.regime == r].saving.median() for r in ["oracle", "synthetic", "issued"]}
        iss = g[g.regime == "issued"]
        rows.append(dict(sched=s, f=f, oracle=med["oracle"], synthetic=med["synthetic"], issued=med["issued"],
                         loss_pp=med["oracle"] - med["issued"], trap_pct=100 * iss.trap.mean(),
                         syn_trap_pct=100 * g[g.regime == "synthetic"].trap.mean(), n=len(iss)))
prim = pd.DataFrame(rows)
print(prim.round(2).to_string(index=False))

drop = all((r.loss_pp < 5) and (r.trap_pct < 2) for r in prim.itertuples())
print("\nSTOP RULE ->", "DROP the topic" if drop else "CONTINUE to confirmatory study")

print("\n== Exploratory: gated schedulers")
rows = []
for s in ["CA-List+Gate", "CA-LS+Gate"]:
    for f in FACT:
        g = ca[(ca.sched == s) & (ca.f == f)]
        rows.append(dict(sched=s, f=f, oracle=100 * g[g.regime == "oracle"].saving.median(),
                         issued=100 * g[g.regime == "issued"].saving.median(),
                         trap_pct=100 * g[g.regime == "issued"].trap.mean()))
print(pd.DataFrame(rows).round(2).to_string(index=False))

print("\n== Exploratory: by makespan target (CA-LS, issued vs oracle)")
g = ca[ca.sched == "CA-LS"]
t = g.pivot_table(index=["T", "f"], columns="regime", values="saving", aggfunc="median") * 100
t["trap_issued_pct"] = g[g.regime == "issued"].groupby(["T", "f"]).trap.mean() * 100
print(t.round(2).to_string())

print("\n== Exploratory: mean (not median) saving and trap severity, CA-LS issued")
iss = g[g.regime == "issued"]
print("mean saving %:", (100 * iss.groupby("f").saving.mean()).round(2).to_dict())
tr = iss[iss.trap]
print("trap runs: median excess emissions % over HEFT:", (100 * (-tr.saving)).median().round(2) if len(tr) else None)
