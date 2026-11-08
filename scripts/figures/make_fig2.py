"""Fig. 2: the quantity the gate uses. Development data only (GB, Mar 2023 - Feb 2024), horizons 0-48 h.
Difference error for a deferral over lag L: e = (F(a) - F(b)) - (A(a) - A(b)), both directions (as in cwf/gate.py).
Plotted against the lag: the 0.9-quantile of e (the difference-gate threshold, alpha = 0.9) and, for comparison,
the threshold of a level-interval rule in the style of Li et al.: q0.9(A - F) + q0.9(F - A), which does not depend on the lag."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cwf.data import load_national, CIData
months = [f"2023-{m:02d}" for m in range(3, 13)] + ["2024-01", "2024-02"]
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", months)
ci = CIData(fc, act)
caps = ci.captures[::12]  # about one vintage every 6 h
lags = np.arange(1, 94)
lev, dif = [], {L: [] for L in lags}
for c in caps:
    g = ci._by_cap[c]
    g = g[(g.window_utc >= c) & (g.window_utc < c + 48 * 3600)].drop_duplicates("window_utc", keep="last")
    A = ci.act.reindex(g.window_utc.to_numpy()).to_numpy(float); F = g.forecast.to_numpy(float)
    ok = ~np.isnan(A); A, F = A[ok], F[ok]
    if len(F) < 94: continue
    lev.append(F - A)
    for L in lags:
        e = (F[:-L] - F[L:]) - (A[:-L] - A[L:]); dif[L] += [e, -e]
lev = np.concatenate(lev)
q_level_rule = np.quantile(-lev, 0.9) + np.quantile(lev, 0.9)
q_dif = np.array([np.quantile(np.concatenate(dif[L]), 0.9) for L in lags])
np.savetxt("figures/fig2_data.csv", np.c_[lags / 2, q_dif], delimiter=",", header="lag_h,q90_signed_diff_error", comments="")
plt.rcParams.update({"font.family": "Liberation Serif", "mathtext.fontset": "stix", "font.size": 8.5})
fig, ax = plt.subplots(figsize=(4.8, 3.0))
ax.plot(lags / 2, q_dif, color="#2a78d6", lw=2, label="Difference gate: 0.9-quantile of difference error")
ax.axhline(q_level_rule, color="#eb6834", lw=1.5, ls="--", label="Level-interval rule: sum of 0.9-quantiles of level error")
ax.set_xlabel("Deferral lag (h)"); ax.set_ylabel("Required forecast gain\n(gCO$_2$/kWh)")
ax.set_xlim(0, 47); ax.set_ylim(0, None)
ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e5e5e5", lw=0.6)
fig.legend(loc="lower center", ncol=1, frameon=False, fontsize=7.5, bbox_to_anchor=(0.55, -0.01))
fig.tight_layout(rect=(0, 0.16, 1, 1))
fig.savefig("figures/fig2_gate_intuition.pdf"); fig.savefig("figures/fig2_gate_intuition.png", dpi=300)
print("level rule", round(q_level_rule, 1), "diff gate at 0.5,3,6,12,24,47h:", [round(q_dif[i], 1) for i in (0, 5, 11, 23, 47, 92)])
