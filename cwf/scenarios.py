"""Forecast-error scenarios from past vintages (RC-CAS)."""
import numpy as np

from .data import WIN


def error_bank(ci, t0, days=7, step=6, nwin=96):
    """Rows: error trajectories A - F of past vintages (captured t0-7d .. t0-49h), indexed by horizon window j."""
    caps = ci.captures[(ci.captures >= t0 - days * 86400) & (ci.captures <= t0 - 49 * 3600)][::step]
    rows = []
    for c in caps:
        g = ci._by_cap[c]
        g = g[(g.window_utc >= c) & (g.window_utc < c + nwin * WIN)].drop_duplicates("window_utc", keep="last")
        j = ((g.window_utc.to_numpy() - c) // WIN).astype(int)
        A = ci.act.reindex(g.window_utc.to_numpy()).to_numpy(float)
        e = np.full(nwin, np.nan); e[j] = A - g.forecast.to_numpy(float)
        if np.isnan(e).mean() > 0.1:
            continue
        idx = np.arange(nwin); ok = ~np.isnan(e)
        rows.append(np.interp(idx, idx[ok], e[ok]))
    return np.array(rows) if rows else None


def scenarios(ci, t0, fc, bank):
    """Scenario intensities (K x len(fc)) for the vintage used at t0 (windows t0 + 30 min * i)."""
    idx = np.searchsorted(ci.captures, t0 - WIN, side="right") - 1
    c0 = ci.captures[idx]
    j = np.clip(((t0 + WIN * np.arange(len(fc)) - c0) // WIN).astype(int), 0, bank.shape[1] - 1)
    return np.maximum(fc[None, :] + bank[:, j], 1.0)
