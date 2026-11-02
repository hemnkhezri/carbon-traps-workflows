# Platform-sensitivity results (pre-registered in EXT2_PREREG.md, sealed at 071e77f)

Raw: `results/het/*_30.csv` (merged `results/hetero.csv`); analysis log `results/hetero_analysis.txt`.
There are no deviations from the pre-registration.

## Sanity checks
1,600 / 1,600 jobs; 0 nominal misses (safeguarded schedulers and Shift); oracle trap rate 0 for CA-List+SG,
CA-LS+SG and CWM+SG; no CWM schedule was invalid. All checks passed.

## Hypotheses (pooled over CISO, DE, ERCO, PJM)

| | Criterion | Estimate [95% CI] | Verdict |
|---|---|---|---|
| G1 | R upper bound < 0.75 (CA-LS+SG, f >= 1.5) | R = 0.85 [0.80, 0.90] | **Not supported** |
| G2 | trap1 lower bound > 2% at every f | 1.6% (f=1.2) to 5.4% (f=3.0); bounds 0.6-2.5% | **Not supported** |
| G3 | gate trap diff upper bound < 0, retention lower bound >= 0.5 | -2.2 pp [-3.8, -1.0]; retention 1.06 [1.02, 1.09] | Supported |
| G4 | CWM+SG native-objective R upper bound < 0.75 | R_native = 0.32 [0.01, 0.57] | Supported |
| G5 | CA-LS+SG miss - HEFT miss lower bound > 10 pp at every f | +49.9 to +76.0 pp | Supported |

## Descriptive
- **Most of the heterogeneous saving does not depend on carbon intensity.** CA-LS+SG saves 6.8% (oracle) and 5.8% (issued) of emissions, against 5.1% and 3.5% on the homogeneous platform for the same submissions and workflows. Part of this saving comes from putting work on the more efficient fast machines and from shorter idle periods, and needs no forecast. This dilutes R and the trap rate. See the exploratory check below.
- **Native objective.** Even on this platform the forecast loss is large. CA-LS+SG: oracle 42-48%; issued 36-37% (CISO, DE) and -22% to -30% (PJM, ERCO). CWM+SG: oracle 13-19%; issued 15-16% (CISO, DE) and -3% to -10% (PJM, ERCO).
- **CWM on its home platform.** Raw CWM still does not reduce emissions relative to heterogeneous HEFT (oracle -1.9% to +0.3%) and trips the 1% trap threshold in 24-40% of runs even under oracle CI. CWM+SG saves 0.6-2.0% (oracle). The homogeneous platform therefore did not cause CWM's weak emission results: its green-budget objective does not track emissions on either platform.
- **The gate helps more here.** It raised the mean saving (retention 1.06) and cut misses at f >= 2.0 (45.0% vs 63.2% at f = 2; 27.9% vs 49.9% at f = 3).
- **Runtime noise is worse on this platform.** CA-LS+SG misses 50-76% of deadlines; Shift misses 20-50% and HEFT almost none. Plans that move work onto fast machines leave less slack for overruns.
- **Shift is weaker on this platform** (2.8% oracle, 2.0% issued), because it cannot change the machine mapping.

## Exploratory (post hoc): saving with no carbon signal
`explore_flat_het.py`: CA-LS+SG planned on a flat CI signal (energy-aware only), 5 submissions per region
(seed 30), all workflows, T and f (n = 800 per regime). Flat-CI saving 6.05% vs 7.00% oracle and 6.18% issued
on the same jobs. The carbon-timing gain is about 0.95 pp under the oracle, and issued forecasts keep about
0.13 pp of it (around 14%). Small subset; reported as an indication, not a test.

## Reading
The pre-registered emission criteria G1 and G2 are not met on the heterogeneous platform, and the paper
reports this. The likely reason is dilution: when the machine choice can save energy at any time, the share of
the saving that depends on forecasts is small. The forecast-dependent part (native objective, G4; timing gain,
exploratory) is lost to an even larger degree than on the homogeneous platform.
