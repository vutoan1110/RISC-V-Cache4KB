#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
out_dir="$repo_root/verification/results/directed"
mkdir -p "$out_dir"

gcc_bin="${RISCV_GCC:-riscv64-unknown-elf-gcc}"
objcopy_bin="${RISCV_OBJCOPY:-riscv64-unknown-elf-objcopy}"
objdump_bin="${RISCV_OBJDUMP:-riscv64-unknown-elf-objdump}"

"$gcc_bin" -march=rv32i_zmmul_zicsr -mabi=ilp32 -nostdlib -nostartfiles \
  -Wl,--no-relax -Wl,-T,"$repo_root/verification/directed/link.ld" \
  "$repo_root/verification/directed/directed_isa.S" \
  -o "$out_dir/directed_isa.elf"
"$objcopy_bin" -O binary "$out_dir/directed_isa.elf" "$out_dir/directed_isa.bin"
python3 "$repo_root/verification/scripts/bin_to_word_hex.py" \
  "$out_dir/directed_isa.bin" "$repo_root/verification/directed/directed_isa.hex"
"$objdump_bin" -d -M no-aliases,numeric "$out_dir/directed_isa.elf" \
  > "$out_dir/directed_isa.dis"
sha256sum "$repo_root/verification/directed/directed_isa.hex" \
  > "$out_dir/directed_isa.sha256"
