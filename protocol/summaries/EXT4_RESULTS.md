# ENTSO-E study: results (EXT4_PREREG.md)

Run 10 Nov 2026 after sealing (410956e), on confirmatory files that match `data/entsoe/SHA256_confirm.txt`.
Full output: `reports/entsoe_report.txt`; kappa: `reports/entsoe_kappa.txt`. No deviations.

| Hypothesis | Estimate (95% CI) | Holm p | Verdict |
|---|---|---|---|
| X1 forecast loss, R < 1 | R = 0.907 [0.871, 0.935] | <0.001 | Supported |
| X2 traps > 2% at every f | 3.6 [1.9, 5.4]% at f = 1.2; 8.5-10.7% at f >= 1.5 | 0.033 | Not supported (lower bound 1.9% at f = 1.2) |
| X3 gate | -5.0 pp [-6.7, -3.5]; retention 0.90 [0.87, 0.94] | <0.001 | Supported |
| X4 R(DE-LU) > R(ES) | +0.083 [0.024, 0.151] | 0.010 | Supported |
| X5 misses vs HEFT > 10 pp | +38.5 to +48.0 pp | <0.001 | Supported |

Clustering by local day leaves every verdict unchanged (X4 Holm p = 0.022). Clustering by ISO week keeps
the intervals of X1, X3-X5 clear of their thresholds, but X4's Holm p rises to 0.040 (> 0.025).
The E1 criterion (R < 0.75) is not met on either zone (DE-LU 0.95, ES 0.86).
Confirmatory-year kappa: DE-LU 0.39, ES 0.68. R was lowest in spring on both zones (0.91 and 0.72).
