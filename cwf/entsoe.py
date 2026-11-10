"""ENTSO-E Transparency Platform data -> realised carbon intensity and as-issued forecast vintages.

Realised intensity: production-based average over ENTSO-E production types (Actual Aggregated,
A75), weighted by IPCC AR5 (2014) life-cycle median emission factors. All series are put on
30-min windows (mean of the 15-min or hourly values in each window).

Forecasts: ENTSO-E publishes no intensity forecast. A vintage for delivery day D is built only
from what was public at 18:00 Europe/Brussels on D-1: the day-ahead load forecast (A65/A01) and
the day-ahead wind and solar forecast (A69/A01) for day D, converted to intensity with a model
fitted on realised data that ended before that time (see fit_model). The capture time of the
vintage is 18:00 on D-1, and it covers day D-1 (the previous day-ahead values) and day D.
"""
import glob
import os

import numpy as np
import pandas as pd

from .data import WIN

TZ = "Europe/Brussels"

# IPCC AR5 WGIII Annex III (Schlomer et al. 2014) life-cycle medians, g CO2-eq/kWh.
# Lignite uses the coal value; oil, waste and "other" have no IPCC median and use the
# approximations marked below.
EF = {
    "Biomass": 230, "Fossil Brown coal/Lignite": 820, "Fossil Coal-derived gas": 490,
    "Fossil Gas": 490, "Fossil Hard coal": 820, "Fossil Oil": 650, "Fossil Oil shale": 650,
    "Fossil Peat": 820, "Geothermal": 38, "Hydro Pumped Storage": 24,
    "Hydro Run-of-river and poundage": 24, "Hydro Run-of-river and pondage": 24,
    "Hydro Water Reservoir": 24, "Marine": 24, "Nuclear": 12,
    "Energy storage": 24, "Other": 490, "Waste": 230,                          # approx.
    "Other renewable": 24, "Solar": 48,
    "Wind Offshore": 12, "Wind Onshore": 11,
}


def _read(root, zone, kind):
    fs = sorted(glob.glob(os.path.join(root, "*", zone, kind, "*.csv")))
    parts = []
    for f in fs:
        if os.path.getsize(f) < 5:
            continue
        d = pd.read_csv(f, index_col=0)
        if len(d) == 0:
            continue
        d.index = pd.to_datetime(d.index, utc=True)
        parts.append(d)
    if not parts:
        return pd.DataFrame()
    d = pd.concat(parts)
    d = d[~d.index.duplicated(keep="last")].sort_index()
    return d


def _to30(d):
    """Mean over 30-min windows; index = window start in unix seconds."""
    r = d.resample("30min").mean()
    r.index = (r.index - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")
    return r


def realised(root, zone):
    g = _read(root, zone, "gen")
    cols = [c for c in g.columns if c.endswith("|Actual Aggregated") or "|" not in c]
    g = g[cols].copy()
    g.columns = [c.split("|")[0] for c in cols]
    unknown = sorted(set(g.columns) - set(EF))
    if unknown:
        raise KeyError(f"no emission factor for {unknown}")
    g = _to30(g.clip(lower=0))
    tot = g.sum(axis=1, min_count=1)
    em = sum(g[c].fillna(0) * EF[c] for c in g.columns)
    ci = em / tot
    ci[tot <= 0] = np.nan
    return ci.rename("ci"), g


def drivers(root, zone):
    """Realised and day-ahead load, wind and solar on 30-min windows."""
    L = _to30(_read(root, zone, "load")).iloc[:, 0].rename("load")
    Lf = _to30(_read(root, zone, "load_da")).iloc[:, 0].rename("load_da")
    ws = _to30(_read(root, zone, "ws_da"))
    wsf = ws.sum(axis=1, min_count=1).rename("vre_da")
    _, g = realised(root, zone)
    vre_cols = [c for c in g.columns if c.startswith("Wind") or c == "Solar"]
    vre = g[vre_cols].sum(axis=1, min_count=1).rename("vre")
    return pd.concat([L, Lf, vre, wsf], axis=1)


def local_day_start(t_unix):
    t = pd.to_datetime(t_unix, unit="s", utc=True).tz_convert(TZ)
    return t.normalize()


TRAIN_DAYS = 28      # rolling training window for the conversion model
ISSUE_HOUR = 18      # local hour on D-1 at which the day-ahead inputs for D are public
DATA_LAG_S = 3600    # realised data are used for training only if older than 1 h at issue time


def _design(L, V, hod):
    """Conversion model M3 (chosen on development data): CI ~ residual-load share + hour-of-day."""
    return np.c_[(L - V) / L, np.eye(24)[hod]]


def build_vintages(root, zone):
    """Return (fc, act): fc rows (window_utc, capture_utc, forecast) as for the GB loader."""
    ci, _ = realised(root, zone)
    d = drivers(root, zone)
    df = pd.concat([ci, d], axis=1)
    loc = pd.to_datetime(df.index, unit="s", utc=True).tz_convert(TZ)
    df["day"] = loc.normalize()
    df["hod"] = loc.hour
    days = sorted(df["day"].unique())
    per_day = {}
    for D in days[TRAIN_DAYS + 1:]:
        cap = (D - pd.DateOffset(days=1)).replace(hour=ISSUE_HOUR)   # wall-clock day (DST-safe)
        capu = int((cap.tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s"))
        tr = df[(df.index < capu - DATA_LAG_S) & (df.index >= capu - TRAIN_DAYS * 86400)]
        tr = tr.dropna(subset=["ci", "load", "vre"])
        te = df[df["day"] == D]
        if len(tr) < 0.8 * TRAIN_DAYS * 48 or len(te) == 0 or te[["load_da", "vre_da"]].isna().any().any():
            continue
        coef, *_ = np.linalg.lstsq(_design(tr.load.values, tr.vre.values, tr.hod.values), tr.ci.values, rcond=None)
        f = _design(te.load_da.values, te.vre_da.values, te.hod.values) @ coef
        per_day[D] = (capu, pd.Series(f, index=te.index))
    rows = []
    ks = sorted(per_day)
    for i, D in enumerate(ks):
        capu, f = per_day[D]
        parts = [f]
        prev = D - pd.DateOffset(days=1)
        if prev in per_day:                 # the previous day-ahead values are still the latest for day D-1
            parts.insert(0, per_day[prev][1])
        s = pd.concat(parts)
        rows.append(pd.DataFrame({"window_utc": s.index.to_numpy(), "capture_utc": capu,
                                  "forecast": s.to_numpy(float)}))
    fc = pd.concat(rows, ignore_index=True).sort_values(["capture_utc", "window_utc"]).reset_index(drop=True)
    act = ci.dropna()
    full = np.arange(act.index.min(), act.index.max() + WIN, WIN)
    act = act.reindex(full).interpolate(limit=4)    # gaps longer than 2 h stay missing
    return fc, act
