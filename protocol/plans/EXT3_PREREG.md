# Plan: Revision robustness study (requested by internal review; written before any result of these variants on the GB confirmatory data)

**Status:** post hoc with respect to CONFIRM_PREREG.md (the confirmatory data have been analysed), but every
variant below is new and none of its results has been computed on these data. Development checks used only
GB pilot months (Jun-Jul 2023, seed 0). Sealed by the git commit that adds this file; later changes go to
EXT3_DEVIATIONS.md. All results are reported as **robustness analyses**, not as confirmatory tests.

## Data and design
GB confirmatory data and code configuration (confirm_config.json), seeds **10 and 11** (the same workflow instances
and submission times as the confirmatory study; 2 x 30 x 10 x 2 = 1,200 jobs, 4 f each). The unchanged static
CA-LS+SG is re-run as a reference and must reproduce the confirmatory values exactly for these seeds.

## Variants (run_revision.py; cwf/replan.py; cwf/gates_alt.py)
- **Re-planning (R1-M1).** Receding horizon every 120 min on the newest NESO vintage (captured <= t0 + t - 30 min):
  RH-CA-LS+SG, RH-CA-LS+SG+Gate, RH-Shift, RH-Shift+Gate. Started tasks are fixed; each re-plan keeps the cheapest
  feasible of {new CA-LS plan, ASAP completion, previous plan} on the current forecast. Nominal runtimes.
- **Reactive executor (R1-M2).** Same plans executed with runtime noise under a work-conserving catch-up rule
  (a task waits for its planned start only while all its ancestors are on time). Applied to every static plan and to HEFT.
- **Slack reserve (R1-M2).** CA-LS+SG planned against D' = M + rho (D - M), rho in {0.75, 0.5}.
- **Gate alternatives (R1-M6, R2-M5).** Difference gate at alpha in {0.5, 0.8, 0.9, 0.95}; constant threshold
  (one 0.9-quantile, no bins); level-interval rule in the style of Li et al. (alpha 0.9); deferral cap of 6 h.
  Gated Shift (difference gate, alpha 0.9).
- **Official tools with the authors' budget band (R1-M5).** CaWoSched+SG and CWM(+SG) with frac in {0.2, 0.4};
  CWM also with frac 1.0 (not run on GB before).

## Questions and pre-stated readings (95% cluster bootstrap over calendar days of t0, 2000 resamples)
- **Q1 Re-planning.** R_RH = mean issued saving of RH-CA-LS+SG / mean oracle saving of CA-LS+SG, f >= 1.5.
  Reading A ("the static loss is mostly an artefact of open-loop planning"): upper bound of R_RH >= 0.9 and
  upper bound of the RH trap1 rate < 2%. Otherwise reading B ("re-planning does not remove the loss").
- **Q2 Executor.** Under the reactive executor, CA-LS+SG miss rate - HEFT miss rate: lower bound > 10 pp at every f
  means the deadline finding is robust to the executor; otherwise it is reported as executor-dependent.
- **Q3 Slack reserve.** Saving vs miss rate (both executors) for rho in {1, 0.75, 0.5} and the gate; descriptive.
- **Q4 Gate alternatives.** Pooled issued (mean saving, trap1) of every gate; the difference gate (alpha 0.9) is
  "dominated" if another gate has a higher saving and a lower trap rate with both paired-difference intervals excluding 0.
- **Q5 Gate coverage.** Empirical coverage of the alpha = 0.9 difference bounds on the realised errors of the vintage
  used at t0, per lag x horizon bin (script gate_coverage.py); nominal 0.9.
- **Q6 Official tools.** Oracle and issued emission saving, R and trap1 per frac; descriptive.

## Sanity checks
Planned jobs; no nominal miss for safeguarded and RH variants; oracle trap rate 0 for safeguarded variants; the
reference CA-LS+SG equals the confirmatory rows.
