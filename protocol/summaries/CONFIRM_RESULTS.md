# Confirmatory results (30 Oct 2026)

Plan: `CONFIRM_PREREG.md` (sealed at `55fff17`). Deviations: `CONFIRM_DEVIATIONS.md` (planning-horizon padding; run split by seed). Full output: `reports/confirm_report.txt`. Data: GB national CI, 16 Jul - 28 Oct 2026; seeds 10-14; 3,000 jobs; 156,000 runs.

## Sanity checks: all passed

3,000/3,000 jobs (147 distinct submission times); no nominal deadline miss for any scheduler; oracle trap rate 0 for every safeguarded scheduler. An independent recomputation reproduced R for all three schedulers.

## Hypotheses

95% intervals: cluster bootstrap over submission times (2,000 resamples).

| Hypothesis | Criterion | Result | Verdict |
| --- | --- | --- | --- |
| H1 relative loss (CA-LS+SG, f >= 1.5) | upper bound of R < 0.75 | R = 0.68 [0.62, 0.74] | Supported |
| H2 forecast-attributable traps (CA-LS+SG, issued) | lower bound > 2% at every f | 7.5% [5.5, 9.7] at f = 1.2; 13.2-15.9% at f = 1.5-3.0 | Supported |
| H3 synthetic noise overstates savings | lower bound of difference > 0 | +0.68 pp [-0.09, 1.48] | Not supported |
| H4 difference-error gate (alpha = 0.9) | trap difference < 0 and retention >= 0.5 | traps -8.65 pp [-10.81, -6.62]; retention 0.84 [0.77, 0.92] | Supported |
| H5 generality: CA-List+SG | H1 and H2 criteria | R = 0.68 [0.61, 0.74]; traps 6.5-16.0% | Both met |
| H5 generality: CaWoSched+SG | H1 and H2 criteria | R = 0.73 [0.67, 0.78]; traps 7.6-14.0% | H1 not met, H2 met |

Per seed, R for CA-LS+SG ranged 0.57-0.80 and the trap rate at f >= 1.5 ranged 4.7-20.2%; the direction held in all five seeds.

## Main findings

1. **Issued forecasts remove about a third of the oracle saving** (R = 0.68 for CA-LS+SG and CA-List+SG, 0.73 for CaWoSched).
2. **Carbon traps are frequent and not caused by the schedulers.** With the HEFT safeguard, oracle traps are 0, yet under issued forecasts 7.5-15.9% of runs emit more than 1% above HEFT. In trap runs the median excess is 6.2%, and one in ten exceeds 24.5%.
3. **The difference-error gate works.** It cuts traps from 7.5-15.9% to 1.4-6.1% while keeping 84% of the mean saving.
4. **Synthetic i.i.d. noise is not a faithful stand-in, but not in the predicted way (exploratory).** Mean savings were similar (H3 not supported). Trap rates differed by scheduler: higher than issued for the DAG schedulers (e.g., 21.4% vs 15.9% at f = 2.0), lower for Shift (9.3% vs 16.5%).
5. **Runtime variability is the largest operational risk (exploratory).** With +/-20% runtime noise, carbon-aware plans missed the deadline in 14-49% of runs versus at most 1.5% for HEFT, because deferral consumes the slack. The gate roughly halved misses (e.g., CA-LS+SG at f = 1.5: 49.0% to 23.9%).
6. **A whole-workflow shift is a strong baseline (exploratory).** Under issued forecasts it matched the DAG schedulers within about 1 pp of mean saving at every f.

Mean savings (issued) rose with slack: CA-LS+SG 2.1% (f = 1.2) to 14.4% (f = 3.0); 19.8% for 12-h workflows at f = 3.0. Oracle savings were larger than in the pilot (up to 21.2%), consistent with a more variable 2026 summer grid.

## Limitations

- One grid (GB national), summer-autumn only; the winter replication is pre-registered (seeds 20-24).
- Homogeneous machines, idle power not attributed, no transfer time.
- CaWoSched optimises brown power above a green budget (CI mapped as in CWM), not emissions directly; its smaller loss may reflect that proxy.
- Runtime variability results are exploratory; the deadline-miss finding should be a primary hypothesis in the winter replication or a follow-up.
