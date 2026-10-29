"""GB national carbon-intensity forecasts (issued vintages) and actuals.

Source: nmpowell/carbon-intensity-forecast-tracking (NESO API snapshots, MIT).
Each row: window_utc (start of 30-min window), capture_utc (when the forecast
was scraped), forecast, actual.
"""
import glob
import os
import sqlite3

import numpy as np
import pandas as pd

WIN = 1800  # seconds per CI window


def load_national(archive_dir, months):
    """months: list like ['2023-03', ...]. Returns forecast rows and actual series."""
    frames = []
    for m in months:
        y = m[:4]
        f = os.path.join(archive_dir, "data", "db", y, f"national_{m}.sqlite")
        if not os.path.exists(f):
            raise FileNotFoundError(f)
        with sqlite3.connect(f) as c:
            frames.append(pd.read_sql("select window_utc, capture_utc, forecast, actual from national_intensity", c))
    d = pd.concat(frames, ignore_index=True)
    act = (d.dropna(subset=["actual"]).sort_values("capture_utc")
             .groupby("window_utc")["actual"].last())
    full = np.arange(act.index.min(), act.index.max() + WIN, WIN)
    act = act.reindex(full).interpolate(limit_direction="both")
    fc = d.dropna(subset=["forecast"])[["window_utc", "capture_utc", "forecast"]]
    fc = fc.sort_values(["capture_utc", "window_utc"]).reset_index(drop=True)
    return fc, act


class CIData:
    def __init__(self, fc, act):
        self.act = act
        self.fc = fc
        self.captures = np.sort(fc.capture_utc.unique())
        self._by_cap = {c: g for c, g in fc.groupby("capture_utc")}
        # errors of forecasts issued 12-36 h ahead, for the gate threshold
        h = (fc.window_utc - fc.capture_utc) / 3600.0
        e = fc[(h >= 12) & (h < 36)].copy()
        e["err"] = (e.forecast - e.window_utc.map(act)).abs()
        self._err = e.dropna(subset=["err"]).groupby("window_utc")["err"].mean()

    def vintage(self, t0, n_windows):
        """Forecast vector for windows t0, t0+WIN, ... from the latest capture
        strictly before t0 - WIN (conservative: issued and observable before t0)."""
        idx = np.searchsorted(self.captures, t0 - WIN, side="right") - 1
        if idx < 0:
            return None
        cap = self.captures[idx]
        g = self._by_cap[cap].drop_duplicates("window_utc", keep="last").set_index("window_utc")["forecast"]
        wins = t0 + WIN * np.arange(n_windows)
        v = g.reindex(wins)
        if v.isna().all():
            return None
        if v.notna().sum() < 0.9 * n_windows:
            return None
        return v.ffill().bfill().to_numpy(float)

    def actual(self, t0, n_windows):
        wins = t0 + WIN * np.arange(n_windows)
        v = self.act.reindex(wins)
        if v.isna().any():
            return None
        return v.to_numpy(float)

    def tau(self, t0, days=7):
        """Mean abs error of 12-36 h-ahead forecasts for windows that ended before t0."""
        lo, hi = t0 - days * 86400, t0 - WIN
        s = self._err[(self._err.index >= lo) & (self._err.index < hi)]
        return float(s.mean()) if len(s) >= 48 else None  # None -> submission skipped (no history)
