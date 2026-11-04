"""Exploratory (R2-M2): does forecast error relative to intraday variability predict the forecast loss at
grid x month resolution, and does it beat simpler predictors? R per grid-month = mean issued / mean oracle saving
of CA-LS+SG (f >= 1.5). Predictors per grid-month, from the vintages used for planning (0-47 h):
 ratio = MAE / mean within-vintage SD of actual CI;  MAPE;  1 - Kendall tau (forecast vs actual within vintage);
 q90 of 6-h difference errors / mean within-vintage SD."""
import numpy as np, pandas as pd
from scipy.stats import kendalltau, spearmanr
from cwf.carboncast import load_carboncast
from cwf.data import load_national
def skill(fc, act):
    h = (fc.window_utc - fc.capture_utc) / 3600
    f = fc[(h >= 0) & (h < 47)].copy(); f["a"] = f.window_utc.map(act); f = f.dropna()
    f = f.drop_duplicates(["capture_utc", "window_utc"], keep="last")
    f["month"] = pd.to_datetime(f.capture_utc, unit="s").dt.to_period("M").astype(str)
    out = []
    for m, g in f.groupby("month"):
        caps = g.groupby("capture_utc")
        sd = caps.a.std().mean(); mae = (g.forecast - g.a).abs().mean(); mape = ((g.forecast - g.a).abs() / g.a).mean()
        taus, d6 = [], []
        for _, v in caps:
            if len(v) < 24 or v.a.std() == 0: continue
            taus.append(kendalltau(v.forecast, v.a)[0])
            F, A = v.forecast.to_numpy(), v.a.to_numpy(); L = 12
            if len(F) > L: d6.append(np.abs((F[:-L] - F[L:]) - (A[:-L] - A[L:])))
        out.append(dict(month=m, ratio=mae / sd, mape=mape, one_minus_tau=1 - np.nanmean(taus),
                        diff6_over_sd=np.quantile(np.concatenate(d6), 0.9) / sd))
    return pd.DataFrame(out)
S = []
for R in ["CISO", "DE", "ERCO", "PJM"]:
    s = skill(*load_carboncast("/home/claude/carbonfirst_CarbonCast", R)); s["region"] = R; S.append(s)
fc, act = load_national("/home/claude/nmpowell/carbon-intensity-forecast-tracking", ["2026-07", "2026-08", "2026-09", "2026-10"])
fc = fc[(fc.capture_utc % 21600) == 0]
s = skill(fc, act); s["region"] = "GB"; S.append(s)
S = pd.concat(S)
E = pd.read_csv("results/extension.csv"); C = pd.read_csv("results/confirm.csv"); C["region"] = "GB"
D = pd.concat([E, C]); D = D[(D.sched == "CA-LS+SG") & (D.f >= 1.5)]
D["month"] = pd.to_datetime(D.t0, unit="s").dt.to_period("M").astype(str)
p = D.pivot_table(index=["region", "month"], columns="regime", values="saving", aggfunc="mean")
n = D[D.regime == "issued"].groupby(["region", "month"]).t0.nunique().rename("subs")
R = (p.issued / p.oracle).rename("R").reset_index().merge(n.reset_index(), on=["region", "month"])
M = R.merge(S, on=["region", "month"]); M = M[M.subs >= 3]
print(M.round(3).to_string(index=False))
rng = np.random.default_rng(2026)
print(f"\n{len(M)} grid-months. Spearman correlation with R [95% bootstrap over grid-months]:")
for c in ["ratio", "mape", "one_minus_tau", "diff6_over_sd"]:
    r = spearmanr(M[c], M.R)[0]
    bs = [spearmanr(*M.iloc[rng.integers(0, len(M), len(M))][[c, "R"]].T.values)[0] for _ in range(2000)]
    print(f"  {c:15s} rho = {r:+.2f} [{np.nanpercentile(bs, 2.5):+.2f}, {np.nanpercentile(bs, 97.5):+.2f}]")
M.to_csv("results/skill_by_month.csv", index=False)
