// Revision-study sections (EXT3, seeds 10 and 11 of the main study; robustness analyses).
const rev63 = [H2("6.3 Re-planning on newer forecasts"), P("«REV63»"), P("«REV63B»")];


const rev64 = [
  P("«REV64»"),
  P("«REV64B»"),
  P("«REV64C»"),
  ...figure("fig_frontier.png", 600, 245,
    "**Fig. 6.** Carbon saving against the share of runs that are carbon traps; points towards the upper left are better. (a) Strategies on GB issued forecasts (robustness study, seeds 10–11, all f): the difference gate for α from 0.5 to 0.95, simpler gates, an upper-quantile planner, re-planning and whole-workflow shifting. (b) The gate at α = 0.8–0.95 against two risk-controlled planners at target trap risks of 0.05–0.20 (development data, pilot 2, f ≥ 1.5; exploratory). Intervals: Supplementary Table S4."),
];

const rev65 = [
  H2("6.5 Deadlines under runtime variability"),
  P("«REV65»"),
  P("«REV65B»"),
  P("«REV65C»"),
  ...figure("fig6_deadline_tradeoff.png", 600, 220,
    "**Fig. 7.** Saving and deadline risk with runtime noise (robustness study, GB issued forecasts, seeds 10–11). (a) Mean saving against the share of missed deadlines, all f; filled: static executor, hollow: reactive executor; the reserves plan against D′ = M + ρ(D − M) with ρ = 0.75 and 0.5. (b) Miss rate by deadline factor. Whiskers: 95% cluster-bootstrap intervals over calendar days."),
];
