# Sensitivity analyses before submission (exploratory, descriptive; no decision rules)

Written before running. GB confirmatory data, seed 10 (30 submissions, all 10 workflows, T in {4, 12} h, f in {1.2..3.0}).

S1 Cluster size. P in {32, 64} (P = 8 is the main study). Schedulers: HEFT, Shift, CA-LS+SG, CA-LS+SG+Gate[diff0.9],
CA-LS+SG+Res75; regimes oracle and issued. Report R (f >= 1.5), trap rate, deadline misses (static executor, sigma 0.2).

S2 Runtime variability on P = 8. Same plans, executed with: lognormal sigma in {0.05, 0.1, 0.2, 0.4}; and an empirical
model that resamples run-to-run log-ratios of task runtimes measured in repeated executions of the same WfCommons
workflows (WfInstances, makeflow and pegasus traces with identical task sets; per-run log-ratio / sqrt(2); tasks >= 5 s;
results/emp_runtime_logratio.npy; per-workflow sigma 0.04-0.78, pooled SD 0.47, MAD-based 0.34).
Report miss rates of HEFT, CA-LS+SG, Gate, Res75 and Shift by noise model.
