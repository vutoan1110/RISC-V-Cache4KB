#!/usr/bin/env bash
# Is the lemon-graph GCC internal compiler error reproducible?
#
# It crashed in pass_copy_prop while compiling test/maps_test.cc. A compiler
# that segfaults on itself is either a compiler bug, in which case it fails in
# exactly the same place every time, or bad memory, in which case the crash
# wanders. That distinction matters more than lemon does, because this machine
# is now showing memory-corruption symptoms in three unrelated tool families:
# OpenROAD's odb (39 of 40 runs), GCC here, and Quartus (~8% Access Violations,
# recorded earlier in this project).
#
# Nix leaves no cached failure, so each run is a genuine rebuild.
set -uo pipefail
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
LEMON=/nix/store/xgywsyrqffbl04skzmnzz77w1fs8rscw-lemon-graph-1.3.1.drv
for i in 1 2; do
  echo "===== attempt $i $(date -Is) ====="
  if nix-store --realise "$LEMON" >/tmp/lemon_$i.out 2>&1; then
    echo "attempt $i: BUILT OK"
  else
    echo "attempt $i: FAILED at ->"
    grep -Eo 'test/CMakeFiles/[a-z_]+\.dir|internal compiler error|crash_signal|pass_[a-z_]+' /tmp/lemon_$i.out \
      | sort -u | tr '\n' ' '
    echo
  fi
done
