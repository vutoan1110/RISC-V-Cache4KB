#!/usr/bin/env bash
set -euo pipefail

# Reference setup commands only. Review install prefixes before running.
# Historical results do not claim that this helper script was executed.

sudo apt-get update
sudo apt-get install -y make git curl device-tree-compiler \
  libboost-regex-dev libboost-system-dev build-essential

mkdir -p "$HOME/.local/riscv"
if [ ! -d riscv-isa-sim ]; then
  git clone https://github.com/riscv-software-src/riscv-isa-sim.git
fi
mkdir -p riscv-isa-sim/build
cd riscv-isa-sim/build
../configure --prefix="$HOME/.local/riscv"
make -j"$(nproc)"
make install

echo 'Add $HOME/.local/riscv/bin to PATH, then verify with: spike --help'
echo 'For ACT4, follow the current upstream riscv-arch-test README.'
echo 'It requires mise/uv, UDB, a current RISC-V compiler, and Sail.'
