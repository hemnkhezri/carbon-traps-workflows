"""Revision study runner (EXT3_PREREG.md). GB confirmatory data; same instances and submissions as
run_confirm.py for the given seeds. Part A: re-planning, executors, slack reserve, gate alternatives,
gated Shift. Part B: CaWoSched and CWM with the authors' budget band (frac 0.2 and 0.4).
Usage: python run_revision.py ARCHIVE OUT_CSV --part A|B --seeds 10 [--wf 0,1,...] [--every 120]
"""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import argparse
import json
import os
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from cwf import cawosched, cwm
from cwf.data import CIData, WIN, load_national
from cwf.execute import execute, noisy_durations
from cwf.gate import HOR_EDGES_H, DiffGate
from cwf.gates_alt import calibrate_all
from cwf.replan import execute_reactive, gated_shift, plan_ls_from, receding_ls, receding_shift
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "confirm_config.json")))
P = CFG["P"]; TARGETS_H = CFG["targets_h"]; FACTORS = CFG["factors"]; N_SUB = CFG["n_sub"]
RT_SIGMA = CFG["runtime_sigma"]
PLAN_WIN = 94
EXEC_WIN = PLAN_WIN + int(max(TARGETS_H) * 2)
CI = None; INSTANCES = {}; GATES = {}; PART = "A"; EVERY = 120


def carbon_of(dur, start, prefix):
    s = np.asarray(start, int); d = np.asarray(dur, int)
    return float(np.sum(prefix[s + d] - prefix[s]))


def pad(ci, H):
    n = int(np.ceil(H / 30))
    return np.concatenate([ci, np.full(max(0, n - len(ci)), ci[-1])])


