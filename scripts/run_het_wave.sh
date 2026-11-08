#!/bin/bash
# usage (from the repository root): scripts/run_het_wave.sh CARBONCAST_DIR REGION ...
cd "$(dirname "$0")/.."; CC="$1"; shift; mkdir -p results/het logs
for R in "$@"; do out=results/het/${R}_30.csv; [ -f "$out" ] && continue
  python3 scripts/run_hetero.py "$CC" "$out.part" --source carboncast:$R --seeds 30 --n-sub 20 > logs/het_${R}.log 2>&1 && mv "$out.part" "$out"
done
