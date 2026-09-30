#!/usr/bin/env bash
# nix-shell wants GitHub again (its flake-input tarball TTL expired), so call the
# openroad binary straight out of the store. It is the exact same executable the
# flow runs -- the path appears in every step-47 crash trace.
#
# Three arms, same workload, progressively less of the stack involved:
#   A  odb probe level 4      the failing step, for reference
#   B  pure python, openroad  same interpreter, odb removed
#   C  pure python, system    different interpreter entirely
set -uo pipefail
ASIC=/mnt/e/Projects/RISCV-research/asic
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
ODB=$ASIC/soc_dm_control/runs/sync_final/43-openroad-detailedrouting/soc_asic_top.odb
export OMP_NUM_THREADS=1 COLUMNS=200 LINES=50 TERM=xterm-256color

arm () { # name cmd... ; prints clean/8
  local name=$1; shift
  local ok=0; local line=""
  for i in $(seq 1 8); do
    out=$("$@" 2>&1); rc=$?
    if [[ $out == *_OK* ]]; then ok=$((ok+1))
    else
      s=other
      [[ $out == *'Signal 11'* ]] && s=SEGV
      [[ $out == *'CORRUPT'* ]]   && s=CORRUPT-DATA
      [[ $out == *Error* ]]       && s="${s}+pyerr"
      line="$line $s(rc$rc)"
    fi
  done
  echo "$name: clean=$ok/8 $line"
}

arm "A odb level4          " $OR -exit -no_splash -python $ASIC/probe_odb_iter.py $ODB 4
arm "B pure-py, openroad py" $OR -exit -no_splash -python $ASIC/probe_pure_python.py 1100000
arm "C pure-py, system py  " python3 $ASIC/probe_pure_python.py 1100000
