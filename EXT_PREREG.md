# Pre-registration: Generality extension

**Sealed:** the git commit that adds this file, before any result on the extension data is computed.
Smoke tests before sealing use only the GB development period (Mar 2023 - Feb 2024).
Later changes go to `EXT_DEVIATIONS.md`.

## 1. Purpose

Test whether the confirmatory findings (H1, H2, H4) hold on other grids and forecasters, test the
runtime-variability finding as a pre-registered hypothesis, and add the official CWM code.

## 2. Data

- **Forecasts and actuals:** CarbonCast out-of-sample day-ahead forecasts (Maji et al., EIR 2023;
  github.com/carbonfirst/CarbonCast, direct emissions), regions **CISO, DE, ERCO, PJM**, 1 Jul - 31 Dec 2021.
  One vintage per day issued at 00:00 UTC with a 96-h hourly horizon; each hour is split into two
  30-min windows. These are research-model forecasts, not operator forecasts; the paper says so.
- Regions chosen before any result: two US grids with different forecast error (ERCO high, PJM low),
  a solar-driven grid (CISO) and a wind-driven European grid (DE). ISNE and SE are not used.
- **Workflows, platform, factors:** identical to `CONFIRM_PREREG.md` (10 WfCommons recipes, P = 8,
  T in {4 h, 12 h}, f in {1.2, 1.5, 2.0, 3.0}, runtime noise sigma = 0.2, synthetic sigma = 0.20).
- **Seeds:** 30, 31, 32 (never used). 20 submission times per seed and region, same validity rule.
  Planned jobs: 4 regions x 3 seeds x 20 submissions x 10 workflows x 2 T = 4,800.

## 3. Schedulers

All schedulers of the confirmatory study, unchanged (gate alpha = 0.9, no retuning), plus:

- **CWM+SG:** official CWM code (KIT-EAE/CWM @ 50e9ef5, variant `local-search`; non-algorithmic
  patch in `external/cwm_patch.diff`), CI-to-budget mapping as for CaWoSched (full range, frac = 1.0),
  HEFT safeguard. Oracle and issued regimes.

## 4. Outcomes

As in the confirmatory study, plus for CaWoSched, CWM and HEFT the **native objective**: brown
energy above the green budget derived from actual CI (same mapping), and its saving relative to HEFT.

## 5. Hypotheses (pooled over regions unless stated; 95% cluster bootstrap over region x submission)

- **E1 (H1 generality).** CA-LS+SG, f >= 1.5: upper bound of R = issued/oracle mean saving < 0.75.
- **E2 (H2 generality).** CA-LS+SG, issued: trap1 lower bound > 2% at every f.
- **E3 (H4 generality).** Gate: trap1 difference upper bound < 0 and retention lower bound >= 0.5.
- **E4 (runtime variability, new).** With runtime noise, issued forecasts: (a) CA-LS+SG deadline-miss
  rate exceeds HEFT's by more than 10 percentage points at every f (lower bound of the difference > 10);
  (b) the gate lowers the CA-LS+SG miss rate pooled over f (upper bound of gated - ungated < 0).

**Secondary (per region):** E1-E3 criteria evaluated per region and reported; no pooled claim depends on them.

**Descriptive (no criterion):** CWM and CaWoSched on emissions and native objective, oracle vs issued.

## 6. Sanity checks

Planned job count reached or shortfall reported; no nominal deadline miss; oracle trap rate 0 for
every safeguarded scheduler.
