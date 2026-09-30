#!/usr/bin/env bash
# Reach global placement without re-running synthesis.
#
# ABC segfaults on this 90,767-gate netlist far more often than it survives --
# twelve consecutive failures after one success. Each attempt costs a minute and
# the netlist it would produce already exists: tag synth4kb step 06 completed,
# with both state_out.json and soc_asic_top.nl.v.
#
# So resume that tag from the step AFTER synthesis. Steps 07-12 are wreckage
# from an earlier `RESUME=1` without `--from`, which restarted the flow instead
# of resuming it; --from names the step explicitly so that wreckage is ignored.
#
# The die and macro placement changed since step 06 ran. That is intended:
# synthesis does not read DIE_AREA or MACRO_PLACEMENT_CFG, and every step from
# here on picks up the current config.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
MAX=${MAX:-10}
for n in $(seq 1 "$MAX"); do
  start=$(date +%s)
  RESUME=1 bash "$ASIC/run_pd.sh" soc_dm_4kb synth4kb \
      --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement \
      >/tmp/fp_good.log 2>&1
  rc=$?; el=$(( $(date +%s) - start ))
  if ls -1 "$ASIC/soc_dm_4kb/runs/synth4kb"/*-openroad-globalplacement/state_out.json >/dev/null 2>&1; then
    echo "[$n] rc=$rc ${el}s  reached GlobalPlacement"; exit 0
  fi
  last=$(ls -1d "$ASIC/soc_dm_4kb/runs/synth4kb"/*/ 2>/dev/null | grep -v '/tmp/$' \
         | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr | head -1)
  why=$(grep -oE "return code [0-9]+|Signal 11|MemoryError|GRT-[0-9]+|DPL-[0-9]+|ORD-[0-9]+|PSM-[0-9]+|error:" /tmp/fp_good.log 2>/dev/null | tail -1)
  printf '[%2d] rc=%-3s %4ds  at %-34s %s\n' "$n" "$rc" "$el" "${last:-?}" "${why:-}"
done
echo "gave up after $MAX attempts"; exit 1
