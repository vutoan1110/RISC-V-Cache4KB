#!/usr/bin/env bash
# 2026-10-20 SA2 acceptance pair on the development config config_..._rszctsall_rtl6c4c.json (LAYERS_RC_SCOPE
# repair_design): the rcrep pair is byte-identical but 0.4-0.5 ns worse at ss; the development run r1 of this file is not
# rule-Q compliant (continued past an undeclared p2 hold threshold). Fresh r2 and r3, the declared gates of
# pipeline_acceptance_20261020.sh (P1/P2 setup >= 0, P2 hold >= -0.5, STOP_AFTER=p2, G5_UNLIMITED_LATE_PHASE=1 in the
# heavy phase). Light phases start after the DM_VC4 r2 light phase (memory next to a detailed routing); heavy phases
# after pipeline_vc4_d34_20261020.sh, one at a time.
# Cooperative stop: touch asic/.abort_pipeline_sa2_acc (checked between phases; asic/.abort_gated_pd stops the flows).
set -u
cd /mnt/e/Projects/RISCV-research/asic
CFG=config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c.json
P=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c
VC4R2=vc4_corr3800x3400_f220_rszctsall_d34_rtl6c4c_r2
ABORT=.abort_pipeline_sa2_acc
say () { echo "$(date -u +%FT%T+00:00) $*" >> gated_pd.log; }
light () {
    local t=$1
    P1_MIN_SETUP=0 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 STOP_AFTER=p2 ITEMS="soc_sa2_4kb:$t:$CFG" bash run_gated_pd.sh \
        > queue_sa2_acc_${t##*_}_20261020.out 2>&1
    bash sta_query/ss_proxy.sh soc_sa2_4kb/runs/$t \
        /mnt/e/Projects/RISCV-research/results/acceptance_20261020/${t}_ss_proxy_grt.txt grt >> queue_sa2_acc_${t##*_}_20261020.out 2>&1
}
heavy () {
    local t=$1
    grep -q "HOLD $t after P2" gated_pd.log || { say "NOTE pipeline_sa2_acc: $t not held after P2, no heavy phase"; return 1; }
    G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_sa2_4kb $t $CFG \
        "acceptance run: planned pause after the p2 gate (STOP_AFTER=p2, same config); heavy phases one at a time" drt \
        > queue_sa2_acc_${t##*_}_drt_20261020.out 2>&1
}
say "NOTE pipeline_sa2_acc_20261020 start: ${P}_r2 / _r3 on $CFG; light after $VC4R2 p2, heavy after pipeline_vc4_d34"
until grep -q -E "(HOLD|STOP) $VC4R2|GATE $VC4R2 FAIL" gated_pd.log; do
    [ -e $ABORT ] && { say "NOTE pipeline_sa2_acc aborted before its light phases"; exit 1; }
    sleep 60
done
light ${P}_r2
[ -e $ABORT ] && { say "NOTE pipeline_sa2_acc aborted after ${P}_r2 light"; exit 1; }
light ${P}_r3 &
L3=$!
until grep -q -E "NOTE pipeline_vc4_d34_20261020 done|NOTE pipeline_vc4_d34 (aborted|:)" gated_pd.log; do
    [ -e $ABORT ] && { say "NOTE pipeline_sa2_acc aborted before its heavy phases"; exit 1; }
    sleep 60
done
heavy ${P}_r2
wait $L3
[ -e $ABORT ] && { say "NOTE pipeline_sa2_acc aborted before ${P}_r3 heavy"; exit 1; }
heavy ${P}_r3
say "NOTE pipeline_sa2_acc_20261020 done"
