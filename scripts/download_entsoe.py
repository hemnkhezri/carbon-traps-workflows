"""Download ENTSO-E Transparency Platform data for the ENTSO-E study (DE-LU, ES, NL).

Run on a computer that can reach web-api.tp.entsoe.eu, with your own security token in the
environment variable ENTSOE_TOKEN (the token is never written to disk by this script):

    pip install entsoe-py pandas
    # Windows PowerShell:  $env:ENTSOE_TOKEN = "your-token"
    # Linux / macOS:       export ENTSOE_TOKEN=your-token
    python scripts/download_entsoe.py OUT_DIR

Months up to 2025-10 go to OUT_DIR/dev (development data, including a warm-up month),
months 2025-11 to 2026-10 go to OUT_DIR/confirm (confirmatory data). Keep the two folders
separate: the confirmatory folder is not opened until the study plan is sealed.

Series per zone and month (all as published; timestamps in UTC):
  gen       actual generation per production type (A75, realised)
  load      actual total load (A65, realised)
  load_da   day-ahead total load forecast (A65, process A01)
  ws_da     day-ahead wind and solar generation forecast (A69, process A01)
  gen_da    day-ahead aggregated generation forecast (A71, process A01)
The script can be re-run; finished files are skipped.
"""
import hashlib
import os
import sys
import time

import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError

ZONES = ["DE_LU", "ES", "NL"]
FIRST, LAST = "2024-10", "2026-10"     # inclusive months
CONFIRM_FROM = "2025-11"
TZ = "Europe/Brussels"


def months():
    m = pd.Period(FIRST, "M")
    while m <= pd.Period(LAST, "M"):
        yield m
        m += 1


def flat(df):
    if isinstance(df, pd.Series):
        df = df.to_frame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["|".join(str(x) for x in c if str(x) != "") for c in df.columns]
    df.index = df.index.tz_convert("UTC")
    df.index.name = "time_utc"
    return df


def fetch(client, kind, zone, start, end):
    if kind == "gen":
        return client.query_generation(zone, start=start, end=end)
    if kind == "load":
        return client.query_load(zone, start=start, end=end)
    if kind == "load_da":
        return client.query_load_forecast(zone, start=start, end=end, process_type="A01")
    if kind == "ws_da":
        return client.query_wind_and_solar_forecast(zone, start=start, end=end, process_type="A01")
    if kind == "gen_da":
        return client.query_generation_forecast(zone, start=start, end=end, process_type="A01")
    raise ValueError(kind)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entsoe_data"
    token = os.environ.get("ENTSOE_TOKEN")
    if not token:
        sys.exit("Set the environment variable ENTSOE_TOKEN first (see the docstring).")
    client = EntsoePandasClient(api_key=token, retry_count=5, retry_delay=20, timeout=120)
    kinds = ["gen", "load", "load_da", "ws_da", "gen_da"]
    failed = []
    for m in months():
        part = "confirm" if m >= pd.Period(CONFIRM_FROM, "M") else "dev"
        start = pd.Timestamp(m.start_time, tz=TZ)
        end = pd.Timestamp((m + 1).start_time, tz=TZ)
        for zone in ZONES:
            for kind in kinds:
                d = os.path.join(out, part, zone, kind)
                os.makedirs(d, exist_ok=True)
                f = os.path.join(d, f"{m}.csv")
                if os.path.exists(f):
                    continue
                for attempt in range(3):
                    try:
                        df = flat(fetch(client, kind, zone, start, end))
                        df.to_csv(f + ".part")
                        os.replace(f + ".part", f)
                        print(f"ok   {part:7s} {zone:5s} {kind:7s} {m}  {len(df)} rows", flush=True)
                        break
                    except NoMatchingDataError:
                        pd.DataFrame().to_csv(f)
                        print(f"none {part:7s} {zone:5s} {kind:7s} {m}", flush=True)
                        break
                    except Exception as e:  # network errors, rate limits
                        print(f"retry {zone} {kind} {m}: {type(e).__name__}: {str(e)[:120]}", flush=True)
                        time.sleep(30 * (attempt + 1))
                else:
                    failed.append((zone, kind, str(m)))
                time.sleep(0.5)
    # checksums of every file, so the confirmatory data can be fixed before it is opened
    for part in ("dev", "confirm"):
        lines = []
        for root, _, files in os.walk(os.path.join(out, part)):
            for name in sorted(files):
                p = os.path.join(root, name)
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()
                lines.append(f"{h}  {os.path.relpath(p, out)}")
        with open(os.path.join(out, f"SHA256_{part}.txt"), "w") as fh:
            fh.write("\n".join(sorted(lines, key=lambda s: s[66:])) + "\n")
    if failed:
        print("FAILED (re-run the script to retry):", failed)
    else:
        print("done; now zip the folders dev and confirm separately")


if __name__ == "__main__":
    main()
