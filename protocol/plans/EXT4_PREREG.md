# Pre-registration: ENTSO-E study (operator day-ahead inputs, DE-LU and ES, twelve months)

**Sealed:** the git commit that adds this file. The confirmatory ENTSO-E files (months 2025-11 to 2026-10)
were checksummed on receipt and committed unopened in 5cd777a (`data/entsoe/SHA256_confirm.txt`);
they are opened only after this commit. Later changes go to `protocol/deviations/EXT4_DEVIATIONS.md`.

## 1. Purpose

The main study used operator-issued vintages for one grid (GB) in one season. This study adds a second
source of genuinely issued information, over a full year, on two further grids:

1. Do the main findings (forecast loss, traps, the gate, deadline misses under runtime noise) hold?
2. Does the forecast-error-to-variability ratio kappa, an exploratory finding of the main paper, predict
   which grid keeps more of its saving? This is tested here as a sealed prediction.

## 2. Data

- **Source:** ENTSO-E Transparency Platform, downloaded with `scripts/download_entsoe.py` on
  9 Nov 2026: actual generation per production type (A75), actual load (A65/A16), day-ahead load
  forecast (A65/A01), day-ahead wind and solar forecast (A69/A01).
- **Zones:** DE-LU (wind and solar, high intraday swing) and ES (solar, nuclear, hydro).
  NL was downloaded but is excluded before any confirmatory result: in the development year its reported
  actual solar generation averages 55 MW against 872 MW in its own day-ahead solar forecast, so the
  realised intensity would miss the solar dip.
- **Development data:** 2024-10 to 2025-10 (used for every design choice below).
  **Confirmatory data:** submissions from 1 Nov 2025 00:00 to 1 Nov 2026 00:00 Europe/Brussels; October
  2025 (development) is used only as warm-up for the forecast model and the gate.

## 3. Realised intensity and as-issued forecasts (`cwf/entsoe.py`)

- **Realised intensity:** production-based average of the A75 "Actual Aggregated" values on 30-min windows,
  weighted by IPCC AR5 (Schlomer et al. 2014) life-cycle medians (coal and lignite 820, gas 490, oil 650,
  biomass 230, solar 48, wind 11/12, hydro and storage 24, nuclear 12, geothermal 38; waste 230 and
  other 490 as approximations). Imports are not counted.
- **Forecasts:** ENTSO-E publishes no intensity forecast. For each delivery day D a vintage is built from what
  was public at 18:00 Europe/Brussels on D-1: the day-ahead load and wind-plus-solar forecasts for D,
  converted with model M3, CI = b * (L - V) / L + hour-of-day intercept, fitted by least squares on the
  realised CI, load and wind-plus-solar of the 28 days that ended 1 h before 18:00 on D-1.
  The vintage captured at 18:00 on D-1 also carries the previous day-ahead values for the rest of D-1.
- **Model choice (development data only):** among M1 (residual-load share), M2 (residual load and load) and
  M3, M3 had the lowest mean absolute error on both zones (DE-LU 32.9, ES 20.1 g/kWh; M1 36.1 and 21.1;
  M2 37.7 and 20.1). A 48-h persistence forecast had 91.4 and 30.5.
- **kappa on development data** (MAE of day-ahead forecast / mean within-day SD of realised CI):
  DE-LU 0.48, ES 0.76.

## 4. Design

- **Workflows, platform, schedulers, regimes:** as in `EXT_PREREG.md` (10 WfCommons recipes, P = 8, runtime noise
  sigma = 0.2, synthetic sigma = 0.20, gate alpha = 0.9 without retuning, CA-List, CA-LS, gate, Shift,
  CaWoSched, CWM, HEFT safeguard; regimes oracle, synthetic, issued).
- **Only T = 4 h** (deadlines up to about 12.3 h), because a day-ahead vintage covers at most the end of the
  next local day. Planning window 13 h (26 windows). A submission is valid only if the latest vintage covers
  at least 90% of the planning window (the rule of the earlier studies); this excludes submissions between
  about 12:30 and 18:30 local time.
- **Seeds 50, 51, 52** (never used), **40 submissions per seed and zone** drawn uniformly from valid times in the
  confirmatory year. Planned jobs: 2 zones x 3 seeds x 40 submissions x 10 workflows = 2,400.
- **Development pilot** (seed 90, 4 submissions per zone, development year), run only to check the code:
  R = 0.95 (DE-LU) and 0.76 (ES); no nominal deadline miss; oracle trap rate 0.

## 5. Hypotheses

Pooled over zones; 95% cluster bootstrap over (zone, submission), 2,000 resamples, seed 2026;
CA-LS = CA-LS+SG; R = mean issued saving / mean oracle saving at f >= 1.5.

- **X1 (forecast loss).** Upper bound of R < 1.
- **X2 (traps).** CA-LS, issued: lower bound of the 1%-trap rate > 2% at every f.
- **X3 (gate).** Gated minus ungated 1%-trap rate: upper bound < 0; and retention (gated / ungated saving)
  lower bound >= 0.5.
- **X4 (kappa predicts the loss).** R(DE-LU) - R(ES): lower bound > 0 (DE-LU has the lower kappa).
- **X5 (runtime variability).** With runtime noise, CA-LS miss rate minus HEFT miss rate: lower bound > 10
  percentage points at every f.

**Decision:** a hypothesis is supported if its criterion holds and its Holm-adjusted one-sided bootstrap
p-value (family X1-X5, m = 5) is at most 0.025. A p-value is the share of bootstrap replicates on the null
side; for criteria with several parts (X2, X3, X5) it is the largest part.

**Secondary (reported, no claim depends on them):** the same criteria with clusters (zone, local day) and
(zone, ISO week); X1-X3 and X5 per zone; the E1 criterion (upper bound of R < 0.75).

**Descriptive:** R and trap rates by season and zone; kappa on the confirmatory year; CaWoSched and CWM on
emissions and native objective; deadline misses by scheduler.

## 6. Sanity checks

Planned job count reached or shortfall reported; no nominal deadline miss; oracle trap rate 0 for every
safeguarded scheduler.

## 7. Code

`cwf/entsoe.py`, `scripts/run_entsoe.py` and `scripts/analyse_entsoe.py` as committed with this file.
Run: `python scripts/run_entsoe.py ROOT results/entsoe_<ZONE>.csv --zone <ZONE> --seeds 50,51,52 --n-sub 40
--t0-from 2025-11-01 --t0-to 2026-11-01`, then `python scripts/analyse_entsoe.py results/entsoe_DE_LU.csv
results/entsoe_ES.csv`.
