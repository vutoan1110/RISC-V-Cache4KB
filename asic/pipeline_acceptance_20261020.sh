#!/usr/bin/env bash
# 2026-10-20 acceptance pairs on RTL 6c4ccffd (owner: continue the open work; the rsztf sign-off was rejected for ss):
#   DM  config_R14_FINAL_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep.json   (development noor34_r1 signed clean, max_ss -6.755)
#   SA2 config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rcrep_rtl6c4c.json (development
#       rszctsall_r1 signed clean, max_ss -8.373, max_tt +0.616)
# Each run is one gated flow from step 1 with a fresh tag and the thresholds declared below (QUY_TRINH D / rule Q):
# P1 + P2 by run_gated_pd.sh with STOP_AFTER=p2 (a planned pause, same config), then detailed routing + sign-off part
# by run_gated_resume.sh ... drt. Schedule: at most ONE heavy phase (detailed routing or sign-off part) at a time; the
# P1 / P2 of the next run may overlap it (the 24 GB VM: ~10.5 GB detailed routing or ~13 GB sign-off peak + ~4.5 GB
# P1 / P2). After every passed p2 gate the ss proxy (asic/sta_query/ss_proxy.sh, global-route estimate) is logged,
# for information only. Order DM r1, SA2 r1, DM r2, SA2 r2 (r2 = the second execution of the same recipe).
# Re-running this script after an interruption skips finished runs and continues held ones; a run stopped in the
# middle of a phase is reported and left for a decision. Log-based waits only. Cooperative stop: asic/.abort_gated_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
O=/mnt/e/Projects/RISCV-research/results/acceptance_20261020
mkdir -p $O
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
aborted () { [ -e $A/.abort_gated_pd ]; }
cd $A
DMC=config_R14_FINAL_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep.json
S2C=config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rcrep_rtl6c4c.json
DES=(soc_dm_4kb soc_sa2_4kb soc_dm_4kb soc_sa2_4kb)
TAG=(dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_r1 sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rcrep_rtl6c4c_r1
     dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_r2 sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rcrep_rtl6c4c_r2)
CFG=($DMC $S2C $DMC $S2C)
HOLDMIN=(0 -0.5 0 -0.5)          # P2_MIN_HOLD: SA2 as its signed runs (pre-route hold repaired by the two-pass hold ECO)
N=${#TAG[@]}
held () { grep -q "HOLD $1 after P2" $LOG; }
p12_failed () { grep -q -E "(STOP|SKIP) $1 " $LOG && ! held $1; }
finished () { grep -q -E "SIGNOFF (CLEAN|FAILED) $1\$|STOP $1 in detailed routing|STOP $1 .*sign-off" $LOG; }
light () {   # P1 + P2 of item $1, then the ss proxy
    local i=$1 t=${TAG[$1]}
    P1_MIN_SETUP=0 P2_MIN_SETUP=0 P2_MIN_HOLD=${HOLDMIN[$i]} G5_UNLIMITED_LATE_PHASE=1 STOP_AFTER=p2 \
        ITEMS="${DES[$i]}:$t:${CFG[$i]}" bash run_gated_pd.sh > $O/${t}_p12_queue.out 2>&1
    if held $t; then
        bash $A/sta_query/ss_proxy.sh $A/${DES[$i]}/runs/$t $O/${t}_ss_proxy_grt.txt grt > /dev/null 2>&1
        say "NOTE ss proxy $t (information, post-GRT database, global-route estimate): $(grep -E '^SS_PROXY nom_' $O/${t}_ss_proxy_grt.txt | awk '{printf "%s %s, ", $2, $4}')"
    fi
}
heavy () {   # detailed routing + sign-off part of item $1
    local i=$1 t=${TAG[$1]}
    G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh ${DES[$i]} $t ${CFG[$i]} \
        "acceptance run: planned pause after the p2 gate (STOP_AFTER=p2, same config); heavy phases one at a time" drt \
        > $O/${t}_p34.out 2>&1
}
say "NOTE acceptance pipeline 2026-10-20 start: ${TAG[*]}"
ln=0; hn=0; lp=""; hp=""
while :; do
    aborted && { say "NOTE acceptance pipeline: abort flag, no new phase (running phases finish)"; wait; exit 0; }
    if [ -n "$lp" ] && ! kill -0 $lp 2>/dev/null; then lp=""; fi
    if [ -n "$hp" ] && ! kill -0 $hp 2>/dev/null; then hp=""; fi
    # next light phase: at most one run waiting for its heavy phases
    if [ -z "$lp" ] && [ $ln -lt $N ] && [ $((ln - hn)) -le 1 ]; then
        t=${TAG[$ln]}
        if [ -d ${DES[$ln]}/runs/$t ]; then
            say "NOTE acceptance pipeline: $t exists already, no new P1 / P2"
        else
            light $ln & lp=$!
        fi
        ln=$((ln + 1))
    fi
    # next heavy phase, in order
    if [ -z "$hp" ] && [ $hn -lt $ln ]; then
        t=${TAG[$hn]}
        if finished $t; then
            hn=$((hn + 1))
        elif held $t && ! grep -q "RESUME $t (acceptance run" $LOG; then
            heavy $hn & hp=$!
            hn=$((hn + 1))
        elif p12_failed $t; then
            say "NOTE acceptance pipeline: $t stopped in P1 / P2, no heavy phase"
            hn=$((hn + 1))
        elif grep -q "RESUME $t (acceptance run" $LOG; then
            say "NOTE acceptance pipeline: $t heavy phase started before an interruption and did not finish; left for a decision"
            hn=$((hn + 1))
        fi
    fi
    [ $hn -ge $N ] && [ -z "$hp" ] && [ -z "$lp" ] && break
    sleep 60
done
say "NOTE acceptance pipeline 2026-10-20 done"
