# Carbon traps in carbon-aware workflow scheduling

Code, sealed analysis plans, deviation logs and raw results for the article

> H. Khezri, M. Trik, *Mitigating Carbon Traps in Carbon-Aware Workflow Scheduling under Real Carbon-Intensity Forecasts* (submitted to Future Generation Computer Systems).

The study replays deadline-constrained WfCommons workflows against carbon-intensity forecasts that the Great Britain grid
operator actually issued (and CarbonCast model forecasts for four further grids), with our list and local-search
schedulers, whole-workflow shifting and the official code of CaWoSched and CWM.

## Layout
| Path | Content |
|---|---|
| `cwf/` | simulator, schedulers (HEFT, Shift, CA-List, CA-LS), difference-error gate, adapters for CaWoSched and CWM, re-planning, scenarios |
| `PREREG.md`, `CONFIRM_PREREG.md`, `EXT_PREREG.md`, `EXT2_PREREG.md`, `EXT3_PREREG.md`, `PILOT_RC*_PREREG.md`, `SENS_PLAN.md` | analysis plans, each committed before its results were computed (see `git log`) |
| `*_DEVIATIONS.md`, `*_RESULTS.md` | logged deviations and result summaries per study |
| `run_*.py` | runners (pilot, confirmatory, extension, heterogeneous platform, robustness, RC-CAS pilots, sensitivity) |
| `analyse_*.py`, `gate_coverage.py`, `skill_by_month.py`, `dag_stats.py`, `measure_overhead.py` | analyses |
| `results/` | raw per-run results (CSV) |
| `reports/` | analysis outputs quoted in the article |
| `figures/`, `make_fig*.py`, `figsrc/` | figures and the scripts that draw them |
| `manuscript/` | sources of the manuscript (docx build) |
| `osf_registration/` | registration of the winter replication |
| `external/` | adapters and pinned references to CaWoSched and CWM |

## Data
- GB forecast vintages: public archive `nmpowell/carbon-intensity-forecast-tracking` (commit 578de5b). Clone it and pass its path as `ARCHIVE`.
- CarbonCast forecasts: public CarbonCast repository (see `EXT_PREREG.md`).
- Run-to-run runtime variability: repeated executions in `wfcommons/WfInstances` (`results/emp_runtime_logratio.npy`).

## Reproducing
```bash
pip install numpy pandas scipy matplotlib wfcommons==1.6
python run_confirm.py ARCHIVE results/confirm.csv          # main study (several hours on 2 cores)
python analyse_confirm.py results/confirm.csv               # sealed hypotheses H1-H5
python analyse_robust_stats.py confirm                      # clustering by day/week, Holm
python make_figures.py ARCHIVE                              # figures
```
Other studies follow the same pattern (`run_extension.py`, `run_hetero.py`, `run_revision.py`, `run_sens.py`).

## Licence
MIT (code). Results and documentation: CC BY 4.0.
