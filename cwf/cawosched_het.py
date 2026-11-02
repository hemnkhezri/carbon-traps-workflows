"""CaWoSched on the heterogeneous platform (exploratory addition, EXT2_DEVIATIONS.md item 1).
CaWoSched keeps a fixed mapping; its input gives each task one weight, so with the mapping fixed
(heterogeneous HEFT) each task's weight is its duration on its mapped machine. Per-machine idle and
work powers from cwf/hetero.py; green budget = idle + rel x frac x dynamic power (as cwf/cwm_het.py).
Same binary as cwf/cawosched.py; best of slackR / pressR by CaWoSched's own cost."""
import os
import subprocess
import tempfile

import numpy as np

from . import hetero as H

BIN = os.path.join(os.path.dirname(__file__), "..", "external", "cawo_dump")
SCALE = 10


def run(h, D, st, mc, plan_ci_windows, frac=1.0):
    n = len(st)
    dur = h.d[np.arange(n), mc]
    n_int = int(np.ceil(D / 30))
    ci = np.asarray(plan_ci_windows[:n_int], float)
    lo, hi = ci.min(), ci.max()
    rel = (hi - ci) / (hi - lo) if hi > lo else np.ones_like(ci)
    budget = np.round((H.IDLE.sum() + rel * frac * (H.WORK - H.IDLE).sum()) * SCALE).astype(int)
    bounds = [min(30 * k, D) for k in range(n_int + 1)]
    P = H.P
    with tempfile.TemporaryDirectory() as td:
        dag = os.path.join(td, "wf.dot")
        with open(dag, "w") as f:
            f.write('strict digraph "G" {\n')
            for i, d in enumerate(dur):
                f.write(f"{i} [weight={int(d)}];\n")
            for i, ss in enumerate(h.succs):
                for j in ss:
                    f.write(f"{i} -> {j} [size=1];\n")
            f.write("}\n")
        mp = os.path.join(td, "map.txt")
        order = np.argsort(st, kind="stable")
        with open(mp, "w") as f:
            f.write(f"{P}\n")
            for k in range(P):
                f.write(" ".join(str(int(t)) for t in order if mc[t] == k) + "\n")
        su = os.path.join(td, "setup.txt")
        npe = P * P
        with open(su, "w") as f:
            f.write(f"{D}\n{n_int}\n")
            f.write(" ".join(str(int(H.IDLE[k] * SCALE) if k < P else "0") for k in range(npe)) + "\n")
            f.write(" ".join(str(int(H.WORK[k] * SCALE) if k < P else "0") for k in range(npe)) + "\n")
            f.write("1\n")
            f.write(" ".join(str(b) for b in budget) + "\n")
            f.write(" ".join(str(b) for b in bounds) + "\n")
        best = None
        for variant in ("slackR", "pressR"):
            out = subprocess.run([BIN, dag, mp, su, variant], capture_output=True, text=True, timeout=600)
            lines = out.stdout.splitlines()
            valid = any(l.strip() == "VALID 1" for l in lines)
            cost = next((int(l.split()[1]) for l in lines if l.startswith("COST")), -1)
            s = np.full(n, -1, dtype=int)
            for l in lines:
                if l.startswith("Task "):
                    p = l.split()
                    if int(p[1]) < n:
                        s[int(p[1])] = int(p[3])
            if valid and (s >= 0).all() and (best is None or cost < best[1]):
                best = (s, cost)
    return None if best is None else best[0]
