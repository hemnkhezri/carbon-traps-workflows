# Deviations from PREREG.md

All entries below were decided before any stop-rule metric (loss, trap rate) was computed.

1. **Deadline repair added to CA-List (and therefore CA-LS).** Smoke test on one Epigenomics instance showed CA-List overrunning the deadline even with oracle CI (1169 min vs D = 1066 min), because the latest start time LST = D - bottom level ignores machine capacity. Without repair, carbon "savings" could come from breaking deadlines. Fix: if the plan overruns D, re-plan with an internal deadline D' in [M, D] chosen by bisection (largest D' whose plan meets D, 6 steps); if none works, fall back to the HEFT schedule. This mirrors CWM's deadline-repair step. The repair mode (direct / repaired / heft-fallback) is logged per run.
2. **Submissions need 7 days of forecast-error history** (at least 48 windows) so the gate threshold tau uses only past data; this excludes roughly the first week of the pilot period.
3. **Makespan scaling tolerance.** Runtime scaling converges to within about 7% of the target T for some instances (e.g., Montage-s: 224 min for T = 4 h) because durations are rounded to whole minutes. Deadlines are set from the realised HEFT makespan M, so the design is unaffected.
4. **Recipe sizes.** All recipes produced 198-395 tasks, within the pre-registered 200-400 range except Montage-s (198).
