# Quartus, all four seeds: results/fpga_points_r7r8_p1.csv

Every field `run_fpga_points.py` scrapes, for seeds 1-4. `spread` = max - min over the four seeds.

## dm_4kb

| Field | seed 1 | seed 2 | seed 3 | seed 4 | min | max | mean | spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| le | 15380 | 15425 | 15357 | 15363 | 15357 | 15425 | 1.538e+04 | 68 |
| le_margin | 4620 | 4575 | 4643 | 4637 | 4575 | 4643 | 4619 | 68 |
| comb | 13739 | 13739 | 13739 | 13739 | 13739 | 13739 | 1.374e+04 | 0 |
| regs | 8422 | 8422 | 8422 | 8422 | 8422 | 8422 | 8422 | 0 |
| mem_bits | 141312 | 141312 | 141312 | 141312 | 141312 | 141312 | 1.413e+05 | 0 |
| setup_slack | 1.275 | 1.34 | 1.246 | 2.174 | 1.246 | 2.174 | 1.509 | 0.928 |
| fmax | 53.4 | 53.59 | 53.32 | 56.1 | 53.32 | 56.1 | 54.1 | 2.78 |
| map_le | 17912 | 17912 | 17912 | 17912 | 17912 | 17912 | 1.791e+04 | 0 |
| map_comb | 13734 | 13734 | 13734 | 13734 | 13734 | 13734 | 1.373e+04 | 0 |
| map_regs | 8422 | 8422 | 8422 | 8422 | 8422 | 8422 | 8422 | 0 |
| le_comb_only | 6958 | 7003 | 6935 | 6941 | 6935 | 7003 | 6959 | 68 |
| le_reg_only | 1641 | 1686 | 1618 | 1624 | 1618 | 1686 | 1642 | 68 |
| le_comb_reg | 6781 | 6736 | 6804 | 6798 | 6736 | 6804 | 6780 | 68 |
| lut4 | 9130 | 9130 | 9130 | 9130 | 9130 | 9130 | 9130 | 0 |
| lut3 | 2633 | 2633 | 2633 | 2633 | 2633 | 2633 | 2633 | 0 |
| lut2 | 1976 | 1976 | 1976 | 1976 | 1976 | 1976 | 1976 | 0 |
| le_normal | 12061 | 12061 | 12061 | 12061 | 12061 | 12061 | 1.206e+04 | 0 |
| le_arith | 1678 | 1678 | 1678 | 1678 | 1678 | 1678 | 1678 | 0 |
| io_regs | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| labs | 1160 | 1170 | 1173 | 1171 | 1160 | 1173 | 1168 | 13 |
| pins | 81 | 81 | 81 | 81 | 81 | 81 | 81 | 0 |
| m9k | 18 | 18 | 18 | 18 | 18 | 18 | 18 | 0 |
| mem_impl_bits | 165888 | 165888 | 165888 | 165888 | 165888 | 165888 | 1.659e+05 | 0 |
| mult9 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 0 |
| plls | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| global_clocks | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| interconnect_avg_pct | 6.4 | 6.4 | 6.5 | 6.3 | 6.3 | 6.5 | 6.4 | 0.2 |
| interconnect_peak_pct | 44.2 | 47.1 | 48.7 | 48.2 | 44.2 | 48.7 | 47.05 | 4.5 |
| fanout_max | 8456 | 8456 | 8456 | 8456 | 8456 | 8456 | 8456 | 0 |
| fanout_max_nonglobal | 1026 | 1026 | 1026 | 1026 | 1026 | 1026 | 1026 | 0 |
| fanout_total | 84015 | 84067 | 84002 | 84025 | 84002 | 84067 | 8.403e+04 | 65 |
| fanout_avg | 3.55 | 3.55 | 3.55 | 3.55 | 3.55 | 3.55 | 3.55 | 0 |
| fmax_s85 | 53.4 | 53.59 | 53.32 | 56.1 | 53.32 | 56.1 | 54.1 | 2.78 |
| fmax_s0 | 58.7 | 58.67 | 58.63 | 61.48 | 58.63 | 61.48 | 59.37 | 2.85 |
| fmax_restricted_s85 | 53.4 | 53.59 | 53.32 | 56.1 | 53.32 | 56.1 | 54.1 | 2.78 |
| fmax_restricted_s0 | 58.7 | 58.67 | 58.63 | 61.48 | 58.63 | 61.48 | 59.37 | 2.85 |
| setup_s85_slack | 1.275 | 1.34 | 1.246 | 2.174 | 1.246 | 2.174 | 1.509 | 0.928 |
| setup_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s85_slack | 0.382 | 0.383 | 0.383 | 0.346 | 0.346 | 0.383 | 0.3735 | 0.037 |
| hold_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s85_slack | 15.853 | 16.484 | 16.029 | 16.308 | 15.853 | 16.484 | 16.17 | 0.631 |
| recovery_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s85_slack | 3.048 | 2.419 | 2.885 | 2.611 | 2.419 | 3.048 | 2.741 | 0.629 |
| removal_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s85_slack | 9.547 | 9.547 | 9.547 | 9.546 | 9.546 | 9.547 | 9.547 | 0.001 |
| mpw_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_s0_slack | 2.964 | 2.956 | 2.945 | 3.734 | 2.945 | 3.734 | 3.15 | 0.789 |
| setup_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s0_slack | 0.335 | 0.336 | 0.336 | 0.336 | 0.335 | 0.336 | 0.3358 | 0.001 |
| hold_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s0_slack | 16.261 | 16.865 | 16.421 | 16.673 | 16.261 | 16.865 | 16.55 | 0.604 |
| recovery_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s0_slack | 2.718 | 2.155 | 2.562 | 2.31 | 2.155 | 2.718 | 2.436 | 0.563 |
| removal_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s0_slack | 9.558 | 9.558 | 9.554 | 9.556 | 9.554 | 9.558 | 9.556 | 0.004 |
| mpw_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_f0_slack | 10.657 | 10.593 | 10.7 | 10.97 | 10.593 | 10.97 | 10.73 | 0.377 |
| setup_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_f0_slack | 0.167 | 0.172 | 0.172 | 0.139 | 0.139 | 0.172 | 0.1625 | 0.033 |
| hold_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_f0_slack | 17.803 | 18.11 | 17.875 | 18.027 | 17.803 | 18.11 | 17.95 | 0.307 |
| recovery_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_f0_slack | 1.588 | 1.294 | 1.513 | 1.375 | 1.294 | 1.588 | 1.442 | 0.294 |
| removal_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_f0_slack | 9.199 | 9.199 | 9.197 | 9.199 | 9.197 | 9.199 | 9.198 | 0.002 |
| mpw_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_setup_slack | 1.275 | 1.34 | 1.246 | 2.174 | 1.246 | 2.174 | 1.509 | 0.928 |
| mc_setup_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_hold_slack | 0.167 | 0.172 | 0.172 | 0.139 | 0.139 | 0.172 | 0.1625 | 0.033 |
| mc_hold_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_recovery_slack | 15.853 | 16.484 | 16.029 | 16.308 | 15.853 | 16.484 | 16.17 | 0.631 |
| mc_recovery_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_removal_slack | 1.588 | 1.294 | 1.513 | 1.375 | 1.294 | 1.588 | 1.442 | 0.294 |
| mc_removal_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_mpw_slack | 9.199 | 9.199 | 9.197 | 9.199 | 9.197 | 9.199 | 9.198 | 0.002 |
| mc_mpw_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| unconstrained | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| clocks_constrained | 1/1 | 1/1 | 1/1 | 1/1 |  |  |  | same |
| pow_total_mw | 270.22 | 268.26 | 270.28 | 270.42 | 268.26 | 270.42 | 269.8 | 2.16 |
| pow_core_dyn_mw | 102.95 | 101.14 | 103.11 | 103.27 | 101.14 | 103.27 | 102.6 | 2.13 |
| pow_core_static_mw | 100.09 | 100.08 | 100.09 | 100.09 | 100.08 | 100.09 | 100.1 | 0.01 |
| pow_io_mw | 67.18 | 67.04 | 67.08 | 67.05 | 67.04 | 67.18 | 67.09 | 0.14 |
| pow_confidence | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data |  |  |  | same |
| pow_blk_m9k_mw | 3.09 | 2.84 | 2.79 | 2.75 | 2.75 | 3.09 | 2.867 | 0.34 |
| pow_blk_mult_mw | 1.6 | 1.53 | 1.71 | 1.52 | 1.52 | 1.71 | 1.59 | 0.19 |
| pow_blk_mult_out_mw | 0.19 | 0.26 | 0.28 | 0.23 | 0.19 | 0.28 | 0.24 | 0.09 |
| pow_blk_comb_mw | 37.87 | 36.15 | 37.5 | 36.38 | 36.15 | 37.87 | 36.98 | 1.72 |
| pow_blk_clkctrl_mw | 20.09 | 20.34 | 20.65 | 22.28 | 20.09 | 22.28 | 20.84 | 2.19 |
| pow_blk_reg_mw | 40.09 | 39.99 | 40.16 | 40.08 | 39.99 | 40.16 | 40.08 | 0.17 |
| pow_blk_io_mw | 32.41 | 32.27 | 32.3 | 32.28 | 32.27 | 32.41 | 32.31 | 0.14 |
| pow_clk_dyn_mw | 101.36 | 99.61 | 101.41 | 101.76 | 99.61 | 101.76 | 101 | 2.15 |
| pow_noclk_dyn_mw | 1.6 | 1.53 | 1.71 | 1.52 | 1.52 | 1.71 | 1.59 | 0.19 |
| cur_vccint_ma | 115.15 | 113.63 | 115.28 | 115.41 | 113.63 | 115.41 | 114.9 | 1.78 |
| cur_vccio_ma | 14.03 | 13.99 | 14.0 | 13.99 | 13.99 | 14.03 | 14 | 0.04 |
| cur_vcca_ma | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 0 |
| cur_vccd_ma | 2.8 | 2.8 | 2.8 | 2.8 | 2.8 | 2.8 | 2.8 | 0 |
| pow_soc_mw | 82.77 | 80.72 | 82.37 | 80.92 | 80.72 | 82.77 | 81.7 | 2.05 |
| pow_core_mw | 40.79 | 40.28 | 40.89 | 40.18 | 40.18 | 40.89 | 40.53 | 0.71 |
| pow_icache_mw | 10.3 | 9.99 | 10.26 | 10.0 | 9.99 | 10.3 | 10.14 | 0.31 |
| pow_dcache_mw | 10.67 | 8.94 | 9.34 | 9.13 | 8.94 | 10.67 | 9.52 | 1.73 |
| pow_axi_master_mw | 1.32 | 1.4 | 1.37 | 1.46 | 1.32 | 1.46 | 1.387 | 0.14 |
| pow_axi_ram_mw | 1.27 | 1.27 | 1.3 | 1.32 | 1.27 | 1.32 | 1.29 | 0.05 |
| pow_axil2apb_mw | 1.58 | 1.77 | 1.71 | 1.8 | 1.58 | 1.8 | 1.715 | 0.22 |
| pow_observability_mw | 8.49 | 8.76 | 8.77 | 8.9 | 8.49 | 8.9 | 8.73 | 0.41 |
| pow_perf_counters_mw | 5.77 | 6.03 | 5.98 | 6.11 | 5.77 | 6.11 | 5.973 | 0.34 |
| pow_sysmon_mw | 2.72 | 2.73 | 2.8 | 2.8 | 2.72 | 2.8 | 2.763 | 0.08 |
| pow_uart_mw | 2.48 | 2.4 | 2.32 | 2.34 | 2.32 | 2.48 | 2.385 | 0.16 |

