"""Alternative deferral gates for the revision study (EXT3_PREREG.md). Each object has
threshold_vec(s_from, s_to, d) in CI units (mean-CI gain a deferral must exceed), like cwf.gate.DiffGate.

- DiffGate at several alpha values (same calibration as cwf/gate.py).
- ConstGate: one alpha-quantile of all difference errors, no binning.
- LevelGate: interval rule in the style of Li et al.: defer a -> b only if the upper bound of the
  actual CI at b lies below the lower bound at a, i.e. F(a) - F(b) > qU(h_b) + qL(h_a), with qU, qL the
  alpha-quantiles of (A - F) and (F - A) per horizon bin.
- LagCap: no gate on the gain, but deferrals longer than `cap_h` hours are forbidden.
Calibration window and data exactly as in cwf/gate.py (vintages captured 7 d to 49 h before t0,
windows realised before t0)."""
import numpy as np

from .data import WIN
from .gate import HOR_EDGES_H, LAG_EDGES_H, MAX_LAG_W, DiffGate, _bin

NL, NH = len(LAG_EDGES_H) - 1, len(HOR_EDGES_H) - 1


def _hbin(h):
    return np.clip(np.searchsorted(HOR_EDGES_H, h, side="right") - 1, 0, NH - 1)


class ConstGate:
    def __init__(self, q):
        self.q = q

    def threshold_vec(self, s_from, s_to, d):
        return np.full(np.shape(s_to), self.q, float)


class LevelGate:
    def __init__(self, qU, qL, cap_lag_min):
        self.qU, self.qL, self.cap = qU, qL, cap_lag_min

    def threshold_vec(self, s_from, s_to, d):
        s_to = np.asarray(s_to)
        hb_to = _hbin((self.cap + s_to + d / 2) / 60.0)
        hb_from = _hbin(np.full(s_to.shape, (self.cap + s_from + d / 2) / 60.0))
        return self.qU[hb_to] + self.qL[hb_from]


class LagCap:
    def __init__(self, cap_h):
        self.cap_h = cap_h

    def threshold_vec(self, s_from, s_to, d):
        lag = np.abs(np.asarray(s_to) - s_from) / 60.0
        return np.where(lag <= self.cap_h, 0.0, np.inf)


def calibrate_all(ci, t0, alphas=(0.5, 0.7, 0.8, 0.9, 0.95), alpha_alt=0.9, days=7):
    caps = ci.captures[(ci.captures >= t0 - days * 86400) & (ci.captures <= t0 - 49 * 3600)]
    errs = [[[] for _ in range(NH)] for _ in range(NL)]
    lev = [[] for _ in range(NH)]
    for c in caps:
        g = ci._by_cap[c]
        g = g[(g.window_utc >= c) & (g.window_utc < t0 - WIN)].drop_duplicates("window_utc", keep="last")
        if len(g) < 8:
            continue
        w = g.window_utc.to_numpy(); F = g.forecast.to_numpy(float); A = ci.act.reindex(w).to_numpy(float)
        ok = ~np.isnan(A); w, F, A = w[ok], F[ok], A[ok]
        hor = (w - c) / 3600.0
        hb_all = _hbin(hor)
        for b in range(NH):
            lev[b].append((F - A)[hb_all == b])
        for L in range(1, min(MAX_LAG_W, len(w))):
            dF = F[:-L] - F[L:]; dA = A[:-L] - A[L:]
            lb = _bin(L * 0.5, LAG_EDGES_H); hb = _hbin(hor[L:])
            for b in np.unique(hb):
                m = hb == b
                errs[lb][b].append(dF[m] - dA[m]); errs[lb][b].append(-dF[m] + dA[m])
    cat = [[np.concatenate(errs[i][j]) if errs[i][j] else np.zeros(0) for j in range(NH)] for i in range(NL)]
    if all(len(cat[i][j]) < 50 for i in range(NL) for j in range(NH)):
        return None
    idx = np.searchsorted(ci.captures, t0 - WIN, side="right") - 1
    cap_lag_min = (t0 - ci.captures[idx]) / 60.0
    out = {}
    for a in alphas:
        q = np.full((NL, NH), np.nan)
        for i in range(NL):
            for j in range(NH):
                if len(cat[i][j]) >= 50:
                    q[i, j] = np.quantile(cat[i][j], a)
        out[f"diff{a}"] = DiffGate(np.where(np.isnan(q), np.nanmax(q), q), cap_lag_min)
    allerr = np.concatenate([x for row in cat for x in row])
    out["const"] = ConstGate(float(np.quantile(allerr, alpha_alt)))
    L = [np.concatenate(x) if x else np.zeros(0) for x in lev]
    qU = np.array([np.quantile(-x, alpha_alt) if len(x) >= 50 else np.nan for x in L])
    qL = np.array([np.quantile(x, alpha_alt) if len(x) >= 50 else np.nan for x in L])
    out["level"] = LevelGate(np.where(np.isnan(qU), np.nanmax(qU), qU), np.where(np.isnan(qL), np.nanmax(qL), qL), cap_lag_min)
    out["lagcap6"] = LagCap(6.0)
    return out
