"""Fig. 9: (a) heterogeneous platform: emission saving of CA-LS+SG planned on a flat signal (mapping only), on the
oracle and on model forecasts (exploratory subset, seed 30, 5 submissions per grid, all workflows, T and f);
(b) official schedulers on the homogeneous platform (generality extension): native objective vs emission saving."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "figsrc")
import style
from style import BLUE, INK, INK2, NEUTRAL, ORANGE, plt
style.apply()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
H = pd.read_csv("results/hetero.csv"); FL = pd.read_csv("results/hetero_flat_explore.csv")
sys.path.insert(0, "."); from cwf.workflows import SPECS
if FL.wf.dtype != object: FL["wf"] = FL.wf.map(lambda i: SPECS[int(i)][0])
k = ["region", "f", "T", "t0", "wf"]
h = H[(H.sched == "CA-LS+SG") & (H.seed == 30)]
m = FL.merge(h[h.regime == "oracle"][k + ["saving"]].rename(columns={"saving": "o"}), on=k).merge(
    h[h.regime == "issued"][k + ["saving"]].rename(columns={"saving": "i"}), on=k)
regs = ["CISO", "DE", "ERCO", "PJM"]; X = np.arange(len(regs) + 1); w = 0.26
vals = [[100 * m[m.region == r][c].mean() for r in regs] + [100 * m[c].mean()] for c in ("saving_flat", "o", "i")]
for j, (v, c, lab) in enumerate(zip(vals, (NEUTRAL, BLUE, ORANGE), ("flat signal (mapping only)", "oracle", "model forecast"))):
    a1.bar(X + (j - 1) * w, v, w * 0.92, color=c, label=lab)
a1.axhline(0, color=INK, lw=0.8)
a1.set_xticks(X, regs + ["all"]); a1.set_ylabel("emission saving vs HEFT (%)")
a1.legend(loc="upper left", fontsize=7.5, ncol=3, handlelength=1.2, columnspacing=0.8, bbox_to_anchor=(0, 1.02))
a1.set_ylim(min(0, min(map(min, vals)) - 0.5), max(map(max, vals)) * 1.32)
a1.set_title("(a) Heterogeneous platform, CA-LS", loc="left", fontweight="bold")
print("hetero subset n per regime", len(m), {lab: [round(x, 2) for x in v] for lab, v in zip(("flat", "oracle", "issued"), vals)})
E = pd.read_csv("results/extension.csv")
tools = [("CaWoSched+SG", "CaWoSched"), ("CWM+SG", "CWM")]; X = np.arange(2); w = 0.19
spec = [("native_saving", "oracle", "native objective, oracle", "#9fc3ed", None), ("native_saving", "issued", "native objective, forecast", "#9fc3ed", "////"),
        ("saving", "oracle", "emissions, oracle", BLUE, None), ("saving", "issued", "emissions, forecast", BLUE, "////")]
for j, (col, reg, lab, c, hat) in enumerate(spec):
    v = [100 * E[(E.sched == s) & (E.regime == reg)][col].mean() for s, _ in tools]
    a2.bar(X + (j - 1.5) * w, v, w * 0.92, color=c, hatch=hat, edgecolor="white", lw=0.5, label=lab)
    print(lab, [round(x, 1) for x in v])
a2.axhline(0, color=INK, lw=0.8); a2.set_xticks(X, [t for _, t in tools]); a2.set_ylabel("reduction vs HEFT (%)")
a2.legend(loc="upper right", fontsize=7, handlelength=1.4)
a2.set_title("(b) Official schedulers", loc="left", fontweight="bold")
fig.tight_layout(w_pad=1.5)
fig.savefig("figures/fig_platform.png", dpi=400, bbox_inches="tight"); fig.savefig("figures/fig_platform.pdf", bbox_inches="tight")
