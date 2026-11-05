"""Fig. 1: visual overview of the evaluation framework and the proposed components.
Panels (a)-(d) are schematic; panel (e) uses the confirmatory GB results (CA-LS+SG, issued forecasts, f >= 1.5)."""
import sys

import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

sys.path.insert(0, "figsrc")
import style
from style import AQUA, BLUE, INK, INK2, NEUTRAL, ORANGE, RED, plt

style.apply()
fig = plt.figure(figsize=(7.0, 3.3))
SYM = dict(fontfamily="DejaVu Sans", fontweight="bold")
LIGHTBLUE = "#a9c9ef"


def clean(ax):
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def head(x, text):
    fig.text(x, 0.955, text, fontsize=9.5, fontweight="bold", color=INK, va="bottom")


t = np.linspace(0, 24, 400)
real = 190 - 38 * np.exp(-((t - 3.5) / 2.2) ** 2) - 5 * np.exp(-((t - 15) / 3) ** 2)
fc = 197 - 2 * np.exp(-((t - 4) / 3) ** 2) - 75 * np.exp(-((t - 14.5) / 2.0) ** 2)
fc2 = 196 - 50 * np.exp(-((t - 15) / 2.4) ** 2) - 8 * np.exp(-((t - 4) / 2) ** 2)
fc3 = 194 - 30 * np.exp(-((t - 13) / 3) ** 2) - 20 * np.exp(-((t - 4) / 2.5) ** 2)
D, Dp = 22.5, 19.5

# ---------- (a) workflow DAG ----------
head(0.01, "(a) Workflow")
ax = fig.add_axes([0.02, 0.56, 0.16, 0.36]); clean(ax)
pos = {0: (0.5, 0.95), 1: (0.12, 0.65), 2: (0.37, 0.65), 3: (0.63, 0.65), 4: (0.88, 0.65),
       5: (0.25, 0.35), 6: (0.5, 0.35), 7: (0.75, 0.35), 8: (0.5, 0.05)}
for a, b in [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (2, 5), (2, 6), (3, 6), (3, 7), (4, 7), (5, 8), (6, 8), (7, 8)]:
    ax.annotate("", xy=pos[b], xytext=pos[a], arrowprops=dict(arrowstyle="-|>", color=NEUTRAL, lw=0.8,
                shrinkA=5, shrinkB=5, mutation_scale=6))
for x, y in pos.values():
    ax.plot(x, y, "o", ms=7.5, color=BLUE, mec="white", mew=0.8, zorder=3)
ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)

# ---------- (b) forecasts vs realised ----------
fig.text(0.01, 0.425, "(b) Carbon intensity", fontsize=9.5, fontweight="bold", color=INK, va="bottom")
ax = fig.add_axes([0.025, 0.11, 0.155, 0.29])
for f_, a in ((fc3, 0.3), (fc2, 0.5), (fc, 1.0)):
    ax.plot(t, f_, color=ORANGE, lw=1.1, ls="--", alpha=a)
ax.plot(t, real, color=BLUE, lw=1.6)
ax.text(6.5, 160, "realised", color=BLUE, fontsize=8, ha="left", va="center")
ax.text(19.5, 140, "issued\nforecasts", color=ORANGE, fontsize=8, ha="left", va="center")
ax.set_xlim(0, 24); ax.set_ylim(105, 210); ax.set_xticks([0, 12, 24]); ax.set_yticks([])
ax.set_xlabel("hours after submission", fontsize=8, labelpad=1); ax.grid(False); ax.tick_params(length=2, pad=1)

# ---------- (c) planning ----------
head(0.255, "(c) Planning on the forecast")
ax = fig.add_axes([0.26, 0.08, 0.30, 0.84]); clean(ax)
ax.set_xlim(-1.2, 24); ax.set_ylim(-0.75, 6.3)
ax.plot(t, 4.6 + (fc - 115) / 90 * 1.4, color=ORANGE, ls="--", lw=1.3)
ax.text(0, 6.25, "forecast", fontsize=8, color=ORANGE, va="top")
heft = [(0, 0, 3), (0, 3, 2.5), (1, 0, 4), (1, 4, 2), (2, 0, 2.5), (2, 2.5, 3.5)]
for m, s0, d in heft:
    ax.add_patch(Rectangle((s0, 3 - m - 0.38), d, 0.76, fc="none", ec=NEUTRAL, lw=0.8, ls=(0, (2, 1.5))))
ca = [(0, 0, 3), (0, 12.2, 2.5), (1, 11.5, 4), (1, 15.5, 2), (2, 0, 2.5), (2, 13.0, 3.5)]
for m, s0, d in ca:
    ax.add_patch(Rectangle((s0, 3 - m - 0.38), d, 0.76, fc=BLUE, ec="white", lw=0.8))
for y, lab in ((3, "m1"), (2, "m2"), (1, "m3")):
    ax.text(-0.4, y, lab, fontsize=7.5, color=INK2, ha="right", va="center")
ax.text(0, 0.35, "dashed: HEFT plan", fontsize=7.5, color=INK2, va="top")
# allowed deferral (green) and deferral blocked by the gate (red)
ax.add_patch(FancyArrowPatch((3.2, 3.15), (12.0, 3.15), connectionstyle="arc3,rad=-0.3", arrowstyle="-|>",
                             mutation_scale=8, color=AQUA, lw=1.2))
ax.add_patch(FancyArrowPatch((6.2, 0.85), (18.8, 0.85), connectionstyle="arc3,rad=0.25", arrowstyle="-|>",
                             mutation_scale=8, color=RED, lw=1.2, ls="--"))
