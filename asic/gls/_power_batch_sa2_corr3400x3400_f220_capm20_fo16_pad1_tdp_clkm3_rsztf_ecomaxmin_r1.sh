set -u
S=/mnt/e/Projects/RISCV-research/asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/59-openroad-stapostpnr
O=/mnt/e/Projects/RISCV-research/results/gls_power_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1
C=nom_tt_025C_1v80
bash /mnt/e/Projects/RISCV-research/asic/gls/sta_power.sh $S "" $C > $O/vectorless.power.p2.rpt 2>&1; echo "vectorless rc=$? $(grep -m1 '^Total' $O/vectorless.power.p2.rpt | tr -s ' ')"
for k in up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud; do
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 5000 ]; do sleep 60; done
  bash /mnt/e/Projects/RISCV-research/asic/gls/sta_power.sh $S $O/$k.pins.saif $C > $O/$k.power.p2.rpt 2>&1
  echo "$k rc=$? $(grep -m1 '^Total' $O/$k.power.p2.rpt | tr -s ' ')"
done