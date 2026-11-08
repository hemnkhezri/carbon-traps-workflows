# Deviations from EXT2_PREREG.md

1. **Exploratory addition: CaWoSched on the heterogeneous platform (added after the G1-G5 results were read).**
   The plan excluded CaWoSched because "its input format has no processor speeds". The CaWoSched paper itself
   models heterogeneous speeds, and because CaWoSched keeps a fixed mapping, each task can be given its duration on
   its mapped machine (heterogeneous HEFT). It was therefore runnable, and the exclusion reason was wrong. We run it
   now (`cwf/cawosched_het.py`, `explore_cawo_het.py`, same jobs, budget mapping as CWM, frac = 1.0) and report it
   as exploratory. It changes no pre-registered verdict.
