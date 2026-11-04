"""Fig. 1 (concept, illustrative curves, not data): how a deferral planned on a forecast becomes a carbon trap."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
BLUE, ORANGE, AQUA, NEUTRAL = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
t = np.linspace(0, 24, 481)
actual = 195 - 50 * np.exp(-((t - 3.5) / 3.0) ** 2) + 6 * np.sin(t / 3.2)
forecast = 195 - 70 * np.exp(-((t - 14.5) / 2.6) ** 2) + 6 * np.sin(t / 3.2)
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [2.1, 1]})
a.plot(t, forecast, color=ORANGE, lw=2, ls="--", label="Issued forecast (at submission)")
a.plot(t, actual, color=BLUE, lw=2, label="Realised carbon intensity")
heft = (0.0, 6.0); ca = (12.0, 18.0); D = 20
a.axvspan(*heft, ymin=0.02, ymax=0.12, color=NEUTRAL, alpha=0.9)
a.axvspan(*ca, ymin=0.02, ymax=0.12, color=AQUA, alpha=0.9)
a.text(np.mean(heft), 104, "HEFT plan", ha="center", va="center", color="white", fontsize=8)
a.text(np.mean(ca), 104, "carbon-aware", ha="center", va="center", color="white", fontsize=8)
a.axvline(D, color="#444", lw=1, ls=":"); a.text(D + 0.3, 104, "D", fontsize=9, color="#444", ha="left", style="italic")
a.annotate("forecast dip", xy=(13.9, 124), xytext=(11.6, 126), ha="right", va="center", fontsize=7.5,
           arrowprops=dict(arrowstyle="->", color=ORANGE), color=ORANGE)
a.annotate("actual dip (now)", xy=(3.5, 147), xytext=(0.4, 127), va="center", fontsize=7.5, arrowprops=dict(arrowstyle="->", color=BLUE), color=BLUE)
a.set_xlim(0, 24); a.set_ylim(98, 228); a.set_xlabel("Hours after submission"); a.set_ylabel("gCO$_2$/kWh")
a.set_title("(a) Planning on a forecast", loc="left", fontsize=9)
a.legend(loc="upper left", frameon=False, fontsize=7.5, ncol=2)
def em(c, w):
    m = (t >= w[0]) & (t < w[1]); return c[m].mean()
vals = [em(actual, heft), em(forecast, ca), em(actual, ca)]
labs = ["HEFT\nrealised", "CA plan\nforecast", "CA plan\nrealised"]
cols = [NEUTRAL, AQUA, ORANGE]
b.bar(range(3), vals, color=cols, width=0.62)
for i, v in enumerate(vals):
    b.text(i, v - 9, f"{v:.0f}", ha="center", fontsize=8, color="white")
b.axhline(vals[0] * 1.01, color="#444", lw=0.8, ls=":")
b.text(1.0, vals[0] * 1.01 + 3, "trap threshold\n(HEFT + 1%)", ha="center", fontsize=7, color="#444")
b.set_xticks(range(3), labs, fontsize=7.5); b.set_ylim(100, 215); b.set_ylabel("Mean gCO$_2$/kWh of the work")
b.set_title("(b) The carbon trap", loc="left", fontsize=9)
for ax in (a, b):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("figures/fig1_concept.pdf"); fig.savefig("figures/fig1_concept.png", dpi=300)
print([round(v) for v in vals])
