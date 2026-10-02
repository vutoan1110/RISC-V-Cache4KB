#!/usr/bin/env bash
# SA2 / DM_VC4 ASIC builds (2026-09-30, FLOW_JOURNAL: SA2 and DM_VC4 ASIC builds): synthesis only
# (--to Yosys.Synthesis), before any PD run, to check what the netlists contain:
#   - macro count: 8 x 2 KiB RAM + 8 x 1 KiB cache expected in both (SA2: two lanes per macro;
#     DM_VC4: the never-written way-1 banks removed by synthesis);
#   - std-cell count and area from the synthesis statistics.
set -u
A=/mnt/e/Projects/RISCV-research/asic
cd $A
for d in soc_sa2_4kb:sa2_synth soc_vc4_4kb:vc4_synth; do
    des=${d%%:*}; tag=${d##*:}
    echo "$(date -Is) start $tag"
    ( bash run_pd_mk.sh $des $tag --to Yosys.Synthesis > $A/$tag.log 2>&1; echo "$(date -Is) end $tag rc=$?" ) &
done
wait
for d in soc_sa2_4kb:sa2_synth soc_vc4_4kb:vc4_synth; do
    des=${d%%:*}; tag=${d##*:}
    N=$A/$des/runs/$tag/06-yosys-synthesis/soc_asic_top.nl.v
    [ -f "$N" ] || { echo "$tag: no netlist"; continue; }
    echo "== $tag: $(grep -c 'sky130_sram_2kbyte_1rw1r_32x512_8 ' $N) x 2 KiB, $(grep -c 'sky130_sram_1kbyte_1rw1r_32x256_8 ' $N) x 1 KiB macro instances"
    grep -o 'sky130_sram_1kbyte_1rw1r_32x256_8 [^ ]*' $N | sort
done
