"""Graphical abstract (SUSCOM): plan on a forecast -> carbon trap -> difference-error gate.
Conceptual curves (not data); the numbers quoted are from the abstract / reports."""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import style
from style import BLUE, ORANGE, AQUA, RED, INK, INK2, NEUTRAL
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, Polygon
style.apply()
plt.rcParams.update({"axes.grid": False, "font.size": 8})

W, H = 13/2.54, 5.2/2.54
fig = plt.figure(figsize=(W, H))
t = np.linspace(0, 24, 400)
real = 190 - 32*np.exp(-((t-4)/2.6)**2) + 6*np.sin(t/3.2)
fc   = 196 - 6*np.exp(-((t-4)/3)**2) - 70*np.exp(-((t-15)/2.4)**2) + 4*np.sin(t/3.2)

def dag(ax, x, y, s, col, alpha=1):
    """Small workflow glyph (4-task DAG) centred at (x, y)."""
    pts = [(-1, 0), (0, 1), (0, -1), (1, 0)]
    P = [(x + s*1.25*a, y + s*9*b) for a, b in pts]
    for i, j in [(0, 1), (0, 2), (1, 3), (2, 3)]:
        ax.plot([P[i][0], P[j][0]], [P[i][1], P[j][1]], color=col, lw=1.0, alpha=alpha, zorder=5)
    ax.scatter([q[0] for q in P], [q[1] for q in P], s=13, facecolor="white", edgecolor=col,
               lw=1.2, alpha=alpha, zorder=6)

def panel(x0, title, sub):
    ax = fig.add_axes([x0, .30, .27, .50])
    ax.set_xlim(0, 24); ax.set_ylim(100, 225)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    ax.plot([0, 24], [100, 100], color=INK2, lw=.7)
    fig.text(x0 + .135, .93, title, ha="center", va="center", fontsize=10, weight="bold", color=INK)
    fig.text(x0 + .135, .845, sub, ha="center", va="center", fontsize=7.5, color=INK2, style="italic")
    return ax

# 1. plan on the forecast
a = panel(.035, "Plan on the forecast", "issued by the grid operator")
a.plot(t, fc, color=ORANGE, ls=(0, (4, 2)), lw=1.6)
a.fill_between(t, 100, fc, color=ORANGE, alpha=.06, lw=0)
dag(a, 2.2, 196, 1.0, NEUTRAL)
dag(a, 15.0, 147, 1.0, AQUA)
a.add_patch(FancyArrowPatch((4.2, 212), (13.0, 162), connectionstyle="arc3,rad=-.35",
            arrowstyle="-|>", mutation_scale=9, color=AQUA, lw=1.3))
a.text(15, 106, "forecast valley", ha="center", fontsize=7.5, color=ORANGE)
a.text(2.2, 166, "now", ha="center", fontsize=7, color=NEUTRAL)

# 2. the carbon trap
b = panel(.365, "Carbon trap", "realised intensity after the run")
b.plot(t, fc, color=ORANGE, ls=(0, (4, 2)), lw=1.1, alpha=.35)
b.plot(t, real, color=BLUE, lw=1.8)
b.fill_between(t, 100, real, color=BLUE, alpha=.06, lw=0)
b.scatter([15], [real[np.argmin(abs(t-15))]+3], s=520, color=RED, alpha=.13, lw=0, zorder=3)
dag(b, 15.0, real[np.argmin(abs(t-15))]+3, 1.0, RED)
b.text(4.3, 140, "missed\nclean hours", ha="center", fontsize=7.5, color=BLUE, linespacing=1.0)
b.text(15, 213, "emits more than\ncarbon-agnostic", ha="center", va="center", fontsize=7.5, color=RED, linespacing=1.0)
b.text(15, 106, "valley never came", ha="center", fontsize=7, color=ORANGE, alpha=.8)

# 3. the gate
c = panel(.695, "Difference-error gate", "defer only if gain > calibrated q")
c.plot(t, real, color=BLUE, lw=1.8)
c.fill_between(t, 100, real, color=BLUE, alpha=.06, lw=0)
gx = 9.0
c.plot([gx, gx], [125, 212], color=INK, lw=2.4, solid_capstyle="butt", zorder=4)
c.text(gx+.9, 206, "q", ha="left", fontsize=9, style="italic", color=INK)
y0 = real[np.argmin(abs(t-3.0))]+9
dag(c, 3.0, y0, 1.0, AQUA)
c.add_patch(FancyArrowPatch((4.9, y0+5), (gx-.3, y0+12), connectionstyle="arc3,rad=-.25",
            arrowstyle="-|>", mutation_scale=8, color=NEUTRAL, lw=1.0, ls=(0, (2, 1.5))))
xc, yc = gx-1.4, y0+12
c.plot([xc-.6, xc+.6], [yc-5, yc+5], color=RED, lw=1.6, zorder=7)
c.plot([xc-.6, xc+.6], [yc+5, yc-5], color=RED, lw=1.6, zorder=7)
c.text(16.8, 150, "risky deferral\nblocked", ha="center", fontsize=7.5, color=INK2, va="center", linespacing=1.0)
c.text(3.4, 106, "runs now", ha="center", fontsize=7.5, color=AQUA)

for x in (.318, .648):
    fig.patches.append(FancyArrowPatch((x, .55), (x + .035, .55), transform=fig.transFigure,
                       arrowstyle="simple,head_width=6,head_length=6,tail_width=2.4",
                       color="#c9c8c3", lw=0))

# result strip
fig.text(.035 + .135, .16, "68%", ha="center", fontsize=13, weight="bold", color=ORANGE)
fig.text(.035 + .135, .06, "of the oracle saving kept\nwith issued GB forecasts", ha="center",
         fontsize=7, color=INK2, linespacing=1.0)
fig.text(.365 + .135, .16, "1 in 7", ha="center", fontsize=13, weight="bold", color=RED)
fig.text(.365 + .135, .06, "plans with moderate slack\nfall into a carbon trap", ha="center",
         fontsize=7, color=INK2, linespacing=1.0)
fig.text(.695 + .135, .16, "5–9 pp", ha="center", fontsize=13, weight="bold", color=AQUA)
fig.text(.695 + .135, .06, "fewer carbon traps, with\n84–90% of the saving kept", ha="center",
         fontsize=7, color=INK2, linespacing=1.0)

out = sys.argv[1] if len(sys.argv) > 1 else "figures/graphical_abstract"
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=600); fig.savefig(out + ".tiff", dpi=600,
            pil_kwargs={"compression": "tiff_lzw"})
