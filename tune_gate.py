"""Tune the difference-based conformal gate on DEVELOPMENT data only.

Data: pilot period (Mar 2023 - Feb 2024), seed 0 (same submissions as the pilot).
Grid: alpha in {0.5, 0.6, 0.7, 0.8, 0.9}.
Schedulers: CA-List and CA-LS, each with the HEFT safeguard, issued forecasts.

SELECTION RULE (fixed before running, commit 'Gate tuning script'):
  Pool CA-List and CA-LS over all workflows, T and f.
  Choose the alpha with the highest mean issued saving among alphas whose pooled
  trap rate (excess > 1% over HEFT) is <= 5%. If no alpha qualifies, choose the
  alpha with the lowest pooled trap rate. Ties -> larger alpha (more conservative).
The chosen alpha is frozen in CONFIRM_PREREG.md.
Usage: python tune_gate.py ARCHIVE OUT_CSV
"""
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import run_pilot as rp
from cwf.data import WIN
from cwf.gate import calibrate
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, realised, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance

ALPHAS = [0.5, 0.6, 0.7, 0.8, 0.9]
GATES = {}


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
        plan_p = minute_series(iss, H)
        base = heft(inst, rp.P, H)
        cb, _, _ = realised(inst, base, act_p, D)
        for a in [None] + ALPHAS:
            g = None if a is None else GATES[(t0, a)]
            s_list, cl, _ = ca_list_repaired(inst, rp.P, H, D, M, plan_p, tau=g)
            rng = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 2])
            s_ls = local_search(inst, rp.P, H, D, plan_p, s_list, cl, rng, tau=g)
            for name, st in (("CA-List", s_list), ("CA-LS", s_ls)):
                st, _ = safeguard(inst, st, base, plan_p)
                c, _, miss = realised(inst, st, act_p, D)
                rows.append(dict(wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=name,
                                 alpha=-1 if a is None else a, saving=1 - c / cb,
                                 trap1=c > cb * 1.01, miss=miss))
    return rows


def main(archive, out):
    t = time.time()
    rp.init(archive)
    cand = rp.candidate_submissions()
    seed = 0
    rng = np.random.default_rng(seed)
    subs = []
    for t0 in rng.permutation(cand):
        if rp.valid(t0):
            subs.append(t0)
        if len(subs) == rp.N_SUB:
            break
    for t0 in subs:
        for a in ALPHAS:
            GATES[(t0, a)] = calibrate(rp.CI, t0, a)
    print(f"gates calibrated in {time.time()-t:.0f}s", flush=True)
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
    print(f"{len(jobs)} jobs in {time.time()-t:.0f}s; deadline misses {int(d.miss.sum())}")
    s = d.groupby("alpha").agg(mean_saving=("saving", "mean"), median_saving=("saving", "median"),
                               trap1=("trap1", "mean")).mul(100).round(2)
    print(s.to_string())
    print(d.pivot_table(index="alpha", columns="f", values=["saving", "trap1"], aggfunc="mean").mul(100).round(2).to_string())
    s = s.drop(index=-1)
    ok = s[s.trap1 <= 5]
    if len(ok):
        best = ok.sort_values(["mean_saving"], ascending=False)
        top = best.mean_saving.max()
        chosen = max(best[best.mean_saving == top].index)
    else:
        top = s.trap1.min()
        chosen = max(s[s.trap1 == top].index)
    print(f"CHOSEN alpha = {chosen}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
