"""Revision study (EXT3_PREREG.md): receding-horizon re-planning and a reactive executor.

Receding horizon (nominal runtimes): at t = 0 the scheduler plans on the vintage available at t0. Every
`every` minutes it re-plans all tasks that have not started on the newest vintage available at that time
(captured at or before t0 + t - 30 min). Tasks that have started keep their start. Re-planned tasks may not
start before t. Each re-plan uses CA-List (with deadline repair) + local search, and the safeguard compares the
new plan with the as-soon-as-possible completion of the remaining tasks on the same forecast; the cheaper one
is kept. Shift re-optimises its single offset at each re-plan time until the workflow has started.

Reactive executor (runtime noise): tasks are dispatched in order of planned start; a task waits for its planned
start only while all its ancestors are on time; once any ancestor finished later than planned, the task is
released as soon as it is ready (work-conserving catch-up). Same rule for every scheduler.
"""
import numpy as np

from .sched import Cluster, _earliest, cost


def _plan_from(inst, P, H, D, prefix, fixed, now, tau=None):
    """CA-List over unfixed tasks with starts >= now; fixed: dict task -> start. Returns (start, cluster)."""
    cl = Cluster(P, H)
    n = len(inst.dur)
    start = np.zeros(n, dtype=int)
    for i, s in fixed.items():
        start[i] = s
        cl.place(s, int(inst.dur[i]))
    for i in inst.order:
        if i in fixed:
            continue
        d = int(inst.dur[i])
        est = max([start[j] + inst.dur[j] for j in inst.preds[i]] + [now])
        lst = int(D - inst.bl[i])
        s_early = _earliest(cl, d, est, H)
        best = s_early
        if lst > s_early:
            lo, ok = cl.free_starts(d, s_early, lst)
            cand = lo + np.flatnonzero(ok)
            if len(cand):
                c = prefix[cand + d] - prefix[cand]
                c0 = cost(prefix, s_early, d)
                if tau is not None:
                    adj = (c0 - c) / d - tau.threshold_vec(s_early, cand, d)
                    k = int(np.argmax(adj))
                    if adj[k] > 0:
                        best = int(cand[k])
                else:
                    k = int(np.argmin(c))
                    if c[k] < c0:
                        best = int(cand[k])
        start[i] = best
        cl.place(best, d)
    return start, cl


def _asap_from(inst, P, H, fixed, now):
    cl = Cluster(P, H)
    start = np.zeros(len(inst.dur), dtype=int)
    for i, s in fixed.items():
        start[i] = s; cl.place(s, int(inst.dur[i]))
    for i in inst.order:
        if i in fixed:
            continue
        est = max([start[j] + inst.dur[j] for j in inst.preds[i]] + [now])
        start[i] = _earliest(cl, int(inst.dur[i]), est, H); cl.place(start[i], int(inst.dur[i]))
    return start


def _ls_from(inst, P, H, D, prefix, start, cl, fixed, now, rng, tau=None, iters_per_task=2):
    free = [i for i in range(len(start)) if i not in fixed]
    start = start.copy()
    for _ in range(iters_per_task * len(free)):
        i = free[int(rng.integers(len(free)))]
        d = int(inst.dur[i])
        lo = max([start[j] + inst.dur[j] for j in inst.preds[i]] + [now])
        hi = min([start[j] for j in inst.succs[i]] + [D]) - d
        if hi <= lo:
            continue
        cur = cost(prefix, start[i], d)
        cl.place(start[i], d, -1)
        l0, ok = cl.free_starts(d, lo, hi)
        cand = l0 + np.flatnonzero(ok)
        if len(cand):
            c = prefix[cand + d] - prefix[cand]
            if tau is not None:
                adj = (cur - c) / d - tau.threshold_vec(start[i], cand, d)
                k = int(np.argmax(adj))
                if adj[k] > 0 and c[k] < cur - 1e-9:
                    start[i] = int(cand[k])
            else:
                k = int(np.argmin(c))
                if c[k] < cur - 1e-9:
                    start[i] = int(cand[k])
        cl.place(start[i], d, +1)
    return start


def _plan_cost(inst, start, prefix, idx):
    return float(sum(prefix[start[i] + inst.dur[i]] - prefix[start[i]] for i in idx))


