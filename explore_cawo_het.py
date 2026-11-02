"""Exploratory addition to the platform-sensitivity study (EXT2_DEVIATIONS.md item 1): CaWoSched+SG
on the heterogeneous platform, same jobs as run_hetero.py (seed 30, 20 submissions per region).
Usage: python explore_cawo_het.py REGION OUT_CSV [--n-sub 20]"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
import run_hetero as RH, run_extension as RX
from cwf import hetero as Hh, cawosched_het
from cwf.sched import minute_series
from cwf.execute import noisy_durations
from cwf.data import WIN, CIData
from cwf.carboncast import load_carboncast
from cwf.gate import calibrate
from cwf.workflows import SPECS, build_raw, scaled_instance

def job(a):
    seed, wi, T, t0 = a
    h, M = RH.INSTANCES[(seed, wi, T)]
    act = RH.CI.actual(t0, RX.EXEC_WIN); iss = RH.CI.vintage(t0, RX.PLAN_WIN)
    Hx = len(act) * 30; ap = minute_series(act, Hx); rows = []
    for f in RX.FACTORS:
        D = int(round(f * M)); Hp = D + T * 60
        bst, bmc = Hh.heft(h, Hp)
        rng_rt = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 9])
        rw = noisy_durations(h.w, rng_rt, RX.RT_SIGMA)
        b = Hh.emissions(h, bst, bmc, Hh.finish(h, bst, bmc) - bst, ap, D)
        _, be, _ = Hh.execute(h, bst, bmc, rw, Hx)
        bn = Hh.brown_energy(h, bst, bmc, D, act, 1.0)
        for regime, ci in (("oracle", act[:RX.PLAN_WIN]), ("issued", iss)):
            pp = minute_series(np.concatenate([ci, np.full(max(0, int(np.ceil(Hp / 30)) - len(ci)), ci[-1])]), Hp)
            s = cawosched_het.run(h, D, bst, bmc, ci)
            ok = s is not None and Hh.finish(h, s, bmc).max() <= D
            s2, m2, used = Hh.safeguard(h, s, bmc, bst, bmc, pp) if ok else (bst, bmc, True)
            c = Hh.emissions(h, s2, m2, Hh.finish(h, s2, m2) - s2, ap, D)
            _, fin, _ = Hh.execute(h, s2, m2, rw, Hx)
            nat = Hh.brown_energy(h, s2, m2, D, act, 1.0)
            rows.append(dict(region=RH.REGION, seed=seed, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched="CaWoSched+SG",
                             regime=regime, saving=1 - c / b, trap=c > b * (1 + 1e-9), trap1=c > b * 1.01,
                             miss=int(Hh.finish(h, s2, m2).max()) > D, miss_rt=int(fin.max()) > D,
                             heft_miss_rt=int(be.max()) > D, used_heft=used, cawo_valid=ok,
                             native_saving=(1 - nat / bn) if bn > 0 else np.nan))
    return rows

if __name__ == "__main__":
    R, out = sys.argv[1], sys.argv[2]
    n_sub = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    fc, act = load_carboncast("/home/claude/carbonfirst_CarbonCast", R)
    RH.CI = CIData(fc, act); RH.REGION = R
    cand = np.arange(RH.CI.act.index.min(), RH.CI.act.index.max() - RX.EXEC_WIN * WIN, WIN)
    rng = np.random.default_rng(30); subs = []
    for t0 in rng.permutation(cand):
        if (RH.CI.vintage(t0, RX.PLAN_WIN) is not None and RH.CI.actual(t0, RX.EXEC_WIN) is not None
                and RH.CI.tau(t0) is not None and calibrate(RH.CI, t0, RX.ALPHA) is not None):
            subs.append(t0)
        if len(subs) == n_sub: break
    jobs = []
    for wi, (l, rec, n) in enumerate(SPECS):
        raw = build_raw(rec, n, 30 * 100 + wi)
        for T in RX.TARGETS_H:
            inst, _ = scaled_instance(raw, RX.P, T * 60); h = Hh.HInst(inst)
            s, m = Hh.heft(h, int(T * 60 * 4)); RH.INSTANCES[(30, wi, T)] = (h, int(Hh.finish(h, s, m).max()))
            jobs += [(30, wi, T, t0) for t0 in subs]
    rows = []
    with Pool(2) as p:
        for r in p.imap_unordered(job, jobs): rows += r
    pd.DataFrame(rows).to_csv(out, index=False); print(out, len(rows))
