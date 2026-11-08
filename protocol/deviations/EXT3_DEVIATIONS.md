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

## 2. Post-hoc additions after the second internal review (2026-11-04; exploratory, not in the sealed plan)

Run as `--part R2` on seeds 10 and 11 (results/rev/R2_s10s11.csv), after all sealed Q1-Q6 results were known:
(a) receding-horizon CA-LS on the oracle signal, and on the submission-time vintage at every re-plan
("stale"), to separate information gain from optimisation gain in Q1 (replaces the use of the
erroneous run of item 1 as a control, which also mis-scaled the gate lag);
(b) an uncertainty-aware planner: CA-LS+SG planning on F + qU(horizon), the 0.9-quantile of level
errors per horizon bin (same calibration as the level gate);
(c) correlated runtime noise: log-runtime = sqrt(0.5) * 0.2 * (job factor + task factor), same
marginal sigma as the main analysis; static executor; CA-LS+SG, CA-LS+SG+Res75 and HEFT.
All results from these runs are reported as exploratory.
