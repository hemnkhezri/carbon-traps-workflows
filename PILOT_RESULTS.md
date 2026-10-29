# Kill-pilot results (29 Oct 2026)

Design: `PREREG.md` (sealed at `caf34db`). Deviations: `DEVIATIONS.md`. Raw outputs: `results/` (CSV not committed; regenerate with `run_pilot.py`).

## Decision under the sealed stop rule: CONTINUE

All sanity checks passed: 2,400/2,400 jobs, no deadline misses for any scheduler, oracle median saving of CA-List >= 0 at every deadline factor.

Issued regime, ungated, pooled over 10 workflows x 2 makespan targets x 3 dev seeds x 40 submissions (n = 2,400 per cell):

| Scheduler | f | Oracle median saving | Issued median saving | Loss (pp) | Trap rate |
| --- | --- | --- | --- | --- | --- |
| CA-List | 1.2 | 0.00% | 0.00% | 0.00 | 19.5% |
| CA-List | 1.5 | 2.15% | 0.23% | 1.91 | 27.7% |
| CA-List | 2.0 | 7.08% | 2.78% | 4.30 | 32.0% |
| CA-LS | 1.2 | 0.48% | 0.03% | 0.46 | 25.8% |
| CA-LS | 1.5 | 2.64% | 0.71% | 1.93 | 29.5% |
| CA-LS | 2.0 | 7.27% | 2.93% | 4.34 | 31.8% |

The loss criterion (< 5 pp) held everywhere; the trap criterion (< 2%) failed everywhere, so the rule says continue.

## Caveats found after reading the results

1. **The loss threshold was poorly chosen.** Oracle savings were only 0-7%, so a 5 pp absolute loss was nearly impossible. In relative terms, issued forecasts removed about 60% (f = 2.0) to about 90% (f = 1.5) of the median oracle saving. The confirmatory plan should state loss relative to the oracle saving.
2. **Part of the trap rate is scheduler weakness, not forecast error.** With oracle CI, CA-List and CA-LS still emitted more than HEFT in 12-17% of runs (greedy per-task deferral can hurt downstream tasks).
3. **Exploratory safeguard check (seed 0, not in the stop rule, `explore_safeguard.py`).** Keeping the HEFT plan whenever the carbon-aware plan is not cheaper on the planning CI removes all oracle traps by construction. Under issued forecasts the trap rate stays at 11.9-21.3% (4.9-16.4% for traps larger than 1%). The forecast-attributable trap effect therefore survives the obvious fix.
4. **The simple gate failed.** With tau = recent MAE (about 25 gCO2/kWh), the gate removed all issued savings (median 0%) and still left 6-12% traps.
5. **Synthetic i.i.d. noise (sigma = 10%) is not a faithful stand-in.** It overstated savings relative to issued forecasts (e.g., 5.4% vs 2.8% at f = 2.0) but produced as many or more traps.
6. **Absolute savings are small** compared with CWM (which uses a different metric, power above a green budget) and West et al. (24-96 h windows). Slack here is 0.2-1.0 x makespan within a 4-12 h workflow.

## Implications for the confirmatory plan (to be sealed before running)

- Primary metrics: relative loss (issued / oracle saving) and forecast-attributable trap rate (issued minus oracle, with the HEFT safeguard on).
- Include the HEFT safeguard in every carbon-aware scheduler, and add real CWM or CaWoSched code if obtainable.
- Add runtime variability, longer slack (f up to 3.0, T = 24 h within the 48 h forecast horizon), and the 2026 months on fresh seeds.
- Replace the MAE gate with an interval-based rule (e.g., conformal forecast intervals, as in Li et al., HotCarbon 2024) and treat the gate as a candidate method, not a baseline.
