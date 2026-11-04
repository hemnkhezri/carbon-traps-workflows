# EXT3 deviations log (revision robustness study)

## 1. Units error in the re-planning loop (found 2026-11-04, after part A was run; fixed before any re-planning result was reported)

`run_revision.py` passed the re-planning time `t` (minutes after submission) to the
vintage lookup and to the gate's lag as if it were seconds (`t0 + t` instead of
`t0 + 60 * t`). Every re-plan therefore used the vintage available at submission,
so the Q1 variants (RH-CA-LS+SG, RH-Shift, with and without the gate) never saw a
newer forecast. The error was found because RH-Shift equalled Shift in all 4,800
runs. It affects only the four RH variants; all other Part A rows are unchanged
(the reference CA-LS+SG still reproduces the confirmatory runs exactly).

Fix: commit after this entry. The four RH variants are re-run for seeds 10 and 11
(`--part RH`, results/rev/RH_s10s11.csv) and replace the RH rows of A_s10/A_s11
in the analysis. The decision rule for Q1 is unchanged. The erroneous interim RH
numbers (R = 0.82 [0.73, 0.90], trap 10.4%) are not reported in the paper.

The gate thresholds q used at a re-plan are those calibrated at submission; only
the vintage age (lag) is updated. Recalibrating at every re-plan was not in the plan.
