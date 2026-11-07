# Pre-registration: winter replication of "Mitigating Carbon Traps in Carbon-Aware Workflow Scheduling under Real Carbon-Intensity Forecasts"

Authors: Hemn Khezri (Young Researchers and Elite Club, Sardasht Branch, Islamic Azad University, Sardasht, Iran),
Mohammad Trik (Department of Computer Engineering, Bou.C., Islamic Azad University, Boukan, Iran).
Contact: hemnkhezri21@gmail.com

## 1. Purpose
The confirmatory study (GB, 16 July - 28 October 2026) found that issued carbon-intensity forecasts keep about two-thirds
of the oracle saving of carbon-aware workflow schedulers and turn about one plan in seven into a carbon trap. It covers one
season. This replication tests the same hypotheses on winter data, without retuning anything, and adds two hypotheses that
the earlier studies supported only in exploratory or robustness analyses.

## 2. Data and status at registration
GB national forecast vintages and realised intensity from the public archive nmpowell/carbon-intensity-forecast-tracking.
**Period: submissions from 1 December 2026 00:00 UTC to 28 February 2027.** At the time of registration (November 2026) the
archive already held data for early November 2026, which the authors have not accessed. To rule out any influence, November
2026 is excluded. No data from the registered period exist at registration.

## 3. Fixed design (identical to the confirmatory study)
Code and configuration as in the public repository at the commit cited in this registration (`confirm_config.json`,
`run_confirm.py`, `run_revision.py`, `analyse_confirm.py`, `analyse_revision.py`). Seeds 20-24; 30 submission times per
seed drawn uniformly from 30-minute slots with a complete vintage, realised intensity for the execution horizon and seven
days of history; 10 WfCommons workflows; T in {4, 12} h; P = 8; f in {1.2, 1.5, 2.0, 3.0}. Schedulers: HEFT, Shift,
CA-List+SG, CA-LS+SG, CaWoSched+SG, gated CA-LS+SG (alpha = 0.9), CA-LS+SG with slack reserve rho = 0.75. Regimes: oracle,
synthetic noise (sigma 0.20), issued. Runtime noise: lognormal sigma 0.2, static executor. Cluster bootstrap over submission
times (2,000 resamples, seed 2026), plus clustering by day and week; Holm correction within the family W1-W5,
one-sided, family alpha 0.025.

## 4. Hypotheses and decision rules
- **W1 (= H1).** CA-LS+SG, f >= 1.5: R = mean issued saving / mean oracle saving; supported if the upper 95% bound < 0.75.
- **W2 (= H2).** CA-LS+SG, issued: trap rate (C > 1.01 C_HEFT) > 2% at every f; supported if every lower bound > 2%.
- **W3 (= H4).** The gate lowers the trap rate (upper bound of the difference < 0) and keeps at least half of the ungated
  saving (lower bound of the ratio >= 0.5), all f pooled.
- **W4 (new; slack reserve).** CA-LS+SG with rho = 0.75, issued, f >= 1.5: deadline-miss rate minus HEFT's miss rate below
  5 percentage points (upper bound < 0.05), and mean saving at least 70% of CA-LS+SG's (lower bound of the ratio >= 0.7).
- **W5 (new; Shift as a baseline).** Issued, f >= 1.5: |mean saving of Shift - mean saving of CA-LS+SG| < 1 percentage
  point (both bounds of the paired difference inside (-1, 1)).
Sanity checks as in the confirmatory plan (job count, no nominal misses, zero oracle traps for safeguarded schedulers).
A hypothesis that is not supported is reported as such; nothing is dropped, reworded or retuned.

## 5. Outputs
Results will be reported as a separate replication (or added to the article if it is still under review), together with
all deviations from this plan.
