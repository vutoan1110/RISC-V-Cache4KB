#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96: synthesis only, WITH the openlane-local SYNTH_OPT_DFF_SAT patch.
#   sa2_synth2 / vc4_synth2 : the SA2 / DM_VC4 builds (config.json sets SYNTH_OPT_DFF_SAT) -- expect 8 cache
#                             macros each (vc4_synth without the pass had 12: the dead D-cache way-1 bank);
#   r14sat_synth            : DM with the same pass (config_R14_FINAL_sat.json), compared cell by cell with the
#                             synthesis of r14F_A (no pass), to measure what the pass changes on DM.
set -u
A=/mnt/e/Projects/RISCV-research/asic
cd $A
( bash run_pd_mk.sh soc_sa2_4kb sa2_synth2 --to Yosys.Synthesis > $A/sa2_synth2.log 2>&1; echo "$(date -Is) end sa2_synth2 rc=$?" ) &
( bash run_pd_mk.sh soc_vc4_4kb vc4_synth2 --to Yosys.Synthesis > $A/vc4_synth2.log 2>&1; echo "$(date -Is) end vc4_synth2 rc=$?" ) &
( CONFIG=config_R14_FINAL_sat.json bash run_pd_mk.sh soc_dm_4kb r14sat_synth --to Yosys.Synthesis > $A/r14sat_synth.log 2>&1; echo "$(date -Is) end r14sat_synth rc=$?" ) &
wait
for d in soc_sa2_4kb:sa2_synth2 soc_vc4_4kb:vc4_synth2 soc_dm_4kb:r14sat_synth soc_dm_4kb:r14F_A; do
    des=${d%%:*}; tag=${d##*:}
    R=$A/$des/runs/$tag/06-yosys-synthesis
    N=$R/soc_asic_top.nl.v
    [ -f "$N" ] || { echo "$tag: no netlist"; continue; }
    grep -q "SYNTH_OPT_DFF_SAT\": true" $R/config.json && s=on || s=off
    echo "== $tag (sat $s): $(grep -c 'sky130_sram_2kbyte_1rw1r_32x512_8 ' $N) x 2 KiB, $(grep -c 'sky130_sram_1kbyte_1rw1r_32x256_8 ' $N) x 1 KiB macros; $(python3 -c "
import json;m=json.load(open('$R/reports/stat.json'));d=m.get('design',m);print('cells', d.get('num_cells'), 'area', d.get('area'))" 2>/dev/null)"
done
