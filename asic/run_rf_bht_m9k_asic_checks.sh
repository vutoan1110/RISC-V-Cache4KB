#!/usr/bin/env bash
# Register file / BHT in M9K (2026-10-08, review A1), ASIC side of rule D. The change is FPGA-only (`ifndef
# __openlane__), so the ASIC view must be the R16 design:
#   1. token identity: regfile.v, bht_2bit.v, datapath.v preprocessed with the defines OpenLane gives Yosys
#      (__openlane__ __pnr__ PDK_sky130A SCL_sky130_fd_sc_hd), comments and white space dropped, new == R16
#      (R16 copies in asic/equiv/rf_bht_m9k/r16/, taken from git HEAD = manifest c09143ea)
#   2. OpenLane lint + synthesis of the DM chip from the snapshot rtl_rfbht (= rtl_r16 + the three files,
#      config_rfbht_synth.json), netlist compared byte for byte with the same flow on rtl_r16 (config_R16_synth.json,
#      run dm_synth_r16_r1 of the same day); the lint log goes through scripts/lint_baseline_check.py (Windows side).
#      The PD runs read RTL snapshots (asic/snapshots/), never hdl/: SA2 and DM_VC4 use rtl_r14, proved equal to R16
#      at FAST_HIT 0 (asic/equiv/r16_eq), so step 1 carries them to this RTL.
# Summary: asic/rf_bht_m9k_asic_checks.log. Cooperative stop between steps: touch asic/.abort_rf_bht_checks
A=/mnt/e/Projects/RISCV-research/asic
R=/mnt/e/Projects/RISCV-research
L=$A/rf_bht_m9k_asic_checks.log
: > $L
say () { echo "$(date -Is) $*" | tee -a $L; }
ram () { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }
gate () {
  for i in $(seq 1 120); do
    [ -f $A/.abort_rf_bht_checks ] && { say "abort flag"; exit 3; }
    [ "$(ram)" -ge "$1" ] && return 0
    sleep 60
  done
  say "gave up waiting for $1 MB (have $(ram))"; exit 4
}
fail=0
export VERILATOR_ROOT=$HOME/tools/src/verilator
VER=$VERILATOR_ROOT/bin/verilator
D="-D__openlane__ -D__pnr__ -DPDK_sky130A -DSCL_sky130_fd_sc_hd"
T=$(mktemp -d)
say "1. token identity of the ASIC view, new vs R16"
for f in hdl/regfile.v hdl/predictor/bht_2bit.v hdl/datapath.v; do
  b=$(basename $f)
  $VER -E -P $D $A/equiv/rf_bht_m9k/r16/$b 2>/dev/null | tr -s ' \t\r\n' ' ' > $T/old_$b
  $VER -E -P $D $R/$f 2>/dev/null | tr -s ' \t\r\n' ' ' > $T/new_$b
  if [ -s $T/old_$b ] && cmp -s $T/old_$b $T/new_$b; then
    say "   $b: IDENTICAL ($(wc -c < $T/new_$b) bytes of tokens)"
  else
    say "   $b: DIFFERENT"; fail=$((fail+1))
  fi
  # negative control: the FPGA view of the same file must differ from R16
  $VER -E -P $R/$f 2>/dev/null | tr -s ' \t\r\n' ' ' > $T/fpga_$b
  cmp -s $T/old_$b $T/fpga_$b && { say "   $b: negative control FAILED (FPGA view equals the R16 ASIC view)"; fail=$((fail+1)); } \
                              || say "   $b: negative control ok (the FPGA view differs)"
done
rm -rf $T
for spec in "$R/asic/snapshots/rtl_rfbht/hdl" ; do
  [ -f $A/.abort_rf_bht_checks ] && { say "abort flag"; exit 3; }
  for f in regfile.v predictor/bht_2bit.v datapath.v; do
    cmp -s $R/hdl/$f $spec/$f || { say "   snapshot rtl_rfbht: $f differs from hdl/"; fail=$((fail+1)); }
  done
done
gate 5000
say "2. soc_dm_4kb: OpenLane lint + synthesis dm_synth_rfbht_r1 (config_rfbht_synth.json, avail $(ram) MB)"
cd $A && CONFIG=config_rfbht_synth.json bash run_pd_mk.sh soc_dm_4kb dm_synth_rfbht_r1 --to Yosys.Synthesis > $A/dm_synth_rfbht_r1.log 2>&1
rc=$?; say "   flow rc=$rc"; [ $rc -eq 0 ] || fail=$((fail+1))
N=$A/soc_dm_4kb/runs/dm_synth_rfbht_r1/06-yosys-synthesis/soc_asic_top.nl.v
O=$A/soc_dm_4kb/runs/dm_synth_r16_r1/06-yosys-synthesis/soc_asic_top.nl.v
sha256sum $O $N | sed 's#^#   #' >> $L
if cmp -s $O $N; then say "   netlist == dm_synth_r16_r1 (R16) byte for byte"
else say "   netlist differs from dm_synth_r16_r1 (information: step 1 is the proof; Yosys names follow source lines)"; fi
say "done: $fail failure(s)"
exit $fail
