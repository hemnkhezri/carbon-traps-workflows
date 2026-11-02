"""Fig. 2: why the gate uses difference errors. Development data only (GB, Mar 2023 - Feb 2024).
For each vintage, level error e_lev = F(w) - A(w) and difference error for a deferral over lag L,
e_diff = (F(a) - F(b)) - (A(a) - A(b)). Plotted: 90% quantile of |error| vs lag, for horizons 0-48 h.
The level-error line is shown for comparison; a naive gate would need sqrt(2) x it if errors were independent."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cwf.data import load_national, CIData
months = [f"2023-{m:02d}" for m in range(3, 13)] + ["2024-01", "2024-02"]
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", months)
ci = CIData(fc, act)
caps = ci.captures[::12]  # every 12th vintage (about one every 6 h) keeps it fast
lags = np.arange(1, 49)   # 30-min windows, up to 24 h
lev, dif = [], {L: [] for L in lags}
for c in caps:
    g = ci._by_cap[c]
    g = g[(g.window_utc >= c) & (g.window_utc < c + 48 * 3600)].drop_duplicates("window_utc", keep="last")
    A = ci.act.reindex(g.window_utc.to_numpy()).to_numpy(float); F = g.forecast.to_numpy(float)
    ok = ~np.isnan(A); A, F = A[ok], F[ok]
    if len(F) < 49: continue
    lev.append(np.abs(F - A))
    for L in lags:
        dif[L].append(np.abs((F[:-L] - F[L:]) - (A[:-L] - A[L:])))
q_lev = np.quantile(np.concatenate(lev), 0.9)
q_dif = np.array([np.quantile(np.concatenate(dif[L]), 0.9) for L in lags])
np.savetxt("figures/fig2_data.csv", np.c_[lags / 2, q_dif], delimiter=",", header="lag_h,q90_abs_diff_error", comments="")
plt.rcParams.update({"font.family": "serif", "font.size": 9})
fig, ax = plt.subplots(figsize=(4.6, 2.9))
ax.plot(lags / 2, q_dif, color="#2a78d6", lw=2, label="Difference error (what the gate uses)")
ax.axhline(q_lev, color="#8a8984", lw=1.5, ls="--", label="Level error of one window")
ax.axhline(q_lev * np.sqrt(2), color="#eb6834", lw=1.5, ls=":", label=r"Difference error if windows were independent ($\sqrt{2}\times$ level)")
ax.set_xlabel("Deferral lag (h)"); ax.set_ylabel("90th pct. of |error|\n(gCO$_2$/kWh)")
ax.set_xlim(0, 24); ax.set_ylim(0, None)
ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e5e5e5", lw=0.6)
fig.legend(loc="lower center", ncol=1, frameon=False, fontsize=7.5, bbox_to_anchor=(0.55, -0.02))
fig.tight_layout(rect=(0, 0.2, 1, 1))
fig.savefig("figures/fig2_gate_intuition.pdf"); fig.savefig("figures/fig2_gate_intuition.png", dpi=300)
print("level q90", round(q_lev, 1), "diff q90 at 0.5h, 3h, 12h, 24h:", [round(q_dif[i], 1) for i in (0, 5, 23, 47)])
