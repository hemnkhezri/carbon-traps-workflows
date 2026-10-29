"""Adapter for the official CaWoSched code (Schweisgut, Benoit, Robert,
Meyerhenke, ICPP 2025; github.com/KIT-EAE/CaWoSched, MIT licence).

CaWoSched keeps a fixed mapping and per-processor order (here: from HEFT) and
shifts start times to minimise brown energy above a time-varying green power
budget. Following CWM (arXiv 2605.27652), carbon intensity is mapped to a
green budget by inverting and linearly rescaling it into [0, P x work power]
over the planning horizon. Idle power is set to 0 (idle power is not
attributed in our model) and every cross-machine edge carries a 1-minute transfer in CaWoSched (its
validity check rejects zero-volume edges), which is slightly conservative for
CaWoSched; our simulator has no transfer time, so its schedules stay valid.
Two variants are run (slackR-LS, pressR-LS); the one with the lower CaWoSched
cost on the planning budget is kept.
"""
import os
import subprocess
import tempfile

import numpy as np

BIN = os.path.join(os.path.dirname(__file__), "..", "external", "cawo_dump")
WORK = 10  # work power units per busy processor
BUDGET_SCALE = 10  # integer resolution of the budget


def machine_assignment(start, dur, P):
    """Assign HEFT intervals to P machines (interval-graph colouring)."""
    order = np.argsort(start, kind="stable")
    free_at = np.zeros(P, dtype=int)
    m = np.zeros(len(start), dtype=int)
    for i in order:
        k = int(np.argmin(np.where(free_at <= start[i], 0, 1) * 10**9 + free_at))
        if free_at[k] > start[i]:
            raise RuntimeError("capacity violated in HEFT plan")
        m[i] = k
        free_at[k] = start[i] + dur[i]
    return m


def run(inst, P, D, heft_start, plan_ci_windows):
    """Return (start_times or None, info)."""
    dur = inst.dur
    mach = machine_assignment(heft_start, dur, P)
    n_int = int(np.ceil(D / 30))
    ci = np.asarray(plan_ci_windows[:n_int], float)
    lo, hi = ci.min(), ci.max()
    rel = (hi - ci) / (hi - lo) if hi > lo else np.ones_like(ci)
    budget = np.round(rel * P * WORK * BUDGET_SCALE).astype(int)
    bounds = [min(30 * k, D) for k in range(n_int + 1)]
    with tempfile.TemporaryDirectory() as td:
        dag = os.path.join(td, "wf.dot")
        with open(dag, "w") as f:
            f.write('strict digraph "G" {\n')
            for i, d in enumerate(dur):
                f.write(f"{i} [weight={int(d)}];\n")
            for i, ss in enumerate(inst.succs):
                for j in ss:
                    f.write(f"{i} -> {j} [size=1];\n")
            f.write("}\n")
        mp = os.path.join(td, "map.txt")
        with open(mp, "w") as f:
            f.write(f"{P}\n")
            for k in range(P):
                tasks = [i for i in np.argsort(heft_start, kind="stable") if mach[i] == k]
                f.write(" ".join(str(int(t)) for t in tasks) + "\n")
        su = os.path.join(td, "setup.txt")
        npe = P * P  # processors + communication processors
        with open(su, "w") as f:
            f.write(f"{D}\n{n_int}\n")
            f.write(" ".join("0" for _ in range(npe)) + "\n")
            f.write(" ".join(str(WORK * BUDGET_SCALE if k < P else 0) for k in range(npe)) + "\n")
            f.write("1\n")
            f.write(" ".join(str(b) for b in budget) + "\n")
            f.write(" ".join(str(b) for b in bounds) + "\n")
        best = None
        for variant in ("slackR", "pressR"):
            out = subprocess.run([BIN, dag, mp, su, variant], capture_output=True, text=True, timeout=600)
            lines = out.stdout.splitlines()
            valid = any(l.strip() == "VALID 1" for l in lines)
            cost = next((int(l.split()[1]) for l in lines if l.startswith("COST")), -1)
            st = np.full(len(dur), -1, dtype=int)
            for l in lines:
                if l.startswith("Task "):
                    parts = l.split()
                    t, a = int(parts[1]), int(parts[3])
                    if t < len(dur):
                        st[t] = a
            if valid and (st >= 0).all() and (best is None or cost < best[1]):
                best = (st, cost, variant)
    if best is None:
        return None, "invalid"
    return best[0], best[2]
