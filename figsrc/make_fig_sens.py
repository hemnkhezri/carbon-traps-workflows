"""Fig. S3: sensitivity to runtime noise and cluster size (seed 10, GB issued forecasts; reports/sensitivity.txt,
Supplementary Tables S5 and S6)."""
import sys
import numpy as np
sys.path.insert(0, "figsrc")
import style
from style import AQUA, BLUE, INK2, NEUTRAL, ORANGE, RED, YELLOW, plt
style.apply()
lab = ["0.05", "0.1", "0.2", "0.4", "empirical"]; x = np.arange(5)
miss = {"HEFT": [0.0, 0.0, 0.3, 3.0, 25.7], "CA-LS": [28.0, 35.0, 43.7, 52.7, 70.0], "CA-LS + gate": [13.3, 17.6, 23.3, 30.6, 50.5],
        "CA-LS + 25% reserve": [0.0, 0.1, 2.8, 13.8, 42.0], "Shift": [30.3, 33.9, 34.9, 39.5, 58.2]}
col = {"HEFT": NEUTRAL, "CA-LS": RED, "CA-LS + gate": AQUA, "CA-LS + 25% reserve": BLUE, "Shift": YELLOW}
mk = {"HEFT": "o", "CA-LS": "s", "CA-LS + gate": "D", "CA-LS + 25% reserve": "^", "Shift": "v"}
fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.0, 2.55), gridspec_kw={"width_ratios": [1.35, 1, 1]})
for k, v in miss.items():
    a.plot(x, v, "-" + mk[k], color=col[k], ms=4.5, mec="white", lw=1.4, label=k)
a.axvspan(3.5, 4.5, color="#f3f3f1", zorder=0)
a.set_xticks(x, lab); a.set_xlabel("Runtime noise (log-normal spread)", labelpad=1); a.set_ylabel("Deadline misses (%)", labelpad=1)
a.set_ylim(-2, 75); a.legend(loc="upper left", fontsize=7, handlelength=1.4, labelspacing=0.25)
a.set_title("(a) Misses vs runtime noise", loc="left", fontweight="bold")
P = [8, 32, 64]; xp = np.arange(3)
b.plot(xp, [5.5, 7.4, 9.7], "-s", color=RED, ms=4.5, mec="white", lw=1.4, label="CA-LS")
b.plot(xp, [1.5, 2.2, 2.5], "-D", color=AQUA, ms=4.5, mec="white", lw=1.4, label="CA-LS + gate")
b.set_xticks(xp, P); b.set_xlabel("Machines", labelpad=1); b.set_ylabel("Carbon traps (%)", labelpad=1); b.set_ylim(0, 12)
b.legend(loc="upper left", fontsize=7, handlelength=1.4)
b.set_title("(b) Traps vs cluster size", loc="left", fontweight="bold")
c.plot(xp, [43.7, 52.1, 58.1], "-s", color=RED, ms=4.5, mec="white", lw=1.4, label="CA-LS")
c.plot(xp, [2.8, 16.2, 27.8], "-^", color=BLUE, ms=4.5, mec="white", lw=1.4, label="+ 25% reserve")
c.plot(xp, [0.3, 3.5, 8.8], "-o", color=NEUTRAL, ms=4.5, mec="white", lw=1.4, label="HEFT")
c.set_xticks(xp, P); c.set_xlabel("Machines", labelpad=1); c.set_ylabel("Deadline misses (%)", labelpad=1); c.set_ylim(-2, 75)
c.legend(loc="upper left", fontsize=7, handlelength=1.4)
c.set_title("(c) Misses vs cluster size", loc="left", fontweight="bold")
fig.tight_layout(w_pad=1.2)
fig.savefig("figures/figS3_sensitivity.png", dpi=400, bbox_inches="tight"); fig.savefig("figures/figS3_sensitivity.pdf", bbox_inches="tight")
