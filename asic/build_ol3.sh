#!/usr/bin/env bash
# Build OpenROAD 2024-12-08 (rev 87af90f7) straight from the derivation.
#
# Why this can work when the flake cannot: evaluating openlane-next/shell.nix
# needs api.github.com, which is unreachable from this machine right now (TCP
# connects, the TLS ClientHello goes out, no ServerHello ever comes back --
# same from Windows, so it is the network path, not WSL). But the derivation was
# already evaluated earlier today while GitHub was up, so it is in the store,
# and `nix-store --realise` on an existing .drv needs no evaluation. The dry run
# confirms it: two derivations to build, 154.6 MiB to fetch, and every fetch is
# from cache.nixos.org, which answers in 0.2 s.
#
# lemon-graph-1.3.1 is the one that failed last time, in `make check`. Building
# it first and alone, so its log is not buried under OpenROAD's.
set -uo pipefail
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
LEMON=/nix/store/xgywsyrqffbl04skzmnzz77w1fs8rscw-lemon-graph-1.3.1.drv
OR=/nix/store/64pmcgp95cf4zq6mgy68v5acm6ir349l-openroad-2024-12-08.drv

echo "=== lemon-graph $(date -Is) ==="
nix-store --realise "$LEMON" --keep-going 2>&1 | tail -40
echo "=== lemon rc=$? ==="

echo "=== openroad $(date -Is) ==="
nix-store --realise "$OR" 2>&1 | tail -60
echo "=== openroad rc=$? $(date -Is) ==="
