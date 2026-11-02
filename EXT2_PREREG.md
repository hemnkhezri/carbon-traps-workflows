# Pre-registration: Platform sensitivity (heterogeneous platform with idle power)

**Sealed:** the git commit that adds this file, before any heterogeneous-platform result on the
CarbonCast data is computed. Development checks used only GB data (Jun-Aug 2023). Later changes go to
`EXT2_DEVIATIONS.md`.

## 1. Purpose
The main study uses 8 identical machines with no idle power. CWM is designed for heterogeneous
clusters with idle power, so a reviewer could say the comparison is unfair to it, or that the
forecast-loss findings depend on the simple platform. This study repeats the extension on a
heterogeneous platform with idle power.

## 2. Platform (`cwf/hetero.py`)
CWM's own example processor types (KIT-EAE/CWM `examples/cluster.json`): slow (speed 1, idle 1, work 10)
and fast (speed 2, idle 2, work 15); 4 of each (P = 8); 1 unit = 0.02 kW. A task with work w runs
ceil(w/speed) minutes. Idle power is attributed to all machines until max(D, makespan). No transfer time.
The deadline is D = f x M, where M is the makespan of heterogeneous (insertion-based, EFT) HEFT.

## 3. Data and design
CarbonCast CISO, DE, ERCO, PJM (as in EXT_PREREG.md); seed 30 only, 20 submissions; the same
submissions and workflow instances as seed 30 of the extension, so the two platforms can be compared
descriptively. Regimes: oracle and issued. Factors, targets and runtime noise unchanged.
Planned jobs: 4 x 1 x 20 x 10 x 2 = 1,600.

## 4. Schedulers
- HEFT (baseline), Shift (whole-plan shift), CA-List+SG and CA-LS+SG, now choosing machine and start
  time on the marginal (work - idle) cost; the gated versions (issued only) use the same calibrated
  gate (alpha = 0.9), with the risk term scaled by the larger of the two task energies.
- CWM (raw) and CWM+SG: official code, variant local-search; green budget = idle + rel x frac x dynamic
  power. frac = 1.0, fixed by a development check on GB data (frac in {0.2, 0.4, 1.0}; 1.0 gave CWM
  the best oracle emission saving and the best native-objective saving; EXTENSION_NOTES.md section 3).
- CaWoSched is not run: its input format has no processor speeds.

## 5. Hypotheses (pooled over regions; 95% cluster bootstrap over region x submission)
- **G1.** CA-LS+SG, f >= 1.5: upper bound of R = issued/oracle mean emission saving < 0.75.
- **G2.** CA-LS+SG, issued: trap1 lower bound > 2% at every f.
- **G3.** Gate: trap1 difference upper bound < 0 and saving retention lower bound >= 0.5.
- **G4.** CWM+SG, f >= 1.5: upper bound of R_native = issued/oracle mean native-objective saving < 0.75
  (the forecast loss also holds for a heterogeneity-aware scheduler on its own objective and platform).
- **G5.** With runtime noise, issued: CA-LS+SG miss rate - HEFT miss rate lower bound > 10 pp at every f.

**Descriptive:** savings of CWM, CWM+SG, CA-LS+SG and Shift on both metrics, oracle and issued, per
region; share of tasks on fast machines; heterogeneous vs homogeneous (seed 30 of the extension).

## 6. Sanity checks
1,600 jobs or a reported shortfall; no nominal deadline miss for safeguarded schedulers; oracle trap
rate 0 for every safeguarded scheduler; every CWM schedule valid or replaced by HEFT (count reported).
