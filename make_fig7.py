"""Fig. 7: forecast loss across grids (exploratory). R and its 95% CI come from the sealed analyses
(GB: reports of analyse_confirm.py / CONFIRM_RESULTS.md; regions: results/extension_analysis.txt).
Error-to-variability ratio = MAE of 0-47 h forecasts / mean within-vintage SD of actual CI
(computed by forecast_skill.py). Trap rates: CA-LS+SG under issued forecasts, all f pooled."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
S = json.load(open("figures/fig7_data.json"))
plt.rcParams.update({"font.family": "serif", "font.size": 9})
BLUE, ORANGE, NEUTRAL = "#2a78d6", "#eb6834", "#8a8984"
fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.1, 1]})
for r in S:
    x, (m, lo, hi) = r["ratio"], r["R"]
    a.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="o", color=BLUE if r["region"] != "GB" else ORANGE,
               ms=6, capsize=3, lw=1.2, mec="white", mew=1)
    a.annotate(r["region"], (x, m), xytext=(7, 3), textcoords="offset points", fontsize=8)
a.axhline(0.75, color=NEUTRAL, ls="--", lw=1); a.text(1.5, 0.77, "H1/E1 threshold", fontsize=7, color="#555", ha="right")
a.set_xlabel("Forecast error / intraday variability of CI"); a.set_ylabel("R = issued / oracle saving")
a.set_ylim(-0.1, 1.0); a.set_xlim(0.3, 1.6); a.set_title("(a) Share of the oracle saving kept", fontsize=9, loc="left")
order = sorted(S, key=lambda r: r["ratio"])
y = np.arange(len(order))
b.barh(y + 0.19, [r["trap"] for r in order], height=0.36, color=BLUE, label="CA-LS+SG")
b.barh(y - 0.19, [r["trap_gate"] for r in order], height=0.36, color=ORANGE, label="CA-LS+SG+Gate")
b.set_yticks(y, [r["region"] for r in order]); b.invert_yaxis()
b.set_xlabel("Carbon-trap rate, issued (%)"); b.set_title("(b) Traps without and with the gate", fontsize=9, loc="left")
for ax in (a, b):
    ax.spines[["top", "right"]].set_visible(False)
a.grid(axis="y", color="#e5e5e5", lw=0.6); b.grid(axis="x", color="#e5e5e5", lw=0.6)
fig.legend(*b.get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.75, -0.01))
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig("figures/fig7_regions.pdf"); fig.savefig("figures/fig7_regions.png", dpi=300)