## dse_4kb

| Field | seed 1 | seed 2 | seed 3 | seed 4 | min | max | mean | spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| le | 16842 | 16921 | MISSING | MISSING |  |  |  | differs |
| le_margin | 3158 | 3079 | MISSING | MISSING |  |  |  | differs |
| comb | 15213 | 15213 | MISSING | MISSING |  |  |  | differs |
| regs | 8712 | 8712 | MISSING | MISSING |  |  |  | differs |
| mem_bits | 141312 | 141312 | MISSING | MISSING |  |  |  | differs |
| setup_slack | 1.297 | 0.928 | MISSING | MISSING |  |  |  | differs |
| fmax | 53.47 | 52.43 | MISSING | MISSING |  |  |  | differs |
| map_le | 19415 | 19415 | MISSING | MISSING |  |  |  | differs |
| map_comb | 15208 | 15208 | MISSING | MISSING |  |  |  | differs |
| map_regs | 8712 | 8712 | MISSING | MISSING |  |  |  | differs |
| le_comb_only | 8130 | 8209 | MISSING | MISSING |  |  |  | differs |
| le_reg_only | 1629 | 1708 | MISSING | MISSING |  |  |  | differs |
| le_comb_reg | 7083 | 7004 | MISSING | MISSING |  |  |  | differs |
| lut4 | 10663 | 10663 | MISSING | MISSING |  |  |  | differs |
| lut3 | 2643 | 2643 | MISSING | MISSING |  |  |  | differs |
| lut2 | 1907 | 1907 | MISSING | MISSING |  |  |  | differs |
| le_normal | 13535 | 13535 | MISSING | MISSING |  |  |  | differs |
| le_arith | 1678 | 1678 | MISSING | MISSING |  |  |  | differs |
| io_regs | 0 | 0 | MISSING | MISSING |  |  |  | differs |
| labs | 1278 | 1276 | MISSING | MISSING |  |  |  | differs |
| pins | 81 | 81 | MISSING | MISSING |  |  |  | differs |
| m9k | 18 | 18 | MISSING | MISSING |  |  |  | differs |
| mem_impl_bits | 165888 | 165888 | MISSING | MISSING |  |  |  | differs |
| mult9 | 8 | 8 | MISSING | MISSING |  |  |  | differs |
| plls | 0 | 0 | MISSING | MISSING |  |  |  | differs |
| global_clocks | 2 | 2 | MISSING | MISSING |  |  |  | differs |
| interconnect_avg_pct | 7.2 | 7.1 | MISSING | MISSING |  |  |  | differs |
| interconnect_peak_pct | 48.3 | 56.4 | MISSING | MISSING |  |  |  | differs |
| fanout_max | 8746 | 8746 | MISSING | MISSING |  |  |  | differs |
| fanout_max_nonglobal | 1026 | 1026 | MISSING | MISSING |  |  |  | differs |
| fanout_total | 90916 | 90984 | MISSING | MISSING |  |  |  | differs |
| fanout_avg | 3.58 | 3.57 | MISSING | MISSING |  |  |  | differs |
| fmax_s85 | 53.47 | 52.43 | MISSING | MISSING |  |  |  | differs |
| fmax_s0 | 58.6 | 57.63 | MISSING | MISSING |  |  |  | differs |
| fmax_restricted_s85 | 53.47 | 52.43 | MISSING | MISSING |  |  |  | differs |
| fmax_restricted_s0 | 58.6 | 57.63 | MISSING | MISSING |  |  |  | differs |
| setup_s85_slack | 1.297 | 0.928 | MISSING | MISSING |  |  |  | differs |
| setup_s85_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| hold_s85_slack | 0.369 | 0.384 | MISSING | MISSING |  |  |  | differs |
| hold_s85_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| recovery_s85_slack | 16.429 | 16.378 | MISSING | MISSING |  |  |  | differs |
| recovery_s85_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| removal_s85_slack | 2.475 | 2.548 | MISSING | MISSING |  |  |  | differs |
| removal_s85_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mpw_s85_slack | 9.546 | 9.548 | MISSING | MISSING |  |  |  | differs |
| mpw_s85_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| setup_s0_slack | 2.936 | 2.649 | MISSING | MISSING |  |  |  | differs |
| setup_s0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| hold_s0_slack | 0.336 | 0.337 | MISSING | MISSING |  |  |  | differs |
| hold_s0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| recovery_s0_slack | 16.824 | 16.74 | MISSING | MISSING |  |  |  | differs |
| recovery_s0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| removal_s0_slack | 2.208 | 2.26 | MISSING | MISSING |  |  |  | differs |
| removal_s0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mpw_s0_slack | 9.555 | 9.558 | MISSING | MISSING |  |  |  | differs |
| mpw_s0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| setup_f0_slack | 10.628 | 10.397 | MISSING | MISSING |  |  |  | differs |
| setup_f0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| hold_f0_slack | 0.146 | 0.173 | MISSING | MISSING |  |  |  | differs |
| hold_f0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| recovery_f0_slack | 18.081 | 18.065 | MISSING | MISSING |  |  |  | differs |
| recovery_f0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| removal_f0_slack | 1.33 | 1.343 | MISSING | MISSING |  |  |  | differs |
| removal_f0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mpw_f0_slack | 9.2 | 9.2 | MISSING | MISSING |  |  |  | differs |
| mpw_f0_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mc_setup_slack | 1.297 | 0.928 | MISSING | MISSING |  |  |  | differs |
| mc_setup_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mc_hold_slack | 0.146 | 0.173 | MISSING | MISSING |  |  |  | differs |
| mc_hold_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mc_recovery_slack | 16.429 | 16.378 | MISSING | MISSING |  |  |  | differs |
| mc_recovery_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mc_removal_slack | 1.33 | 1.343 | MISSING | MISSING |  |  |  | differs |
| mc_removal_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| mc_mpw_slack | 9.2 | 9.2 | MISSING | MISSING |  |  |  | differs |
| mc_mpw_tns | 0.0 | 0.0 | MISSING | MISSING |  |  |  | differs |
| unconstrained | 0 | 0 | MISSING | MISSING |  |  |  | differs |
| clocks_constrained | 1/1 | 1/1 | MISSING | MISSING |  |  |  | differs |
| pow_total_mw | 283.59 | 283.87 | MISSING | MISSING |  |  |  | differs |
| pow_core_dyn_mw | 116.23 | 116.49 | MISSING | MISSING |  |  |  | differs |
| pow_core_static_mw | 100.29 | 100.29 | MISSING | MISSING |  |  |  | differs |
| pow_io_mw | 67.07 | 67.09 | MISSING | MISSING |  |  |  | differs |
| pow_confidence | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | MISSING | MISSING |  |  |  | differs |
| pow_blk_m9k_mw | 4.62 | 4.78 | MISSING | MISSING |  |  |  | differs |
| pow_blk_mult_mw | 2.17 | 1.76 | MISSING | MISSING |  |  |  | differs |
| pow_blk_mult_out_mw | 0.36 | 0.27 | MISSING | MISSING |  |  |  | differs |
| pow_blk_comb_mw | 44.58 | 40.32 | MISSING | MISSING |  |  |  | differs |
| pow_blk_clkctrl_mw | 20.08 | 24.38 | MISSING | MISSING |  |  |  | differs |
| pow_blk_reg_mw | 44.39 | 44.95 | MISSING | MISSING |  |  |  | differs |
| pow_blk_io_mw | 32.3 | 32.32 | MISSING | MISSING |  |  |  | differs |
| pow_clk_dyn_mw | 114.06 | 114.73 | MISSING | MISSING |  |  |  | differs |
| pow_noclk_dyn_mw | 2.17 | 1.76 | MISSING | MISSING |  |  |  | differs |
| cur_vccint_ma | 126.35 | 126.58 | MISSING | MISSING |  |  |  | differs |
| cur_vccio_ma | 14.0 | 14.0 | MISSING | MISSING |  |  |  | differs |
| cur_vcca_ma | 35.04 | 35.04 | MISSING | MISSING |  |  |  | differs |
| cur_vccd_ma | 2.81 | 2.81 | MISSING | MISSING |  |  |  | differs |
| pow_soc_mw | 96.08 | 92.03 | MISSING | MISSING |  |  |  | differs |
| pow_core_mw | 45.84 | 42.49 | MISSING | MISSING |  |  |  | differs |
| pow_icache_mw | 12.97 | 12.52 | MISSING | MISSING |  |  |  | differs |
| pow_dcache_mw | 15.82 | 15.79 | MISSING | MISSING |  |  |  | differs |
| pow_axi_master_mw | 1.5 | 1.5 | MISSING | MISSING |  |  |  | differs |
| pow_axi_ram_mw | 1.51 | 1.71 | MISSING | MISSING |  |  |  | differs |
| pow_axil2apb_mw | 1.73 | 1.73 | MISSING | MISSING |  |  |  | differs |
| pow_observability_mw | 8.87 | 8.44 | MISSING | MISSING |  |  |  | differs |
| pow_perf_counters_mw | 6.07 | 5.73 | MISSING | MISSING |  |  |  | differs |
| pow_sysmon_mw | 2.81 | 2.71 | MISSING | MISSING |  |  |  | differs |
| pow_uart_mw | 2.36 | 2.35 | MISSING | MISSING |  |  |  | differs |

