#!/usr/bin/env bash
# The derivation for OpenROAD 2024-12-08 (rev 87af90f7 -- the build that does
# NOT share 2.3.10's odb bindings) is already in the store, which means the
# flake was evaluated successfully earlier today while GitHub was still
# reachable. Evaluation is the part that needs api.github.com; building from an
# existing .drv does not, provided the sources or the outputs can be substituted.
#
# So: does the output already exist, and if not, can it be substituted from a
# cache that is reachable right now?
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
DRV=/nix/store/64pmcgp95cf4zq6mgy68v5acm6ir349l-openroad-2024-12-08.drv
echo "=== configured substituters ==="
grep -h 'substituters\|trusted-public-keys' /etc/nix/nix.conf ~/.config/nix/nix.conf 2>/dev/null
echo
echo "=== output path of the drv ==="
OUT=$(nix-store -q --outputs "$DRV" 2>&1)
echo "$OUT"
for o in $OUT; do [ -e "$o" ] && echo "EXISTS  $o" || echo "MISSING $o"; done
echo
echo "=== can it be substituted? (dry run, no build) ==="
timeout 180 nix-store --realise --dry-run "$DRV" 2>&1 | tail -20
