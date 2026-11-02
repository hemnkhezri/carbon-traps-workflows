"""Heterogeneous platform with idle power (platform-sensitivity study, EXT2_PREREG.md).

Platform: the two processor types of CWM's own example cluster (KIT-EAE/CWM examples/cluster.json):
  slow: speed 1, idle power 1, work power 10;  fast: speed 2, idle power 2, work power 15
(power units; 1 unit = 0.02 kW, so a slow machine draws 0.2 kW busy, as in the homogeneous study).
Four machines of each type (P = 8); machines 0-3 slow, 4-7 fast (CWM's processor numbering).
A task with work w runs ceil(w / speed) minutes (CWM's rule). No data-transfer time.

Emissions over [0, W] with W = max(D, makespan):
  sum_tasks (work_m - idle_m) * integral CI over the task + sum_m idle_m * integral_0^W CI.
All machines stay powered until W, so idle power is attributed. The second term is the same for
every plan that finishes by D, so schedulers optimise the marginal (work - idle) term.

A plan is (start[i], mach[i]). Times are minutes from submission.
"""
import numpy as np

SPEED = np.array([1, 1, 1, 1, 2, 2, 2, 2])
IDLE = np.array([1, 1, 1, 1, 2, 2, 2, 2], float)
WORK = np.array([10, 10, 10, 10, 15, 15, 15, 15], float)
MARG = WORK - IDLE
UNIT_KW = 0.02
P = len(SPEED)


class HInst:
    def __init__(self, inst):
        self.w = np.asarray(inst.dur, int)
        self.preds, self.succs = inst.preds, inst.succs
        n = len(self.w)
        self.d = np.ceil(self.w[:, None] / SPEED[None, :]).astype(int)  # n x P
        dmean = self.d.mean(axis=1)
        dfast = self.d.min(axis=1)
        rank = np.zeros(n); blf = np.zeros(n)
        for i in reversed(_topo(self.preds, self.succs)):
            rank[i] = dmean[i] + max((rank[j] for j in self.succs[i]), default=0)
            blf[i] = dfast[i] + max((blf[j] for j in self.succs[i]), default=0)
        self.order = sorted(range(n), key=lambda i: -rank[i])  # valid topological order (dmean >= 1)
        self.tail = blf - dfast  # fastest possible remaining time after task i finishes


