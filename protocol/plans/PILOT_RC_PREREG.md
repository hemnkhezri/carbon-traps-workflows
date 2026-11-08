# Pilot: risk-controlled carbon-aware scheduling (RC-CAS) — go/no-go plan

Written before any RC-CAS result was computed. Development data only (GB, Mar 2023 - Feb 2024);
the confirmatory 2026 data are not used. Seeds 1-2, 10 submissions per seed, all 10 workflows, T in {4, 12} h,
f in {1.2, 1.5, 2.0, 3.0}; nominal runtimes.

## Method under test
Error bank: for submission t0, the error trajectories e_c(j) = A(c + j*30min) - F_c(c + j*30min), j = 0..95, of
vintages c captured between t0 - 7 d and t0 - 49 h (every 6th vintage, i.e. one per 3 h; all windows realised
before t0). Scenario k for the current vintage F (captured c0): I_k(w) = F(w) + e_k(j(w)), j(w) = (w - c0)/30min.
Candidates: HEFT; Shift; CA-LS+SG; CA-LS+SG+Gate at alpha 0.8, 0.9, 0.95; Shift+Gate(0.9); CA-LS+SG planned on
the bias-corrected forecast F + mean_k e_k. RC-CAS(a): among candidates whose scenario trap frequency
(#{k: C_k(s) > 1.01 C_k(HEFT)} + 1)/(K + 1) <= a, choose the one with the highest mean scenario saving
(HEFT always qualifies). Variants a = 0.05, 0.10, 0.20.

## Decision rule (fixed now)
S1 validity: realised trap rate (all f) of RC-CAS(0.10) <= 12% and of RC-CAS(0.05) <= 7%.
S2 usefulness: some RC-CAS(a) has a realised trap rate no higher than CA-LS+SG+Gate[0.9] (point estimate)
and a higher mean realised saving at f >= 1.5 by at least max(1 pp, 10% relative), with the lower bound of a
day-clustered paired bootstrap interval of the saving difference above 0.
GO if S1 and S2 hold; otherwise NO-GO for this method, reported as such.
