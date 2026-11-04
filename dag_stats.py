"""DAG structure statistics of the workflow instances (requested by internal review). Seed 10, T = 12 h."""
import numpy as np, pandas as pd
from cwf.workflows import SPECS, build_raw, scaled_instance
from cwf.sched import heft
rows = []
for seed in (10, 11):
    for wi, (lab, rec, n) in enumerate(SPECS):
        inst, M = scaled_instance(build_raw(rec, n, seed * 100 + wi), 8, 720)
        dur = inst.dur; W = dur.sum(); cp = inst.bl.max()
        # levels (longest path in edges from entry) -> width = max tasks per level
        lvl = np.zeros(len(dur), int)
        for i in sorted(range(len(dur)), key=lambda i: -inst.bl[i]):
            for j in inst.succs[i]:
                lvl[j] = max(lvl[j], lvl[i] + 1)
        width = np.bincount(lvl).max()
        s = heft(inst, 8, int(W) + 10)
        D = int(1.5 * M)
        lst = D - inst.bl  # latest start ignoring capacity
        freedom = (lst - s) > 0
        rows.append(dict(seed=seed, workflow=lab, tasks=len(dur), depth=lvl.max() + 1, width=width,
                         cp_over_M=round(cp / M, 2), work_over_PM=round(W / (8 * M), 2),
                         frac_free_at_1_5=round(freedom.mean(), 2)))
d = pd.DataFrame(rows)
print(d[d.seed == 10].drop(columns="seed").to_string(index=False))
print("\nmeans over seeds 10-11:", d.drop(columns=["seed", "workflow"]).mean().round(2).to_dict())
