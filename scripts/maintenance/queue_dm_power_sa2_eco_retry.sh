#!/usr/bin/env bash
# Foreground queue (2026-10-13), run from Git Bash in the repository root; it holds no detached process.
#   1. Paired exact-window activity power for DM from the verified capture pair
#      (results/gls_exact_dm_full_pair_retry_20261011.json). The earlier attempt
#      (results/activity_power_exact_dm_retry_20261011) stopped on its own memory guard, Windows free 5,323 MiB
#      < 6,000, after the vectorless STA; that directory is kept unchanged and the driver needs a new output dir.
#      Starts only when Windows has >= 7,000 MiB free (same threshold as run_dm_capture_power_retry.ps1).
#   2. One unchanged retry of the SA2 11.305 mm2 sign-off part (PostRouteHoldECO .. Checker.LVS) after the
#      native SIGSEGV in its post-ECO detailed route (asic/gated_pd.log NOTE of 2026-10-12 22:09 UTC), through the
#      existing P4 resource gate (WSL and Windows >= 15,000 MiB, asic/run_resource_gated_resume.sh).
# Stop before the next stage: touch asic/.abort_gated_pd
set -u
cd "$(dirname "$0")/../.."
win_free () { powershell.exe -NoProfile -NonInteractive -Command "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)" | tr -d '\r'; }
echo "$(date -Is) queue start; Windows free $(win_free) MiB"
until [ "$(win_free)" -ge 7000 ]; do
    [ -e asic/.abort_gated_pd ] && { echo "$(date -Is) abort flag before DM power"; exit 0; }
    sleep 60
done
echo "$(date -Is) DM exact-window power start; Windows free $(win_free) MiB"
python -B scripts/metrics/run_activity_power_exact.py --design DM \
    --capture-pass1 results/gls_exact_dm_full_p1_20261011/receipt.json \
    --capture-pass2 results/gls_exact_dm_full_p2_retry_20261011/receipt.json \
    --output results/activity_power_exact_dm_20261013 --run
echo "$(date -Is) DM exact-window power driver rc=$?"
[ -e asic/.abort_gated_pd ] && { echo "$(date -Is) abort flag before SA2 retry"; exit 0; }
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -e bash -c "cd /mnt/e/Projects/RISCV-research/asic && P4_RESOURCE_WAIT=1 bash run_resource_gated_resume.sh soc_sa2_4kb sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 config_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json 'one unchanged retry after the native SIGSEGV in the post-ECO detailed route (crashed-47 kept)' hold; echo rc=\$?"
echo "$(date -Is) queue end"
