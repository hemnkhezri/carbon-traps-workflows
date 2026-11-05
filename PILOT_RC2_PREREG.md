# Pilot 2: RC-CAS v2 (chance-constrained local search) — go/no-go plan

Written before any v2 result was computed. Development data only (GB, Mar 2023 - Feb 2024), NEW seeds 3-4,
20 submissions per seed (40 submissions), all 10 workflows, T in {4, 12} h, f in {1.2, 1.5, 2.0, 3.0}.
Pilot 1 (seeds 1-2) found the risk control valid but no significant saving gain over the gate (NO-GO).

## Method (primary: RCv2, split scenarios)
Scenarios as in pilot 1 (error trajectories of past vintages). Split into half A (even index) and half B (odd).
On A: start from the candidate (HEFT, Shift, Shift+Gate, CA-LS+SG, gated CA-LS at 0.8/0.9/0.95, bias-corrected
CA-LS) with the lowest mean scenario cost among those with #traps_A <= m_A; then 2|V| local-search moves that
minimise the mean scenario cost subject to #traps_A <= m_A, with m = floor(alpha (K + 1) - 1).
Certify on B: keep the plan if #traps_B <= m_B, else use HEFT. alpha in {0.05, 0.10, 0.20}.
Secondary (reported, not used for the decision): RCv2-nosplit (all scenarios, no certification).

## Decision rule (same as pilot 1)
S1 validity: realised trap rate (all f) of RCv2(0.10) <= 12% and of RCv2(0.05) <= 7%.
S2 usefulness: some RCv2(alpha) has a realised trap rate no higher than CA-LS+SG+Gate[0.9] (point estimate) and a
higher mean realised saving at f >= 1.5 by at least max(1 pp, 10% relative), with the lower bound of a
day-clustered paired bootstrap interval of the saving difference above 0.
GO if S1 and S2 hold; otherwise NO-GO for the method paper on this approach.
