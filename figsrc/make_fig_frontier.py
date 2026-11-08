"""Fig. 6: saving-risk frontier. (a) revision study, GB issued forecasts 2026, seeds 10-11, all f;
(b) development pilots: gate vs risk-controlled planners (pilot 2, seeds 3-4, f >= 1.5 for saving)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "figsrc")
import style
from style import AQUA, BLUE, INK, INK2, NEUTRAL, ORANGE, RED, YELLOW, plt
style.apply()
A = pd.concat([pd.read_csv(f"results/rev/{p}") for p in ("A_s10.csv", "A_s11.csv", "RH_s10s11.csv")]).drop_duplicates(
    ["seed", "wf", "T", "f", "t0", "sched", "regime"], keep="last")
R2 = pd.read_csv("results/rev/R2_s10s11.csv")
A = pd.concat([A, R2]); A = A[A.regime == "issued"]
pt = lambda s: (100 * A[A.sched == s].trap1.mean(), 100 * A[A.sched == s].saving.mean())
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw=dict(width_ratios=[1.35, 1]))
gs = ["diff0.5", "diff0.8", "diff0.9", "diff0.95"]
g = np.array([pt(f"CA-LS+SG+Gate[{x}]") for x in gs])
a1.plot(g[:, 0], g[:, 1], "-o", color=BLUE, ms=5, mec="white", zorder=4, label="difference gate (α sweep)")
for (x, y), lab in zip(g, ["0.5", "0.8", "0.9", "0.95"]):
    a1.annotate(f"α={lab}", (x, y), xytext=(4, -9 if lab != "0.5" else 5), textcoords="offset points", fontsize=7.5, color=BLUE)
others = [("CA-LS+SG", "no gate", NEUTRAL, "s"), ("CA-LS+SG+Gate[const]", "constant threshold", ORANGE, "D"),
          ("CA-LS+SG+Gate[level]", "level interval (Li-style)", ORANGE, "^"), ("CA-LS+SG+Gate[lagcap6]", "6-h deferral cap", ORANGE, "v"),
          ("CA-LS+SG[Q0.9]", "plan on upper quantile", RED, "P"), ("RH-CA-LS+SG", "re-planning every 2 h", RED, "X"),
          ("Shift", "Shift", YELLOW, "o"), ("Shift+Gate", "Shift + gate", AQUA, "o")]
for s, lab, c, m in others:
    x, y = pt(s); a1.plot(x, y, m, color=c, ms=6.5, mec="white", mew=0.7, ls="", label=lab, zorder=3)
a1.set_xlabel("Carbon traps (% of runs)"); a1.set_ylabel("Mean saving vs HEFT (%)")
a1.set_xlim(-0.5, 13); a1.set_ylim(3.5, 10.5)
a1.legend(loc="lower right", fontsize=7, ncol=1, handletextpad=0.3, labelspacing=0.25, borderaxespad=0.2)
a1.set_title("(a) Strategies, GB issued forecasts", loc="left", fontweight="bold")
a1.annotate("better", xy=(0.4, 10.1), xytext=(3.2, 8.8), fontsize=7.5, color=INK2,
            arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8, mutation_scale=7), ha="center")
# (b) pilot 2
d = pd.read_csv("results/pilot_rc2.csv")
def q(s):
    x = d[d.sched == s]; return 100 * x.trap1.mean(), 100 * x[x.f >= 1.5].saving.mean()
gg = np.array([q(f"CA-LS+SG+Gate[{a}]") for a in ("0.8", "0.9", "0.95")])
a2.plot(gg[:, 0], gg[:, 1], "-o", color=BLUE, ms=5, mec="white", label="difference gate", zorder=4)
for nm, lab, c, m in (("RC-CAS", "risk-controlled selection", RED, "s"), ("RCv2", "risk-controlled local search", ORANGE, "D")):
    p = np.array([q(f"{nm}[{a}]") for a in ("0.05", "0.1", "0.2")])
    a2.plot(p[:, 0], p[:, 1], "--" + m, color=c, ms=5, mec="white", lw=1.2, label=lab, zorder=3)
x, y = q("CA-LS+SG"); a2.plot(x, y, "s", color=NEUTRAL, ms=6, mec="white", label="no gate")
a2.set_xlabel("Carbon traps (% of runs)"); a2.set_ylabel("Mean saving, f ≥ 1.5 (%)")
a2.legend(loc="lower right", fontsize=7, handletextpad=0.3, labelspacing=0.25)
a2.set_title("(b) Risk-controlled planners (dev.)", loc="left", fontweight="bold")
a2.set_xlim(-0.5, 14); 
fig.tight_layout(w_pad=1.5)
fig.savefig("figures/fig_frontier.png", dpi=400, bbox_inches="tight"); fig.savefig("figures/fig_frontier.pdf", bbox_inches="tight")
print("a:", {s: tuple(round(v, 2) for v in pt(s)) for s, *_ in others}); print("gate", g.round(2).tolist())
