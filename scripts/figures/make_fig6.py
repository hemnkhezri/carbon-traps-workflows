"""Fig 6: saving versus deadline misses under runtime noise (revision study, GB, seeds 10-11, issued forecasts).
Usage: python make_fig6.py results/rev/A_s10.csv,results/rev/A_s11.csv"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, NEUTRAL = "#0b0b0b", "#52514e", "#e4e3df", "#8a8984"
plt.rcParams.update({
    "font.family": "Liberation Serif", "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 2, "legend.frameon": False, "savefig.dpi": 300,
    "pdf.fonttype": 42})
A = pd.concat([pd.read_csv(p) for p in sys.argv[1].split(",")])
A = A[A.regime == "issued"]
A["day"] = pd.to_datetime(A.t0, unit="s").dt.floor("D")
days = np.sort(A.day.unique()); A["c"] = A.day.map({d: i for i, d in enumerate(days)})
rng = np.random.default_rng(2026); BOOT = [rng.integers(0, len(days), len(days)) for _ in range(1000)]


def mci(sub, col):
    g = sub.groupby("c")[col].agg(["sum", "count"]); s = np.zeros(len(days)); n = np.zeros(len(days))
    s[g.index] = g["sum"].astype(float); n[g.index] = g["count"]
    bs = [s[b].sum() / n[b].sum() for b in BOOT]
    return 100 * np.array([s.sum() / n.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)])


fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.1, 2.7), gridspec_kw=dict(width_ratios=[1.25, 1]))
# (a) trade-off: all f pooled. Filled = static executor, hollow = reactive executor.
V = [("CA-LS+SG", "CA-LS", BLUE, "o"), ("CA-LS+SG+Res75", "CA-LS, reserve 25%", BLUE, "s"),
     ("CA-LS+SG+Res50", "CA-LS, reserve 50%", BLUE, "D"), ("CA-LS+SG+Gate[diff0.9]", "CA-LS + gate", AQUA, "o"),
     ("Shift", "Shift", ORANGE, "o"), ("Shift+Gate", "Shift + gate", ORANGE, "D")]
off = {"CA-LS": (6, 6), "CA-LS, reserve 25%": (8, 5), "CA-LS, reserve 50%": (8, -6), "CA-LS + gate": (8, -7),
       "Shift": (0, 9), "Shift + gate": (8, -3)}
x0 = A[A.sched == "CA-LS+SG"]
for s, lab, col, mk in V:
    x = A[A.sched == s]; y = 100 * x.saving.mean(); m1 = 100 * x.miss_rt.mean(); m2 = 100 * x.miss_rr.mean()
    a1.plot([m1, m2], [y, y], color=col, lw=1, alpha=0.6)
    a1.plot(m1, y, marker=mk, color=col, ms=6, ls="", markeredgecolor="white", markeredgewidth=0.8)
    a1.plot(m2, y, marker=mk, color="white", ms=5.5, ls="", markeredgecolor=col, markeredgewidth=1.4)
    ha = "center" if off[lab][0] == 0 else ("right" if off[lab][0] < 0 else "left")
    a1.annotate(lab, ((m1 + m2) / 2 if ha == "center" else max(m1, m2), y), xytext=off[lab], textcoords="offset points",
                ha=ha, va="center", fontsize=7, color=INK)
hm = 100 * x0.heft_miss_rt.mean()
a1.plot(hm, 0, marker="s", color=NEUTRAL, ms=6, ls="", markeredgecolor="white")
a1.annotate("HEFT", (hm, 0), xytext=(5, 3), textcoords="offset points", fontsize=7, color=INK)
a1.plot([], [], marker="o", color=INK2, ls="", ms=5, label="Static executor")
a1.plot([], [], marker="o", color="white", markeredgecolor=INK2, markeredgewidth=1.4, ls="", ms=5, label="Reactive executor")
for c_, l_ in ((BLUE, "CA-LS variants"), (AQUA, "CA-LS + gate"), (ORANGE, "Shift variants")):
    a1.plot([], [], marker="s", color=c_, ls="", ms=5, label=l_)
a1.set_xlabel("Deadline misses with runtime noise (%)"); a1.set_ylabel("Mean carbon saving vs HEFT (%)")
a1.set_xlim(-2, 54); a1.set_ylim(-0.6, 11)
a1.legend(loc="lower right", ncol=1, fontsize=7.2, handletextpad=0.2, labelspacing=0.3); a1.set_title("(a) Saving and deadline risk, all f", loc="left", fontsize=9.5, color=INK, fontweight="bold")
# (b) misses by deadline factor
F = sorted(A.f.unique()); X = np.arange(len(F))
for s, col, lab, col_, ls, mk, dx in [("CA-LS+SG", BLUE, "CA-LS, static", "miss_rt", "-", "o", -0.12),
                                       ("CA-LS+SG", BLUE, "CA-LS, reactive", "miss_rr", "--", "o", -0.04),
                                       ("CA-LS+SG+Res75", BLUE, "CA-LS, reserve 25%, static", "miss_rt", "-.", "s", 0.04),
                                       ("CA-LS+SG", NEUTRAL, "HEFT, static", "heft_miss_rt", ":", "s", 0.12)]:
    arr = np.array([mci(A[(A.sched == s) & (A.f == f)], col_) for f in F])
    a2.errorbar(X + dx, arr[:, 0], yerr=[arr[:, 0] - arr[:, 1], arr[:, 2] - arr[:, 0]], color=col, ls=ls, marker=mk,
                capsize=2, elinewidth=1, label=lab, markeredgecolor="white" if ls != "--" else col,
                markerfacecolor=col if ls != "--" else "white", markeredgewidth=1)
a2.set_xticks(X, [f"{f:g}" for f in F]); a2.set_xlabel("Deadline factor f"); a2.set_ylabel("Deadline misses (%)")
a2.set_ylim(bottom=0); a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
a2.set_title("(b) Misses by deadline factor", loc="left", fontsize=9.5, color=INK, fontweight="bold")
fig.tight_layout()
for e in ("pdf", "png"):
    fig.savefig(f"figures/fig6_deadline_tradeoff.{e}", bbox_inches="tight")
print("ok")
