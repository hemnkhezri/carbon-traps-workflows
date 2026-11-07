// Revision-study sections (EXT3, seeds 10 and 11 of the main study; robustness analyses).
const rev63 = [H2("6.3 Re-planning on newer forecasts"), P("«REV63»"), P("«REV63B»")];


const rev64 = [
  P("«REV64»"),
  P("«REV64B»"),
  P("«REV64C»"),
  ...figure("fig_frontier.png", 600, 245,
    "**Fig. 6.** Carbon saving against the share of runs that are carbon traps. (a) Strategies on GB issued forecasts (robustness study, seeds 10–11, all f): the difference gate for α between 0.5 and 0.95, simpler gates, planning on an upper forecast quantile, re-planning, and whole-workflow shifting with and without the gate. Points towards the upper left are better. (b) The difference gate against two risk-controlled planners for α of 0.05, 0.10 and 0.20 (development data, pilot 2, 40 submissions; saving for f ≥ 1.5; exploratory). Intervals are given in Supplementary Table S4 and in the text."),
];

const rev65 = [
  H2("6.5 Deadlines under runtime variability"),
  P("«REV65»"),
  P("«REV65B»"),
  ...figure("fig6_deadline_tradeoff.png", 600, 220,
    "**Fig. 7.** Carbon saving and deadline risk with runtime noise (robustness study, GB issued forecasts, seeds 10–11). (a) Mean saving against the share of runs that miss the deadline, all f pooled; filled markers: static executor, hollow markers: reactive executor; the reserve variants plan against D′ = M + ρ(D − M) with ρ = 0.75 and 0.5. (b) Miss rate by deadline factor. Whiskers: 95% cluster-bootstrap intervals over calendar days."),
];
