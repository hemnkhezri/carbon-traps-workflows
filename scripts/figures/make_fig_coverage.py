"""Fig. S2: empirical coverage of the alpha = 0.9 gate thresholds on the GB confirmatory data
(reports/gate_coverage.txt, reports/gate_coverage_mean.txt)."""
import os, sys
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _REPO_ROOT)  # scripts are run from the repository root: python scripts/<name>.py
import sys
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style
from style import BLUE, INK, INK2, NEUTRAL, ORANGE, plt
style.apply()
cov = np.array([[0.908, 0.902, 0.900, 0.899], [0.899, 0.895, 0.896, 0.898], [np.nan, 0.887, 0.907, 0.891],
                [np.nan, np.nan, 0.890, 0.898], [np.nan, np.nan, np.nan, 0.902]])
dur = np.array([0.5, 1, 2, 4, 8]); c = np.array([0.898, 0.899, 0.905, 0.922, 0.953]); p10 = np.array([0.820, 0.817, 0.820, 0.831, 0.871])
fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1, 1.15]})
cmap = LinearSegmentedColormap.from_list("d", ["#eb6834", "#f7f6f2", "#2a78d6"]); cmap.set_bad("#f3f3f1")
a.imshow(np.ma.masked_invalid(cov), cmap=cmap, vmin=0.85, vmax=0.95, aspect="auto")
for i in range(5):
    for j in range(4):
        a.text(j, i, "–" if np.isnan(cov[i, j]) else f"{100*cov[i, j]:.1f}", ha="center", va="center", fontsize=8.5,
               color=NEUTRAL if np.isnan(cov[i, j]) else INK)
a.set_xticks(range(4), ["0–6", "6–12", "12–24", "24–48"]); a.set_yticks(range(5), ["0–3", "3–6", "6–12", "12–24", "24–48"])
a.set_xlabel("Forecast horizon (h)", labelpad=1); a.set_ylabel("Deferral lag (h)", labelpad=1); a.grid(False); a.tick_params(length=0)
for s in a.spines.values():
    s.set_visible(False)
a.set_title("(a) Coverage per bin, 30-min windows (%)", loc="left", fontweight="bold")
b.axhline(90, color=INK2, ls="--", lw=1); b.text(8.3, 90.4, "nominal 90%", fontsize=7.5, color=INK2, ha="right", va="bottom")
b.plot(dur, 100 * c, "-o", color=BLUE, ms=5, mec="white", label="all decisions")
b.plot(dur, 100 * p10, ":s", color=ORANGE, ms=4.5, mec="white", lw=1.4, label="10th percentile over submissions")
b.set_xscale("log", base=2); b.set_xticks(dur, ["0.5", "1", "2", "4", "8"]); b.minorticks_off()
b.set_xlabel("Task duration (h)", labelpad=1); b.set_ylabel("Coverage (%)", labelpad=1); b.set_ylim(78, 98)
b.legend(loc="upper left", fontsize=7.5)
b.set_title("(b) Coverage by task duration", loc="left", fontweight="bold")
fig.tight_layout(w_pad=2.0)
fig.savefig("figures/figS2_coverage.png", dpi=400, bbox_inches="tight"); fig.savefig("figures/figS2_coverage.pdf", bbox_inches="tight")
