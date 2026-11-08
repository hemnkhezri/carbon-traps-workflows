"""Fig. 2: a real carbon trap (GB confirmatory data, seed 11, epigenomics, T = 4 h, f = 3.0, submitted 25 Jul 2026
08:00 BST). Data from figsrc/real_trap_data.py (figures/real_trap_epigenomics.json)."""
import json, sys
import numpy as np
sys.path.insert(0, "figsrc")
import style
from style import AQUA, BLUE, INK, INK2, NEUTRAL, ORANGE, RED, plt
style.apply()
d = json.load(open("figures/real_trap_epigenomics.json"))
D, dur = d["D"], np.array(d["dur"])
xmax = 13.0
fig = plt.figure(figsize=(7.0, 2.45))
# (a) issued vintage vs realised intensity
ax = fig.add_axes([0.06, 0.18, 0.27, 0.66])
n = int(xmax * 2) + 1
th = np.arange(n) * 0.5
iss = np.array(d["iss"])[:n]; act = np.array(d["act"])[:n]
ax.step(th, iss, where="post", color=ORANGE, ls="--", lw=1.5, label="issued forecast")
ax.step(th, act, where="post", color=BLUE, lw=1.6, label="realised")
ax.axvline(D / 60, color=INK, lw=1.0); ax.text(D / 60 - 0.15, ax.get_ylim()[1], "D", ha="right", va="top", fontsize=9)
ax.set_xlim(0, xmax); ax.set_xlabel("Hours after submission", labelpad=1); ax.set_ylabel("Intensity (gCO$_2$/kWh)", labelpad=1)
ax.legend(loc="upper center", fontsize=7.5, handlelength=1.8, bbox_to_anchor=(0.5, 1.0))
ax.set_title("(a) Forecast and realised intensity", loc="left", fontweight="bold")
# (b) busy machines over time
ax = fig.add_axes([0.41, 0.18, 0.30, 0.66])
t = np.arange(0, int(xmax * 60))
def busy(st):
    st = np.array(st); b = np.zeros(len(t))
    for s, w in zip(st, dur):
        b[s:min(s + w, len(t))] += 1
    return b
for key, lab, c, ls in (("heft", "HEFT", NEUTRAL, "-"), ("issued", "CA-LS", RED, "-"), ("issued_gate", "CA-LS + gate", AQUA, "-")):
    ax.plot(t / 60, busy(d[key]), color=c, lw=1.4 if key != "heft" else 1.2, ls=ls, label=lab, alpha=0.95)
ax.axvline(D / 60, color=INK, lw=1.0)
ax.set_xlim(0, xmax); ax.set_ylim(0, 10.6); ax.set_yticks([0, 4, 8])
ax.set_xlabel("Hours after submission", labelpad=1); ax.set_ylabel("Busy machines", labelpad=4)
ax.legend(loc="upper left", fontsize=7.5, ncol=3, handlelength=1.0, columnspacing=0.6, handletextpad=0.4, borderaxespad=0.1)
ax.set_title("(b) Plans built on the forecast", loc="left", fontweight="bold")
# (c) planned vs realised saving
ax = fig.add_axes([0.79, 0.18, 0.20, 0.66])
rows = [("CA-LS", "issued", RED), ("CA-LS\n+ gate", "issued_gate", AQUA), ("CA-LS\noracle", "oracle", BLUE)]
x = np.arange(len(rows)); w = 0.36
for i, (lab, k, c) in enumerate(rows):
    p, r = 100 * d[k + "_planned_saving"], 100 * d[k + "_saving"]
    ax.bar(i - w / 2, p, w, color=c, alpha=0.35, edgecolor=c, lw=0.8, label="planned" if i == 0 else None)
    ax.bar(i + w / 2, r, w, color=c, label="realised" if i == 0 else None)
    ax.text(i + w / 2, r + (2 if r >= 0 else -2), f"{r:.0f}".replace("-", "\u2212"), ha="center", va="bottom" if r >= 0 else "top", fontsize=7.5, color=INK)
ax.axhline(0, color=INK, lw=0.8)
ax.set_xticks(x, [r[0] for r in rows], fontsize=7.5); ax.set_ylabel("Saving vs HEFT (%)", labelpad=1)
ax.set_ylim(-32, 50); ax.grid(axis="x", visible=False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=NEUTRAL, alpha=0.35, ec=NEUTRAL), Patch(fc=NEUTRAL)], labels=["planned", "realised"],
          loc="upper right", fontsize=7.5, handlelength=1.2)
ax.set_title("(c) Outcome", loc="left", fontweight="bold")
fig.savefig("figures/fig_real_trap.png", dpi=400, bbox_inches="tight"); fig.savefig("figures/fig_real_trap.pdf", bbox_inches="tight")
print({k: round(100 * d[k + "_saving"], 1) for k in ("oracle", "issued", "issued_gate")})
