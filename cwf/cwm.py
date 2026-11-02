"""Adapter for the official CWM code (Schweisgut, Benoit, Robert, Meyerhenke,
Euro-Par 2026; github.com/KIT-EAE/CWM commit 50e9ef5, MIT licence).

CWM jointly maps and schedules a DAG on a cluster whose green power budget
varies over time. Our platform is homogeneous (one processor type, P
processors, speed 1, idle power 0), with no communication cost (edge sizes 0,
communication powers 0). Carbon intensity is mapped to a green budget exactly
as in the CaWoSched adapter: inverted and rescaled to [0, P x work power] over
the planning windows up to the deadline. The 'local-search' variant (CWM with
its local search, as evaluated in the paper) is used. Changes to the official
code: read-only accessors for the final schedule and #include <queue> for GCC
13 (external/cwm_patch.diff); no algorithmic change.
"""
import json
import os
import subprocess
import tempfile

import numpy as np

BIN = os.path.join(os.path.dirname(__file__), "..", "external", "cwm_dump")
WORK = 10
BUDGET_SCALE = 10


def run(inst, P, D, plan_ci_windows, variant="local-search", frac=1.0):
    dur = inst.dur
    n_int = int(np.ceil(D / 30))
    ci = np.asarray(plan_ci_windows[:n_int], float)
    lo, hi = ci.min(), ci.max()
    rel = (hi - ci) / (hi - lo) if hi > lo else np.ones_like(ci)
    budget = [int(x) for x in np.round(rel * frac * P * WORK * BUDGET_SCALE)]
    bounds = [min(30 * k, D) for k in range(n_int + 1)]
    with tempfile.TemporaryDirectory() as td:
        dag = os.path.join(td, "wf.dot")
        with open(dag, "w") as f:
            for i, d in enumerate(dur):
                f.write(f"{i} [weight={int(d)}]\n")
            for i, ss in enumerate(inst.succs):
                for j in ss:
                    f.write(f"{i} -> {j} [size=0]\n")
        cl = os.path.join(td, "cluster.json")
        json.dump({"number_of_processor_types": 1,
                   "processors": [{"speed_value": 1, "idle_power": 0, "work_power": WORK * BUDGET_SCALE}],
                   "clusters": [{"cluster_id": "c", "processors_per_type": P,
                                 "communication_idle_powers": [0] * (P * (P - 1)),
                                 "communication_work_powers": [0] * (P * (P - 1))}]}, open(cl, "w"))
        pr = os.path.join(td, "profile.json")
        json.dump({"horizon": D, "number_of_intervals": n_int, "intervals": bounds, "budgets": budget}, open(pr, "w"))
        out = subprocess.run([BIN, dag, cl, "c", pr, variant, str(D)], capture_output=True, text=True, timeout=900)
    lines = out.stdout.splitlines()
    if not any(l.strip() == "VALID 1" for l in lines):
        return None, "invalid"
    st = np.full(len(dur), -1, dtype=int)
    proc = np.full(len(dur), -1, dtype=int)
    for l in lines:
        if l.startswith("T "):
            _, t, a, e, p = l.split()
            st[int(t)] = int(a); proc[int(t)] = int(p)
    if (st < 0).any():
        return None, "incomplete"
    return st, "ok"
