"""ENTSO-E study runner (EXT4_PREREG.md). Same jobs as run_extension.py (all schedulers, regimes
oracle / synthetic / issued, runtime noise), on day-ahead vintages built by cwf/entsoe.py.

Day-ahead inputs cover at most the end of the next local day, so only T = 4 h workflows are run
(deadlines up to about 12.3 h) and the planning window is 13 h (26 windows).

Usage (from the repository root):
  python scripts/run_entsoe.py DATA_ROOT OUT_CSV --zone DE_LU --seeds 50,51,52 --n-sub 40 \
      --t0-from 2025-11-01 --t0-to 2026-11-01
DATA_ROOT holds the folders written by download_entsoe.py (dev/ and, for the confirmatory run, confirm/).
"""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import run_extension as rx
from cwf.data import CIData, WIN
from cwf.entsoe import TZ, build_vintages
from cwf.gate import calibrate
from cwf.workflows import SPECS, build_raw, scaled_instance

rx.TARGETS_H = [4]
rx.PLAN_WIN = 26                      # 13 h
rx.EXEC_WIN = rx.PLAN_WIN + 4 * 2     # actual CI for noisy overruns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("--zone", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--n-sub", type=int, default=40)
    ap.add_argument("--t0-from", required=True)
    ap.add_argument("--t0-to", required=True)
    a = ap.parse_args()
    t_start = time.time()
    fc, act = build_vintages(a.root, a.zone)
    rx.CI = CIData(fc, act)
    rx.REGION = a.zone
    CI = rx.CI
    lo = int(pd.Timestamp(a.t0_from, tz=TZ).tz_convert("UTC").timestamp())
    hi = int(pd.Timestamp(a.t0_to, tz=TZ).tz_convert("UTC").timestamp())
    cand = np.arange(max(lo, CI.act.index.min()), min(hi, CI.act.index.max() - rx.EXEC_WIN * WIN), WIN)

    def valid(t0):
        return (CI.vintage(t0, rx.PLAN_WIN) is not None and CI.actual(t0, rx.EXEC_WIN) is not None
                and CI.tau(t0) is not None)

    jobs = []
    for seed in [int(s) for s in a.seeds.split(",")]:
        rng = np.random.default_rng(seed)
        subs = []
        for t0 in rng.permutation(cand):
            if valid(t0):
                g = calibrate(CI, t0, rx.ALPHA)
                if g is not None:
                    rx.GATES[t0] = g
                    subs.append(t0)
            if len(subs) == a.n_sub:
                break
        for wi, (label, recipe, n) in enumerate(SPECS):
            raw = build_raw(recipe, n, seed * 100 + wi)
            for T in rx.TARGETS_H:
                rx.INSTANCES[(seed, wi, T)] = scaled_instance(raw, rx.P, T * 60)
                jobs += [(seed, wi, T, t0) for t0 in subs]
        print(f"seed {seed}: {len(subs)} submissions", flush=True)
    print(f"{len(jobs)} jobs; setup {time.time()-t_start:.0f}s", flush=True)
    rows = []
    with Pool(os.cpu_count()) as pool:
        for k, r in enumerate(pool.imap_unordered(rx.job, jobs, chunksize=2)):
            rows += r
            if k % 100 == 0:
                print(f"  {k}/{len(jobs)} done, {time.time()-t_start:.0f}s", flush=True)
                pd.DataFrame(rows).to_csv(a.out + ".partial", index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(rows)} rows in {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
