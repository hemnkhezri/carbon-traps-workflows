"""Sensitivity analyses (SENS_PLAN.md): cluster size and runtime-noise models. Day-clustered bootstrap for key numbers."""
import sys
import numpy as np, pandas as pd
d = pd.concat([pd.read_csv(f) for f in sys.argv[1:]])
FS = d.f >= 1.5
print("== S1 cluster size (issued; R for f >= 1.5; trap and miss over all f; miss with sigma 0.2, static executor)")
for P, x in d.groupby("P"):
    o = x[(x.sched == "CA-LS+SG") & (x.regime == "oracle") & (x.f >= 1.5)].saving.mean()
    line = [f"P={P:3d}: oracle saving (f>=1.5) {100*o:5.2f}%"]
    for s in ("CA-LS+SG", "CA-LS+SG+Gate", "CA-LS+SG+Res75", "Shift"):
        y = x[(x.sched == s) & (x.regime == "issued")]
        line.append(f"{s}: R {y[y.f>=1.5].saving.mean()/o:.2f}, trap {100*y.trap1.mean():.1f}%, miss {100*y['miss_ln0.2'].mean():.1f}%")
    h = x[(x.sched == "CA-LS+SG") & (x.regime == "issued")]
    line.append(f"HEFT miss {100*h['heft_miss_ln0.2'].mean():.1f}%")
    print("\n  ".join(line))
print("\n== S2 runtime noise (P = 8, issued, all f): miss rate %")
x = d[(d.P == 8) & (d.regime == "issued")]
cols = ["ln0.05", "ln0.1", "ln0.2", "ln0.4", "emp"]
print(f"{'':16s}" + "".join(f"{c:>9s}" for c in cols))
print(f"{'HEFT':16s}" + "".join(f"{100*x[x.sched=='CA-LS+SG'][f'heft_miss_{c}'].mean():9.1f}" for c in cols))
for s in ("CA-LS+SG", "CA-LS+SG+Gate", "CA-LS+SG+Res75", "Shift"):
    y = x[x.sched == s]; print(f"{s:16s}" + "".join(f"{100*y[f'miss_{c}'].mean():9.1f}" for c in cols))
