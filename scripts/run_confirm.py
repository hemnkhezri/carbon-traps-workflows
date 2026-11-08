"""Confirmatory study runner. See CONFIRM_PREREG.md.
Usage: python run_confirm.py ARCHIVE OUT_CSV [--months 2026-07,...] [--seeds 10,11,...]
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

from cwf import cawosched
from cwf.data import CIData, WIN, load_national
from cwf.execute import execute, noisy_durations
from cwf.gate import calibrate
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance

CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "confirm_config.json")))
P = CFG["P"]
POWER_KW = CFG["power_kw"]
TARGETS_H = CFG["targets_h"]
FACTORS = CFG["factors"]
N_SUB = CFG["n_sub"]
SYN_SIGMA = CFG["synthetic_sigma"]
ALPHA = CFG["gate_alpha"]
RT_SIGMA = CFG["runtime_sigma"]
PLAN_WIN = 94  # 47 h: the issued 48-h forecast minus the capture lag
EXEC_WIN = PLAN_WIN + int(max(TARGETS_H) * 2)  # actual CI for noisy overruns

CI = None
INSTANCES = {}
GATES = {}


def carbon_of(inst_dur, start, prefix):
    s = np.asarray(start, dtype=int)
    d = np.asarray(inst_dur, dtype=int)
    return float(np.sum(prefix[s + d] - prefix[s]))


def shift_plan(inst, base, M, D, plan_p):
    """Whole-workflow shift: move the HEFT plan by delta in [0, D - M] to the
    cheapest offset on the planning CI (delta = 0 is HEFT itself)."""
    deltas = np.arange(0, D - M + 1)
    s = base[None, :] + deltas[:, None]
    c = (plan_p[s + inst.dur[None, :]] - plan_p[s]).sum(axis=1)
    k = int(np.argmin(c))  # first minimum: delta = 0 (HEFT) wins ties
    return base + int(deltas[k])


def job(args):
    seed, wi, T, t0 = args
    inst, M = INSTANCES[(seed, wi, T)]
    act = CI.actual(t0, EXEC_WIN)
    iss = CI.vintage(t0, PLAN_WIN)
    rng_syn = np.random.default_rng([seed, int(t0) // WIN, 7])
    syn = act[:PLAN_WIN] * (1 + rng_syn.normal(0, SYN_SIGMA, size=PLAN_WIN))
    gate = GATES[t0]
    rows = []
    for f in FACTORS:
        D = int(round(f * M))
        H = D + T * 60  # scheduler horizon; planning CI padded beyond the forecast (see CONFIRM_DEVIATIONS.md)
        Hx = len(act) * 30
        act_p = minute_series(act, Hx)
        base = heft(inst, P, H)
        rng_rt = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 9])
        rdur = noisy_durations(inst.dur, rng_rt, RT_SIGMA)
        hb_st, hb_fin = execute(inst, base, rdur, P, Hx)
        cb_nom = carbon_of(inst.dur, base, act_p)
        cb_rt = carbon_of(rdur, hb_st, act_p)

        def record(name, regime, plan, used_heft):
            c_nom = carbon_of(inst.dur, plan, act_p)
            st, fin = execute(inst, plan, rdur, P, Hx)
            c_rt = carbon_of(rdur, st, act_p)
            rows.append(dict(seed=seed, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=name, regime=regime,
                             saving=1 - c_nom / cb_nom, trap=c_nom > cb_nom * (1 + 1e-9),
                             trap1=c_nom > cb_nom * 1.01, miss=int(max(plan + inst.dur)) > D,
                             saving_rt=1 - c_rt / cb_rt, trap1_rt=c_rt > cb_rt * 1.01,
                             miss_rt=int(fin.max()) > D, heft_miss_rt=int(hb_fin.max()) > D,
                             used_heft=used_heft, carbon_kg=c_nom * POWER_KW / 60 / 1000,
                             heft_carbon_kg=cb_nom * POWER_KW / 60 / 1000, M=M, D=D))

        for regime, ci in (("oracle", act[:PLAN_WIN]), ("synthetic", syn), ("issued", iss)):
            n_need = int(np.ceil(H / 30))
            ci_pad = np.concatenate([ci, np.full(max(0, n_need - len(ci)), ci[-1])])
            plan_p = minute_series(ci_pad, H)
            # whole-workflow shift
            sp = shift_plan(inst, base, M, D, plan_p)
            record("Shift", regime, sp, bool((sp == base).all()))
            # own carbon-aware list scheduler + local search, safeguarded
            gates = [None, gate] if regime == "issued" else [None]
            for g in gates:
                s_list, cl, _ = ca_list_repaired(inst, P, H, D, M, plan_p, tau=g)
                rng = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 0 if g is None else 1])
                s_ls = local_search(inst, P, H, D, plan_p, s_list, cl, rng, tau=g)
                suffix = "" if g is None else "+Gate"
                for name, st in (("CA-List", s_list), ("CA-LS", s_ls)):
                    st2, used = safeguard(inst, st, base, plan_p)
                    record(name + "+SG" + suffix, regime, st2, used)
            # official CaWoSched, safeguarded (oracle and issued only)
            if regime in ("oracle", "issued"):
                st, info = cawosched.run(inst, P, D, base, ci)
                if st is None:
                    record("CaWoSched+SG", regime, base, True)
                else:
                    st2, used = safeguard(inst, st, base, plan_p)
                    record("CaWoSched+SG", regime, st2, used)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("out")
    ap.add_argument("--months", default=",".join(CFG["months"]))
    ap.add_argument("--seeds", default=",".join(str(s) for s in CFG["seeds"]))
    a = ap.parse_args()
    global CI
    t_start = time.time()
    fc, act = load_national(a.archive, a.months.split(","))
    CI = CIData(fc, act)
    seeds = [int(s) for s in a.seeds.split(",")]
    cand = np.arange(CI.act.index.min(), CI.act.index.max() - EXEC_WIN * WIN, WIN)

    def valid(t0):
        return (CI.vintage(t0, PLAN_WIN) is not None and CI.actual(t0, EXEC_WIN) is not None
                and CI.tau(t0) is not None)

    jobs = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        subs = []
        for t0 in rng.permutation(cand):
            if valid(t0):
                g = calibrate(CI, t0, ALPHA)
                if g is not None:
                    GATES[t0] = g
                    subs.append(t0)
            if len(subs) == N_SUB:
                break
        for wi, (label, recipe, n) in enumerate(SPECS):
            raw = build_raw(recipe, n, seed * 100 + wi)
            for T in TARGETS_H:
                INSTANCES[(seed, wi, T)] = scaled_instance(raw, P, T * 60)
                jobs += [(seed, wi, T, t0) for t0 in subs]
        print(f"seed {seed}: {len(subs)} submissions", flush=True)
    print(f"{len(jobs)} jobs; setup {time.time()-t_start:.0f}s", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=2)):
            rows += r
            if k % 100 == 0:
                print(f"  {k}/{len(jobs)} done, {time.time()-t_start:.0f}s", flush=True)
                pd.DataFrame(rows).to_csv(a.out + ".partial", index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(rows)} rows in {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
