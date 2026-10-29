# Pre-registration: Confirmatory study

**Study:** Do carbon-aware workflow schedulers survive real carbon-intensity forecasts?
**Authors:** Hemn Khezri, Mohammad Trik
**Sealed:** the git commit that adds this file. It is made before any confirmatory-period (2026) scheduler result is computed. Later changes are deviations and go to `CONFIRM_DEVIATIONS.md`.

Everything in this plan was designed on development data only (pilot period Mar 2023 - Feb 2024, seeds 0-2). See `PREREG.md`, `PILOT_RESULTS.md` and `reports/`.

## 1. Data

- **Carbon intensity:** GB national CI, issued 48-h forecast vintages and actuals, from `nmpowell/carbon-intensity-forecast-tracking`, commit `578de5b3c3b999bdccd4aaf8401d1b31a5405423` (29 Oct 2026).
- **Confirmatory period:** files `national_2026-07` to `national_2026-10` (windows from 16 Jul 2026 to 28 Oct 2026). The archive has no data between Feb 2024 and Jul 2026 (scraper outage documented by the archive maintainer).
- **Forecast at decision time:** latest capture issued at or before t0 - 30 min.
- **Workflows:** WfCommons 1.6 recipes as in the pilot (10 instances per seed, 198-395 tasks), fresh instances generated from the seed.
- **Seeds:** 10, 11, 12, 13, 14 (never used before). 30 submission times per seed, uniform over valid 30-min slots. A slot is valid if the issued vintage covers 47 h, actuals cover the execution horizon, and 7 days of earlier forecast history exist for gate calibration.

## 2. Platform and workload factors

- P = 8 identical machines, busy power 0.2 kW, idle power not attributed, no transfer time.
- Makespan targets T in {4 h, 12 h} (runtimes scaled so the HEFT makespan M is close to T).
- Deadline factors f in {1.2, 1.5, 2.0, 3.0}, D = round(f x M).
- Runtime variability (secondary factor): realised runtime = planned x exp(N(0, 0.2^2)), i.i.d. per task; execution rule in `cwf/execute.py`, identical for all schedulers.

## 3. Information regimes

- **Oracle:** plan with actual CI.
- **Synthetic:** plan with actual x (1 + e), e ~ N(0, 0.20^2) i.i.d. per 30-min window. sigma = 0.20 matches the median absolute relative error of 0-36 h forecasts in the development period (13.7%).
- **Issued:** plan with the issued forecast vintage.

## 4. Schedulers

All carbon-aware schedulers use the **HEFT safeguard**: the carbon-aware plan is kept only if it is cheaper than the HEFT plan on the planning CI.

| Name | Description |
| --- | --- |
| HEFT | Carbon-agnostic reference (earliest start, bottom-level order). |
| Shift | Whole-workflow shift of the HEFT plan by the cheapest offset in [0, D - M] on the planning CI (offset 0 = HEFT). |
| CA-List+SG | Carbon-aware list scheduling with deadline repair (pilot `DEVIATIONS.md` item 1), safeguarded. |
| CA-LS+SG | CA-List followed by local search (2n moves), safeguarded. **Primary scheduler.** |
| CA-LS+SG+Gate | As CA-LS+SG, deferrals allowed only if the forecast mean-CI gain exceeds the difference-error quantile q_alpha (lag x horizon bins, calibrated on the previous 7 days of realised vintages; `cwf/gate.py`). Issued regime only. **alpha = 0.9** (selected on development data by the rule in `tune_gate.py`; output in `reports/tune_gate.txt`). |
| CA-List+SG+Gate | Same gate on CA-List. |
| CaWoSched+SG | Official CaWoSched code (KIT-EAE/CaWoSched, commit `dfc8e49`), fixed HEFT mapping, CI mapped to a green budget as in CWM, best of slackR-LS and pressR-LS; adapter `cwf/cawosched.py`. Oracle and issued regimes. |

## 5. Outcomes

Per run, with nominal runtimes: saving = 1 - C / C_HEFT (realised with actual CI); trap1 = C > 1.01 x C_HEFT; miss = makespan > D. With noisy runtimes: the same quantities with suffix `_rt`.

Uncertainty: cluster bootstrap over submission times (2000 resamples, seed 2026), percentile 95% intervals. Means are pooled over workflows, T and seeds.

## 6. Hypotheses and decision criteria (fixed; `analyse_confirm.py`)

**Primary**
- **H1 (relative loss).** For CA-LS+SG, pooled over f in {1.5, 2.0, 3.0}: R = mean issued saving / mean oracle saving. Supported if the upper 95% bound of R < 0.75.
- **H2 (forecast-attributable traps).** For CA-LS+SG under issued forecasts, trap1 rate > 2% at every f. Supported if every lower 95% bound > 2%. (Under oracle CI the safeguard makes the trap rate 0 by construction; this is checked.)

**Secondary**
- **H3 (synthetic noise misleads).** For CA-LS+SG, pooled over f >= 1.5: mean synthetic saving - mean issued saving > 0 (lower bound > 0).
- **H4 (gate).** For CA-LS+SG under issued forecasts, all f pooled: the gate lowers the trap1 rate (upper bound of the difference < 0) and retains at least half of the ungated mean saving (lower bound of the ratio >= 0.5). Both required.
- **H5 (generality).** The H1 and H2 criteria also hold for CA-List+SG and for CaWoSched+SG (reported per scheduler).

**Exploratory (no decision attached):** Shift baseline; runtime-variability outcomes (deadline misses, savings, traps); breakdowns by T, f and workflow; trap severity.

A hypothesis that is not supported is reported as such; no hypothesis is dropped or reworded after the run.

## 7. Sanity checks (before reading the hypotheses)

1. Planned job count reached (5 seeds x 30 submissions x 10 workflows x 2 T = 3,000 jobs), or the shortfall reported.
2. No nominal deadline miss for any scheduler.
3. Oracle trap rate of every safeguarded scheduler = 0.

## 8. Winter extension (pre-registered now, run later)

When the archive holds national data for Nov 2026 - Feb 2027, the same code, configuration and analysis are run on those months with seeds 20-24. Results are reported as a separate replication; no parameter is retuned.

## 9. Planned outputs

Paper-ready tables from `analyse_confirm.py`; raw results CSV; code, configuration and this plan archived together (Zenodo) at submission.
