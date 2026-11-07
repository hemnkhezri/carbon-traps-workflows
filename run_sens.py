"""Sensitivity runs (SENS_PLAN.md). Usage: python run_sens.py ARCHIVE OUT --P 8 [--seeds 10]"""
import argparse, json, os, time
from multiprocessing import Pool
import numpy as np, pandas as pd
from cwf.data import CIData, WIN, load_national
from cwf.execute import execute
from cwf.gates_alt import calibrate_all
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance
CFG = json.load(open("confirm_config.json")); PLAN_WIN = 94; EXEC_WIN = PLAN_WIN + 24
CI = None; INST = {}; G = {}; P = 8; EMP = np.load("results/emp_runtime_logratio.npy")
NOISE = [("ln0.05", 0.05), ("ln0.1", 0.1), ("ln0.2", 0.2), ("ln0.4", 0.4), ("emp", None)]

def pad(ci, H):
    n = int(np.ceil(H / 30)); return np.concatenate([ci, np.full(max(0, n - len(ci)), ci[-1])])

def cost(dur, s, pref):
    s = np.asarray(s, int); return float(np.sum(pref[s + dur] - pref[s]))

def job(a):
    seed, wi, T, t0 = a; inst, M = INST[(seed, wi, T)]
    act = CI.actual(t0, EXEC_WIN); iss = CI.vintage(t0, PLAN_WIN); g = G[t0]
    Hx = len(act) * 30; ap = minute_series(act, Hx); rows = []
    for f in CFG["factors"]:
        D = int(round(f * M)); H = D + T * 60; base = heft(inst, P, H); cb = cost(inst.dur, base, ap)
        rng = lambda k: np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), k])
        z = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 21])
        noises = {}
        for nm, sg in NOISE:
            eta = z.normal(0, sg, len(inst.dur)) if sg else z.choice(EMP, len(inst.dur))
            noises[nm] = np.maximum(1, np.round(inst.dur * np.exp(eta))).astype(int)
        hm = {nm: int(execute(inst, base, rd, P, int(base.max() + rd.sum() + 1))[1].max()) > D for nm, rd in noises.items()}
        for regime, ci in (("oracle", act[:PLAN_WIN]), ("issued", iss)):
            pp = minute_series(pad(ci, H), H)
            def calsg(Dp, tau=None, k=0):
                s, cl, _ = ca_list_repaired(inst, P, H, Dp, M, pp, tau=tau)
                s = local_search(inst, P, H, Dp, pp, s, cl, rng(k), tau=tau); return safeguard(inst, s, base, pp)[0]
            plans = {"CA-LS+SG": calsg(D), "Shift": base + int(np.argmin([(pp[base + d + inst.dur] - pp[base + d]).sum() for d in range(0, D - M + 1)]))}
            if regime == "issued":
                plans["CA-LS+SG+Gate"] = calsg(D, g["diff0.9"], 1); plans["CA-LS+SG+Res75"] = calsg(int(M + 0.75 * (D - M)))
            for nm, s in plans.items():
                c = cost(inst.dur, s, ap)
                r = dict(seed=seed, P=P, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=nm, regime=regime, saving=1 - c / cb, trap1=c > 1.01 * cb,
                         miss=int(max(s + inst.dur)) > D, cp_ratio=float(M))
                for nn, rd in noises.items():
                    r[f"miss_{nn}"] = int(execute(inst, s, rd, P, int(s.max() + rd.sum() + 1))[1].max()) > D; r[f"heft_miss_{nn}"] = hm[nn]
                rows.append(r)
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("archive"); ap.add_argument("out"); ap.add_argument("--P", type=int, default=8)
    ap.add_argument("--seeds", default="10"); a = ap.parse_args(); global CI, P; P = a.P
    fc, act = load_national(a.archive, CFG["months"]); CI = CIData(fc, act)
    cand = np.arange(CI.act.index.min(), CI.act.index.max() - EXEC_WIN * WIN, WIN); jobs = []
    for seed in [int(s) for s in a.seeds.split(",")]:
        rng = np.random.default_rng(seed); subs = []
        for t0 in rng.permutation(cand):
            if CI.vintage(t0, PLAN_WIN) is not None and CI.actual(t0, EXEC_WIN) is not None and CI.tau(t0) is not None:
                g = calibrate_all(CI, t0)
                if g is not None: G[t0] = g; subs.append(t0)
            if len(subs) == CFG["n_sub"]: break
        for wi in range(len(SPECS)):
            raw = build_raw(SPECS[wi][1], SPECS[wi][2], seed * 100 + wi)
            for T in CFG["targets_h"]:
                INST[(seed, wi, T)] = scaled_instance(raw, P, T * 60); jobs += [(seed, wi, T, t0) for t0 in subs]
    print(len(jobs), "jobs", flush=True); rows = []; t = time.time()
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            rows += r
            if k % 20 == 0: print(f"  {k}/{len(jobs)} {time.time()-t:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(a.out, index=False); print("wrote", len(rows))

if __name__ == "__main__":
    main()
