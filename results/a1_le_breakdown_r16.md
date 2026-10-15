# A1: logic cells per module, Cyclone IV E (EP4CE115), RTL r16, seed 2

Source: the archived fit reports results/fpga_points/r16_p1 and _p2 ("Fitter Resource Utilization by Entity"). Logic cells (LE) include each module's children. Pass 1 vs pass 2: identical on every row of every point.

The groups add up to about 1 % more than the fit total (last row): Quartus counts a logic cell that packs a LUT of one module with a register of another module in both modules.

| module | dm_4kb | sa2_4kb | vc4_4kb | sa2_4kb_fast | vc4_4kb_fast | dse_4kb | sa4_4kb |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU core, total | 6451 | 6644 | 6564 | 6471 | 6597 | 6552 | 6537 |
| - register file (32 x 32; flip-flops in R16, M9K from 6c4ccffd) | 1386 | 1494 | 1458 | 1408 | 1473 | 1449 | 1445 |
| - branch history table (256 x 2; flip-flops in R16, M9K + valid bits from 6c4ccffd) | 962 | 962 | 962 | 962 | 962 | 963 | 962 |
| - ALU incl. multiplier | 545 | 553 | 541 | 550 | 546 | 542 | 546 |
| - datapath (pipeline registers, forwarding, CSRs, other) | 3199 | 3274 | 3238 | 3185 | 3256 | 3235 | 3225 |
| - control, branch, hazard, extend, wrapper | 359 | 361 | 365 | 366 | 360 | 363 | 359 |
| I-cache | 2439 | 3963 | 4109 | 4195 | 4105 | 2835 | 4974 |
| D-cache (incl. victim buffer) | 1896 | 4159 | 4230 | 4534 | 4321 | 2953 | 5572 |
| cache AXI master | 238 | 241 | 240 | 240 | 240 | 241 | 240 |
| observability, total | 2356 | 2353 | 2543 | 2352 | 2541 | 2355 | 2355 |
| - APB system monitor (snapshot / APB view) | 1318 | 1315 | 1406 | 1314 | 1404 | 1317 | 1317 |
| - hardware performance counters | 1038 | 1038 | 1137 | 1038 | 1137 | 1038 | 1038 |
| main RAM controller (AXI, 16 KiB in M9K) | 144 | 142 | 142 | 141 | 144 | 141 | 141 |
| buses: AXI-Lite master, AXI-Lite to APB, address decoders | 334 | 335 | 335 | 333 | 333 | 333 | 333 |
| UART | 633 | 629 | 629 | 633 | 629 | 636 | 628 |
| timer | 178 | 181 | 179 | 178 | 178 | 177 | 178 |
| board I/O: display registers, LCD, 7-segment decoders | 261 | 266 | 261 | 258 | 263 | 260 | 263 |
| SoC glue (soc_top own logic) | 656 | 727 | 726 | 753 | 724 | 658 | 725 |
| board top own logic | 7 | 7 | 7 | 7 | 7 | 7 | 8 |
| TOTAL (fit) | 15440 | 19474 | 19812 | 19930 | 19927 | 16989 | 21821 |
| check: groups sum - total | 153 | 173 | 153 | 165 | 155 | 159 | 133 |

Registers / memory bits / M9K / DSP of the main blocks:

| module | dm_4kb | sa2_4kb | vc4_4kb | sa2_4kb_fast | vc4_4kb_fast | dse_4kb | sa4_4kb |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU core, total | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP | 2521 reg / 0 bit / 0 M9K / 8 DSP |
| I-cache | 1774 reg / 37888 bit / 5 M9K / 0 DSP | 2015 reg / 38144 bit / 10 M9K / 0 DSP | 2593 reg / 37888 bit / 5 M9K / 0 DSP | 2014 reg / 38144 bit / 10 M9K / 0 DSP | 2593 reg / 37888 bit / 5 M9K / 0 DSP | 1798 reg / 37888 bit / 5 M9K / 0 DSP | 1930 reg / 38400 bit / 20 M9K / 0 DSP |
| D-cache (incl. victim buffer) | 872 reg / 37888 bit / 5 M9K / 0 DSP | 1310 reg / 38144 bit / 10 M9K / 0 DSP | 1925 reg / 37888 bit / 5 M9K / 0 DSP | 1310 reg / 38144 bit / 10 M9K / 0 DSP | 1925 reg / 37888 bit / 5 M9K / 0 DSP | 1130 reg / 37888 bit / 5 M9K / 0 DSP | 1284 reg / 38400 bit / 20 M9K / 0 DSP |
| observability, total | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2242 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2242 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP |
| main RAM controller (AXI, 16 KiB in M9K) | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP |
| TOTAL (fit) | 8430 reg / 206848 bit / 26 M9K / 8 DSP | 9109 reg / 207360 bit / 36 M9K / 8 DSP | 10497 reg / 206848 bit / 26 M9K / 8 DSP | 9108 reg / 207360 bit / 36 M9K / 8 DSP | 10497 reg / 206848 bit / 26 M9K / 8 DSP | 8712 reg / 206848 bit / 26 M9K / 8 DSP | 8998 reg / 207872 bit / 56 M9K / 8 DSP |
