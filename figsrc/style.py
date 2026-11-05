"""Shared figure style: Times-compatible font (matches the manuscript), validated palette."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
BLUE, ORANGE, AQUA, YELLOW, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"
INK, INK2, GRID, NEUTRAL, LIGHT = "#0b0b0b", "#52514e", "#e4e3df", "#8a8984", "#f3f3f1"
def apply():
    plt.rcParams.update({
        "font.family": "Liberation Serif", "mathtext.fontset": "stix", "font.size": 9,
        "axes.titlesize": 9.5, "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
        "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 1.8,
        "legend.frameon": False, "savefig.dpi": 400, "pdf.fonttype": 42})
