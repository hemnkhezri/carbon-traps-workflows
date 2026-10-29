"""Capacity-based workflow simulator and schedulers (1-min resolution).

Platform: P identical machines, one task per machine; busy power constant,
idle power not attributed; no data-transfer time; deterministic runtimes.
Times are minutes from submission t0.
"""
import numpy as np


class Instance:
    def __init__(self, names, dur, preds, succs):
        self.names = names
        self.dur = np.asarray(dur, dtype=int)  # minutes, >= 1
        self.preds = preds  # list of lists of indices
        self.succs = succs
        n = len(dur)
        bl = np.zeros(n)
        order = topo_order(preds, succs)
        for i in reversed(order):
            bl[i] = self.dur[i] + max((bl[j] for j in succs[i]), default=0)
        self.bl = bl
        # descending bottom level is a valid topological order since dur >= 1
        self.order = sorted(range(n), key=lambda i: -bl[i])


def topo_order(preds, succs):
    n = len(preds)
    indeg = [len(p) for p in preds]
    q = [i for i in range(n) if indeg[i] == 0]
    out = []
    while q:
        i = q.pop()
        out.append(i)
        for j in succs[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                q.append(j)
    assert len(out) == n, "cycle"
    return out


def minute_series(ci_windows, horizon_min):
    """Expand 30-min CI windows to per-minute values; returns prefix sums."""
    per_min = np.repeat(ci_windows, 30)[:horizon_min]
    if len(per_min) < horizon_min:
        raise ValueError("CI series shorter than horizon")
    return np.concatenate([[0.0], np.cumsum(per_min)])


class Cluster:
    def __init__(self, P, horizon):
        self.P = P
        self.busy = np.zeros(horizon, dtype=np.int16)

    def free_starts(self, d, lo, hi):
        """Boolean mask over s in [lo, hi] where [s, s+d) has a free machine."""
        H = len(self.busy)
        hi = min(hi, H - d)
        if hi < lo:
            return lo, np.zeros(0, dtype=bool)
        full = (self.busy >= self.P).astype(np.int32)
        cs = np.concatenate([[0], np.cumsum(full)])
        s = np.arange(lo, hi + 1)
        ok = (cs[s + d] - cs[s]) == 0
        return lo, ok

    def place(self, s, d, delta=1):
        self.busy[s:s + d] += delta


def cost(prefix, s, d):
    return prefix[s + d] - prefix[s]


def _earliest(cl, d, est, H):
    lo, ok = cl.free_starts(d, est, H)
    nz = np.flatnonzero(ok)
    if len(nz) == 0:
        raise RuntimeError("horizon too short")
    return lo + nz[0]


def heft(inst, P, H):
    cl = Cluster(P, H)
    start = np.zeros(len(inst.dur), dtype=int)
    for i in inst.order:
        est = max((start[j] + inst.dur[j] for j in inst.preds[i]), default=0)
        s = _earliest(cl, inst.dur[i], est, H)
        start[i] = s
        cl.place(s, inst.dur[i])
    return start


def ca_list(inst, P, H, D, plan_prefix, tau=None):
    """Carbon-aware list scheduling on the planning CI. tau: gate threshold in
    CI units (mean CI gain needed to defer); None = no gate."""
    cl = Cluster(P, H)
    n = len(inst.dur)
    start = np.zeros(n, dtype=int)
    for i in inst.order:
        d = int(inst.dur[i])
        est = max((start[j] + inst.dur[j] for j in inst.preds[i]), default=0)
        lst = int(D - inst.bl[i])
        s_early = _earliest(cl, d, est, H)
        best = s_early
        if lst > s_early:
            lo, ok = cl.free_starts(d, s_early, lst)
            cand = lo + np.flatnonzero(ok)
            if len(cand):
                c = plan_prefix[cand + d] - plan_prefix[cand]
                k = int(np.argmin(c))  # first minimum = earliest tie
                if c[k] < cost(plan_prefix, s_early, d):
                    gain = (cost(plan_prefix, s_early, d) - c[k]) / d
                    if tau is None or gain > tau:
                        best = int(cand[k])
        start[i] = best
        cl.place(best, d)
    return start, cl


def ca_list_repaired(inst, P, H, D, M, plan_prefix, tau=None, steps=6):
    """CA-List with deadline repair: if the plan overruns D (LST ignores machine
    capacity), re-plan with a tighter internal deadline D' in [M, D] (bisection,
    largest feasible D'), else fall back to HEFT. Returns (start, cluster, mode)."""
    s, cl = ca_list(inst, P, H, D, plan_prefix, tau)
    if max(s + inst.dur) <= D:
        return s, cl, "direct"
    lo, hi, best = M, D, None
    for _ in range(steps):
        mid = (lo + hi) // 2
        s2, cl2 = ca_list(inst, P, H, mid, plan_prefix, tau)
        if max(s2 + inst.dur) <= D:
            best, lo = (s2, cl2), mid + 1
        else:
            hi = mid - 1
        if lo > hi:
            break
    if best is not None:
        return best[0], best[1], "repaired"
    s3 = heft(inst, P, H)
    cl3 = Cluster(P, H)
    for a, d in zip(s3, inst.dur):
        cl3.place(int(a), int(d))
    return s3, cl3, "heft-fallback"


def local_search(inst, P, H, D, plan_prefix, start, cl, rng, tau=None, iters_per_task=2):
    n = len(inst.dur)
    start = start.copy()
    for _ in range(iters_per_task * n):
        i = int(rng.integers(n))
        d = int(inst.dur[i])
        lo = max((start[j] + inst.dur[j] for j in inst.preds[i]), default=0)
        hi = min([start[j] for j in inst.succs[i]] + [D]) - d
        if hi <= lo:
            continue
        cur = cost(plan_prefix, start[i], d)
        cl.place(start[i], d, -1)
        l0, ok = cl.free_starts(d, lo, hi)
        cand = l0 + np.flatnonzero(ok)
        moved = False
        if len(cand):
            c = plan_prefix[cand + d] - plan_prefix[cand]
            k = int(np.argmin(c))
            if c[k] < cur - 1e-9 and (tau is None or (cur - c[k]) / d > tau):
                start[i] = int(cand[k])
                moved = True
        cl.place(start[i], d, +1)
    return start


def realised(inst, start, act_prefix, D):
    c = float(sum(cost(act_prefix, int(s), int(d)) for s, d in zip(start, inst.dur)))
    makespan = int(max(start + inst.dur))
    return c, makespan, makespan > D
