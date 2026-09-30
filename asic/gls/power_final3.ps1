# FLOW_JOURNAL Incident 91: activity-based power of a final netlist (same method as Incident 83 for final_A):
# (1) raw Questa SAIF -> driver-pin SAIF (Windows Python; WSL Python faults on this machine),
# (2) OpenSTA report_power at nom_tt with the run's RCX SPEF (sta_power.sh, WSL), vectorless first,
# NB: PowerShell variables are case-insensitive, so the kernel list must not be named like the loop
# variable ($K and $k are the same variable; the first version overwrote the list with the last kernel).
# (3) table with CPI/EPI from the measured window (power_csv.py).
#   .\power_final3.ps1 -Tag final3_A -Step 56-openroad-stapostpnr -Fill 53-openroad-fillinsertion [-Pass 1]
param([string]$Tag, [string]$Step, [string]$Fill, [int]$Pass = 1)
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research
$V = "\\wsl.localhost\Ubuntu\home\toanl\.volare\volare\sky130\versions\0fe599b2afb6708d281543108caf8310912f54af\sky130A\libs.ref\sky130_fd_sc_hd\lib\sky130_fd_sc_hd__tt_025C_1v80.lib"
$M = "asic\soc_dm_4kb\macros\lib"
$NL = "asic\soc_dm_4kb\runs\$Tag\$Fill\soc_asic_top.nl.v"
$O = "results\gls_power_$Tag"
$Kernels = "crc32 depthconv edn fdct huffbench insertsort matmult md5sum mont64 sha256 tarfind wikisort".Split(" ")
if ($Pass -eq 1) {
    foreach ($k in $Kernels) {
        if (Test-Path "$O\$k.pins.saif") { continue }   # redo only missing ones (retry after a machine fault)
        python asic\gls\saif_to_pins.py "$O\$k.raw.saif" $NL "$O\$k.pins.saif" $V "$M\sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib" "$M\sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib" *> "$O\$k.pins.log"
        "$k pins: $(Get-Content "$O\$k.pins.log" -TotalCount 1)"
    }
}
$W = "/mnt/e/Projects/RISCV-research"
$sfx = if ($Pass -eq 1) { "" } else { ".p$Pass" }
$bash = @"
set -u
S=$W/asic/soc_dm_4kb/runs/$Tag/$Step
O=$W/results/gls_power_$Tag
C=nom_tt_025C_1v80
bash $W/asic/gls/sta_power.sh `$S "" `$C > `$O/vectorless.power$sfx.rpt 2>&1; echo "vectorless rc=`$? `$(grep -m1 '^Total' `$O/vectorless.power$sfx.rpt | tr -s ' ')"
for k in $($Kernels -join ' '); do
  while [ "`$(free -m | awk '/Mem/{print `$7}')" -lt 5000 ]; do sleep 60; done
  bash $W/asic/gls/sta_power.sh `$S `$O/`$k.pins.saif `$C > `$O/`$k.power$sfx.rpt 2>&1
  echo "`$k rc=`$? `$(grep -m1 '^Total' `$O/`$k.power$sfx.rpt | tr -s ' ')"
done
"@
$bash | Set-Content -Encoding ascii -NoNewline "asic\gls\_power_batch_$Tag.sh"
(Get-Content "asic\gls\_power_batch_$Tag.sh" -Raw) -replace "`r`n", "`n" | Set-Content -Encoding ascii -NoNewline "asic\gls\_power_batch_$Tag.sh"
wsl.exe -d Ubuntu -e bash "$W/asic/gls/_power_batch_$Tag.sh"
if ($Pass -eq 1) { python asic\gls\power_csv.py $Tag }
