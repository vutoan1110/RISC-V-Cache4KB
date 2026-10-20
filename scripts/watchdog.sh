#!/usr/bin/env bash
# Ten-minute watchdog over both pipelines.
#
# Emits one compact status line per pipeline per tick, and an ALERT line the
# moment a pipeline has no live process while its work is unfinished -- which is
# the failure mode that matters, because a silently dead job looks exactly like
# a slow one. Also flags a stall: the same step for more than 50 minutes.
set -uo pipefail
R=/e/Projects/RISCV-research
[ -d "$R" ] || R=/mnt/e/Projects/RISCV-research
TICK=${TICK:-600}
# Newest chain log, not a fixed name. Each RTL change starts a new one.
chain_log () { ls -1t "$R"/results/fullchain_*.log 2>/dev/null | head -1; }
prev_pd=""; same_pd=0

while true; do
  now=$(date +%H:%M)
  CHAIN_LOG=$(chain_log)

  # ---- PD, 4 KiB ----
  R4=$R/asic/soc_dm_4kb/runs/synth4kb
  pd_alive=$(wsl.exe -d Ubuntu -e bash -c 'pgrep -cf "pd4kb_run|openlane --log-level" 2>/dev/null || echo 0' 2>/dev/null | tr -d ' ')
  pd_step=$(ls -1d "$R4"/*/ 2>/dev/null | grep -v '/tmp/$' | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr | head -1)
  pd_cpu=$(wsl.exe -d Ubuntu -e bash -c 'p=$(pgrep -f "bin/openroad" | head -1); [ -n "$p" ] && ps -o etimes=,times= -p $p 2>/dev/null || echo "0 0"' 2>/dev/null | tr -d '\r')
  pd_el=$(echo $pd_cpu | awk '{print $1+0}'); pd_ct=$(echo $pd_cpu | awk '{print $2+0}')
  pd_last=$(tail -1 "$R"/asic/pd4kb.log 2>/dev/null | tr -s ' ')
  if ls -1 "$R4"/*-misc-reportmanufacturability/state_out.json >/dev/null 2>&1; then
    echo "$now PD4K COMPLETE - Misc.ReportManufacturability wrote state_out.json"
  elif [ "${pd_alive:-0}" = "0" ]; then
    echo "$now PD4K ALERT dead at $pd_step  last=[$pd_last]"
  else
    if [ "${pd_el:-0}" -gt 600 ] && [ "$((pd_ct * 100 / (pd_el > 0 ? pd_el : 1)))" -lt 20 ]; then
      echo "$now PD4K ALERT stalled: ${pd_el}s wall, ${pd_ct}s cpu (<20%), step=$pd_step" 
    else
    echo "$now PD4K ok step=$pd_step last=[$pd_last]"
    fi
  fi

  # ---- full verification chain at 4 KiB (finished; kept for reference) ----
  if false; then
  fc_last=$(grep -E '^########|pass [12]:|VERIFIED|FAIL' "$CHAIN_LOG" 2>/dev/null | tail -1 | tr -s ' ')
  fc_alive=$(tasklist 2>/dev/null | grep -ci 'vsim' || echo 0)
  # Liveness is not progress. A hung vsim keeps its process and this check
  # would have reported "ok" indefinitely -- exactly how a sweep sat stuck on
  # depthconv/SA2 for two hours before a 7,200-second timeout killed it. So
  # count simulation logs touched recently as well.
  fc_moved=$(find "$R"/results/ablation_logs -name '*.log' -mmin -15 2>/dev/null | wc -l)
  if grep -q '^######## fullchain done' "$CHAIN_LOG" 2>/dev/null; then
    echo "$now CHAIN COMPLETE"
  elif [ "${fc_alive:-0}" = "0" ]; then
    echo "$now CHAIN ALERT no vsim, last=[$fc_last]"
  elif echo "$fc_last" | grep -q 'Embench' && [ "${fc_moved:-0}" -eq 0 ]; then
    echo "$now CHAIN ALERT vsim alive but no simulation finished in 15min, last=[$fc_last]"
  else
    echo "$now CHAIN ok (+$fc_moved sims/15min) last=[$fc_last]"
  fi

  fi
  # ---- PD (1 KiB flow, stopped on instruction; kept for reference only) ----
  if false; then
  pd_alive=$(wsl.exe -d Ubuntu -e bash -c 'pgrep -cf "pd_retry|openlane --log-level" 2>/dev/null || echo 0' 2>/dev/null | tr -d '\r ')
  pd_step=$(ls -1d "$R"/asic/soc_dm_control/runs/sync_final/*/ 2>/dev/null \
            | grep -v '/tmp/$' | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr | head -1)
  pd_last=$(tail -1 "$R"/asic/pd_retry.log 2>/dev/null | tr -s ' ')
  done_pd=$(ls -1d "$R"/asic/soc_dm_control/runs/sync_final/*-misc-reportmanufacturability 2>/dev/null | wc -l)

  if [ "$done_pd" -gt 0 ]; then
    echo "$now PD  COMPLETE - Misc.ReportManufacturability present"
  elif [ "${pd_alive:-0}" = "0" ]; then
    echo "$now PD  ALERT dead, step=$pd_step last=[$pd_last]"
  else
    [ "$pd_step" = "$prev_pd" ] && same_pd=$((same_pd+1)) || same_pd=0
    prev_pd=$pd_step
    if [ "$same_pd" -ge 5 ]; then
      echo "$now PD  ALERT stalled ${same_pd}0min on $pd_step"
    else
      echo "$now PD  ok step=$pd_step last=[$pd_last]"
    fi
  fi

  fi

  # ---- Quartus / 4 KiB ----
  q=$(tasklist 2>/dev/null | grep -ci 'quartus_' || echo 0)
  q4_last=$(grep -E '^#####|LE=' "$R"/results/fpga_4kb.log 2>/dev/null | tail -1 | tr -s ' ')
  # Same reasoning for Quartus: a fit takes 7-15 minutes, so a log that has not
  # grown in 40 is stuck, not slow.
  q_age=$(( ($(date +%s) - $(stat -c %Y "$R"/results/fpga_4kb.log 2>/dev/null || echo 0)) / 60 ))
  if grep -q '^##### all done' "$R"/results/fpga_4kb.log 2>/dev/null; then
    echo "$now LE  COMPLETE - 4 KiB sweep finished"
  elif [ "${q:-0}" = "0" ]; then
    echo "$now LE  ALERT no quartus process, last=[$q4_last]"
  elif [ "$q_age" -ge 40 ]; then
    echo "$now LE  ALERT quartus alive but log idle ${q_age}min, last=[$q4_last]"
  else
    echo "$now LE  ok (log ${q_age}min old) last=[$q4_last]"
  fi

  sleep "$TICK"
done
