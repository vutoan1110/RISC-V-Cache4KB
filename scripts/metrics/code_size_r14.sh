#!/usr/bin/env bash
# Code size of every R14 firmware image, for the unified metric table (NHAT_KY / rulebook K, 2026-09-30).
# Each image is rebuilt exactly as scripts/build_fw_r14.sh and scripts/build_upstream_fw.sh build it, with
# one addition: CC gets -save-temps=obj, which keeps the objects under their source names so the linker
# map (-Map=benchmark.map, already in the Makefile) says which source every byte comes from. The code is
# unchanged by that flag; the rebuilt benchmark_rv32.hex must be byte-identical to fw/<kernel>.hex, and a
# kernel whose hex differs is reported, not measured. Build products stay in sw/ only until `make clean`;
# none of them is a manifest file (scripts/rtl_manifest.py: EXTS and SKIP_FILES), so the RTL id holds.
# Maps and `size -A` outputs go to results/code_size_r14/; scripts/metrics/code_size_table.py turns them
# into results/code_size_r14.csv.
# Run in WSL: bash scripts/metrics/code_size_r14.sh
set -uo pipefail
cd "$(dirname "$0")/../../sw"
OUT=../results/code_size_r14
mkdir -p "$OUT"
CC_KEEP="riscv64-unknown-elf-gcc -save-temps=obj"
declare -A SCALE=(
    [aha-mont64]=13 [crc32]=5 [depthconv]=52 [edn]=3 [huffbench]=1 [matmult-int]=1
    [md5sum]=2 [nettle-sha256]=7 [slre]=4 [statemate]=60 [tarfind]=2 [ud]=54
)
: > "$OUT/status.txt"
one () {   # <image name> <make args...>
    local name=$1; shift
    make clean > /dev/null 2>&1
    rm -f ./*.o ./*.i ./*.s
    if ! make "$@" CC="$CC_KEEP" > "$OUT/$name.build.log" 2>&1; then
        echo "$name BUILD_FAIL" | tee -a "$OUT/status.txt"; return
    fi
    if cmp -s benchmark_rv32.hex "../fw/$name.hex"; then st=HEX_IDENTICAL; else st=HEX_DIFFERS; fi
    cp benchmark.map "$OUT/$name.map"
    riscv64-unknown-elf-size -A benchmark.elf > "$OUT/$name.size.txt"
    echo "$name $st" | tee -a "$OUT/status.txt"
}
for k in ramsweep; do   # the project's own Embench-style kernels were removed on 2026-09-30
    one "$k" BENCH="$k"
done
for k in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-sha256 slre statemate tarfind ud; do
    one "up_$k" MODE=upstream BENCH="$k" SCALE="${SCALE[$k]}"
done
make clean > /dev/null 2>&1
rm -f ./*.o ./*.i ./*.s
echo "[DONE] $(grep -c HEX_IDENTICAL "$OUT/status.txt") identical of $(wc -l < "$OUT/status.txt")"
