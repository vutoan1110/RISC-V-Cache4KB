# T6 verified ASIC subset: DM and SA2

This is a partial table, not the final three-configuration PPA result. DM_VC4 has not passed sign-off; SA2 minimum die is not proved. Activity power is included only where independent second STA evidence is verified.

## Sign-off and independent execution gate

| metric | DM | SA2 |
|---|---:|---:|
| Final sign-off, both runs | PASS / PASS | PASS / PASS |
| All non-runtime metrics, identical full key sets | 319 | 319 |
| Final netlist / DEF | byte-identical | byte-identical |
| nom / min / max SPEF | identical except DATE | identical except DATE |
| Route / Magic / KLayout DRC; all LVS differences; XOR; overlap; critical pins; antenna nets/pins | all zero | all zero |
| Setup every tt/ff; hold all 9 corners | PASS | PASS |

## Area and routing

| metric | DM | SA2 |
|---|---:|---:|
| Die mm2 | 10.628500 | 11.560000 |
| Core mm2 | 10.456500 | 11.384800 |
| Standard-cell area mm2 | 1.369600 | 1.471070 |
| Standard-cell count | 197878 | 215979 |
| Macro area mm2 | 3.802010 | 3.802010 |
| Total routed wire m | 6.585103 | 9.274499 |

## Timing: STAPostPNR WNS in ns, ss setup reported only

| metric | DM | SA2 |
|---|---:|---:|
| setup nom_tt_025C_1v80 | 1.894 | 1.118 |
| hold nom_tt_025C_1v80 | 0.186 | 0.152 |
| setup min_tt_025C_1v80 | 2.056 | 1.331 |
| hold min_tt_025C_1v80 | 0.174 | 0.129 |
| setup max_tt_025C_1v80 | 1.708 | 0.838 |
| hold max_tt_025C_1v80 | 0.190 | 0.175 |
| setup nom_ff_n40C_1v95 | 4.611 | 4.056 |
| hold nom_ff_n40C_1v95 | 0.023 | 0.021 |
| setup min_ff_n40C_1v95 | 4.811 | 4.262 |
| hold min_ff_n40C_1v95 | 0.021 | 0.020 |
| setup max_ff_n40C_1v95 | 4.399 | 3.803 |
| hold max_ff_n40C_1v95 | 0.020 | 0.020 |
| setup nom_ss_100C_1v60 | -6.897 | -7.304 |
| hold nom_ss_100C_1v60 | 0.588 | 0.364 |
| setup min_ss_100C_1v60 | -6.401 | -6.719 |
| hold min_ss_100C_1v60 | 0.571 | 0.380 |
| setup max_ss_100C_1v60 | -7.365 | -7.917 |
| hold max_ss_100C_1v60 | 0.599 | 0.473 |

## Buffer accounting

| metric | DM | SA2 |
|---|---:|---:|
| Flow timing-repair-buffer class | 24448 | 15240 |
| Flow clock-buffer class | 3658 | 4519 |
| Flow macro-pin-buffer count | 800 | 775 |
| Hold buffers inserted per post-route ECO pass | 39 | 139 + 11 |
| Final DEF buf + clkbuf masters | 25445 | 19037 |
| Final DEF inv + clkinv masters | 626 | 1168 |

Flow class counters and per-ECO insertions describe different stages and may overlap; do not sum them. The separate DEF census counts final physical cell masters, without inferring clock-net connectivity.

## Power: nom_tt_025C_1v80, sign-off RCX SPEF

| metric | DM | SA2 |
|---|---:|---:|
| Vectorless OpenSTA default activity, mW | 109.152 | 121.985 |
| GLS -> SAIF -> OpenSTA total, mW | pending independent second STA | 127.454..131.751; mean 129.644 |
| Activity dynamic, mW | pending independent second STA | 127.017..131.314; mean 129.207 |
| Activity leakage, mW | pending independent second STA | 0.437..0.437; mean 0.437 |
| Energy/instruction, pJ | pending independent second STA | 2847.993..7354.111; mean 4463.119 |

## Embench on current RTL 6c4ccffd: FPGA view, 12 kernels, both passes identical

| metric | DM | SA2 |
|---|---:|---:|
| Weighted CPI | 1.5136 | 1.6597 |
| I-cache hit % | 99.7028 | 99.6476 |
| D-cache read hit % | 99.1601 | 99.5920 |

ASIC power/EPI use ASIC-view cycles; the architectural rows use FPGA-view counters. SRAM timing models are TT only; ss/ff paths through SRAM retain that limitation.

Recipe notes: DM remains locked at config_R14_FINAL.json (density 55, CTS cluster 8, hold margins 0.03/0.02). SA2 retains cap margin 20, fanout 16, one-site padding, timing-driven placement, clock trunks on met3..5, resizer tt/ff and max_* then min_* hold ECO. Their measured rationales remain in NHAT_KY section 8; no new recipe is selected by this table.

Evidence and per-kernel unrounded values are in the companion JSON. Architecture source: results/rfbht_4kb_p{1,2}.csv. DM power second-pass plan: results/dm_activity_power_second_pass_preparation_20261009.json. DM_VC4 experiment plan: results/vc4_padding_hypothesis_20261009.md.
