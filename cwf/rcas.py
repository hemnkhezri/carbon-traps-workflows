"""RC-CAS v2: chance-constrained local search over forecast-error scenarios."""
import numpy as np

from .sched import Cluster


def cluster_of(inst, start, P, H):
    cl = Cluster(P, H)
    for s, d in zip(start, inst.dur):
        cl.place(int(s), int(d))
    return cl


def plan_costs(inst, start, SP):
    s = np.asarray(start, int); d = np.asarray(inst.dur, int)
    return (SP[:, s + d] - SP[:, s]).sum(axis=1)


def allowed(alpha, K):
    """Largest trap count m with (m + 1) / (K + 1) <= alpha (conformal-style counting rule); -1 if none."""
    return int(np.floor(alpha * (K + 1) - 1 + 1e-9))


def risk_local_search(inst, P, H, D, SP, Cb, start, m_allow, rng, iters_per_task=2):
    """Minimise the mean scenario cost subject to #{k: C_k(s) > 1.01 C_k(HEFT)} <= m_allow.
    SP: K x (H+1) prefix sums of scenario intensities; Cb: K-vector of HEFT costs. start must be feasible."""
    n = len(inst.dur); start = np.array(start, int).copy()
    cl = cluster_of(inst, start, P, H); C = plan_costs(inst, start, SP); lim = 1.01 * Cb
    for _ in range(iters_per_task * n):
        i = int(rng.integers(n)); d = int(inst.dur[i])
        lo = max((start[j] + inst.dur[j] for j in inst.preds[i]), default=0)
        hi = min([start[j] for j in inst.succs[i]] + [D]) - d
        if hi <= lo:
            continue
        cl.place(start[i], d, -1)
        l0, ok = cl.free_starts(d, lo, hi); cand = l0 + np.flatnonzero(ok)
        if len(cand):
            cur = SP[:, start[i] + d] - SP[:, start[i]]
            new = C[:, None] - cur[:, None] + (SP[:, cand + d] - SP[:, cand])
            feas = (new > lim[:, None]).sum(axis=0) <= m_allow
            if feas.any():
                mean = np.where(feas, new.mean(axis=0), np.inf); k = int(np.argmin(mean))
                if mean[k] < C.mean() - 1e-9:
                    start[i] = int(cand[k]); C = new[:, k]
        cl.place(start[i], d, +1)
    return start
