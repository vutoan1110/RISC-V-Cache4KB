#!/usr/bin/env bash
# Build Verilator into the user's tree. No sudo required.
#
# Questa's lint is clean on this RTL, but it does not report width truncation
# inside a module, which is the failure mode that has already cost two
# debugging cycles here. Verilator does, so it is worth the build.
set -uo pipefail

PREFIX=$HOME/tools/verilator
SRC=$HOME/tools/src/verilator

if [ -x "$PREFIX/bin/verilator" ]; then
    echo "already built: $($PREFIX/bin/verilator --version)"
    exit 0
fi

mkdir -p "$(dirname "$SRC")"
if [ ! -d "$SRC" ]; then
    git clone --depth 1 https://github.com/verilator/verilator.git "$SRC" 2>&1 | tail -2
fi

cd "$SRC"
autoconf              > /tmp/vtr_autoconf.log 2>&1 || { tail -20 /tmp/vtr_autoconf.log; exit 1; }
./configure --prefix="$PREFIX" > /tmp/vtr_conf.log 2>&1 || { tail -20 /tmp/vtr_conf.log; exit 1; }
make -j8              > /tmp/vtr_make.log 2>&1 || { tail -30 /tmp/vtr_make.log; exit 1; }
make install          > /tmp/vtr_inst.log 2>&1 || { tail -20 /tmp/vtr_inst.log; exit 1; }

"$PREFIX/bin/verilator" --version
