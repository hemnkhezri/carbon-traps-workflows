"""Fig. 3: the difference-error gate. (a) schematic of a difference error; (b) calibrated 0.9-quantiles per
lag x horizon bin (GB development data, Aug-Oct 2023, pooled; cwf/gate.py calibrate with days=60);
(c) required gain by lag (figures/fig2_data.csv from make_fig2.py, Mar 2023 - Feb 2024) with the decision regions."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import sys

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style
from style import AQUA, BLUE, INK, INK2, NEUTRAL, ORANGE, RED, plt

style.apply()
SYM = dict(fontfamily="DejaVu Sans", fontweight="bold")
fig = plt.figure(figsize=(7.0, 2.55))

# (a) difference error on one window pair: the forecast favours b, the realised intensity favours a
ax = fig.add_axes([0.035, 0.17, 0.27, 0.68])
t = np.linspace(0, 24, 300)
A = 178 - 32 * np.exp(-((t - 5) / 2.5) ** 2) - 8 * np.exp(-((t - 16) / 3) ** 2)
F = 184 - 8 * np.exp(-((t - 5) / 2.5) ** 2) - 44 * np.exp(-((t - 16) / 2.6) ** 2)
ax.plot(t, F, color=ORANGE, ls="--", lw=1.5, label="forecast")
ax.plot(t, A, color=BLUE, lw=1.6, label="realised")
a, b = 5, 16
fa, fb, aa, ab = (np.interp(x, t, y) for x, y in ((a, F), (b, F), (a, A), (b, A)))
for x in (a, b):
    ax.axvline(x, color=NEUTRAL, lw=0.7, ls=":")
ax.plot([a, b], [fa, fb], "o", color=ORANGE, ms=4.5, mec="white", zorder=4)
ax.plot([a, b], [aa, ab], "o", color=BLUE, ms=4.5, mec="white", zorder=4)
ax.annotate("", xy=(b + 2.2, fb), xytext=(b + 2.2, fa), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.2, mutation_scale=8))
ax.text(b + 2.7, (fa + fb) / 2, "forecast\ngain > 0", color=ORANGE, fontsize=8, va="center")
ax.annotate("", xy=(a - 2.2, ab), xytext=(a - 2.2, aa), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.2, mutation_scale=8))
ax.text(a - 2.2, aa - 6, "realised\ngain < 0", color=BLUE, fontsize=8, va="top", ha="center")
ax.set_xticks([a, b], ["start $a$", "deferred $b$"], fontsize=10); ax.set_yticks([]); ax.grid(False)
ax.set_xlim(-1.5, 25); ax.set_ylim(118, 200)
ax.legend(loc="upper center", ncol=2, fontsize=8, handlelength=1.8, borderaxespad=0.1, columnspacing=1.0)
ax.set_title("(a) Error of a deferral decision", loc="left", fontweight="bold")
ax.text(12, 120, r"$e = (\bar F_a-\bar F_b) - (\bar A_a-\bar A_b)$", fontsize=9, ha="center", va="bottom")

# (b) quantile table
ax = fig.add_axes([0.385, 0.17, 0.235, 0.68])
q = np.array([[16, 18, 16, 16], [30, 34, 32, 32], [np.nan, 43, 43, 44], [np.nan, np.nan, 45, 46],
              [np.nan, np.nan, np.nan, 48]])
cmap = LinearSegmentedColormap.from_list("b", ["#eaf2fc", BLUE]); cmap.set_bad("#f3f3f1")
ax.imshow(np.ma.masked_invalid(q), cmap=cmap, vmin=5, vmax=60, aspect="auto")
for i in range(5):
    for j in range(4):
        ax.text(j, i, "–" if np.isnan(q[i, j]) else f"{q[i, j]:.0f}", ha="center", va="center", fontsize=9,
                color=NEUTRAL if np.isnan(q[i, j]) else (INK if q[i, j] < 40 else "white"))
ax.set_xticks(range(4), ["0–6", "6–12", "12–24", "24–48"]); ax.set_yticks(range(5), ["0–3", "3–6", "6–12", "12–24", "24–48"])
ax.set_xlabel("Forecast horizon (h)", labelpad=1); ax.set_ylabel("Deferral lag (h)", labelpad=1)
ax.tick_params(length=0); ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("(b) Calibrated thresholds $q$", loc="left", fontweight="bold")

# (c) decision rule
ax = fig.add_axes([0.715, 0.17, 0.275, 0.68])
lag, qd = np.loadtxt("figures/fig2_data.csv", delimiter=",", skiprows=1, unpack=True)
ax.fill_between(lag, qd, 90, color=AQUA, alpha=0.10, lw=0)
ax.fill_between(lag, 0, qd, color=NEUTRAL, alpha=0.10, lw=0)
ax.plot(lag, qd, color=BLUE, lw=1.8)
ax.axhline(77, color=ORANGE, ls="--", lw=1.4)
ax.text(46.5, 79, "level-interval rule", color=ORANGE, fontsize=8, ha="right", va="bottom")
ax.text(46.5, 52, "difference gate", color=BLUE, fontsize=8, ha="right", va="bottom")
ax.text(30, 66, "defer", color=AQUA, fontsize=8.5, ha="center", fontweight="bold")
ax.text(30, 18, "keep earliest start", color=INK2, fontsize=8.5, ha="center")
ax.plot(1, 25, "o", color=AQUA, ms=6, mec="white"); ax.text(1.0, 31, "✓", color=AQUA, fontsize=9, va="bottom", ha="center", **SYM)
ax.plot(8, 30, "o", color=RED, ms=6, mec="white"); ax.text(9.0, 30, "✗", color=RED, fontsize=9, va="center", **SYM)
ax.set_xlim(0, 47); ax.set_ylim(0, 90); ax.set_xticks([0, 12, 24, 36, 47])
ax.set_xlabel("Deferral lag (h)", labelpad=1); ax.set_ylabel("Forecast gain (gCO$_2$/kWh)", labelpad=1)
ax.set_title("(c) Decision", loc="left", fontweight="bold")
fig.savefig("figures/fig_gate_method.png", dpi=400, bbox_inches="tight")
fig.savefig("figures/fig_gate_method.pdf", bbox_inches="tight")
print("ok")
