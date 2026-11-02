"""Platform-sensitivity runner (EXT2_PREREG.md): heterogeneous platform with idle power.
Same data, submissions, workflows, factors and runtime noise as run_extension.py.
Usage: python run_hetero.py DATA OUT_CSV --source carboncast:<R>|gb [--months ...] --seeds 33 --n-sub 20 [--cwm-frac 0.4] [--only-cwm]
"""
import argparse
import os
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from cwf import cwm_het, hetero as Hh
from cwf.carboncast import load_carboncast
from cwf.data import CIData, WIN, load_national
from cwf.execute import noisy_durations
from cwf.gate import calibrate
from cwf.sched import minute_series
from cwf.workflows import SPECS, build_raw, scaled_instance
import run_extension as RX

CI = None
REGION = "GB"
INSTANCES = {}
GATES = {}
CWM_FRAC = 1.0
ONLY_CWM = False


def job(args):
    seed, wi, T, t0 = args
    h, M = INSTANCES[(seed, wi, T)]
    act = CI.actual(t0, RX.EXEC_WIN)
    iss = CI.vintage(t0, RX.PLAN_WIN)
    gate = GATES[t0]
    rows = []
    Hx = len(act) * 30
    act_p = minute_series(act, Hx)
    for f in RX.FACTORS:
        D = int(round(f * M))
        Hp = D + T * 60
        bst, bmc = Hh.heft(h, Hp)
        rng_rt = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 9])
        rw = noisy_durations(h.w, rng_rt, RX.RT_SIGMA)
        b_nom = Hh.emissions(h, bst, bmc, Hh.finish(h, bst, bmc) - bst, act_p, D)
        ba, be, brd = Hh.execute(h, bst, bmc, rw, Hx)
        b_rt = Hh.emissions(h, ba, bmc, brd, act_p, D)
        b_nat = Hh.brown_energy(h, bst, bmc, D, act, CWM_FRAC)

        def record(name, regime, st, mc, used):
            e = Hh.finish(h, st, mc)
            c = Hh.emissions(h, st, mc, e - st, act_p, D)
            a, fin, rd = Hh.execute(h, st, mc, rw, Hx)
            c_rt = Hh.emissions(h, a, mc, rd, act_p, D)
            nat = Hh.brown_energy(h, st, mc, D, act, CWM_FRAC)
            rows.append(dict(seed=seed, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=name, regime=regime,
                             saving=1 - c / b_nom, trap=c > b_nom * (1 + 1e-9), trap1=c > b_nom * 1.01,
                             miss=int(e.max()) > D, saving_rt=1 - c_rt / b_rt, trap1_rt=c_rt > b_rt * 1.01,
                             miss_rt=int(fin.max()) > D, heft_miss_rt=int(be.max()) > D, used_heft=used,
                             carbon_kg=c * Hh.UNIT_KW / 60 / 1000, heft_carbon_kg=b_nom * Hh.UNIT_KW / 60 / 1000,
                             M=M, D=D, region=REGION, fast_share=float((mc >= 4).mean()),
                             native_saving=(1 - nat / b_nat) if b_nat > 0 else np.nan))

        for regime, ci in (("oracle", act[:RX.PLAN_WIN]), ("issued", iss)):
            n_need = int(np.ceil(Hp / 30))
            ci_pad = np.concatenate([ci, np.full(max(0, n_need - len(ci)), ci[-1])])
            pp = minute_series(ci_pad, Hp)
            if not ONLY_CWM:
                deltas = np.arange(0, D - M + 1)
                s = bst[None, :] + deltas[:, None]
                e = Hh.finish(h, bst, bmc)[None, :] + deltas[:, None]
                k = int(np.argmin((Hh.MARG[bmc][None, :] * (pp[e] - pp[s])).sum(axis=1)))
                record("Shift", regime, bst + int(deltas[k]), bmc, k == 0)
                for g in ([None, gate] if regime == "issued" else [None]):
                    st, mc, ms, _ = Hh.ca_list_repaired(h, Hp, D, M, pp, tau=g)
                    rng = np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), 0 if g is None else 1])
                    s2, m2 = Hh.local_search(h, Hp, D, pp, st, mc, ms, rng, tau=g)
                    sfx = "" if g is None else "+Gate"
                    for name, (a, m) in (("CA-List", (st, mc)), ("CA-LS", (s2, m2))):
                        a2, m3, used = Hh.safeguard(h, a, m, bst, bmc, pp)
                        record(name + "+SG" + sfx, regime, a2, m3, used)
            cst, cmc, info = cwm_het.run(h, D, ci, CWM_FRAC)
            if cst is None:
                record("CWM+SG", regime, bst, bmc, True)
                rows[-1]["cwm_status"] = info
            else:
                record("CWM", regime, cst, cmc, False)
                a2, m3, used = Hh.safeguard(h, cst, cmc, bst, bmc, pp)
                record("CWM+SG", regime, a2, m3, used)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("out")
    ap.add_argument("--source", default="gb")
    ap.add_argument("--months", default="")
    ap.add_argument("--seeds", default="33")
    ap.add_argument("--n-sub", type=int, default=20)
    ap.add_argument("--cwm-frac", type=float, default=1.0)
    ap.add_argument("--only-cwm", action="store_true")
    ap.add_argument("--workflows", default="")
    a = ap.parse_args()
    global CI, REGION, CWM_FRAC, ONLY_CWM
    CWM_FRAC, ONLY_CWM = a.cwm_frac, a.only_cwm
    t_start = time.time()
    if a.source == "gb":
        fc, act = load_national(a.data, a.months.split(","))
    else:
        REGION = a.source.split(":", 1)[1]
        fc, act = load_carboncast(a.data, REGION)
    CI = CIData(fc, act)
    cand = np.arange(CI.act.index.min(), CI.act.index.max() - RX.EXEC_WIN * WIN, WIN)
    wfs = [int(x) for x in a.workflows.split(",")] if a.workflows else range(len(SPECS))
    jobs = []
    for seed in [int(s) for s in a.seeds.split(",")]:
        rng = np.random.default_rng(seed)
        subs = []
        for t0 in rng.permutation(cand):
            if (CI.vintage(t0, RX.PLAN_WIN) is not None and CI.actual(t0, RX.EXEC_WIN) is not None
                    and CI.tau(t0) is not None):
                g = calibrate(CI, t0, RX.ALPHA)
                if g is not None:
                    GATES[t0] = g; subs.append(t0)
            if len(subs) == a.n_sub:
                break
        for wi in wfs:
            label, recipe, n = SPECS[wi]
            raw = build_raw(recipe, n, seed * 100 + wi)
            for T in RX.TARGETS_H:
                inst, _ = scaled_instance(raw, RX.P, T * 60)
                h = Hh.HInst(inst)
                st, mc = Hh.heft(h, int(T * 60 * 4))
                INSTANCES[(seed, wi, T)] = (h, int(Hh.finish(h, st, mc).max()))
                jobs += [(seed, wi, T, t0) for t0 in subs]
    print(f"{len(jobs)} jobs; setup {time.time()-t_start:.0f}s", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            rows += r
            if k % 50 == 0:
                print(f"  {k}/{len(jobs)} done, {time.time()-t_start:.0f}s", flush=True)
                pd.DataFrame(rows).to_csv(a.out + ".partial", index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(rows)} rows in {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
