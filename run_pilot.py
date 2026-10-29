"""Kill-pilot runner. See PREREG.md. Usage: python run_pilot.py ARCHIVE_DIR OUT_CSV"""
import itertools
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from cwf.data import CIData, WIN, load_national
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, realised
from cwf.workflows import SPECS, build_raw, scaled_instance

P = 8
POWER_KW = 0.2
TARGETS_H = [4, 12]
FACTORS = [1.2, 1.5, 2.0]
SEEDS = [0, 1, 2]
N_SUB = 40
SYN_SIGMA = 0.10
PILOT_MONTHS = ["2023-%02d" % m for m in range(3, 13)] + ["2024-01", "2024-02"]
MAX_H_MIN = int(max(FACTORS) * max(TARGETS_H) * 60 + max(TARGETS_H) * 60)
N_WIN = MAX_H_MIN // 30 + 2

CI = None
INSTANCES = {}


def init(archive):
    global CI
    fc, act = load_national(archive, PILOT_MONTHS)
    CI = CIData(fc, act)


def candidate_submissions():
    t = np.arange(CI.act.index.min(), CI.act.index.max() - N_WIN * WIN, WIN)
    return t


def valid(t0):
    return (CI.vintage(t0, N_WIN) is not None and CI.actual(t0, N_WIN) is not None
            and CI.tau(t0) is not None)


def job(args):
    seed, wi, T, t0 = args
    inst, M = INSTANCES[(seed, wi, T)]
    label = SPECS[wi][0]
    act = CI.actual(t0, N_WIN)
    iss = CI.vintage(t0, N_WIN)
    rng_syn = np.random.default_rng([seed, int(t0) // WIN, 7])
    syn = act * (1 + rng_syn.normal(0, SYN_SIGMA, size=act.shape))
    tau = CI.tau(t0)
    rows = []
    for f in FACTORS:
        D = int(round(f * M))
        H = D + T * 60
        act_p = minute_series(act, H)
        base = heft(inst, P, H)
        cb, mb, missb = realised(inst, base, act_p, D)
        rows.append(dict(seed=seed, wf=label, T=T, f=f, t0=int(t0), sched="HEFT", regime="-",
                         carbon=cb * POWER_KW / 60, makespan=mb, miss=missb, heft_carbon=cb * POWER_KW / 60, M=M, tau=tau))
        for regime, ci in (("oracle", act), ("synthetic", syn), ("issued", iss)):
            plan_p = minute_series(ci, H)
            for gated in (False, True):
                t = tau if gated else None
                s_list, cl, mode = ca_list_repaired(inst, P, H, D, M, plan_p, tau=t)
                rng_ls = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), int(gated)])
                s_ls = local_search(inst, P, H, D, plan_p, s_list, cl, rng_ls, tau=t)
                for name, st in (("CA-List", s_list), ("CA-LS", s_ls)):
                    c, m, miss = realised(inst, st, act_p, D)
                    rows.append(dict(seed=seed, wf=label, T=T, f=f, t0=int(t0),
                                     sched=name + ("+Gate" if gated else ""), regime=regime,
                                     carbon=c * POWER_KW / 60, makespan=m, miss=miss,
                                     heft_carbon=cb * POWER_KW / 60, M=M, tau=tau, mode=mode))
    return rows


def main(archive, out):
    t_start = time.time()
    init(archive)
    cand = candidate_submissions()
    jobs = []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        subs = []
        for t0 in rng.permutation(cand):
            if valid(t0):
                subs.append(t0)
            if len(subs) == N_SUB:
                break
        for wi, (label, recipe, n) in enumerate(SPECS):
            raw = build_raw(recipe, n, seed * 100 + wi)
            for T in TARGETS_H:
                INSTANCES[(seed, wi, T)] = scaled_instance(raw, P, T * 60)
                inst, M = INSTANCES[(seed, wi, T)]
                print(f"seed {seed} {label:12s} T={T}h tasks={len(inst.dur)} M={M}min", flush=True)
            for T in TARGETS_H:
                jobs += [(seed, wi, T, t0) for t0 in subs]
    print(f"{len(jobs)} jobs; setup {time.time()-t_start:.0f}s", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:  # fork: workers inherit CI and INSTANCES
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=4)):
            rows += r
            if k % 200 == 0:
                print(f"  {k}/{len(jobs)} done, {time.time()-t_start:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {out}: {len(rows)} rows in {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
