#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: second execution of the gold-context split techmap (rtl_t2.ys) into r2/, then
# the t1 extraction of the second replay; outputs are compared by sha256 with the first execution.
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec/mulproof/r2
Y=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys
sed -e 's|\.\./\.\./sec/gold_pre.il|../../../sec/gold_pre.il|' ../rtl_t2.ys > rtl_t2.ys
$Y -q -l rtl_t2.log rtl_t2.ys > /dev/null 2>&1; echo "r2 rtl_t2 rc=$?"
sed -e 's|\.\./synth_replay_t1/t1_iter1.il|../../synth_replay_t1b/t1_iter1.il|' ../t1_pure.ys > t1_pure.ys
$Y -q -l t1_pure.log t1_pure.ys > /dev/null 2>&1; echo "r2 t1_pure rc=$?"
sha256sum rtl_t2.il ../rtl_t2.il rtl_t2_ctx.aig ../rtl_t2_ctx.aig t1_ctx.aig ../t1_ctx.aig ../../synth_replay_t1b/t1_iter1.il ../../synth_replay_t1/t1_iter1.il