for (x, y, sym, c) in ((7.6, 3.98, "✓", AQUA), (12.5, -0.18, "✗", RED)):
    ax.text(x, y, "gate", fontsize=7.5, color=ORANGE, ha="center", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.5", fc="#fdeee6", ec=ORANGE, lw=0.9))
    ax.text(x + 1.45, y, sym, fontsize=9, color=c, ha="left", va="center", zorder=5, **SYM)
# slack reserve and deadline
ax.add_patch(Rectangle((Dp, 0.55), D - Dp, 2.9, fc="none", ec=ORANGE, hatch="////", lw=0, alpha=0.55))
ax.plot([D, D], [0.55, 3.45], color=INK, lw=1.2); ax.plot([Dp, Dp], [0.55, 3.45], color=ORANGE, lw=1.2, ls="--")
ax.text(D + 0.1, 3.5, "$D$", fontsize=9, ha="center", va="bottom")
ax.text(Dp, 3.5, "D′", fontsize=9, ha="center", va="bottom", color=ORANGE, style="italic")
ax.text((D + Dp) / 2, 2.0, "reserve", fontsize=7.5, color=ORANGE, ha="center", va="center", rotation=90,
        bbox=dict(fc="white", ec="none", pad=0.6))

# ---------- (d) execution ----------
head(0.60, "(d) Execution")
ax = fig.add_axes([0.60, 0.08, 0.205, 0.84]); clean(ax)
ax.set_xlim(-0.5, 24); ax.set_ylim(-0.75, 6.3)
ax.plot(t, 4.6 + (real - 115) / 90 * 1.4, color=BLUE, lw=1.5)
ax.text(0, 6.25, "realised", fontsize=8, color=BLUE, va="top")
ex = [(0, 0, 3, 0.4), (0, 12.2, 2.5, 0.6), (1, 11.5, 4, 1.5), (1, 17.0, 2, 1.0), (2, 0, 2.5, 0.3), (2, 13.0, 3.5, 0.8)]
for m, s0, d, o in ex:
    ax.add_patch(Rectangle((s0, 3 - m - 0.38), d, 0.76, fc=BLUE, ec="white", lw=0.8))
    ax.add_patch(Rectangle((s0 + d, 3 - m - 0.38), o, 0.76, fc=LIGHTBLUE, ec="white", lw=0.8, hatch="////"))
ax.plot([D, D], [0.55, 3.45], color=INK, lw=1.2); ax.plot([Dp, Dp], [0.55, 3.45], color=ORANGE, lw=1.2, ls="--")
ax.text(D + 0.1, 3.5, "$D$", fontsize=9, ha="center", va="bottom")
ax.text(Dp, 3.5, "D′", fontsize=9, ha="center", va="bottom", color=ORANGE, style="italic")
ax.text(21.0, 2.0, "✓", fontsize=9, color=AQUA, ha="center", va="center", **SYM)
ax.text(21.0, 0.3, "met", fontsize=7.5, color=AQUA, ha="center", va="center")
ax.add_patch(Rectangle((0, -0.43), 1.4, 0.36, fc=LIGHTBLUE, ec="white", hatch="////"))
ax.text(1.8, -0.25, "runtime overrun", fontsize=7.5, color=INK2, va="center")

# ---------- (e) outcomes (data) ----------
head(0.855, "(e) Outcomes")
ax = fig.add_axes([0.875, 0.11, 0.12, 0.76])
d = pd.read_csv("results/confirm.csv")
x = d[(d.sched == "CA-LS+SG") & (d.regime == "issued") & (d.f >= 1.5)].saving * 100
bins = np.arange(-30, 46, 3)
h, e = np.histogram(x.clip(-29.9, 44.9), bins)
cols = [RED if b < -1 else (NEUTRAL if b < 1 else AQUA) for b in e[:-1]]
ax.barh(e[:-1] + 1.5, h, height=2.6, color=cols, ec="white", lw=0.3)
ax.axhline(0, color=INK, lw=0.8)
ax.set_ylim(-30, 45); ax.set_yticks([-20, 0, 20, 40]); ax.set_xticks([]); ax.grid(False)
ax.spines["bottom"].set_visible(False); ax.tick_params(length=2, pad=1)
ax.set_yticklabels(["−20%", "0", "+20%", "+40%"])
ax.text(0.0, 1.0, "saving vs HEFT", transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
tr = 100 * (x < -1).mean()
ax.text(max(h), -15, f"carbon\ntraps\n{tr:.0f}%", color=RED, fontsize=8, ha="right", va="center")
ax.text(max(h), 32, "savings", color=AQUA, fontsize=8, ha="right", va="center")
ax.text(max(h), 6, "= HEFT", color=INK2, fontsize=7.5, ha="right", va="center")

for (x0, y0), (x1, y1) in (((0.185, 0.72), (0.25, 0.56)), ((0.185, 0.27), (0.25, 0.40)),
                           ((0.565, 0.47), (0.598, 0.47)), ((0.81, 0.47), (0.838, 0.47))):
    fig.add_artist(FancyArrowPatch((x0, y0), (x1, y1), transform=fig.transFigure, arrowstyle="-|>",
                                   mutation_scale=11, color=NEUTRAL, lw=1.4))
fig.savefig("figures/fig0_framework.png", dpi=400, bbox_inches="tight")
fig.savefig("figures/fig0_framework.pdf", bbox_inches="tight")
print("ok", round(tr, 1))
