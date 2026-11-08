#!/bin/bash
# usage (from the repository root): scripts/run_ext_wave.sh CARBONCAST_DIR REGION:SEED ...
# runs sequentially and skips finished files
cd "$(dirname "$0")/.."; CC="$1"; shift; mkdir -p results/ext logs
for job in "$@"; do R=${job%:*}; S=${job#*:}; out=results/ext/${R}_${S}.csv
  [ -f "$out" ] && continue
  python3 scripts/run_extension.py "$CC" "$out.part" --source carboncast:$R --seeds $S --n-sub 20 > logs/ext_${R}_${S}.log 2>&1 && mv "$out.part" "$out"
done
