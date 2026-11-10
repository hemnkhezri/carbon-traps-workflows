# Carbon traps in carbon-aware workflow scheduling

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24055543.svg)](https://doi.org/10.5281/zenodo.24055543)

Code, sealed analysis plans, deviation logs and raw results for the article

> H. Khezri, M. Trik, *Mitigating Carbon Traps in Carbon-Aware Workflow Scheduling under Real Carbon-Intensity Forecasts*
> (submitted to Future Generation Computer Systems).

The study replays deadline-constrained WfCommons workflows against carbon-intensity forecasts that the Great Britain
grid operator actually issued (and CarbonCast model forecasts for four further grids). It covers our list and
local-search schedulers, whole-workflow shifting and the official code of CaWoSched and CWM.

## Repository layout

```
cwf/                    simulator, schedulers, difference-error gate, adapters, re-planning, scenarios (Python package)
confirm_config.json     sealed configuration shared by all studies
protocol/
  plans/                analysis plans, each committed before the results it governs
  deviations/           logged deviations from the plans
  summaries/            result summaries written after each study
scripts/                runners (run_*), analyses (analyse_*, gate_*, ...), exploratory checks (explore_*)
  figures/              scripts that draw every figure (make_fig*, style.py)
results/                raw per-run results (CSV)
reports/                analysis outputs quoted in the article
figures/                figures as PDF and PNG
logs/                   run logs
external/               pinned builds of and patch to CaWoSched and CWM
osf_registration/       registration of the winter replication
```

## Studies

| Study (article section) | Plan | Runner | Analysis | Raw results | Report |
|---|---|---|---|---|---|
| Pilot and gate design (5.3) | `protocol/plans/PREREG.md` | `scripts/run_pilot.py`, `scripts/tune_gate.py` | `scripts/analyse_pilot.py` | `results/pilot.csv`, `results/tune_gate.csv` | `reports/pilot_report.txt`, `reports/tune_gate.txt` |
| Main confirmatory study, GB (5.3, 6.1-6.5) | `protocol/plans/CONFIRM_PREREG.md` | `scripts/run_confirm.py` | `scripts/analyse_confirm.py`, `scripts/analyse_robust_stats.py` | `results/confirm.csv` | `reports/confirm_report.txt`, `reports/robust_stats_confirm.txt` |
| Generality extension, four grids (5.4, 6.6) | `protocol/plans/EXT_PREREG.md` | `scripts/run_extension.py` | `scripts/analyse_extension.py` | `results/extension.csv` | `reports/robust_stats_extension.txt` |
| Heterogeneous platform (5.5, 6.7) | `protocol/plans/EXT2_PREREG.md` | `scripts/run_hetero.py` | `scripts/analyse_hetero.py`, `scripts/analyse_robust_hetero.py` | `results/hetero.csv`, `results/het/` | `reports/robust_stats_hetero.txt`, `reports/flat_timing.txt` |
| Robustness study (5.6, 6.3-6.5) | `protocol/plans/EXT3_PREREG.md` | `scripts/run_revision.py` | `scripts/analyse_revision.py`, `scripts/analyse_r2.py` | `results/rev/` | `reports/revision_final.txt` |
| Risk-controlled planner pilots (6.4) | `protocol/plans/PILOT_RC_PREREG.md`, `PILOT_RC2_PREREG.md` | `scripts/run_pilot_rc.py`, `scripts/run_pilot_rc2.py` | `scripts/analyse_pilot_rc.py` | `results/pilot_rc*.csv` | `reports/pilot_rc*.txt` |
| ENTSO-E study, DE-LU and ES (5.7, 6.6) | `protocol/plans/EXT4_PREREG.md` | `scripts/download_entsoe.py`, `scripts/run_entsoe.py` | `scripts/analyse_entsoe.py`, `scripts/entsoe_kappa.py` | `results/entsoe_*.csv` | `reports/entsoe_report.txt` |
| Cluster-size sensitivity (7.4) | `protocol/plans/SENS_PLAN.md` | `scripts/run_sens.py` | `scripts/analyse_sens.py` | `results/sens_P*.csv` | `reports/sensitivity.txt` |

The plans are kept exactly as they were sealed, so file names inside them refer to the original flat layout
(for example `run_confirm.py` is now `scripts/run_confirm.py`).

## Data

- GB forecast vintages: public archive `nmpowell/carbon-intensity-forecast-tracking` (commit 578de5b). Clone it and pass
  its path as `ARCHIVE`.
- CarbonCast forecasts: public CarbonCast repository `carbonfirst/CarbonCast` (commit 12d6989).
- ENTSO-E Transparency Platform data: download with `scripts/download_entsoe.py` and your own API token;
  `data/entsoe/` holds the checksums of every file used.
- Run-to-run runtime variability: repeated executions in `wfcommons/WfInstances` (`results/emp_runtime_logratio.npy`).

## Reproducing

Run every script from the repository root.

```bash
pip install numpy pandas scipy matplotlib wfcommons==1.6
python scripts/run_confirm.py ARCHIVE results/confirm.csv     # main study (several hours on 2 cores)
python scripts/analyse_confirm.py results/confirm.csv         # sealed hypotheses H1-H5
python scripts/analyse_robust_stats.py confirm                # clustering by day and week, Holm correction
python scripts/figures/make_figures.py ARCHIVE                # figures
```

The other studies follow the same pattern (see the table above).

## Pre-registration and commit history

Each analysis plan was committed before the results it governs were computed. The commit hashes in Supplementary Table S8 of the
article (for example `55fff17`, the sealed confirmatory plan) can be checked with `git show <hash>`. The files were
moved into the folders above in a later commit; `git log --follow <file>` shows the full history of any file.

## Licence

MIT (code). Results and documentation: CC BY 4.0.