## sa2_4kb

| Field | seed 1 | seed 2 | seed 3 | seed 4 | min | max | mean | spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| le | 19315 | 19346 | 19296 | 19261 | 19261 | 19346 | 1.93e+04 | 85 |
| le_margin | 685 | 654 | 704 | 739 | 654 | 739 | 695.5 | 85 |
| comb | 17538 | 17538 | 17538 | 17538 | 17538 | 17538 | 1.754e+04 | 0 |
| regs | 9109 | 9109 | 9109 | 9109 | 9109 | 9109 | 9109 | 0 |
| mem_bits | 141824 | 141824 | 141824 | 141824 | 141824 | 141824 | 1.418e+05 | 0 |
| setup_slack | 0.747 | 0.97 | 1.17 | 0.813 | 0.747 | 1.17 | 0.925 | 0.423 |
| fmax | 51.94 | 52.55 | 53.11 | 52.12 | 51.94 | 53.11 | 52.43 | 1.17 |
| map_le | 21820 | 21820 | 21820 | 21820 | 21820 | 21820 | 2.182e+04 | 0 |
| map_comb | 17531 | 17531 | 17531 | 17531 | 17531 | 17531 | 1.753e+04 | 0 |
| map_regs | 9109 | 9109 | 9109 | 9109 | 9109 | 9109 | 9109 | 0 |
| le_comb_only | 10206 | 10237 | 10187 | 10152 | 10152 | 10237 | 1.02e+04 | 85 |
| le_reg_only | 1777 | 1808 | 1758 | 1723 | 1723 | 1808 | 1766 | 85 |
| le_comb_reg | 7332 | 7301 | 7351 | 7386 | 7301 | 7386 | 7342 | 85 |
| lut4 | 12568 | 12568 | 12568 | 12568 | 12568 | 12568 | 1.257e+04 | 0 |
| lut3 | 3116 | 3116 | 3116 | 3116 | 3116 | 3116 | 3116 | 0 |
| lut2 | 1854 | 1854 | 1854 | 1854 | 1854 | 1854 | 1854 | 0 |
| le_normal | 15860 | 15860 | 15860 | 15860 | 15860 | 15860 | 1.586e+04 | 0 |
| le_arith | 1678 | 1678 | 1678 | 1678 | 1678 | 1678 | 1678 | 0 |
| io_regs | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| labs | 1437 | 1443 | 1448 | 1432 | 1432 | 1448 | 1440 | 16 |
| pins | 81 | 81 | 81 | 81 | 81 | 81 | 81 | 0 |
| m9k | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 0 |
| mem_impl_bits | 258048 | 258048 | 258048 | 258048 | 258048 | 258048 | 2.58e+05 | 0 |
| mult9 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 0 |
| plls | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| global_clocks | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| interconnect_avg_pct | 7.8 | 7.8 | 7.7 | 7.8 | 7.7 | 7.8 | 7.775 | 0.1 |
| interconnect_peak_pct | 55.8 | 49.9 | 48.9 | 43.1 | 43.1 | 55.8 | 49.42 | 12.7 |
| fanout_max | 9161 | 9161 | 9161 | 9161 | 9161 | 9161 | 9161 | 0 |
| fanout_max_nonglobal | 1026 | 1026 | 1026 | 1026 | 1026 | 1026 | 1026 | 0 |
| fanout_total | 101710 | 101742 | 101685 | 101685 | 101685 | 101742 | 1.017e+05 | 57 |
| fanout_avg | 3.6 | 3.59 | 3.6 | 3.6 | 3.59 | 3.6 | 3.597 | 0.01 |
| fmax_s85 | 51.94 | 52.55 | 53.11 | 52.12 | 51.94 | 53.11 | 52.43 | 1.17 |
| fmax_s0 | 56.32 | 57.45 | 58.15 | 57.39 | 56.32 | 58.15 | 57.33 | 1.83 |
| fmax_restricted_s85 | 51.94 | 52.55 | 53.11 | 52.12 | 51.94 | 53.11 | 52.43 | 1.17 |
| fmax_restricted_s0 | 56.32 | 57.45 | 58.15 | 57.39 | 56.32 | 58.15 | 57.33 | 1.83 |
| setup_s85_slack | 0.747 | 0.97 | 1.17 | 0.813 | 0.747 | 1.17 | 0.925 | 0.423 |
| setup_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s85_slack | 0.35 | 0.346 | 0.366 | 0.346 | 0.346 | 0.366 | 0.352 | 0.02 |
| hold_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s85_slack | 16.467 | 16.375 | 16.515 | 16.292 | 16.292 | 16.515 | 16.41 | 0.223 |
| recovery_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s85_slack | 2.426 | 2.557 | 2.389 | 2.625 | 2.389 | 2.625 | 2.499 | 0.236 |
| removal_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s85_slack | 9.546 | 9.547 | 9.547 | 9.547 | 9.546 | 9.547 | 9.547 | 0.001 |
| mpw_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_s0_slack | 2.244 | 2.594 | 2.802 | 2.574 | 2.244 | 2.802 | 2.554 | 0.558 |
| setup_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s0_slack | 0.335 | 0.337 | 0.337 | 0.337 | 0.335 | 0.337 | 0.3365 | 0.002 |
| hold_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s0_slack | 16.853 | 16.739 | 16.888 | 16.662 | 16.662 | 16.888 | 16.79 | 0.226 |
| recovery_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s0_slack | 2.156 | 2.262 | 2.131 | 2.331 | 2.131 | 2.331 | 2.22 | 0.2 |
| removal_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s0_slack | 9.556 | 9.555 | 9.556 | 9.556 | 9.555 | 9.556 | 9.556 | 0.001 |
| mpw_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_f0_slack | 10.341 | 10.643 | 10.519 | 10.397 | 10.341 | 10.643 | 10.47 | 0.302 |
| setup_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_f0_slack | 0.145 | 0.143 | 0.144 | 0.13 | 0.13 | 0.145 | 0.1405 | 0.015 |
| hold_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_f0_slack | 18.103 | 18.062 | 18.135 | 18.009 | 18.009 | 18.135 | 18.08 | 0.126 |
| recovery_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_f0_slack | 1.295 | 1.345 | 1.272 | 1.382 | 1.272 | 1.382 | 1.323 | 0.11 |
| removal_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_f0_slack | 9.199 | 9.199 | 9.199 | 9.201 | 9.199 | 9.201 | 9.2 | 0.002 |
| mpw_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_setup_slack | 0.747 | 0.97 | 1.17 | 0.813 | 0.747 | 1.17 | 0.925 | 0.423 |
| mc_setup_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_hold_slack | 0.145 | 0.143 | 0.144 | 0.13 | 0.13 | 0.145 | 0.1405 | 0.015 |
| mc_hold_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_recovery_slack | 16.467 | 16.375 | 16.515 | 16.292 | 16.292 | 16.515 | 16.41 | 0.223 |
| mc_recovery_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_removal_slack | 1.295 | 1.345 | 1.272 | 1.382 | 1.272 | 1.382 | 1.323 | 0.11 |
| mc_removal_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_mpw_slack | 9.199 | 9.199 | 9.199 | 9.201 | 9.199 | 9.201 | 9.2 | 0.002 |
| mc_mpw_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| unconstrained | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| clocks_constrained | 1/1 | 1/1 | 1/1 | 1/1 |  |  |  | same |
| pow_total_mw | 294.13 | 296.43 | 300.44 | 297.78 | 294.13 | 300.44 | 297.2 | 6.31 |
| pow_core_dyn_mw | 126.52 | 128.8 | 132.86 | 130.08 | 126.52 | 132.86 | 129.6 | 6.34 |
| pow_core_static_mw | 100.54 | 100.55 | 100.56 | 100.55 | 100.54 | 100.56 | 100.5 | 0.02 |
| pow_io_mw | 67.07 | 67.08 | 67.02 | 67.14 | 67.02 | 67.14 | 67.08 | 0.12 |
| pow_confidence | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data |  |  |  | same |
| pow_blk_m9k_mw | 8.69 | 8.82 | 8.7 | 9.21 | 8.69 | 9.21 | 8.855 | 0.52 |
| pow_blk_mult_mw | 1.56 | 1.74 | 2.19 | 1.66 | 1.56 | 2.19 | 1.788 | 0.63 |
| pow_blk_mult_out_mw | 0.23 | 0.25 | 0.27 | 0.33 | 0.23 | 0.33 | 0.27 | 0.1 |
| pow_blk_comb_mw | 46.1 | 46.39 | 50.02 | 47.94 | 46.1 | 50.02 | 47.61 | 3.92 |
| pow_blk_clkctrl_mw | 21.44 | 22.72 | 23.59 | 22.24 | 21.44 | 23.59 | 22.5 | 2.15 |
| pow_blk_reg_mw | 48.46 | 48.84 | 48.06 | 48.68 | 48.06 | 48.84 | 48.51 | 0.78 |
| pow_blk_io_mw | 32.29 | 32.31 | 32.25 | 32.35 | 32.25 | 32.35 | 32.3 | 0.1 |
| pow_clk_dyn_mw | 124.96 | 127.06 | 130.67 | 128.42 | 124.96 | 130.67 | 127.8 | 5.71 |
| pow_noclk_dyn_mw | 1.56 | 1.74 | 2.19 | 1.66 | 1.56 | 2.19 | 1.788 | 0.63 |
| cur_vccint_ma | 135.13 | 137.04 | 140.42 | 138.11 | 135.13 | 140.42 | 137.7 | 5.29 |
| cur_vccio_ma | 14.0 | 14.0 | 13.98 | 14.02 | 13.98 | 14.02 | 14 | 0.04 |
| cur_vcca_ma | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 0 |
| cur_vccd_ma | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 0 |
| pow_soc_mw | 105.01 | 105.99 | 109.17 | 107.78 | 105.01 | 109.17 | 107 | 4.16 |
| pow_core_mw | 40.74 | 42.05 | 43.82 | 43.09 | 40.74 | 43.82 | 42.42 | 3.08 |
| pow_icache_mw | 18.49 | 18.87 | 18.65 | 18.89 | 18.49 | 18.89 | 18.73 | 0.4 |
| pow_dcache_mw | 23.76 | 22.82 | 24.99 | 24.43 | 22.82 | 24.99 | 24 | 2.17 |
| pow_axi_master_mw | 1.54 | 1.46 | 1.26 | 1.45 | 1.26 | 1.54 | 1.427 | 0.28 |
| pow_axi_ram_mw | 1.58 | 1.75 | 1.54 | 1.53 | 1.53 | 1.75 | 1.6 | 0.22 |
| pow_axil2apb_mw | 1.74 | 1.76 | 1.71 | 1.8 | 1.71 | 1.8 | 1.752 | 0.09 |
| pow_observability_mw | 8.8 | 9.15 | 8.67 | 8.47 | 8.47 | 9.15 | 8.773 | 0.68 |
| pow_perf_counters_mw | 5.99 | 6.25 | 5.95 | 5.77 | 5.77 | 6.25 | 5.99 | 0.48 |
| pow_sysmon_mw | 2.8 | 2.9 | 2.72 | 2.7 | 2.7 | 2.9 | 2.78 | 0.2 |
| pow_uart_mw | 2.53 | 2.43 | 2.36 | 2.4 | 2.36 | 2.53 | 2.43 | 0.17 |

