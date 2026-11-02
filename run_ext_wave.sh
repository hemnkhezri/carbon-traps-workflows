#!/bin/bash
# usage: run_ext_wave.sh REGION:SEED ...  (runs sequentially, skips finished files)
cd /home/claude/carbon-wf-forecast
for job in "$@"; do R=${job%:*}; S=${job#*:}; out=results/ext/${R}_${S}.csv
  [ -f "$out" ] && continue
  python3 run_extension.py /home/claude/carbonfirst_CarbonCast "$out.part" --source carboncast:$R --seeds $S --n-sub 20 > logs/ext_${R}_${S}.log 2>&1 && mv "$out.part" "$out"
done
