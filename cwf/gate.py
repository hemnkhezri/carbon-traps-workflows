"""Difference-based conformal gate.

A deferral from slot a to slot b is worth it only if the realised gain
A(a) - A(b) is positive. The forecast gain is F(a) - F(b). Its error
e = (F(a) - F(b)) - (A(a) - A(b)) is what matters, and it is smaller than the
error of single windows when forecast errors are correlated.

For a submission t0, the gate is calibrated on forecast vintages issued in the
7 days before t0 whose windows have already been realised (actual known
before t0). q[lag_bin, hor_bin] = alpha-quantile of e (one-sided: positive e
means the forecast over-promised). A deferral is allowed iff the forecast
mean-CI gain exceeds q at the deferral's lag and horizon.
"""
import numpy as np

from .data import WIN

LAG_EDGES_H = np.array([0, 3, 6, 12, 24, 48.01])
HOR_EDGES_H = np.array([0, 6, 12, 24, 48.01])
MAX_LAG_W = 96  # windows


def _bin(x, edges):
    return int(np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2))


class DiffGate:
    def __init__(self, q, cap_lag_min):
        self.q = q  # array [lag_bins, hor_bins]
        self.cap_lag_min = cap_lag_min  # minutes between vintage capture and t0

    def threshold(self, s_from, s_to, d):
        lag_h = abs(s_to - s_from) / 60.0
        hor_h = (self.cap_lag_min + max(s_from, s_to) + d / 2) / 60.0
        return self.q[_bin(lag_h, LAG_EDGES_H), _bin(hor_h, HOR_EDGES_H)]

    def threshold_vec(self, s_from, s_to, d):
        s_to = np.asarray(s_to)
        lag_h = np.abs(s_to - s_from) / 60.0
        hor_h = (self.cap_lag_min + np.maximum(s_from, s_to) + d / 2) / 60.0
        li = np.clip(np.searchsorted(LAG_EDGES_H, lag_h, side="right") - 1, 0, len(LAG_EDGES_H) - 2)
        hi = np.clip(np.searchsorted(HOR_EDGES_H, hor_h, side="right") - 1, 0, len(HOR_EDGES_H) - 2)
        return self.q[li, hi]


def calibrate(ci, t0, alpha, days=7, max_vintages=None):
    """Return a DiffGate for submission t0 or None if history is too thin."""
    caps = ci.captures[(ci.captures >= t0 - days * 86400) & (ci.captures <= t0 - 49 * 3600)]
    if max_vintages and len(caps) > max_vintages:
        caps = caps[:: int(np.ceil(len(caps) / max_vintages))]
    errs = [[[] for _ in range(len(HOR_EDGES_H) - 1)] for _ in range(len(LAG_EDGES_H) - 1)]
    act = ci.act
    for c in caps:
        g = ci._by_cap[c]
        g = g[(g.window_utc >= c) & (g.window_utc < t0 - WIN)].drop_duplicates("window_utc", keep="last")
        if len(g) < 8:
            continue
        w = g.window_utc.to_numpy()
        F = g.forecast.to_numpy(float)
        A = act.reindex(w).to_numpy(float)
        ok = ~np.isnan(A)
        w, F, A = w[ok], F[ok], A[ok]
        hor = (w - c) / 3600.0
        n = len(w)
        for L in range(1, min(MAX_LAG_W, n)):
            # pair (i, i+L): defer from earlier i to later i+L, and later to earlier
            dF = F[:-L] - F[L:]
            dA = A[:-L] - A[L:]
            e_fwd = dF - dA            # forecast gain (i -> i+L) minus realised gain
            e_bwd = -dF + dA           # forecast gain (i+L -> i) minus realised gain
            lb = _bin(L * 0.5, LAG_EDGES_H)
            hb = np.clip(np.searchsorted(HOR_EDGES_H, hor[L:], side="right") - 1, 0, len(HOR_EDGES_H) - 2)
            for b in np.unique(hb):
                m = hb == b
                errs[lb][b].append(e_fwd[m])
                errs[lb][b].append(e_bwd[m])
    q = np.full((len(LAG_EDGES_H) - 1, len(HOR_EDGES_H) - 1), np.nan)
    for i in range(q.shape[0]):
        for j in range(q.shape[1]):
            if errs[i][j]:
                e = np.concatenate(errs[i][j])
                if len(e) >= 50:
                    q[i, j] = np.quantile(e, alpha)
    if np.isnan(q).all():
        return None
    # fill empty cells with the most conservative calibrated value
    q = np.where(np.isnan(q), np.nanmax(q), q)
    idx = np.searchsorted(ci.captures, t0 - WIN, side="right") - 1
    cap_lag_min = (t0 - ci.captures[idx]) / 60.0
    return DiffGate(q, cap_lag_min)
