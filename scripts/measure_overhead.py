"""Scheduling overhead (wall-clock, one core): HEFT, Shift, CA-List, CA-LS, gate calibration, gated CA-LS.
GB confirmatory data, seed 10 instances, 10 submissions, f = 2.0."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import time, json
import numpy as np
from cwf.data import CIData, WIN, load_national
from cwf.gate import calibrate
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance
CFG = json.load(open("confirm_config.json")); P = CFG["P"]
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", CFG["months"]); CI = CIData(fc, act)
rng = np.random.default_rng(10); cand = np.arange(CI.act.index.min(), CI.act.index.max() - 142 * WIN, WIN); subs = []
for t0 in rng.permutation(cand):
    if CI.vintage(t0, 94) is not None and CI.actual(t0, 142) is not None: subs.append(t0)
    if len(subs) == 10: break
T = {k: [] for k in ("HEFT", "Shift", "CA-List", "CA-LS", "Gate calibration", "CA-LS+Gate")}; ntask = []
for wi in range(len(SPECS)):
    raw = build_raw(SPECS[wi][1], SPECS[wi][2], 1000 + wi)
    for Th in (4, 12):
        inst, M = scaled_instance(raw, P, Th * 60); ntask.append(len(inst.dur))
        for t0 in subs[:3]:
            D = int(2.0 * M); H = D + Th * 60
            pp = minute_series(np.concatenate([CI.vintage(t0, 94), np.full(200, CI.vintage(t0, 94)[-1])]), H)
            a = time.perf_counter(); base = heft(inst, P, H); T["HEFT"].append(time.perf_counter() - a)
            a = time.perf_counter(); _ = base + int(np.argmin([(pp[base + d + inst.dur] - pp[base + d]).sum() for d in range(0, D - M + 1)])); T["Shift"].append(time.perf_counter() - a)
            a = time.perf_counter(); s, cl, _ = ca_list_repaired(inst, P, H, D, M, pp); T["CA-List"].append(time.perf_counter() - a)
            a = time.perf_counter(); local_search(inst, P, H, D, pp, s, cl, np.random.default_rng(0)); T["CA-LS"].append(T["CA-List"][-1] + time.perf_counter() - a)
            a = time.perf_counter(); g = calibrate(CI, t0, 0.9); T["Gate calibration"].append(time.perf_counter() - a)
            a = time.perf_counter(); s, cl, _ = ca_list_repaired(inst, P, H, D, M, pp, tau=g); local_search(inst, P, H, D, pp, s, cl, np.random.default_rng(0), tau=g); T["CA-LS+Gate"].append(time.perf_counter() - a)
print("tasks per workflow:", min(ntask), "-", max(ntask), "| runs per scheduler:", len(T["HEFT"]))
for k, v in T.items():
    v = np.array(v); print(f"{k:18s} median {np.median(v):7.3f} s   95th pct {np.percentile(v, 95):7.3f} s   max {v.max():7.3f} s")
