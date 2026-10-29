"""Execute a plan with realised (noisy) runtimes.

Rule (same for every scheduler, HEFT included): tasks are dispatched in order
of planned start; a task starts at max(planned start, all predecessors
finished, earliest time a machine is free for its realised duration).
"""
import numpy as np

from .sched import Cluster


def execute(inst, plan, rdur, P, H):
    cl = Cluster(P, H)
    n = len(plan)
    fin = np.zeros(n, dtype=int)
    st = np.zeros(n, dtype=int)
    for i in np.argsort(plan, kind="stable"):
        ready = max([int(plan[i])] + [int(fin[j]) for j in inst.preds[i]])
        d = int(rdur[i])
        lo, ok = cl.free_starts(d, ready, H)
        nz = np.flatnonzero(ok)
        if len(nz) == 0:
            raise RuntimeError("execution horizon too short")
        s = lo + nz[0]
        cl.place(s, d)
        st[i], fin[i] = s, s + d
    return st, fin


def noisy_durations(dur, rng, sigma=0.2):
    return np.maximum(1, np.round(dur * np.exp(rng.normal(0.0, sigma, size=len(dur))))).astype(int)