## vc4_4kb

| Field | seed 1 | seed 2 | seed 3 | seed 4 | min | max | mean | spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| le | 19742 | 19798 | 19817 | 19787 | 19742 | 19817 | 1.979e+04 | 75 |
| le_margin | 258 | 202 | 183 | 213 | 183 | 258 | 214 | 75 |
| comb | 17074 | 17074 | 17074 | 17074 | 17074 | 17074 | 1.707e+04 | 0 |
| regs | 10497 | 10497 | 10497 | 10497 | 10497 | 10497 | 1.05e+04 | 0 |
| mem_bits | 141312 | 141312 | 141312 | 141312 | 141312 | 141312 | 1.413e+05 | 0 |
| setup_slack | 1.133 | 1.132 | 1.358 | 1.364 | 1.132 | 1.364 | 1.247 | 0.232 |
| fmax | 53.0 | 53.0 | 53.64 | 53.66 | 53 | 53.66 | 53.32 | 0.66 |
| map_le | 22555 | 22555 | 22555 | 22555 | 22555 | 22555 | 2.256e+04 | 0 |
| map_comb | 17069 | 17069 | 17069 | 17069 | 17069 | 17069 | 1.707e+04 | 0 |
| map_regs | 10497 | 10497 | 10497 | 10497 | 10497 | 10497 | 1.05e+04 | 0 |
| le_comb_only | 9245 | 9301 | 9320 | 9290 | 9245 | 9320 | 9289 | 75 |
| le_reg_only | 2668 | 2724 | 2743 | 2713 | 2668 | 2743 | 2712 | 75 |
| le_comb_reg | 7829 | 7773 | 7754 | 7784 | 7754 | 7829 | 7785 | 75 |
| lut4 | 12283 | 12283 | 12283 | 12283 | 12283 | 12283 | 1.228e+04 | 0 |
| lut3 | 2640 | 2640 | 2640 | 2640 | 2640 | 2640 | 2640 | 0 |
| lut2 | 2151 | 2151 | 2151 | 2151 | 2151 | 2151 | 2151 | 0 |
| le_normal | 15303 | 15303 | 15303 | 15303 | 15303 | 15303 | 1.53e+04 | 0 |
| le_arith | 1771 | 1771 | 1771 | 1771 | 1771 | 1771 | 1771 | 0 |
| io_regs | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| labs | 1526 | 1515 | 1525 | 1493 | 1493 | 1526 | 1515 | 33 |
| pins | 81 | 81 | 81 | 81 | 81 | 81 | 81 | 0 |
| m9k | 18 | 18 | 18 | 18 | 18 | 18 | 18 | 0 |
| mem_impl_bits | 165888 | 165888 | 165888 | 165888 | 165888 | 165888 | 1.659e+05 | 0 |
| mult9 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 0 |
| plls | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| global_clocks | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| interconnect_avg_pct | 8.3 | 8.1 | 8.2 | 8.1 | 8.1 | 8.3 | 8.175 | 0.2 |
| interconnect_peak_pct | 47.2 | 51.2 | 48.0 | 52.7 | 47.2 | 52.7 | 49.78 | 5.5 |
| fanout_max | 10531 | 10531 | 10531 | 10531 | 10531 | 10531 | 1.053e+04 | 0 |
| fanout_max_nonglobal | 1122 | 1122 | 1122 | 1122 | 1122 | 1122 | 1122 | 0 |
| fanout_total | 104929 | 104966 | 105006 | 104970 | 104929 | 105006 | 1.05e+05 | 77 |
| fanout_avg | 3.5 | 3.49 | 3.49 | 3.49 | 3.49 | 3.5 | 3.493 | 0.01 |
| fmax_s85 | 53.0 | 53.0 | 53.64 | 53.66 | 53 | 53.66 | 53.32 | 0.66 |
| fmax_s0 | 57.37 | 57.95 | 59.05 | 59.0 | 57.37 | 59.05 | 58.34 | 1.68 |
| fmax_restricted_s85 | 53.0 | 53.0 | 53.64 | 53.66 | 53 | 53.66 | 53.32 | 0.66 |
| fmax_restricted_s0 | 57.37 | 57.95 | 59.05 | 59.0 | 57.37 | 59.05 | 58.34 | 1.68 |
| setup_s85_slack | 1.133 | 1.132 | 1.358 | 1.364 | 1.132 | 1.364 | 1.247 | 0.232 |
| setup_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s85_slack | 0.33 | 0.372 | 0.276 | 0.348 | 0.276 | 0.372 | 0.3315 | 0.096 |
| hold_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s85_slack | 16.317 | 16.344 | 16.348 | 16.386 | 16.317 | 16.386 | 16.35 | 0.069 |
| recovery_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s85_slack | 2.596 | 2.562 | 2.569 | 2.528 | 2.528 | 2.596 | 2.564 | 0.068 |
| removal_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s85_slack | 9.547 | 9.545 | 9.546 | 9.546 | 9.545 | 9.547 | 9.546 | 0.002 |
| mpw_s85_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_s0_slack | 2.568 | 2.744 | 3.066 | 3.051 | 2.568 | 3.066 | 2.857 | 0.498 |
| setup_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_s0_slack | 0.337 | 0.336 | 0.281 | 0.335 | 0.281 | 0.337 | 0.3223 | 0.056 |
| hold_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_s0_slack | 16.68 | 16.707 | 16.709 | 16.745 | 16.68 | 16.745 | 16.71 | 0.065 |
| recovery_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_s0_slack | 2.297 | 2.264 | 2.273 | 2.241 | 2.241 | 2.297 | 2.269 | 0.056 |
| removal_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_s0_slack | 9.557 | 9.553 | 9.555 | 9.556 | 9.553 | 9.557 | 9.555 | 0.004 |
| mpw_s0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| setup_f0_slack | 9.993 | 10.458 | 10.455 | 10.509 | 9.993 | 10.509 | 10.35 | 0.516 |
| setup_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| hold_f0_slack | 0.133 | 0.159 | 0.098 | 0.145 | 0.098 | 0.159 | 0.1338 | 0.061 |
| hold_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| recovery_f0_slack | 18.031 | 18.046 | 18.046 | 18.072 | 18.031 | 18.072 | 18.05 | 0.041 |
| recovery_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| removal_f0_slack | 1.365 | 1.351 | 1.349 | 1.333 | 1.333 | 1.365 | 1.35 | 0.032 |
| removal_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mpw_f0_slack | 9.199 | 9.197 | 9.199 | 9.2 | 9.197 | 9.2 | 9.199 | 0.003 |
| mpw_f0_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_setup_slack | 1.133 | 1.132 | 1.358 | 1.364 | 1.132 | 1.364 | 1.247 | 0.232 |
| mc_setup_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_hold_slack | 0.133 | 0.159 | 0.098 | 0.145 | 0.098 | 0.159 | 0.1338 | 0.061 |
| mc_hold_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_recovery_slack | 16.317 | 16.344 | 16.348 | 16.386 | 16.317 | 16.386 | 16.35 | 0.069 |
| mc_recovery_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_removal_slack | 1.365 | 1.351 | 1.349 | 1.333 | 1.333 | 1.365 | 1.35 | 0.032 |
| mc_removal_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| mc_mpw_slack | 9.199 | 9.197 | 9.199 | 9.2 | 9.197 | 9.2 | 9.199 | 0.003 |
| mc_mpw_tns | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| unconstrained | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| clocks_constrained | 1/1 | 1/1 | 1/1 | 1/1 |  |  |  | same |
| pow_total_mw | 301.05 | 296.42 | 297.92 | 300.35 | 296.42 | 301.05 | 298.9 | 4.63 |
| pow_core_dyn_mw | 133.44 | 128.82 | 130.31 | 132.76 | 128.82 | 133.44 | 131.3 | 4.62 |
| pow_core_static_mw | 100.56 | 100.53 | 100.54 | 100.55 | 100.53 | 100.56 | 100.5 | 0.03 |
| pow_io_mw | 67.06 | 67.06 | 67.07 | 67.05 | 67.05 | 67.07 | 67.06 | 0.02 |
| pow_confidence | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data | Low: user provided insufficient toggle rate data |  |  |  | same |
| pow_blk_m9k_mw | 4.94 | 4.84 | 4.51 | 4.68 | 4.51 | 4.94 | 4.742 | 0.43 |
| pow_blk_mult_mw | 2.27 | 1.78 | 1.74 | 2.33 | 1.74 | 2.33 | 2.03 | 0.59 |
| pow_blk_mult_out_mw | 0.28 | 0.26 | 0.3 | 0.3 | 0.26 | 0.3 | 0.285 | 0.04 |
| pow_blk_comb_mw | 49.55 | 44.9 | 44.17 | 48.08 | 44.17 | 49.55 | 46.67 | 5.38 |
| pow_blk_clkctrl_mw | 25.07 | 26.07 | 28.22 | 26.67 | 25.07 | 28.22 | 26.51 | 3.15 |
| pow_blk_reg_mw | 51.29 | 50.97 | 51.35 | 50.68 | 50.68 | 51.35 | 51.07 | 0.67 |
| pow_blk_io_mw | 32.29 | 32.27 | 32.29 | 32.28 | 32.27 | 32.29 | 32.28 | 0.02 |
| pow_clk_dyn_mw | 131.17 | 127.05 | 128.57 | 130.43 | 127.05 | 131.17 | 129.3 | 4.12 |
| pow_noclk_dyn_mw | 2.27 | 1.78 | 1.74 | 2.33 | 1.74 | 2.33 | 2.03 | 0.59 |
| cur_vccint_ma | 140.9 | 137.04 | 138.28 | 140.33 | 137.04 | 140.9 | 139.1 | 3.86 |
| cur_vccio_ma | 13.99 | 13.99 | 14.0 | 13.99 | 13.99 | 14 | 13.99 | 0.01 |
| cur_vcca_ma | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 35.04 | 0 |
| cur_vccd_ma | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 2.82 | 0 |
| pow_soc_mw | 108.28 | 102.67 | 102.02 | 106.02 | 102.02 | 108.28 | 104.7 | 6.26 |
| pow_core_mw | 48.3 | 42.15 | 42.05 | 45.91 | 42.05 | 48.3 | 44.6 | 6.25 |
| pow_icache_mw | 17.42 | 17.08 | 17.67 | 17.41 | 17.08 | 17.67 | 17.39 | 0.59 |
| pow_dcache_mw | 20.37 | 20.7 | 19.7 | 20.25 | 19.7 | 20.7 | 20.25 | 1 |
| pow_axi_master_mw | 1.53 | 1.36 | 1.27 | 1.24 | 1.24 | 1.53 | 1.35 | 0.29 |
| pow_axi_ram_mw | 1.48 | 1.59 | 1.48 | 1.38 | 1.38 | 1.59 | 1.483 | 0.21 |
| pow_axil2apb_mw | 1.68 | 1.78 | 1.8 | 1.76 | 1.68 | 1.8 | 1.755 | 0.12 |
| pow_observability_mw | 9.37 | 9.46 | 9.92 | 10.13 | 9.37 | 10.13 | 9.72 | 0.76 |
| pow_perf_counters_mw | 6.44 | 6.53 | 6.96 | 7.21 | 6.44 | 7.21 | 6.785 | 0.77 |
| pow_sysmon_mw | 2.94 | 2.93 | 2.96 | 2.92 | 2.92 | 2.96 | 2.938 | 0.04 |
| pow_uart_mw | 2.36 | 2.36 | 2.43 | 2.27 | 2.27 | 2.43 | 2.355 | 0.16 |

