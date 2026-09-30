#!/usr/bin/env bash
set -euo pipefail

ACT4_ROOT=${ACT4_ROOT:-$HOME/tools/src/riscv-arch-test}
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
CONFIG_FILE="$SCRIPT_DIR/test_config.yaml"
WORK_DIR="$PROJECT_ROOT/verification/results/act4/work"

export PATH="$SCRIPT_DIR:$HOME/tools/riscv-gcc16/bin:$HOME/tools/riscv/bin:$HOME/.local/bin:/usr/bin:/bin"

cd "$ACT4_ROOT"
mise trust .mise.toml
make \
  CONFIG_FILES="$CONFIG_FILE" \
  EXTENSIONS=I,Zmmul \
  WORKDIR="$WORK_DIR" \
  DEBUG=True
