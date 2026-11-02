"""CWM adapter for the heterogeneous platform (cwf/hetero.py): CWM's own two processor types,
4 of each, idle power included. Green budget = total idle power + rel x frac x total dynamic power,
following CWM's mapping of CI into [P_min, P_min + frac x dynamic power]. Powers are scaled by 10
for integer budget resolution. Same binary and patch as cwf/cwm.py."""
import json
import os
import subprocess
import tempfile

import numpy as np

from . import hetero as H

BIN = os.path.join(os.path.dirname(__file__), "..", "external", "cwm_dump")
SCALE = 10


def run(h, D, plan_ci_windows, frac, variant="local-search"):
    n_int = int(np.ceil(D / 30))
    ci = np.asarray(plan_ci_windows[:n_int], float)
    lo, hi = ci.min(), ci.max()
    rel = (hi - ci) / (hi - lo) if hi > lo else np.ones_like(ci)
    base, dyn = H.IDLE.sum(), (H.WORK - H.IDLE).sum()
    budget = [int(x) for x in np.round((base + rel * frac * dyn) * SCALE)]
    bounds = [min(30 * k, D) for k in range(n_int + 1)]
    with tempfile.TemporaryDirectory() as td:
        dag = os.path.join(td, "wf.dot")
        with open(dag, "w") as f:
            for i, w in enumerate(h.w):
                f.write(f"{i} [weight={int(w)}]\n")
            for i, ss in enumerate(h.succs):
                for j in ss:
                    f.write(f"{i} -> {j} [size=0]\n")
        cl = os.path.join(td, "cluster.json")
        json.dump({"number_of_processor_types": 2,
                   "processors": [{"speed_value": 1, "idle_power": 1 * SCALE, "work_power": 10 * SCALE},
                                  {"speed_value": 2, "idle_power": 2 * SCALE, "work_power": 15 * SCALE}],
                   "clusters": [{"cluster_id": "c", "processors_per_type": 4,
                                 "communication_idle_powers": [0] * (H.P * (H.P - 1)),
                                 "communication_work_powers": [0] * (H.P * (H.P - 1))}]}, open(cl, "w"))
        pr = os.path.join(td, "profile.json")
        json.dump({"horizon": D, "number_of_intervals": n_int, "intervals": bounds, "budgets": budget}, open(pr, "w"))
        out = subprocess.run([BIN, dag, cl, "c", pr, variant, str(D)], capture_output=True, text=True, timeout=900)
    lines = out.stdout.splitlines()
    if not any(l.strip() == "VALID 1" for l in lines):
        return None, None, "invalid"
    n = len(h.w)
    st = np.full(n, -1, int); mc = np.full(n, -1, int); en = np.full(n, -1, int)
    for l in lines:
        if l.startswith("T "):
            _, t, a, e, p = l.split()
            st[int(t)], en[int(t)], mc[int(t)] = int(a), int(e), int(p)
    if (st < 0).any():
        return None, None, "incomplete"
    if not np.array_equal(en - st, h.d[np.arange(n), mc]):
        return None, None, "duration-mismatch"
    return st, mc, "ok"
