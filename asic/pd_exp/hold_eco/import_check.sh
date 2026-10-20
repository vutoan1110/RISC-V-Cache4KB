#!/usr/bin/env bash
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
cd /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb
nix-shell --option tarball-ttl 31536000 --pure /home/toanl/tools/src/openlane2/shell.nix --run \
  "PYTHONPATH=/mnt/e/Projects/RISCV-research/asic/openlane-local python3 /mnt/e/Projects/RISCV-research/asic/pd_exp/hold_eco/import_check.py $*"
