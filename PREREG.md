# Pre-registration: Kill-pilot

**Study:** Do carbon-aware workflow schedulers survive real carbon-intensity forecasts?
**Authors:** Hemn Khezri, Mohammad Trik
**Sealed:** 2026-10-29, before any scheduler result was computed. The git commit that adds this file is the seal; any later change to this file is a deviation and must be listed in `DEVIATIONS.md`.

## 1. Question

When carbon-aware schedulers for deadline-constrained workflows plan with the carbon-intensity (CI) forecast that was actually available at submission time, how much of their perfect-information (oracle) saving survives, and how often do they emit more than a carbon-agnostic baseline?

## 2. Pilot scope (development data only)

- **CI data:** GB national CI from the `nmpowell/carbon-intensity-forecast-tracking` archive (NESO API snapshots), Mar 2023 - Feb 2024. Pilot only; the 2026 months are reserved for the confirmatory study and are not opened during the pilot.
- **Forecast at decision time:** the latest capture issued at or before the submission time; forecast values for each 30-min window up to 48 h ahead. Missing windows are forward-filled within the vintage.
- **Actual CI:** the `actual` value of each window from its latest capture; gaps linearly interpolated.
- **Workflows:** WfCommons 1.6 recipes, one instance each per seed: Montage, Epigenomics, Blast, BWA, Cycles, 1000Genome, Seismology, SoyKB, SRASearch, plus a second Montage size. Target 200-400 tasks.
- **Platform model:** cluster of P = 8 identical machines, 1 task per machine at a time, busy power 200 W, idle power not attributed, data-transfer time ignored, deterministic runtimes. Task runtimes are scaled per instance so that the HEFT makespan M equals a target T.
- **Makespan targets:** T in {4 h, 12 h}.
- **Deadlines:** D = f x M with f in {1.2, 1.5, 2.0}.
- **Submissions:** 40 submission times per seed, uniform over the 30-min grid of the pilot period, restricted so that submission + D <= last forecast window.
- **Dev seeds:** 0, 1, 2 (seed controls workflow instance and submission times).

## 3. Schedulers

All share one simulator, time resolution 1 min.

1. **HEFT:** upward-rank list order, each task starts at the earliest feasible time (carbon-agnostic reference).
2. **CA-List:** same order; each task picks the start in [EST, LST] that minimises forecast carbon, subject to machine capacity. LST is the latest start that still lets the longest downstream path finish by D.
3. **CA-LS:** CA-List followed by local search (2n random single-task moves, accepted if forecast carbon falls and precedence, capacity and deadline still hold). Stands in for CWM-style improvement; CWM itself is not re-implemented in the pilot.
4. **CA-List+Gate, CA-LS+Gate:** a task is deferred from its earliest feasible start only if the forecast mean-CI gain exceeds tau, where tau is the MAE over the previous 7 days of forecasts issued 12-36 h before each window (computed only from data before submission). kappa = 1.

## 4. Information regimes

- **Oracle:** plan with actual CI.
- **Synthetic:** plan with actual x (1 + e), e ~ N(0, 0.10^2) i.i.d. per window.
- **Issued:** plan with the issued forecast vintage.

Realised carbon is always computed with actual CI over the planned execution intervals.

## 5. Outcomes

For each run: saving = 1 - C_scheduler / C_HEFT (realised). Carbon trap = run with C_scheduler > C_HEFT. Deadline miss = makespan > D.

- **Loss (pp)** = median oracle saving - median issued saving, per scheduler and deadline factor (pooled over workflows, T, seeds, submissions).
- **Trap rate** = share of issued-regime runs that are carbon traps.

## 6. Stop rule (decision for the whole topic)

Evaluated on the ungated schedulers (CA-List and CA-LS), issued regime.

**Drop the topic if, at every deadline factor f in {1.2, 1.5, 2.0}, both hold for both schedulers:**
- Loss < 5 percentage points, and
- Trap rate < 2%.

Otherwise, continue: seal the confirmatory plan and run it on fresh seeds and the 2026 months.

Gated schedulers and the synthetic regime are reported as exploratory and do not enter the stop rule.

## 7. Sanity checks (must pass before the stop rule is read)

- HEFT meets every deadline (by construction f >= 1.2).
- Oracle median saving of CA-List is >= 0 at every f.
- Number of completed runs equals the planned grid; failures are reported.
