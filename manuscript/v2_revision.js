// Revision-study sections (EXT3, seeds 10 and 11 of the main study; robustness analyses).
const rev63 = [H2("6.3 Re-planning on newer forecasts"), P("«REV63»"), P("«REV63B»")];

const t5 = smallTable([
  ["Gate", "Saving (%)", "Traps (%)", "Δ saving vs gate (pp)", "Δ traps vs gate (pp)", "Misses (%)"],
  ["None", "8.31", "9.7", "—", "—", "44.0"],
  ["Difference, α = 0.5", "8.29 [6.60, 10.27]", "9.7 [6.6, 13.1]", "+1.37 [0.35, 2.54]", "+6.0 [3.6, 8.4]", "44.1"],
  ["Difference, α = 0.8", "7.79 [6.26, 9.52]", "5.5 [3.3, 7.9]", "+0.87 [0.37, 1.40]", "+1.7 [0.4, 3.3]", "29.9"],
  ["Difference, α = 0.9 (ours)", "6.92 [5.53, 8.52]", "3.7 [2.0, 5.7]", "0", "0", "23.4"],
  ["Difference, α = 0.95", "6.06 [4.60, 7.73]", "2.0 [0.7, 3.8]", "−0.86 [−1.14, −0.61]", "−1.7 [−2.8, −0.8]", "18.7"],
  ["Constant, α = 0.9", "6.14 [4.68, 7.83]", "4.1 [2.2, 6.1]", "−0.79 [−1.20, −0.42]", "+0.3 [−1.0, 1.7]", "21.6"],
  ["Level interval, α = 0.9", "4.82 [3.44, 6.46]", "0.6 [0.0, 1.7]", "−2.11 [−2.58, −1.69]", "−3.1 [−4.7, −1.7]", "12.8"],
  ["Deferral cap 6 h", "6.70 [5.16, 8.38]", "7.6 [4.7, 11.1]", "−0.23 [−1.33, 1.04]", "+3.9 [1.8, 6.3]", "28.6"],
], [2100, 1500, 1350, 1500, 1450, 1126], 4);

const rev64 = [
  P("«REV64»"),
  caption("**Table 6.** Alternative gates for CA-LS with safeguard (revision study, GB issued forecasts, seeds 10–11, all f pooled; 9,600 runs per gate). Δ: paired difference against the difference gate with α = 0.9. Misses: deadline misses with runtime noise, static executor. 95% cluster-bootstrap intervals over calendar days."),
  t5,
];

const rev65 = [
  H2("6.5 Deadlines under runtime variability"),
  P("«REV65»"),
  P("«REV65B»"),
  ...figure("fig6_deadline_tradeoff.png", 600, 220,
    "**Fig. 7.** Carbon saving and deadline risk with runtime noise (revision study, GB issued forecasts, seeds 10–11). (a) Mean saving against the share of runs that miss the deadline, all f pooled; filled markers: static executor, hollow markers: reactive executor; the reserve variants plan against D′ = M + ρ(D − M) with ρ = 0.75 and 0.5. (b) Miss rate by deadline factor. Whiskers: 95% cluster-bootstrap intervals over calendar days."),
];
