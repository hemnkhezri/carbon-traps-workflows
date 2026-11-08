"""Re-run one confirmatory job (seed 11, epigenomics, T = 4 h, f = 3.0, t0 = 1784962800) and save the plans,
the issued vintage and the realised intensity for the real-trap figure. Checks the savings against results/confirm.csv."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import run_confirm as RC
from cwf.data import CIData, WIN, load_national
from cwf.gate import calibrate
from cwf.sched import ca_list_repaired, heft, local_search, minute_series, safeguard
from cwf.workflows import SPECS, build_raw, scaled_instance
SEED, WF, T, F, T0 = 11, sys.argv[1] if len(sys.argv) > 1 else "epigenomics", 4, 3.0, 1784962800
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", RC.CFG["months"])
CI = CIData(fc, act)
wi = [s[0] for s in SPECS].index(WF)
inst, M = scaled_instance(build_raw(SPECS[wi][1], SPECS[wi][2], SEED * 100 + wi), RC.P, T * 60)
a = CI.actual(T0, RC.EXEC_WIN); iss = CI.vintage(T0, RC.PLAN_WIN); g = calibrate(CI, T0, RC.ALPHA)
D = int(round(F * M)); H = D + T * 60; Hx = len(a) * 30
act_p = minute_series(a, Hx)
pad = lambda ci: np.concatenate([ci, np.full(max(0, int(np.ceil(H / 30)) - len(ci)), ci[-1])])
base = heft(inst, RC.P, H)
out = {"M": int(M), "D": D, "dur": inst.dur.tolist(), "act": a.tolist(), "iss": iss.tolist(), "heft": base.tolist(),
       "cap_lag_min": g.cap_lag_min, "t0": T0}
for regime, ci in (("oracle", a[:RC.PLAN_WIN]), ("issued", iss)):
    plan_p = minute_series(pad(ci), H)
    for gate in ([None, g] if regime == "issued" else [None]):
        s_list, cl, _ = ca_list_repaired(inst, RC.P, H, D, M, plan_p, tau=gate)
        rng = np.random.default_rng([SEED, int(T0) // WIN, wi, T, int(F * 10), 0 if gate is None else 1])
        s_ls = local_search(inst, RC.P, H, D, plan_p, s_list, cl, rng, tau=gate)
        st, used = safeguard(inst, s_ls, base, plan_p)
        key = regime + ("_gate" if gate is not None else "")
        out[key] = st.tolist()
        cb = RC.carbon_of(inst.dur, base, act_p); c = RC.carbon_of(inst.dur, st, act_p)
        cbp = RC.carbon_of(inst.dur, base, plan_p); cp = RC.carbon_of(inst.dur, st, plan_p)
        out[key + "_saving"] = 1 - c / cb; out[key + "_planned_saving"] = 1 - cp / cbp
        print(key, "realised saving", round(1 - c / cb, 4), "planned saving", round(1 - cp / cbp, 4))
d = pd.read_csv("results/confirm.csv")
print(d[(d.seed == SEED) & (d.wf == WF) & (d["T"] == T) & (d.f == F) & (d.t0 == T0) & d.sched.isin(["CA-LS+SG", "CA-LS+SG+Gate"])][["sched", "regime", "saving"]].to_string())
json.dump(out, open(f"figures/real_trap_{WF}.json", "w"))
