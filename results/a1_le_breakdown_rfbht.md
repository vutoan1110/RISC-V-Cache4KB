# A1: logic cells per module, Cyclone IV E (EP4CE115), RTL rfbht, seed 2

Source: the archived fit reports results/fpga_points/rfbht_p1 and _p2 ("Fitter Resource Utilization by Entity"). Logic cells (LE) include each module's children. Pass 1 vs pass 2: identical on every row of every point.

The groups add up to about 1 % more than the fit total (last row): Quartus counts a logic cell that packs a LUT of one module with a register of another module in both modules.

| module | dm_4kb | sa2_4kb | vc4_4kb | dse_4kb |
|---|---:|---:|---:|---:|
| CPU core, total | 3818 | 3886 | 3889 | 3912 |
| - register file (32 x 32; flip-flops in R16, M9K from 6c4ccffd) | 52 | 52 | 52 | 52 |
| - branch history table (256 x 2; flip-flops in R16, M9K + valid bits from 6c4ccffd) | 636 | 636 | 636 | 636 |
| - ALU incl. multiplier | 555 | 544 | 541 | 547 |
| - datapath (pipeline registers, forwarding, CSRs, other) | 2234 | 2301 | 2305 | 2327 |
| - control, branch, hazard, extend, wrapper | 341 | 353 | 355 | 350 |
| I-cache | 2446 | 3936 | 4108 | 2846 |
| D-cache (incl. victim buffer) | 1893 | 4161 | 4227 | 2949 |
| cache AXI master | 240 | 240 | 239 | 240 |
| observability, total | 2350 | 2353 | 2544 | 2352 |
| - APB system monitor (snapshot / APB view) | 1313 | 1315 | 1407 | 1314 |
| - hardware performance counters | 1038 | 1038 | 1137 | 1038 |
| main RAM controller (AXI, 16 KiB in M9K) | 144 | 141 | 144 | 141 |
| buses: AXI-Lite master, AXI-Lite to APB, address decoders | 332 | 336 | 334 | 333 |
| UART | 622 | 628 | 625 | 620 |
| timer | 177 | 173 | 177 | 179 |
| board I/O: display registers, LCD, 7-segment decoders | 262 | 263 | 265 | 261 |
| SoC glue (soc_top own logic) | 660 | 716 | 730 | 662 |
| board top own logic | 7 | 7 | 6 | 7 |
| TOTAL (fit) | 12815 | 16689 | 17130 | 14340 |
| check: groups sum - total | 136 | 151 | 158 | 162 |

Registers / memory bits / M9K / DSP of the main blocks:

| module | dm_4kb | sa2_4kb | vc4_4kb | dse_4kb |
|---|---:|---:|---:|---:|
| CPU core, total | 1289 reg / 2816 bit / 4 M9K / 8 DSP | 1289 reg / 2816 bit / 4 M9K / 8 DSP | 1289 reg / 2816 bit / 4 M9K / 8 DSP | 1289 reg / 2816 bit / 4 M9K / 8 DSP |
| I-cache | 1774 reg / 37888 bit / 5 M9K / 0 DSP | 2015 reg / 38144 bit / 10 M9K / 0 DSP | 2593 reg / 37888 bit / 5 M9K / 0 DSP | 1798 reg / 37888 bit / 5 M9K / 0 DSP |
| D-cache (incl. victim buffer) | 872 reg / 37888 bit / 5 M9K / 0 DSP | 1310 reg / 38144 bit / 10 M9K / 0 DSP | 1925 reg / 37888 bit / 5 M9K / 0 DSP | 1130 reg / 37888 bit / 5 M9K / 0 DSP |
| observability, total | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP | 2242 reg / 0 bit / 0 M9K / 0 DSP | 2047 reg / 0 bit / 0 M9K / 0 DSP |
| main RAM controller (AXI, 16 KiB in M9K) | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP | 96 reg / 131072 bit / 16 M9K / 0 DSP |
| TOTAL (fit) | 7198 reg / 209664 bit / 30 M9K / 8 DSP | 7877 reg / 210176 bit / 40 M9K / 8 DSP | 9265 reg / 209664 bit / 30 M9K / 8 DSP | 7480 reg / 209664 bit / 30 M9K / 8 DSP |
