# Extension notes (development data only, 2 Nov 2026)

Exploratory checks on the pilot period (Mar 2023 - Feb 2024). No 2026 data used.

## 1. CaWoSched adapter documentation error
The adapter docstring said the CI-to-budget mapping "follows CWM". CWM maps CI into
[P_min, P_min + 0.2 or 0.4 x dynamic power]; the adapter used the full range [0, P x work power].
The code was unchanged during the confirmatory run; only the description was wrong and is now corrected.
Check (5 workflows x 2 T x 6 submissions x 2 f, n = 120 per cell), mean emission saving vs HEFT:

| budget fraction | oracle | issued |
| --- | --- | --- |
| 0.2 | 2.34% | 2.97% |
| 0.4 | 2.56% | 2.93% |
| 1.0 (used) | 4.85% | 3.21% |

The full range gives CaWoSched its best oracle saving, so the confirmatory CaWoSched results are not
handicapped by the mapping. To be reported in the paper (methods) and in CONFIRM_DEVIATIONS.md.

## 2. Official CWM code (KIT-EAE/CWM @ 50e9ef5)
Built with two non-algorithmic changes (external/cwm_patch.diff): read-only accessors for the final
schedule and missing #include <queue> for GCC 13. All schedules valid (precedence, capacity, deadline).
On our homogeneous platform with zero idle power, CWM reduces its own objective (brown energy above the
green budget) by 12-19% vs HEFT but does not reduce emissions (mean -0.4% to -10%, oracle CI).
CaWoSched: 25-56% on its own objective, 2.6-5.8% on emissions.

Interpretation: the green-budget proxy used by CWM and CaWoSched can diverge from grid emissions,
and CWM is designed for heterogeneous clusters with idle power, which our platform lacks.
Consequence for the extension: evaluate CWM and CaWoSched on both emissions and their native
objective, and add a heterogeneous platform with idle power.

## 3. CWM budget fraction on the heterogeneous platform (GB dev data, Jun-Aug 2023)
Seed 0, 6 submissions, 5 workflows, 2 T, 4 f (n = 240 per regime); raw CWM (no safeguard), mean vs heterogeneous HEFT:

| frac | oracle emission saving | oracle native saving | issued emission saving |
| --- | --- | --- | --- |
| 0.2 | -1.85% | 2.43% | -1.68% |
| 0.4 | -1.38% | 6.43% | -1.48% |
| 1.0 (chosen) | -0.11% | 15.90% | -0.41% |

frac = 1.0 is best for CWM on both metrics, so it is used in EXT2_PREREG.md.
A 2-workflow smoke test (8 jobs) ran without invalid CWM schedules or nominal misses.
