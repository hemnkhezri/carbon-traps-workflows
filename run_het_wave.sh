#!/bin/bash
cd /home/claude/carbon-wf-forecast
for R in "$@"; do out=results/het/${R}_30.csv; [ -f "$out" ] && continue
  python3 run_hetero.py /home/claude/carbonfirst_CarbonCast "$out.part" --source carboncast:$R --seeds 30 --n-sub 20 > logs/het_${R}.log 2>&1 && mv "$out.part" "$out"
done