## Across configurations (mean of four seeds, [min, max])

| Field | dm_4kb | dse_4kb | sa2_4kb | vc4_4kb |
|---|---:|---:|---:|---:|
| le | 1.538e+04 [15357, 15425] | MISSING | 1.93e+04 [19261, 19346] | 1.979e+04 [19742, 19817] |
| regs | 8422 [8422, 8422] | MISSING | 9109 [9109, 9109] | 1.05e+04 [10497, 10497] |
| comb | 1.374e+04 [13739, 13739] | MISSING | 1.754e+04 [17538, 17538] | 1.707e+04 [17074, 17074] |
| m9k | 18 [18, 18] | MISSING | 28 [28, 28] | 18 [18, 18] |
| mult9 | 8 [8, 8] | MISSING | 8 [8, 8] | 8 [8, 8] |
| setup_s85_slack | 1.509 [1.246, 2.174] | MISSING | 0.925 [0.747, 1.17] | 1.247 [1.132, 1.364] |
| setup_s0_slack | 3.15 [2.945, 3.734] | MISSING | 2.554 [2.244, 2.802] | 2.857 [2.568, 3.066] |
| setup_f0_slack | 10.73 [10.593, 10.97] | MISSING | 10.47 [10.341, 10.643] | 10.35 [9.993, 10.509] |
| hold_f0_slack | 0.1625 [0.139, 0.172] | MISSING | 0.1405 [0.13, 0.145] | 0.1338 [0.098, 0.159] |
| fmax_restricted_s85 | 54.1 [53.32, 56.1] | MISSING | 52.43 [51.94, 53.11] | 53.32 [53, 53.66] |
| fmax_restricted_s0 | 59.37 [58.63, 61.48] | MISSING | 57.33 [56.32, 58.15] | 58.34 [57.37, 59.05] |
| pow_total_mw | 269.8 [268.26, 270.42] | MISSING | 297.2 [294.13, 300.44] | 298.9 [296.42, 301.05] |
| pow_core_dyn_mw | 102.6 [101.14, 103.27] | MISSING | 129.6 [126.52, 132.86] | 131.3 [128.82, 133.44] |
| pow_core_static_mw | 100.1 [100.08, 100.09] | MISSING | 100.5 [100.54, 100.56] | 100.5 [100.53, 100.56] |
| pow_io_mw | 67.09 [67.04, 67.18] | MISSING | 67.08 [67.02, 67.14] | 67.06 [67.05, 67.07] |

## Completeness gate

- FAIL: dse_4kb: seeds [1, 2], expected [1, 2, 3, 4]