def plan_ls_from(inst, P, H, D, M, prefix, fixed, now, rng, tau=None, steps=6, prev=None):
    """CA-List + repair + local search from time `now`, safeguarded against ASAP completion."""
    def attempt(Dp):
        s, cl = _plan_from(inst, P, H, Dp, prefix, fixed, now, tau)
        return s, cl
    s, cl = attempt(D)
    if max(s + inst.dur) > D:
        lo, hi, best = max(M, now), D, None
        for _ in range(steps):
            mid = (lo + hi) // 2
            s2, cl2 = attempt(mid)
            if max(s2 + inst.dur) <= D:
                best, lo = (s2, cl2), mid + 1
            else:
                hi = mid - 1
            if lo > hi:
                break
        s = None if best is None else best[0]
        cl = None if best is None else best[1]
    cands = []
    if s is not None:
        cands.append(_ls_from(inst, P, H, D, prefix, s, cl, fixed, now, rng, tau))
    base = _asap_from(inst, P, H, fixed, now)
    cands.append(base)
    if prev is not None:
        cands.append(prev)
    idx = [i for i in range(len(base)) if i not in fixed]
    feas = [c for c in cands if max(c + inst.dur) <= D]
    if not feas:
        return prev if prev is not None else base
    # safeguard: keep the carbon-aware plan only if strictly cheaper than the alternatives on this forecast
    costs = [_plan_cost(inst, c, prefix, idx) for c in feas]
    order = sorted(range(len(feas)), key=lambda k: (costs[k], 0 if feas[k] is base else 1))
    return feas[order[0]]


def receding_ls(inst, P, H, D, M, prefix_at, every, rng, tau_at=None):
    """prefix_at(t) -> planning prefix (aligned to t0) using the vintage available at t0 + t.
    Returns final start times (nominal runtimes) and the number of re-plans."""
    fixed = {}
    s = plan_ls_from(inst, P, H, D, M, prefix_at(0), fixed, 0, rng, tau_at(0) if tau_at else None)
    n_re = 0
    t = every
    while t < D:
        fixed = {i: int(s[i]) for i in range(len(s)) if s[i] < t}
        if len(fixed) == len(s):
            break
        s = plan_ls_from(inst, P, H, D, M, prefix_at(t), fixed, t, rng, tau_at(t) if tau_at else None, prev=s)
        n_re += 1
        t += every
    return s, n_re


def receding_shift(inst, base, M, D, prefix_at, every, tau_at=None):
    """Whole-workflow shift re-optimised at each re-plan time until the workflow starts."""
    def best_offset(prefix, lo_delta, tau):
        deltas = np.arange(lo_delta, D - M + 1)
        if len(deltas) == 0:
            return lo_delta
        st = base[None, :] + deltas[:, None]
        c = (prefix[st + inst.dur[None, :]] - prefix[st]).sum(axis=1)
        if tau is None:
            return int(deltas[int(np.argmin(c))])
        W = float(inst.dur.sum())
        adj = (c[0] - c) / W - tau.threshold_vec(int(lo_delta), deltas, int(M))
        k = int(np.argmax(adj))
        return int(deltas[k]) if adj[k] > 0 else int(lo_delta)
    delta = best_offset(prefix_at(0), 0, tau_at(0) if tau_at else None)
    t = every
    while t <= delta and t <= D - M:
        delta = best_offset(prefix_at(t), t, tau_at(t) if tau_at else None)
        t += every
    return base + delta


def gated_shift(inst, base, M, D, prefix, tau):
    deltas = np.arange(0, D - M + 1)
    st = base[None, :] + deltas[:, None]
    c = (prefix[st + inst.dur[None, :]] - prefix[st]).sum(axis=1)
    W = float(inst.dur.sum())
    adj = (c[0] - c) / W - tau.threshold_vec(0, deltas, int(M))
    k = int(np.argmax(adj))
    return base + (int(deltas[k]) if adj[k] > 0 else 0)


def execute_reactive(inst, plan, rdur, P, H):
    cl = Cluster(P, H)
    n = len(plan)
    fin = np.zeros(n, dtype=int); st = np.zeros(n, dtype=int)
    late = np.zeros(n, dtype=bool)
    pfin = plan + inst.dur
    for i in np.argsort(plan, kind="stable"):
        ready = max([0] + [int(fin[j]) for j in inst.preds[i]])
        late[i] = any(late[j] or fin[j] > pfin[j] for j in inst.preds[i])
        rel = ready if late[i] else max(int(plan[i]), ready)
        d = int(rdur[i])
        lo, ok = cl.free_starts(d, rel, H)
        nz = np.flatnonzero(ok)
        if len(nz) == 0:
            raise RuntimeError("execution horizon too short")
        s = lo + nz[0]
        cl.place(s, d)
        st[i], fin[i] = s, s + d
    return st, fin
