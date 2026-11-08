"""RC-CAS v2 pilot (PILOT_RC2_PREREG.md). Development data. Usage: python run_pilot_rc.py ARCHIVE OUT_CSV [--seeds 1,2] [--n-sub 10]"""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import argparse
import os
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from cwf.data import CIData, WIN, load_national
from cwf.gates_alt import calibrate_all
from cwf.replan import gated_shift
from cwf.scenarios import error_bank, scenarios
from cwf.rcas import allowed, plan_costs, risk_local_search
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance

P = 8; TARGETS_H = [4, 12]; FACTORS = [1.2, 1.5, 2.0, 3.0]; PLAN_WIN = 94; EXEC_WIN = PLAN_WIN + 24
DEV = [f"2023-{m:02d}" for m in range(3, 13)] + ["2024-01", "2024-02"]
CI = None; INST = {}; G = {}; BANK = {}


def pad(ci, H):
    n = int(np.ceil(H / 30)); return np.concatenate([ci, np.full(max(0, n - len(ci)), ci[-1])])


def cost(dur, s, pref):
    s = np.asarray(s, int); return float(np.sum(pref[s + dur] - pref[s]))


def job(args):
    seed, wi, T, t0 = args
    inst, M = INST[(seed, wi, T)]
    act = CI.actual(t0, EXEC_WIN); iss = CI.vintage(t0, PLAN_WIN)
    gates = G[t0]; S = scenarios(CI, t0, iss, BANK[t0]); K = len(S)
    act_p = minute_series(act, len(act) * 30)
    rows = []
    for f in FACTORS:
        D = int(round(f * M)); H = D + T * 60
        base = heft(inst, P, H)
        rng = lambda k: np.random.default_rng([seed, int(t0) // WIN, wi, T, int(f * 10), k])
        pp_o = minute_series(pad(act[:PLAN_WIN], H), H); pp = minute_series(pad(iss, H), H)
        pp_m = minute_series(pad(iss + (S - iss[None, :]).mean(0), H), H)
        sp = [minute_series(pad(S[k], H), H) for k in range(K)]
        cb = cost(inst.dur, base, act_p)
        def calsg(pref, tau=None, k=0):
            s, cl, _ = ca_list_repaired(inst, P, H, D, M, pref, tau=tau)
            s = local_search(inst, P, H, D, pref, s, cl, rng(k), tau=tau)
            return safeguard(inst, s, base, pref)[0]
        so = calsg(pp_o)
        cand = {"HEFT": base}
        cand["Shift"] = base + int(np.argmin([(pp[base + d + inst.dur] - pp[base + d]).sum() for d in range(0, D - M + 1)]))
        cand["Shift+Gate"] = gated_shift(inst, base, M, D, pp, gates["diff0.9"])
        cand["CA-LS+SG"] = calsg(pp)
        for a in ("0.8", "0.9", "0.95"):
            cand[f"CA-LS+SG+Gate[{a}]"] = calsg(pp, gates[f"diff{a}"], 1)
        cand["CA-LS+SG[biascorr]"] = calsg(pp_m)
        cbk = np.array([cost(inst.dur, base, q) for q in sp])
        info = {}
        for nm, s in cand.items():
            ck = np.array([cost(inst.dur, s, q) for q in sp])
            info[nm] = ((np.sum(ck > 1.01 * cbk) + 1) / (K + 1), float(np.mean(1 - ck / cbk)))
        def rec(name, s, extra=None):
            c = cost(inst.dur, s, act_p)
            r = dict(seed=seed, wf=SPECS[wi][0], T=T, f=f, t0=int(t0), sched=name, saving=1 - c / cb,
                     trap1=c > 1.01 * cb, miss=int(max(s + inst.dur)) > D, K=K)
            if extra: r.update(extra)
            rows.append(r)
        rec("CA-LS+SG[oracle]", so)
        for nm, s in cand.items():
            rec(nm, s, dict(scen_trap=info[nm][0], scen_saving=info[nm][1]))
        for a in (0.05, 0.10, 0.20):
            ok = [nm for nm in cand if info[nm][0] <= a or nm == "HEFT"]
            best = max(ok, key=lambda nm: info[nm][1])
            rec(f"RC-CAS[{a}]", cand[best], dict(chosen=best))
        # v2: scenario split. Optimise on half A (selection of a feasible start, then chance-constrained LS),
        # certify on half B; fall back to HEFT if the certification fails.
        SPall = np.array(sp); iA = np.arange(0, K, 2); iB = np.arange(1, K, 2)
        SA, SB = SPall[iA], SPall[iB]; CbA = plan_costs(inst, base, SA); CbB = plan_costs(inst, base, SB)
        for a in (0.05, 0.10, 0.20):
            mA, mB = allowed(a, len(iA)), allowed(a, len(iB))
            feas = []
            for nm, s in cand.items():
                cA = plan_costs(inst, s, SA)
                if (cA > 1.01 * CbA).sum() <= mA or nm == "HEFT":
                    feas.append((cA.mean(), nm))
            s0 = cand[min(feas)[1]]
            s2 = risk_local_search(inst, P, H, D, SA, CbA, s0, max(mA, 0) if mA >= 0 else 0, rng(7)) if mA >= 0 else s0
            cB = plan_costs(inst, s2, SB); cert = (cB > 1.01 * CbB).sum() <= mB
            rec(f"RCv2[{a}]", s2 if cert else base, dict(certified=bool(cert), start_from=min(feas)[1]))
            sall = risk_local_search(inst, P, H, D, SPall, cbk, cand[max([nm for nm in cand if info[nm][0] <= a or nm == "HEFT"], key=lambda nm: info[nm][1])],
                                     max(allowed(a, K), 0), rng(8))
            rec(f"RCv2-nosplit[{a}]", sall)
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("archive"); ap.add_argument("out")
    ap.add_argument("--seeds", default="3,4"); ap.add_argument("--n-sub", type=int, default=20)
    a = ap.parse_args(); global CI
    t = time.time(); fc, act = load_national(a.archive, DEV); CI = CIData(fc, act)
    cand = np.arange(CI.act.index.min(), CI.act.index.max() - EXEC_WIN * WIN, WIN); jobs = []
    for seed in [int(s) for s in a.seeds.split(",")]:
        rng = np.random.default_rng(seed + 500); subs = []  # v2 uses new seeds (3, 4)
        for t0 in rng.permutation(cand):
            if CI.vintage(t0, PLAN_WIN) is not None and CI.actual(t0, EXEC_WIN) is not None:
                g = calibrate_all(CI, t0); b = error_bank(CI, t0)
                if g is not None and b is not None and len(b) >= 19:
                    G[t0] = g; BANK[t0] = b; subs.append(t0)
            if len(subs) == a.n_sub: break
        for wi in range(len(SPECS)):
            raw = build_raw(SPECS[wi][1], SPECS[wi][2], seed * 100 + wi)
            for T in TARGETS_H:
                INST[(seed, wi, T)] = scaled_instance(raw, P, T * 60); jobs += [(seed, wi, T, t0) for t0 in subs]
    print(f"{len(jobs)} jobs, setup {time.time()-t:.0f}s, K per submission {[len(BANK[s]) for s in list(BANK)[:5]]}", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            rows += r
            if k % 20 == 0:
                print(f"  {k}/{len(jobs)} {time.time()-t:.0f}s", flush=True); pd.DataFrame(rows).to_csv(a.out + ".partial", index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False); print("wrote", len(rows))


if __name__ == "__main__":
    main()
