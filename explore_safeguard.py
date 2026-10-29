"""EXPLORATORY (not part of the sealed stop rule), added after pilot results.

Question: if each carbon-aware plan is compared with the HEFT plan on the
planning CI and the cheaper one is kept (a safeguard any deployed scheduler
would have), how much of the trap rate remains under oracle vs issued CI?
Runs seed 0 only. Usage: python explore_safeguard.py ARCHIVE OUT_CSV
"""
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import run_pilot as rp
from cwf.data import WIN
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, realised
from cwf.workflows import SPECS, build_raw, scaled_instance


def plan_cost(inst, start, prefix):
    return float(sum(prefix[s + d] - prefix[s] for s, d in zip(start, inst.dur)))


def job(args):
    seed, wi, T, t0 = args
    inst, M = rp.INSTANCES[(seed, wi, T)]
    act = rp.CI.actual(t0, rp.N_WIN)
    iss = rp.CI.vintage(t0, rp.N_WIN)
    rows = []
    for f in rp.FACTORS:
        D = int(round(f * M))
        H = D + T * 60
        act_p = minute_series(act, H)
        base = heft(inst, rp.P, H)
        cb, _, _ = realised(inst, base, act_p, D)
        for regime, ci in (("oracle", act), ("issued", iss)):
            plan_p = minute_series(ci, H)
            base_plan = plan_cost(inst, base, plan_p)
            s_list, cl, _ = ca_list_repaired(inst, rp.P, H, D, M, plan_p)
            rng = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 0])
            s_ls = local_search(inst, rp.P, H, D, plan_p, s_list, cl, rng)
            for name, st in (("CA-List", s_list), ("CA-LS", s_ls)):
                for guard in (False, True):
                    chosen = st
                    if guard and plan_cost(inst, st, plan_p) >= base_plan:
                        chosen = base
                    c, _, miss = realised(inst, chosen, act_p, D)
                    rows.append(dict(wf=SPECS[wi][0], T=T, f=f, t0=int(t0), regime=regime,
                                     sched=name + ("+Safeguard" if guard else ""),
                                     saving=1 - c / cb, trap=c > cb * (1 + 1e-9),
                                     trap1=c > cb * 1.01, miss=miss))
    return rows


def main(archive, out):
    t = time.time()
    rp.init(archive)
    cand = rp.candidate_submissions()
    seed = 0
    rng = np.random.default_rng(seed)  # same draw as the pilot -> same submissions
    subs = []
    for t0 in rng.permutation(cand):
        if rp.valid(t0):
            subs.append(t0)
        if len(subs) == rp.N_SUB:
            break
    jobs = []
    for wi, (label, recipe, n) in enumerate(SPECS):
        raw = build_raw(recipe, n, seed * 100 + wi)
        for T in rp.TARGETS_H:
            rp.INSTANCES[(seed, wi, T)] = scaled_instance(raw, rp.P, T * 60)
            jobs += [(seed, wi, T, t0) for t0 in subs]
    rows = []
    with Pool(os.cpu_count()) as pool:
        for r in pool.imap_unordered(job, jobs, chunksize=4):
            rows += r
    d = pd.DataFrame(rows)
    d.to_csv(out, index=False)
    print(f"{len(jobs)} jobs in {time.time()-t:.0f}s")
    print(d.pivot_table(index=["sched", "f"], columns="regime",
                        values=["saving", "trap", "trap1"], aggfunc="mean").mul(100).round(2).to_string())
    print("\nmedian saving %:")
    print(d.pivot_table(index=["sched", "f"], columns="regime", values="saving", aggfunc="median").mul(100).round(2).to_string())
    print("deadline misses:", int(d.miss.sum()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