def job(args):
    seed, wi, T, t0 = args
    inst, M = INSTANCES[(seed, wi, T)]
    act = CI.actual(t0, EXEC_WIN); iss = CI.vintage(t0, PLAN_WIN)
    G = GATES[t0]
    Hx = len(act) * 30; act_p = minute_series(act, Hx)
    rows = []
    for f in FACTORS:
        D = int(round(f * M)); H = D + T * 60
        base = heft(inst, P, H)
        rng_rt = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 9])
        rdur = noisy_durations(inst.dur, rng_rt, RT_SIGMA)
        cb = carbon_of(inst.dur, base, act_p)
        hb_s, hb_f = execute(inst, base, rdur, P, Hx)
        hr_s, hr_f = execute_reactive(inst, base, rdur, P, Hx)
        cb_rt = carbon_of(rdur, hb_s, act_p); cb_rr = carbon_of(rdur, hr_s, act_p)

        def rec(name, regime, plan, used, rt=True, extra=None):
            c = carbon_of(inst.dur, plan, act_p)
            r = dict(seed=seed, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=name, regime=regime, M=M, D=D,
                     saving=1 - c / cb, trap=c > cb * (1 + 1e-9), trap1=c > cb * 1.01, trap0=c > cb * (1 + 1e-9),
                     trap2=c > cb * 1.02, trap5=c > cb * 1.05, excess=max(0.0, c / cb - 1),
                     miss=int(max(plan + inst.dur)) > D, used_heft=used, heft_kg=cb * CFG["power_kw"] / 60 / 1000,
                     n_moved=int((plan != base).sum()))
            if rt:
                s1, f1 = execute(inst, plan, rdur, P, Hx); s2, f2 = execute_reactive(inst, plan, rdur, P, Hx)
                r.update(miss_rt=int(f1.max()) > D, heft_miss_rt=int(hb_f.max()) > D,
                         miss_rr=int(f2.max()) > D, heft_miss_rr=int(hr_f.max()) > D,
                         tard_rt=max(0, int(f1.max()) - D) / D, tard_rr=max(0, int(f2.max()) - D) / D,
                         saving_rt=1 - carbon_of(rdur, s1, act_p) / cb_rt, saving_rr=1 - carbon_of(rdur, s2, act_p) / cb_rr)
            if extra:
                r.update(extra)
            rows.append(r)

        regimes = (("oracle", act[:PLAN_WIN]), ("issued", iss))
        if PART in ("A", "RH"):
            for regime, ci in regimes:
                pp = minute_series(pad(ci, H), H)
                rng = lambda k: np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), k])
                if PART == "RH" and regime != "issued":
                    continue
                # reference static CA-LS+SG and slack-reserve variants
                for rho, nm in ((1.0, "CA-LS+SG"), (0.75, "CA-LS+SG+Res75"), (0.5, "CA-LS+SG+Res50")) if PART == "A" else ():
                    Dp = int(M + rho * (D - M))
                    s, cl, _ = ca_list_repaired(inst, P, H, Dp, M, pp)
                    s = local_search(inst, P, H, Dp, pp, s, cl, rng(0))
                    s2, used = safeguard(inst, s, base, pp); rec(nm, regime, s2, used)
                sh = None if PART == "RH" else base + int(np.argmin([(pp[base + d + inst.dur] - pp[base + d]).sum() for d in range(0, D - M + 1)]))
                if sh is not None:
                    rec("Shift", regime, sh, bool((sh == base).all()))
                if regime == "issued":
                    for gname in ("diff0.9", "diff0.5", "diff0.8", "diff0.95", "const", "level", "lagcap6") if PART == "A" else ():
                        g = G[gname]
                        s, cl, _ = ca_list_repaired(inst, P, H, D, M, pp, tau=g)
                        s = local_search(inst, P, H, D, pp, s, cl, rng(1), tau=g)
                        s2, used = safeguard(inst, s, base, pp); rec(f"CA-LS+SG+Gate[{gname}]", regime, s2, used)
                    if PART == "A":
                        gs = gated_shift(inst, base, M, D, pp, G["diff0.9"]); rec("Shift+Gate", regime, gs, bool((gs == base).all()))
                    # receding horizon (nominal runtimes only)
                    def prefix_at(t):
                        if t == 0:
                            return pp
                        v = CI.vintage(t0 + 60 * t, PLAN_WIN)  # t in minutes, t0 in seconds
                        k = t // 30
                        ci_t = np.concatenate([act[:k], v]) if v is not None else ci
                        return minute_series(pad(ci_t, H), H)

                    def tau_at(t):
                        idx = np.searchsorted(CI.captures, t0 + 60 * t - WIN, side="right") - 1
                        return DiffGate(G["diff0.9"].q, (t0 - CI.captures[idx]) / 60.0)
                    for gated in (False, True):
                        tt = tau_at if gated else None
                        s, nre = receding_ls(inst, P, H, D, M, prefix_at, EVERY, rng(5 + gated), tt)
                        rec("RH-CA-LS+SG" + ("+Gate" if gated else ""), regime, s, False, rt=False, extra=dict(n_replans=nre))
                        s = receding_shift(inst, base, M, D, prefix_at, EVERY, tt)
                        rec("RH-Shift" + ("+Gate" if gated else ""), regime, s, bool((s == base).all()), rt=False)
        elif PART == "R2":
            # Post-hoc additions requested by the second internal review (EXT3_DEVIATIONS.md item 2; exploratory).
            rng = lambda k: np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), k])
            pp_o = minute_series(pad(act[:PLAN_WIN], H), H); pp_i = minute_series(pad(iss, H), H)
            # (a) receding horizon on the oracle signal and on the stale submission-time vintage
            s, nre = receding_ls(inst, P, H, D, M, lambda t: pp_o, EVERY, rng(5))
            rec("RH-CA-LS+SG", "oracle", s, False, rt=False, extra=dict(n_replans=nre))
            s, nre = receding_ls(inst, P, H, D, M, lambda t: pp_i, EVERY, rng(5))
            rec("RH-CA-LS+SG[stale]", "issued", s, False, rt=False, extra=dict(n_replans=nre))
            # (b) uncertainty-aware planning on an upper forecast quantile F + qU(horizon), alpha 0.9
            lg = G["level"]
            hor_h = (lg.cap + 30 * np.arange(len(iss)) + 15) / 60.0
            hb = np.clip(np.searchsorted(HOR_EDGES_H, hor_h, side="right") - 1, 0, len(HOR_EDGES_H) - 2)
            pq = minute_series(pad(iss + lg.qU[hb], H), H)
            sq, cl, _ = ca_list_repaired(inst, P, H, D, M, pq)
            sq = local_search(inst, P, H, D, pq, sq, cl, rng(0))
            sq2, used = safeguard(inst, sq, base, pq); rec("CA-LS+SG[Q0.9]", "issued", sq2, used)
            # (c) correlated runtime noise: a job-wide factor plus task noise, same marginal sigma
            z = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 11])
            eta = np.sqrt(0.5) * RT_SIGMA * (z.normal() + z.normal(size=len(inst.dur)))
            rc = np.maximum(1, np.round(inst.dur * np.exp(eta))).astype(int)
            hc_s, hc_f = execute(inst, base, rc, P, Hx)
            for rho, nm in ((1.0, "CA-LS+SG"), (0.75, "CA-LS+SG+Res75")):
                Dp = int(M + rho * (D - M))
                s1, cl, _ = ca_list_repaired(inst, P, H, Dp, M, pp_i)
                s1 = local_search(inst, P, H, Dp, pp_i, s1, cl, rng(0))
                s1, used = safeguard(inst, s1, base, pp_i)
                _, fc = execute(inst, s1, rc, P, Hx)
                rec(nm + "[corr]", "issued", s1, used, rt=False,
                    extra=dict(miss_corr=int(fc.max()) > D, heft_miss_corr=int(hc_f.max()) > D))
        else:
            for regime, ci in regimes:
                pp = minute_series(pad(ci, H), H)
                for frac in (0.2, 0.4, 1.0):
                    if frac < 1.0:  # frac 1.0 for CaWoSched is already in the confirmatory results
                        st, _ = cawosched.run(inst, P, D, base, ci, frac=frac)
                        if st is None:
                            rec(f"CaWoSched+SG[{frac}]", regime, base, True)
                        else:
                            s2, used = safeguard(inst, st, base, pp); rec(f"CaWoSched+SG[{frac}]", regime, s2, used)
                    st, _ = cwm.run(inst, P, D, ci, frac=frac)
                    if st is None:
                        rec(f"CWM+SG[{frac}]", regime, base, True)
                    else:
                        rec(f"CWM[{frac}]", regime, st, False, rt=False)
                        s2, used = safeguard(inst, st, base, pp); rec(f"CWM+SG[{frac}]", regime, s2, used)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive"); ap.add_argument("out")
    ap.add_argument("--part", default="A"); ap.add_argument("--seeds", default="10")
    ap.add_argument("--wf", default=""); ap.add_argument("--every", type=int, default=120)
    ap.add_argument("--n-sub", type=int, default=N_SUB)
    ap.add_argument("--months", default=",".join(CFG["months"]))
    a = ap.parse_args()
    global CI, PART, EVERY
    PART, EVERY = a.part, a.every
    t_start = time.time()
    fc, act = load_national(a.archive, a.months.split(","))
    CI = CIData(fc, act)
    cand = np.arange(CI.act.index.min(), CI.act.index.max() - EXEC_WIN * WIN, WIN)
    wfs = [int(x) for x in a.wf.split(",")] if a.wf else range(len(SPECS))
    jobs = []
    for seed in [int(s) for s in a.seeds.split(",")]:
        rng = np.random.default_rng(seed)
        subs = []
        for t0 in rng.permutation(cand):  # identical draw and validity rule to run_confirm.py
            if CI.vintage(t0, PLAN_WIN) is not None and CI.actual(t0, EXEC_WIN) is not None and CI.tau(t0) is not None:
                g = calibrate_all(CI, t0)
                if g is not None:
                    GATES[t0] = g; subs.append(t0)
            if len(subs) == N_SUB:
                break
        subs = subs[: a.n_sub]
        for wi in wfs:
            label, recipe, n = SPECS[wi]
            raw = build_raw(recipe, n, seed * 100 + wi)
            for T in TARGETS_H:
                INSTANCES[(seed, wi, T)] = scaled_instance(raw, P, T * 60)
                jobs += [(seed, wi, T, t0) for t0 in subs]
    print(f"{len(jobs)} jobs; setup {time.time()-t_start:.0f}s", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            rows += r
            if k % 20 == 0:
                print(f"  {k}/{len(jobs)} done, {time.time()-t_start:.0f}s", flush=True)
                pd.DataFrame(rows).to_csv(a.out + ".partial", index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(rows)} rows in {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
