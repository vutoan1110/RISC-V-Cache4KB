# FLOW_JOURNAL Incident 96: power_final3.ps1 generalised (design dir, upstream kernels, reference CSV).
# Activity-based power of a final netlist, the method of Incidents 83 / 91:
# (1) raw Questa SAIF -> driver-pin SAIF (Windows Python; WSL Python faults on this machine),
# (2) OpenSTA report_power at nom_tt with the run's RCX SPEF (sta_power.sh, WSL), vectorless first,
# (3) table with CPI / EPI from the measured window (power_csv.py <tag> <ref_csv> <config>).
#   .\power_cfg.ps1 -Design soc_dm_4kb -Tag r14F_A -Step 57-openroad-stapostpnr -Fill 55-openroad-fillinsertion `
#                   -RefCsv results\upstream_asic_r15_p1.csv -Config DM [-Pass 1]
# NB: PowerShell variables are case-insensitive: the kernel list is $Kernels, the loop variable $k.
param([string]$Design = "soc_dm_4kb", [string]$Tag, [string]$Step, [string]$Fill,
      [string]$RefCsv = "results\upstream_asic_r15_p1.csv", [string]$Config = "DM", [int]$Pass = 1)
$ErrorActionPreference = "Stop"
Set-Location E:\Projects\RISCV-research
$V = "\\wsl.localhost\Ubuntu\home\toanl\.volare\volare\sky130\versions\0fe599b2afb6708d281543108caf8310912f54af\sky130A\libs.ref\sky130_fd_sc_hd\lib\sky130_fd_sc_hd__tt_025C_1v80.lib"
$M = "asic\soc_dm_4kb\macros\lib"
$NL = "asic\$Design\runs\$Tag\$Fill\soc_asic_top.nl.v"
$O = "results\gls_power_$Tag"
$Kernels = "up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud".Split(" ")
if (-not (Test-Path $NL)) { throw "netlist not found: $NL" }
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
S=$W/asic/$Design/runs/$Tag/$Step
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
if ($Pass -eq 1) { python asic\gls\power_csv.py $Tag $RefCsv $Config }
