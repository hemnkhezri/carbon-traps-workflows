"""Exploratory (post hoc): how much of the heterogeneous-platform saving needs no carbon forecast at all?
CA-LS+SG planned on a flat CI signal (energy-aware only), same jobs as run_hetero.py (first N submissions of seed 30)."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
import run_hetero as RH, run_extension as RX
from cwf import hetero as Hh
from cwf.sched import minute_series
from cwf.data import WIN

def job(a):
    seed, wi, T, t0 = a
    h, M = RH.INSTANCES[(seed, wi, T)]
    act = RH.CI.actual(t0, RX.EXEC_WIN); Hx = len(act) * 30; ap = minute_series(act, Hx)
    out = []
    for f in RX.FACTORS:
        D = int(round(f * M)); Hp = D + T * 60
        bst, bmc = Hh.heft(h, Hp)
        b = Hh.emissions(h, bst, bmc, Hh.finish(h, bst, bmc) - bst, ap, D)
        pp = minute_series(np.full(int(np.ceil(Hp / 30)), act.mean()), Hp)
        st, mc, ms, _ = Hh.ca_list_repaired(h, Hp, D, M, pp)
        rng = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 0])
        s2, m2 = Hh.local_search(h, Hp, D, pp, st, mc, ms, rng)
        s3, m3, _ = Hh.safeguard(h, s2, m2, bst, bmc, pp)
        c = Hh.emissions(h, s3, m3, Hh.finish(h, s3, m3) - s3, ap, D)
        out.append(dict(region=RH.REGION, f=f, T=T, t0=int(t0), wf=wi, saving_flat=1 - c / b))
    return out

if __name__ == "__main__":
    rows = []
    for R in ["CISO", "DE", "ERCO", "PJM"]:
        sys.argv = ["x", "/home/claude/carbonfirst_CarbonCast", "/dev/null", "--source", f"carboncast:{R}", "--seeds", "30", "--n-sub", "5"]
        RH.INSTANCES.clear(); RH.GATES.clear()
        # reuse main()'s setup without running jobs
        import argparse
        from cwf.carboncast import load_carboncast
        from cwf.data import CIData
        from cwf.gate import calibrate
        from cwf.workflows import SPECS, build_raw, scaled_instance
        fc, act = load_carboncast("/home/claude/carbonfirst_CarbonCast", R); RH.CI = CIData(fc, act); RH.REGION = R
        cand = np.arange(RH.CI.act.index.min(), RH.CI.act.index.max() - RX.EXEC_WIN * WIN, WIN)
        rng = np.random.default_rng(30); subs = []
        for t0 in rng.permutation(cand):
            if RH.CI.vintage(t0, RX.PLAN_WIN) is not None and RH.CI.actual(t0, RX.EXEC_WIN) is not None and RH.CI.tau(t0) is not None and calibrate(RH.CI, t0, RX.ALPHA) is not None:
                subs.append(t0)
            if len(subs) == 5: break
        jobs = []
        for wi, (l, rec, n) in enumerate(SPECS):
            raw = build_raw(rec, n, 30 * 100 + wi)
            for T in RX.TARGETS_H:
                inst, _ = scaled_instance(raw, RX.P, T * 60); h = Hh.HInst(inst)
                s, m = Hh.heft(h, T * 240); RH.INSTANCES[(30, wi, T)] = (h, int(Hh.finish(h, s, m).max()))
                jobs += [(30, wi, T, t0) for t0 in subs]
        with Pool(2) as p:
            for r in p.imap_unordered(job, jobs): rows += r
    d = pd.DataFrame(rows); d.to_csv("results/hetero_flat_explore.csv", index=False)
    het = pd.read_csv("results/hetero.csv")
    het = het[(het.sched == "CA-LS+SG") & het.t0.isin(d.t0.unique())]
    print("flat-CI CA-LS+SG saving %:", d.groupby("region").saving_flat.mean().mul(100).round(2).to_dict(), "pooled", round(100 * d.saving_flat.mean(), 2))
    print("same jobs, oracle / issued %:", het.groupby(["regime"]).saving.mean().mul(100).round(2).to_dict())