def _topo(preds, succs):
    indeg = [len(p) for p in preds]
    q = [i for i in range(len(preds)) if indeg[i] == 0]
    out = []
    while q:
        i = q.pop(); out.append(i)
        for j in succs[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                q.append(j)
    return out


class Machines:
    def __init__(self, H):
        self.busy = np.zeros((P, H), dtype=np.int8)

    def starts(self, m, d, lo, hi):
        """Feasible starts s in [lo, hi] with [s, s+d) free on machine m."""
        H = self.busy.shape[1]
        hi = min(hi, H - d)
        if hi < lo:
            return np.zeros(0, dtype=int)
        cs = np.concatenate([[0], np.cumsum(self.busy[m], dtype=np.int32)])
        s = np.arange(lo, hi + 1)
        return s[(cs[s + d] - cs[s]) == 0]

    def earliest(self, m, d, lo):
        c = self.starts(m, d, lo, self.busy.shape[1])
        if len(c) == 0:
            raise RuntimeError("horizon too short")
        return int(c[0])

    def place(self, m, s, d, v=1):
        self.busy[m, s:s + d] += v


def heft(h, H):
    """Insertion-based HEFT (earliest finish time over all machines)."""
    n = len(h.w)
    st = np.zeros(n, int); mc = np.zeros(n, int)
    ms = Machines(H)
    for i in h.order:
        est = max((st[j] + h.d[j, mc[j]] for j in h.preds[i]), default=0)
        best = None
        for m in range(P):
            s = ms.earliest(m, h.d[i, m], est)
            if best is None or s + h.d[i, m] < best[0]:
                best = (s + h.d[i, m], s, m)
        _, st[i], mc[i] = best
        ms.place(mc[i], st[i], h.d[i, mc[i]])
    return st, mc


def finish(h, st, mc):
    return st + h.d[np.arange(len(st)), mc]


def marg_cost(h, st, mc, prefix):
    e = finish(h, st, mc)
    return float(np.sum(MARG[mc] * (prefix[e] - prefix[st])))


def emissions(h, st, mc, dur_used, prefix, D):
    """Full emissions (power units x CI x minutes), idle attributed until max(D, makespan)."""
    e = st + dur_used
    W = int(max(D, e.max()))
    return float(np.sum(MARG[mc] * (prefix[e] - prefix[st])) + IDLE.sum() * prefix[W])


def _risk(tau, s0, cand, d):
    return tau.threshold_vec(s0, cand, d)


def ca_list(h, H, D, prefix, tau=None):
    """Carbon-aware list scheduling over machines and start times. For each task the reference
    is its earliest-finish choice; among (machine, start) pairs that can still meet the deadline
    (start + d + fastest tail <= D) the cheapest marginal cost is taken. With a gate, a pair is
    taken only if its forecast gain exceeds the calibrated error quantile times the larger of
    the two energies (marginal power x duration)."""
    n = len(h.w)
    st = np.zeros(n, int); mc = np.zeros(n, int)
    ms = Machines(H)
    for i in h.order:
        est = max((st[j] + h.d[j, mc[j]] for j in h.preds[i]), default=0)
        early = [ms.earliest(m, h.d[i, m], est) for m in range(P)]
        m0 = int(np.argmin([early[m] + h.d[i, m] for m in range(P)]))
        s0, d0 = early[m0], h.d[i, m0]
        c0 = MARG[m0] * (prefix[s0 + d0] - prefix[s0])
        best, bval = (s0, m0), 0.0
        for m in range(P):
            d = h.d[i, m]
            lst = int(D - h.tail[i] - d)
            cand = ms.starts(m, d, early[m], lst)
            if len(cand) == 0:
                continue
            c = MARG[m] * (prefix[cand + d] - prefix[cand])
            gain = c0 - c
            if tau is not None:
                gain = gain - _risk(tau, s0, cand, d) * np.maximum(MARG[m] * d, MARG[m0] * d0)
            k = int(np.argmax(gain))
            if gain[k] > bval + 1e-9:
                best, bval = (int(cand[k]), m), float(gain[k])
        st[i], mc[i] = best
        ms.place(mc[i], st[i], h.d[i, mc[i]])
    return st, mc, ms


def ca_list_repaired(h, H, D, M, prefix, tau=None, steps=6):
    st, mc, ms = ca_list(h, H, D, prefix, tau)
    if finish(h, st, mc).max() <= D:
        return st, mc, ms, "direct"
    lo, hi, best = M, D, None
    for _ in range(steps):
        mid = (lo + hi) // 2
        r = ca_list(h, H, mid, prefix, tau)
        if finish(h, r[0], r[1]).max() <= D:
            best, lo = r, mid + 1
        else:
            hi = mid - 1
        if lo > hi:
            break
    if best is not None:
        return (*best, "repaired")
    st, mc = heft(h, H)
    ms = Machines(H)
    for i in range(len(st)):
        ms.place(mc[i], st[i], h.d[i, mc[i]])
    return st, mc, ms, "heft-fallback"


def local_search(h, H, D, prefix, st, mc, ms, rng, tau=None, iters_per_task=2):
    """Move one random task to the cheapest (machine, start) that keeps precedence and D."""
    st, mc = st.copy(), mc.copy()
    n = len(st)
    for _ in range(iters_per_task * n):
        i = int(rng.integers(n))
        lo = max((st[j] + h.d[j, mc[j]] for j in h.preds[i]), default=0)
        ub = min([st[j] for j in h.succs[i]] + [D])
        m0, s0, d0 = mc[i], st[i], h.d[i, mc[i]]
        cur = MARG[m0] * (prefix[s0 + d0] - prefix[s0])
        ms.place(m0, s0, d0, -1)
        best, bval = (s0, m0), 0.0
        for m in range(P):
            d = h.d[i, m]
            cand = ms.starts(m, d, lo, ub - d)
            if len(cand) == 0:
                continue
            gain = cur - MARG[m] * (prefix[cand + d] - prefix[cand])
            if tau is not None:
                gain = gain - _risk(tau, s0, cand, d) * np.maximum(MARG[m] * d, MARG[m0] * d0)
            k = int(np.argmax(gain))
            if gain[k] > bval + 1e-9:
                best, bval = (int(cand[k]), m), float(gain[k])
        st[i], mc[i] = best
        ms.place(mc[i], st[i], h.d[i, mc[i]])
    return st, mc


def safeguard(h, st, mc, bst, bmc, prefix):
    if marg_cost(h, st, mc, prefix) < marg_cost(h, bst, bmc, prefix):
        return st, mc, False
    return bst, bmc, True


def execute(h, st, mc, rdur_w, H):
    """Run the plan with realised work rdur_w on the planned machines: tasks dispatched in order of
    planned start; each starts at max(planned start, predecessors done, first free slot on its machine)."""
    n = len(st)
    rd = np.ceil(rdur_w / SPEED[mc]).astype(int)
    ms = Machines(H)
    a = np.zeros(n, int); e = np.zeros(n, int)
    for i in np.argsort(st, kind="stable"):
        ready = max([int(st[i])] + [int(e[j]) for j in h.preds[i]])
        a[i] = ms.earliest(mc[i], rd[i], ready)
        e[i] = a[i] + rd[i]
        ms.place(mc[i], a[i], rd[i])
    return a, e, rd


def brown_energy(h, st, mc, D, ci_windows, frac):
    """CWM's native objective: power above the green budget, budget = idle + rel x frac x dynamic."""
    n = int(np.ceil(D / 30))
    c = np.asarray(ci_windows[:n], float)
    lo, hi = c.min(), c.max()
    rel = (hi - c) / (hi - lo) if hi > lo else np.ones_like(c)
    base, dyn = IDLE.sum(), (WORK - IDLE).sum()
    bud = np.repeat(base + rel * frac * dyn, 30)[:D]
    pw = np.full(D, base)
    e = finish(h, st, mc)
    for i in range(len(st)):
        a, b = int(st[i]), min(int(e[i]), D)
        if b > a:
            pw[a:b] += MARG[mc[i]]
    return float(np.maximum(0.0, pw - bud).sum())
