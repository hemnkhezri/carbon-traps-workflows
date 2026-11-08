"""Paper figures from the sealed confirmatory results (exploratory presentation;
numbers match analyse_confirm.py). Usage: python make_figures.py ARCHIVE"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cwf.data import load_national

OUT = "figures"
os.makedirs(OUT, exist_ok=True)
# Reference categorical palette, slots 1-3 (validated all-pairs), plus neutral ink.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, NEUTRAL = "#0b0b0b", "#52514e", "#e4e3df", "#8a8984"
plt.rcParams.update({
    "font.family": "Liberation Serif", "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 2, "lines.markersize": 5,
    "legend.frameon": False, "savefig.dpi": 300, "pdf.fonttype": 42,
})
RNG = np.random.default_rng(2026)
B = 1000

d = pd.read_csv("results/confirm.csv")
t0s = np.sort(d.t0.unique())
d["c"] = d.t0.map({t: i for i, t in enumerate(t0s)})
BOOT = [RNG.integers(0, len(t0s), len(t0s)) for _ in range(B)]


def mean_ci(sub, col):
    g = sub.groupby("c")[col].agg(["sum", "count"])
    s = np.zeros(len(t0s)); n = np.zeros(len(t0s))
    s[g.index] = g["sum"]; n[g.index] = g["count"]
    est = s.sum() / n.sum()
    with np.errstate(invalid="ignore"):
        bs = np.array([s[b].sum() / n[b].sum() for b in BOOT])
    bs = bs[np.isfinite(bs)]
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def series(sched, regime, col, fs):
    out = [mean_ci(d[(d.sched == sched) & (d.regime == regime) & (d.f == f)], col) for f in fs]
    return np.array(out) * 100


def plot_ci(ax, x, arr, color, label, ls="-", marker="o", dx=0.0):
    est, lo, hi = arr[:, 0], arr[:, 1], arr[:, 2]
    ax.errorbar(np.array(x) + dx, est, yerr=[est - lo, hi - est], color=color, ls=ls, marker=marker,
                capsize=2, elinewidth=1, label=label, markeredgecolor="white", markeredgewidth=0.8)


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight")
    plt.close(fig)


F = sorted(d.f.unique())
X = np.arange(len(F))
XL = [f"{f:g}" for f in F]

# Fig 4: mean saving vs slack, three schedulers, three information regimes
fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.4), sharey=True)
for ax, (s, title) in zip(axes, [("CA-LS+SG", "(a) CA-LS + safeguard"),
                                 ("CaWoSched+SG", "(b) CaWoSched + safeguard"),
                                 ("Shift", "(c) Whole-workflow shift")]):
    plot_ci(ax, X, series(s, "oracle", "saving", F), NEUTRAL, "Oracle CI", ls="--", marker="s", dx=-0.12)
    if (d[(d.sched == s)].regime == "synthetic").any():
        plot_ci(ax, X, series(s, "synthetic", "saving", F), ORANGE, "Synthetic noise", marker="^", dx=0.0)
    plot_ci(ax, X, series(s, "issued", "saving", F), BLUE, "Issued forecast", dx=0.12)
    ax.set_title(title, loc="left", color=INK, fontweight="bold")
    ax.set_xticks(X, XL)
fig.supxlabel("Deadline factor f (D = f × HEFT makespan)", fontsize=8, y=-0.04)
axes[0].set_ylabel("Mean carbon saving vs HEFT (%)")
axes[0].set_ylim(bottom=0)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.08))
save(fig, "fig4_saving_vs_slack")

# Fig 5: carbon-trap rate, CA-LS + safeguard
fig, ax = plt.subplots(figsize=(3.5, 2.5))
plot_ci(ax, X, series("CA-LS+SG", "synthetic", "trap1", F), ORANGE, "Synthetic noise, no gate", marker="^", dx=-0.1)
plot_ci(ax, X, series("CA-LS+SG", "issued", "trap1", F), BLUE, "Issued forecast, no gate")
plot_ci(ax, X, series("CA-LS+SG+Gate", "issued", "trap1", F), AQUA, "Issued forecast, with gate", marker="D", dx=0.1)
ax.axhline(2, color=INK2, lw=0.8, ls=":")
ax.text(len(F) - 1 + 0.25, 2.4, "H2 threshold 2%", ha="right", va="bottom", color=INK2, fontsize=7)
ax.set_xticks(X, XL); ax.set_xlabel("Deadline factor f")
ax.set_ylabel("Runs > 1% above HEFT (%)")
ax.set_ylim(bottom=0)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=1)
save(fig, "fig5_trap_rate")

# Fig 6: deadline misses with +/-20% runtime noise (issued forecasts)
fig, ax = plt.subplots(figsize=(3.5, 2.5))
heft = np.array([mean_ci(d[(d.sched == "CA-LS+SG") & (d.regime == "issued") & (d.f == f)], "heft_miss_rt") for f in F]) * 100
plot_ci(ax, X, heft, NEUTRAL, "HEFT", ls="--", marker="s", dx=-0.15)
plot_ci(ax, X, series("CaWoSched+SG", "issued", "miss_rt", F), ORANGE, "CaWoSched + SG", marker="^", dx=-0.05)
plot_ci(ax, X, series("CA-LS+SG", "issued", "miss_rt", F), BLUE, "CA-LS + SG", dx=0.05)
plot_ci(ax, X, series("CA-LS+SG+Gate", "issued", "miss_rt", F), AQUA, "CA-LS + SG + gate", marker="D", dx=0.15)
ax.set_xticks(X, XL); ax.set_xlabel("Deadline factor f")
ax.set_ylabel("Deadline misses (%)")
ax.set_ylim(bottom=0)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=2)
save(fig, "fig6_deadline_misses")

# Fig 3: forecast error by horizon, development vs confirmatory period
archive = sys.argv[1]
periods = {"Mar 2023 – Feb 2024 (development)": ["2023-%02d" % m for m in range(3, 13)] + ["2024-01", "2024-02"],
           "Jul – Oct 2026 (confirmatory)": ["2026-07", "2026-08", "2026-09", "2026-10"]}
edges = np.array([0, 1, 3, 6, 12, 18, 24, 30, 36, 42, 48.01])
mid = (edges[:-1] + edges[1:]) / 2
fig, ax = plt.subplots(figsize=(3.5, 2.4))
rows = []
for (lab, months), col, mk in zip(periods.items(), [NEUTRAL, BLUE], ["s", "o"]):
    fc, act = load_national(archive, months)
    h = (fc.window_utc - fc.capture_utc) / 3600.0
    e = fc[(h >= 0) & (h < 48.01)].copy()
    e["h"] = h[(h >= 0) & (h < 48.01)]
    e["a"] = e.window_utc.map(act)
    e = e.dropna(subset=["a"])
    e["ae"] = (e.forecast - e.a).abs()
    e["bin"] = pd.cut(e.h, edges, right=False, labels=False)
    m = e.groupby("bin").ae.mean()
    ax.plot(mid[m.index.astype(int)], m.values, color=col, marker=mk, ls="--" if col == NEUTRAL else "-",
            label=lab, markeredgecolor="white", markeredgewidth=0.8)
    for b_, v in m.items():
        rows.append(dict(period=lab, horizon_mid_h=mid[int(b_)], mae=v))
    rows.append(dict(period=lab, horizon_mid_h=-1, mae=float(act.mean())))
ax.set_xlabel("Forecast horizon (h)")
ax.set_ylabel("MAE (gCO$_2$/kWh)")
ax.set_xticks([0, 12, 24, 36, 48])
ax.set_ylim(bottom=0)
ax.legend(loc="lower right")
save(fig, "fig3_forecast_error")
pd.DataFrame(rows).to_csv(f"{OUT}/fig3_data.csv", index=False)
print("done")
