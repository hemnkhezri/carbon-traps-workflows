# Extension results (pre-registered in EXT_PREREG.md, sealed at 1eb3069)

Data: CarbonCast day-ahead forecasts, CISO / DE / ERCO / PJM, Jul-Dec 2021; seeds 30-32; 20 submissions.
Raw output: `results/ext/*.csv` (merged: `results/extension.csv`); full analysis log: `results/extension_analysis.txt`.
There are no deviations from the pre-registration.

## Sanity checks
4,800 / 4,800 planned jobs; 0 nominal deadline misses; oracle trap rate 0 for every safeguarded scheduler. All checks passed.

## Primary hypotheses (pooled; 95% cluster bootstrap over region x submission)

| | Criterion | Estimate [95% CI] | Verdict |
|---|---|---|---|
| E1 | R upper bound < 0.75 (CA-LS+SG, f >= 1.5) | R = 0.66 [0.60, 0.72] | Supported |
| E2 | trap1 lower bound > 2% at every f | 6.4% (f=1.2) to 16.4% (f=3.0); lowest bound 4.8% | Supported |
| E3 | gate trap diff upper bound < 0 and retention lower bound >= 0.5 | -8.1 pp [-9.8, -6.5]; retention 0.87 [0.82, 0.93] | Supported |
| E4a | CA-LS+SG miss - HEFT miss lower bound > 10 pp at every f | 27.6 to 43.4 pp; lowest bound 24.7 pp | Supported |
| E4b | gated - ungated miss upper bound < 0 | -21.5 pp [-23.1, -19.8] | Supported |

## Secondary (per region; no pooled claim depends on these)

| Region | R (f >= 1.5) | Trap1 range | E3 | Note |
|---|---|---|---|---|
| CISO | 0.85 [0.81, 0.89] | 2.9-8.3% | met | Best-forecast grid; E1 and E2 not met |
| DE | 0.76 [0.67, 0.84] | 5.2-12.6% | met | E1 not met (bound 0.84) |
| ERCO | 0.19 [-0.05, 0.36] | 15.5-35.3% | not met (retention CI wide) | Forecast error wipes out most of the saving |
| PJM | 0.52 [0.41, 0.62] | 2.1-12.4% | not met (retention 0.61 [0.46, 0.79]) | Small oracle saving (1.8%) |

E4 (runtime noise) was met in every region.

## Descriptive
- **Loss depends on the region.** The pooled R of 0.66 is close to the GB confirmatory value (0.68), but per region R ranges from 0.19 (ERCO) to 0.85 (CISO). Forecast quality, not the scheduler, decides how much of the oracle saving survives.
- **Shift stays competitive.** With issued forecasts, Shift is within 0.3 pp of CA-LS+SG in every region and ahead of it in ERCO (1.15% vs 0.87%), as in GB.
- **CWM and CaWoSched on their native objective (brown energy).** The oracle saving is large: CWM about 22%, CaWoSched 40-44%. With issued forecasts it drops sharply and turns negative in ERCO (CWM -7%, CaWoSched -13%). The forecast-loss finding therefore also holds on the algorithms' own objective.
- **CWM has the lowest trap rate.** It traps least among the non-gated schedulers (2.4-14%) but saves least on emissions (0.4-3.5%), which matches the homogeneous-platform caveat in EXTENSION_NOTES.md.
- **Deadline misses with runtime noise.** Every carbon-aware scheduler misses 8-43% of deadlines; HEFT misses at most 3.5%. The gate roughly halves the miss rate of CA-LS.

## Exploratory (post hoc, not pre-registered): what explains the regional spread
The ratio of forecast MAE (0-47 h) to the intraday SD of actual CI orders the grids exactly as R does
(`forecast_skill.py`, Fig. 7): CISO 0.46 -> R 0.85; DE 0.56 -> 0.76; GB 0.67 -> 0.68; PJM 1.03 -> 0.52;
ERCO 1.47 -> 0.19. The relative MAE alone does not (PJM has the lowest relative MAE, 4.5%, but a flat
CI profile). What decides the loss is forecast error relative to the variation that scheduling exploits.
Five points, two data sources (operator vs research forecaster, 2026 vs 2021): reported as a pattern, not a fitted law.
