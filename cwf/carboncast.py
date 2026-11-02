"""Load CarbonCast out-of-sample forecasts (Maji et al.; github.com/carbonfirst/CarbonCast)
into the same (forecast rows, actual series) format as the GB archive loader.

Files: data/<R>/<R>_carbon_from_src_forecasts_direct_Jul_Dec_2021.csv, with 181 daily
vintages; each vintage is issued at 00:00 UTC and gives 96 hourly forecasts plus actuals.
Each hourly value is split into two 30-min windows so the rest of the code is unchanged.
A vintage is treated as captured at 00:00 UTC of its day.
"""
import glob
import os

import numpy as np
import pandas as pd

from .data import WIN


def load_carboncast(cc_dir, region):
    f = glob.glob(os.path.join(cc_dir, "data", region, f"{region}_carbon_from_src_forecasts_direct_*.csv"))
    if len(f) != 1:
        raise FileNotFoundError(region)
    a = pd.read_csv(f[0])
    t = (pd.to_datetime(a["UTC time"]) - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
    k = np.arange(len(a))
    cap = t.to_numpy()[(k // 96) * 96]          # vintage start = capture time
    rows = []
    for half in (0, 1800):
        rows.append(pd.DataFrame({"window_utc": t.to_numpy() + half, "capture_utc": cap,
                                  "forecast": a["forecasted_carbon_intensity_direct"].to_numpy()}))
    fc = pd.concat(rows, ignore_index=True).sort_values(["capture_utc", "window_utc"]).reset_index(drop=True)
    act_h = pd.Series(a["actual_carbon_intensity_direct"].to_numpy(), index=t.to_numpy())
    act_h = act_h[~act_h.index.duplicated(keep="last")].sort_index()
    act = pd.concat([act_h, pd.Series(act_h.values, index=act_h.index + 1800)]).sort_index()
    full = np.arange(act.index.min(), act.index.max() + WIN, WIN)
    act = act.reindex(full).interpolate(limit_direction="both")
    return fc, act
