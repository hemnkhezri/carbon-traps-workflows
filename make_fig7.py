"""Fig. 7: forecast loss across grids (exploratory). R and its 95% CI come from the sealed analyses
(GB: reports of analyse_confirm.py / CONFIRM_RESULTS.md; regions: results/extension_analysis.txt).
Error-to-variability ratio = MAE of 0-47 h forecasts / mean within-vintage SD of actual CI
(grid-month points from skill_by_month.py). Trap rates: CA-LS+SG under issued forecasts, all f pooled."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
S = json.load(open("figures/fig7_data.json"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
BLUE, ORANGE, NEUTRAL = "#2a78d6", "#eb6834", "#8a8984"
fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.1, 1]})
import pandas as pd
from scipy.stats import spearmanr
M = pd.read_csv("results/skill_by_month.csv")
mk = {"CISO": "o", "DE": "s", "GB": "D", "PJM": "^", "ERCO": "v"}
for reg, g in M.groupby("region"):
    a.scatter(g.ratio, g.R, marker=mk[reg], s=26, color=ORANGE if reg == "GB" else BLUE, edgecolor="white", lw=0.6, label=reg, zorder=3)
rho = spearmanr(M.ratio, M.R)[0]
a.text(0.97, 0.97, f"Spearman $r_s$ = {rho:.2f} ({len(M)} grid-months)", transform=a.transAxes, ha="right", va="top", fontsize=7.5)
a.axhline(0.75, color=NEUTRAL, ls="--", lw=1)
a.text(1.84, 0.73, "R = 0.75", fontsize=6.5, color="#52514e", va="top", ha="right")
a.set_xlabel(r"$\kappa$ = forecast MAE / SD of intensity (47-h window)"); a.set_ylabel("R = forecast / oracle saving")
a.legend(frameon=False, fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.22), handletextpad=0.1, columnspacing=0.6)
a.set_title("(a) Share of the oracle saving kept, per grid-month", fontsize=9, loc="left")
order = sorted(S, key=lambda r: r["ratio"])
y = np.arange(len(order))
b.barh(y + 0.19, [r["trap"] for r in order], height=0.36, color=BLUE, label="CA-LS+SG")
b.barh(y - 0.19, [r["trap_gate"] for r in order], height=0.36, color=ORANGE, label="CA-LS+SG+Gate")
b.set_yticks(y, [r["region"] for r in order]); b.invert_yaxis()
b.set_xlabel("Carbon-trap rate, forecast regime (%)"); b.set_title("(b) Traps without and with the gate", fontsize=9, loc="left")
for ax in (a, b):
    ax.spines[["top", "right"]].set_visible(False)
a.grid(axis="y", color="#e5e5e5", lw=0.6); b.grid(axis="x", color="#e5e5e5", lw=0.6)
fig.legend(*b.get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.75, -0.02))
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("figures/fig7_regions.pdf"); fig.savefig("figures/fig7_regions.png", dpi=300)
