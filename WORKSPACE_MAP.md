# Ban do workspace va pham vi ket qua

Trang vao de hieu du an bang chuc nang thay vi so phien ban. Pham vi: ban nghien cuu
`E:/Projects/RISCV-research`; ban cong bo 1 KiB o thu muc khac chi doc. Khong sua manuscript.
Quy tac: QUY_TRINH.md. Trang thai cong viec: PROJECT_STATE.md. So lieu: RESULTS.md.
Lich su va bai hoc debug: NHAT_KY.md, dac biet muc 9. Bao cao kiem toan: 2026-10-09.

## 1. Doc theo nhu cau

| Can biet | File can doc |
|---|---|
| He thong hien tai la gi, so lieu nao con dung? | Trang nay, RESULTS.md, PROJECT_STATE.md |
| Moi y phan bien da xu ly toi dau? | REVIEW_RESPONSE.md, danh_gia.txt |
| Gui dong nghiep tai lieu nao? | results/colleague_materials_20261010.zip; README/SOURCE_ORIGINS/SHA trong goi |
| Lam the nao de chay / do / ky ten dung quy tac? | QUY_TRINH.md |
| Vi sao da chon knob / bo ung vien, loi cu debug the nao? | NHAT_KY.md muc 8, 9; archive run |
| Chuc nang tung file nguon / script / Markdown? | results/workspace_audit/SOURCE_CATALOG.md va source_catalog.json |
| Moi file, ke ca ignored/build/binary, nam dau? | results/workspace_audit/paths.jsonl va inventory.json |
| Da xoa chinh xac gi va giu bang chung o dau? | results/cleanup_deleted.txt; cleanup_execution.json; cache_cleanup.json |

Kiem ke truoc don: 73,861 file, 11,891 thu muc, khoang 254.6 GiB byte logic. Moi path
duoc liet ke; symlink/reparse point khong duoc theo ra ngoai workspace. Text nguon/config
duoc doc de trich heading, symbol va docstring; code va raw bang chung quan trong duoc
doi chieu rieng. Khong coi viec quet ten file la da doc / kiem chung moi byte cua binary,
PDK, tool ben thu ba hay hang tram GiB database PD. Danh muc tu dong la chi muc, khong
thay the review logic. Inventory sau don va ban truoc don duoc giu rieng.

## 2. Ban RTL hien tai va cac ten cu

Ten chuc nang de dung trong bao cao: **SoC RAM 16 KiB, RF/BHT trong M9K tren FPGA,
cache FAST_HIT tuy chon**. Fingerprint manifest la khoa tra cuu bang chung, khong phai
ten chuc nang hay thu tu phien ban.

| Ten cu | Thay doi co nghia | Con ap dung the nao |
|---|---|---|
| R14 | RAM chinh 8 -> 16 KiB; linker/stack/firmware va ramsweep theo RAM moi | Snapshot ten cu cho PD DM/SA2/VC4, khong phai RTL moi nhat |
| R15 | Them core cache N-way, SA4 va SA2N doi chung | Co trong RTL hien tai; ASIC chinh chi DM/SA2/VC4 |
| R16 | Them CACHE_FAST_HIT: main-array hit tra o LOOKUP, bo 1 chu ky rieng cua DSE/N-way | Mac dinh 0; ma tran FAST=1 la thi nghiem kien truc rieng, chua co ASIC FAST=1 |
| Thay doi 2026-10-08, sau R16 | RF va BHT FPGA sang M9K, read-ahead + bypass + valid-reset | Ban dang dung; giu nguyen tung chu ky, giam LE, khong giam CPI |
| R17 trong ghi chu cu | Alias cua thay doi R8 dong bo dau vao tu 2026-09-25 | Khong la ban tiep theo R16 FAST_HIT |
| R1..R16 trong dot 2026-09-24 | So hang muc sua RTL cua mot dot cu | Khong cung he so voi R14/R15/R16 cuoi thang |

Gia tri truoc/sau da do, cung seed 2: DM 15,440 -> 12,815 LE; RF 1,386 -> 52 LE;
BHT 962 -> 636 LE; them 4 M9K cho RF/BHT. Ket qua chi tiet va pham vi fit:
RESULTS.md muc 3. SA4/8-KiB-cache chua fit lai voi cai tien M9K; khong tron so LE cu
vao bang PPA cua bon diem 4 KiB hien tai.

SoC co pipeline 5 tang RV32I + Zmmul, forwarding/stall/redirect, BHT 256 entry x 2 bit,
cache I/D, AXI4 burst, posted-write buffer 2 entry, MMIO AXI-Lite -> APB, UART, timer,
LED/HEX/LCD, counter chu ky/su kien va snapshot. RAM chinh thong nhat 16 KiB, khong phai
hai RAM instruction/data 16 KiB rieng. D-cache write-through/no-write-allocate.
Tap CSR/timer IRQ/mret co gioi han; khong co synchronous exception day du hay DIV/REM.

Profile nghien cuu: moi cache 4 KiB = 256 line x 16 B, RAM 16 KiB, FAST_HIT=0 cho
bon diem board/ASIC chinh. HDL chung van mac dinh 64 line = 1 KiB; QSF va wrapper
chot profile, nen chi doc default trong soc_top.v se hieu sai diem dang do.

| CACHE_CONFIG | Ten | Cau truc |
|---:|---|---|
| 0 | DM | Direct mapped, I$ FSM 5 state / D$ 7 state |
| 1 | SA2 | 2 way tren DSE, I$ 10 state / D$ 11 state |
| 2 | DM_VC4 | Direct mapped + 4 victim entry tren DSE |
| 3 | DM_DSE | Direct mapped tren DSE de tach chi phi controller |
| 4 | SA4 | 4 way tren N-way, tree pseudo-LRU |
| 5 | SA2N | 2 way tren N-way de doi chung SA2; khong thuoc bon diem board chinh |

## 3. RTL va PD da khop toi dau?

| Cau hoi | Ket luan va bang chung |
|---|---|
| Tree hien tai co doi sau dong bang? | --check: 227 file IDENTICAL; khong rewrite manifest |
| RTL current co tuong duong snapshot R14 cua PD? | Co o FAST_HIT=0: proof SoC DM/SA2/VC4; sau M9K, ASIC token cua 3 file thay doi identical voi R16, co negative control |
| M9K co lam doi ASIC? | Khong tren ASIC view; synthesis DM truoc/sau M9K byte-identical. M9K chi FPGA |
| DM RTL -> netlist routed cuoi? | Legacy mapped SAT/CEC/algebra x2 va negative control con nguyen; full sequential reset/clock/invariant closure dang audit; PD sign-off hai luot |
| SA2 RTL -> netlist routed cuoi? | Chua co LEC cuoi. Co PD sign-off hai luot, N1 replay byte-exact, GLS 12 kernel; khong thay cho LEC |
| DM_VC4 RTL -> netlist routed cuoi? | Chua sign-off / LEC cuoi; baseline truot DRT, candidate padding12.24mm2 da route chinh DRC0 va dang xu ly antenna |
| Hai view co cung MCYCLE? | Khong: ASIC RAM wrapper khong co hook do tre FPGA. GLS doi chieu ASIC-view; board doi chieu FPGA-view |

Proof: asic/equiv/r16_eq/r16_eq_verdict.txt (29 checks, 0 FAIL), cac .status SoC;
asic/rf_bht_m9k_asic_checks.log; asic/equiv/rf_bht_m9k/run_live.log;
asic/equiv/lec/; results/asic_ppa_verified_subset_20261010.md/.json.
Gate DRC/LVS/antenna va tung corner phai PASS truoc khi dung PPA. Corner ss bao cao,
khong gate; cong suat SAIF dung nom_tt, khong lay power__total flow max_ff lam power tt.

Manifest chua phu top SA2/VC4 va adapter asic/dse_sram, cung khong phu SDC/config/.do/
fw_board/sw_metrics. Receipt results/workspace_audit/asic_input_provenance.json luu
42 input moi design va SHA hien tai. Hash quan sat hom nay khong tu chung minh lich su;
proof va resolved input cu van la bang chung goc. Firmware board/fit co receipt rieng.

## 4. UVM, Embench va cac gioi han kiem chung

Bang nay phan biet ket qua frozen da kiem toan voi cac luot kiem chung bo sung ngay 2026-10-09.

| Hang muc | Da xac nhan | Chua duoc ket luan |
|---|---|---|
| Regression | 178 dau PASS moi luot, x2; khong FAIL | PASS count khong thay cho coverage |
| UVM | 48 ca bo sung x2, scoreboard moi truong khop; 4 cache cfg, seed 1/2/3, RX hai byte, AXI stress 4 line size; doi chung sai byte bi bat | Functional coverage, chua code coverage; bo UVM frozen cu van la subset DM |
| Embench base | 72 dong moi pass, tat ca cot khop; 144 raw log khop CSV | 12 kernel vua RAM 16 KiB; khong full suite / official score |
| Embench FAST | 60 dong moi pass, tat ca cot khop; 120 raw log khop CSV | Khong suy ra PPA ASIC FAST_HIT=1 |
| ACT4 | 43/43 x2 qua adapter 1 MiB da sua, signature/cycles/retirements khop cu; them test data va instruction tren 512 KiB x2 va doi chung alias | Unprivileged I/Zmmul; TB frozen cu giu de truy nguon, runner moi generate correction rieng |
| Random differential | 50 seed x2 do lai voi gate rc/completion/full trace; moi byte khop cu, raw luu rieng hai pass | Cung core, khong oracle Spike doc lap; raw overwrite chi la gioi han evidence cua dot cu |
| Board reference | 100 case x2, toan bo 43 cot khop; input/firmware/compile/case hashes khop | Tham chieu simulation, khong phai da chay board |
| CoreMark | 92diem sweep hop le x2,184fresh simulation, CRC numeric+40counter khop2reference cu va raw audit doc lap; canonical DM x2 khop43cot | Window gom initialize/report; RAM32KiB, khong officialscore; SA4_256B_L16 khong hop le voi L0=8, khong la ket qua |

Embench harness warm-up ngoai window, chi do benchmark(), verify_benchmark(result)
AND voi counter invariant, report/UART ngoai window. Firmware routine simulation
giam iteration; fw_board/upfull_* la original iteration, tham chieu board hien tai da
do ca hai nhom x2. Khong build canonical voi BENCHMARK_FAST_UART.

Coverage/stress tong trong verification/uvm/out/ ngay 2026-09-18 la lich su. Current
evidence la results/uvm_rfbht* va results/uvm_cache_uart_20261009/; khong ghi coverage 100%. Chi tiet loi runner, CRC,
memory index, manifest va cach tranh lap lai nam duy nhat trong NHAT_KY.md muc 9.
RESULTS.md va REVIEW_RESPONSE.md da ghi ro cac gioi han nay.

## 5. Chuc nang thu muc

| Thu muc / nhom file | Chuc nang | Cach quan ly |
|---|---|---|
| hdl/ | RTL core, cache, buses, RAM, peripherals, counters, board top | Current, manifest khoa |
| tb/ | Unit/directed/integration benches, compile/regression | Current; diag/ la probe loi cu |
| verification/assertions, coverage, directed, random, diff | Assertion, functional coverage, ISA tests, random generator, ISS/trace reference | Source can giu; doc dung pham vi moi runner |
| verification/uvm/{intf,env,seq,test,tb} | Interface/driver/monitor/scoreboard/ISS/coverage, test/sequence va DUT adapter | Source current; out/ mix current va legacy |
| verification/architecture | ACT4 linker/target/Spike/signature infrastructure | Giu input; limitation chi TB frozen cu, maintained adapter44ca x2 da sua |
| verification/results | Raw verification logs/signatures/summaries | Bang chung, khong coi la build rac |
| sw/ | Harness/platform/linker/firmware C/S | Current; embench_upstream/coremark la nguon ben thu ba / port |
| fw/ | Canonical hex routine simulation, CoreMark/ramsweep/cachesweep | Giu firmware va hash |
| fw_board/ | 12 Embench hex original iteration | Giu, khong doi khi board receipt dang co hieu luc |
| sw_metrics/{irq,conflict} | IRQ/context-switch va conflict probe/model | Receipt ngoai manifest |
| scripts/ | Build/run/parser/checker/metric drivers | Tach current driver va patch mot lan lich su |
| scripts/fpga/ | Common ten-seed fit, reference x2, SOF builder, audit | Diem board seed 2 chung; fitdb can giu |
| scripts/m2/ | Design-space sweep, worker compile library rieng, analysis | Sweep lich su con hop le do cycle-exact |
| scripts/metrics/ | PPA/power/ACT4/code-size/IRQ/unified table | Current generators va mot so legacy runners |
| scripts/rf_bht_m9k/ | Checker mutation/negative control M9K | Bang chung restructuring |
| scripts/r16_fasthit/ | Patch/dry-run/proof restructuring FAST_HIT | Lich su co dependency, khong chay patch len tree current |
| scripts/maintenance/ | Inventory, archive verification va removal receipt helpers | Tool quan ly workspace, khong thay doi RTL |
| quartus/ | QSF/SDC/device/DE2 pins va experiment projects | Giu constraint va source seed/RTL |
| point_*.qpf/.qsf, db/, incremental_db/ | Bon project + fit database da seed | Giu: con can tao SOF seed 2; qsf seed phai doi chieu report |
| output_files_*_4kb/ | Report/database/SOF cua cac point fit | Khong prune truoc fit receipt/SOF build |
| output_files_de2_115_*/ | Board project fit cu | Legacy; giu SOF/provenance, khong dung lam current board result |
| output_files_board_matrix_r14/ | SOF RTL RAM-16-KiB truoc RF/BHT M9K | Legacy board package, khong program de bao cao current RTL |
| asic/soc_dm_4kb/ | DM wrappers/config/SDC/macros/run | DM 16-KiB signed pair locked, DM 8-KiB/golden provenance giu |
| asic/soc_sa2_4kb/ | SA2 wrappers/recipe/macros/run | Signed pair + source pair giu; minimality chua chay |
| asic/soc_vc4_4kb/ | VC4 wrappers/recipe/macros/run | DRT failure/current diagnostics va controls can giu |
| asic/soc_dm_control/ | Baseline cache 1 KiB sync_final | Baseline bat buoc giu |
| asic/dse_sram/ | Adapter cache data bank sang OpenRAM | Input that cua SA2/VC4, ngoai manifest |
| asic/snapshots/ | RTL co dinh cho PD va equivalence | Khong rename / sua duong dan baked vao state |
| asic/openlane-local/, eqy-local/ | Tool ben thu ba co local fixes | Khong coi la rac; thay doi theo QUY_TRINH |
| asic/equiv/ | Formal RTL equivalence, k-induction, negative controls, synthesis replay, custom LEC | Giu proof inputs/verdict/raw logs; negative Fatal co the la PASS cua doi chung |
| asic/gls/ | Netlist simulation, SAIF conversion, activity power/OpenSTA | Giu SAIF/SPEF/NL/rawpower/receipts |
| asic/fp_tools/, fp_explore/ | Floorplan/congestion/pin/clock/DRC diagnostics va screening | Source/recipe/evidence, khong signed result neu chi screen |
| asic/sta_query/ | Timing path/DRV/clock query, what-if | Mot so query co net/cell cua run cu |
| asic/pd_exp/ | Thi nghiem PD/timing theo co che | Legacy source/evidence, khong current layout |
| results/ | Paired CSV, raw logs, reports, proof receipts | Phan loai theo RTL/profile/method/status; R tag cu khong tu lam so sai |
| results/m2/ | Base/FAST design-space sweep va phan tich | Giu paired CSV va independent model results |
| results/report_page/ | Local source report HTML va updater | Trang cu co ten v5; khong tu coi la current results |
| results/pd_run_archive/ | Config/metric/report/log/step list cua run cu | Giu de debug sau khi binary run da xoa |
| results/source_archive/ | Original helper/coordinator/docs, ZIP legacy scripts va UVM coverage | Khong current driver; archived originals co hash |
| results/workspace_audit/ | All-path/source catalogue, provenance supplement, cleanup preflight/execution | Bang chung quan ly workspace; inventory co timestamp |
| evidence_runs/ | Text bang chung thi nghiem / baseline cu | Giu provenance va bai hoc |
| backups/pre_ram16k_20260929/ | Ban truoc tang RAM | Frozen lineage, khong merge vao current source |
| work* | Questa compiled libraries, tai tao tu nguon | 22 thu muc idle da xoa; lan compile sau tu tao lai |
| .git/ | Git index/objects/history/uncommitted changes | Khong cleanup/commit/checkout trong cong viec nay |

## 6. Vai tro file RTL chinh

File paired trong cung dong co cung vai tro cho I$ va D$, chi khac giao thuc/doc-ghi.
Danh muc tung path, symbol va fingerprint chi tiet nam trong SOURCE_CATALOG.md.

| File duoi hdl/ | Chuc nang |
|---|---|
| soc_top.v | Ghep CPU/cache/AXI RAM/MMIO/peripheral/instrumentation |
| board/de2_115_top.v | Board pins, reset/KEY/RX synchronizer, parameter profile |
| riscv_core.v, riscv_core_native.v | Core controller/datapath va request/response adapter, response buffering |
| datapath.v | Pipeline registers/PC/forwarding/CSR/IRQ/retire, RF/BHT read-ahead |
| controller.v, maindec.v, aludec.v | Pipeline control, opcode va ALU/Zmmul decode |
| alu.v, branch.v, extend.v, hazard_unit.v | ALU/shared multiplier, branch compare, immediate, stall/flush |
| regfile.v | 2 read ports; FPGA M9K+bypass, ASIC implementation cu |
| predictor/bht_2bit.v | Predictor counter; FPGA M9K+valid+bypass, ASIC array cu |
| cache/icache.v, dcache.v | Chon cache controller theo CACHE_CONFIG/FAST_HIT |
| cache/icache_controller.v, dcache_controller.v | DM lookup/refill/L0, D$ store-through |
| cache/icache_dse_core.v, dcache_dse_core.v | SA2/VC4/DM_DSE; lookup, victim swap/evict/refill, D$ coherence |
| cache/icache_nway_core.v, dcache_nway_core.v | N-way 2/4 ways va tree pseudo-LRU |
| cache/icache_tag_ram.v, dcache_tag_ram.v | Tag sync read, valid reset rieng |
| cache/icache_data_ram.v, dcache_data_ram.v | DM data array sync read, word banks |
| cache/cache_dse_data_bank.v | Data bank tung way, line length parameter |
| axi/cache_axi_master.v | I$/D$ refill arbitration, burst, posted-write FIFO |
| axi/axi_ram_32.v | Unified FPGA RAM, byte-lane MIF, simulation injection |
| axi/native_axi_lite_master.v, axi/axi_lite_to_apb.v | CPU MMIO -> AXI-Lite -> APB |
| bus/soc_address_decoder.v | Low memory va UART/display/timer/monitor pages |
| perf_counters.v, performance_observability.v, apb_performance_monitor.v | Cycle classifier/event bank va clear/start/freeze/atomic snapshot |
| apb_timer.v, apb_display_regs.v | Timer/count/IRQ va LED/HEX/LCD/KEY register map |
| uart_apb.v, uart_core.sv, fifo.sv | UART registers, prefetch/FIFO/status va RX/TX glue |
| baudrate_gen_block.sv, rx_block.sv, tx_block.sv | Baud tick, UART RX/TX start/data/parity/stop |
| hex7seg_decoder.v, lcd_1602_hex.v | Hex display decoder, LCD init/write |
| riscv_full.hex, riscv_full_byte0..3.mif | Canonical initialization words/byte lanes |

Adapter ASIC: axi_ram_32_asic_macro.v dung 8 macro 2 KiB cho RAM; cache_data_ram_sram4.v
dung 4 macro 1 KiB moi cache; cache_dse_data_bank_sram.v dong goi set/word theo cache
organisation; soc_asic_top.v tung design chot profile va synchronizer.

## 7. Markdown: doc nao dang duy tri, doc nao la bang chung

| File | Chuc nang / pham vi |
|---|---|
| README.md | Cua vao, layout, tools, lenh reproduce |
| QUY_TRINH.md | Quy tac rang buoc, thu tu thuc thi |
| NHAT_KY.md | Lich su duy nhat, debug issues, cleanup, name aliases |
| PROJECT_STATE.md | Trang thai va ordered tasks; thay ten handover cu |
| RESULTS.md | So lieu verified va pending, corner/method |
| REVIEW_RESPONSE.md | Phan bien M1..M3/A1..A9 va gap/manuscript |
| WORKSPACE_MAP.md | Chi muc chuc nang/pham vi, lien ket bang chung |
| CODEX_PROMPT.md | Duplicate instructions cu; archive san, xoa bi tool review chan; khong la rule current |
| tb/diag/README.md | Sau probe ASIC-view cu, khong regression; link NHAT_KY da sua |
| backups/pre_ram16k_20260929/tb/diag/README.md | Ban dong bang cua README probe, khong sua |
| sw/embench_upstream/README.md | Upstream source/scale/licence/profile |
| asic/evidence/MAGIC_NAMESPACE_COLLISION.md | Evidence bat buoc giu cua hai Magic/OpenRAM namespace fixes |
| asic/pd_log.md | START/DONE/STOP raw log tu launcher, khong lich su bien tap |
| asic/fp_explore/fp_summary_20261006.md | Floorplan/GRT screening, chua signed result |
| results/m2/M1_M2_REPORT.md | Controller confound, matched latency, DSE, limits |
| results/m2/M1_M2_analysis.md | Generated capacity/line/victim analysis tu paired sweeps |
| results/a1_le_breakdown_r16.md | FPGA hierarchy truoc RF/BHT M9K |
| results/a1_le_breakdown_rfbht.md | FPGA hierarchy RF/BHT M9K, chung seed 2 |
| results/asic_compare_dm_r14.md | Legacy generator subset DM; khong full corner/gate audit |
| results/asic_compare_dm_sa2_20261009.md | Legacy generator subset DM/SA2 |
| results/asic_ppa_verified_subset_20261010.md | Current full-evidence subset DM/SA2, power hai STA, chua T6 cuoi |
| results/asic_ppa_verified_subset_20261009.md | Snapshot truoc khi DM power STA thu hai hoan tat |
| results/unified_metrics.md | Unified table, FPGA common seed 2, ASIC power/board gaps |
| results/paper_figures_20261010/README.md | Hai figure research PDF/SVG/PNG, source/paired inputs va portable verifier; khong thay asset bai 1 KiB |
| .tools/paper_plotting/ | Dependency plotting pin rieng trong research, khong sua Windows Python global; khong phai phep do |
| results/fpga_seed_summary_r12b_p1.md | Historical RAM 8 KiB, four seeds |
| results/fpga_seed_summary_r14_p1.md | Historical RAM 16 KiB, flip-flop RF/BHT |
| results/fpga_seed_summary_rfbht_p1.md, _p2.md | Current M9K four-seed paired provenance |
| results/fpga_seed_summary_paired_method_4seed_20261009.md | Same-seed paired differences, verified four-seed subset |
| results/board_6c4ccffd_20261009_seed_comparison.md | Withdrawn per-config best-seed choice; SUPERSEDED, archive san nhung xoa bi chan |
| results/vc4_padding_hypothesis_20261009.md | Frozen padding-only experiment plan; execution/retry status in PROJECT_STATE.md and gated_pd.log |
| results/cleanup_proposal_20261009.md | Proposal truoc cleanup; current outcome o cleanup_proposal_outcome.json |
| results/workspace_audit/SOURCE_CATALOG.md | Generated entry tung source/config/Markdown, khong manual sign-off |

## 8. Ket qua don va nhung gi con giu

17 run PD da xoa sau khi so SHA archive/source, merged metrics va step lists; 22 Questa
library idle da xoa. Tong 85,424,751,170 byte logic, khoang 79.558 GiB. NTFS hardlink /
allocation co the lam disk reclaim khac byte logic. Moi thu muc xoa co receipt/log.

19 proposed run khong phai 19 run deu rac. Sau migration, 6 input LEC/replay cua final_B
da archive dung byte va 14 reader da doi path; lenh xoa run bi tool review chan nen folder
van giu. VC4 clkm3_pad1_r1 la input cua 3 branch screening. Chung duoc giu, cung signed/locked runs,
source runs, synthesis controls, baseline 1 KiB, golden, SOF, paired CSV, raw log va proof.
Ten Rxx trong path immutable can giu vi resolved/state/proof co absolute paths;
ten chuc nang va alias duoc dung cho nguoi doc. r1/r2 la luot do lap, khong so phien ban.

20 source/document/legacy-coverage files da ZIP-archive va verified, nhung lenh xoa
ban goc + doi ten golden helper bi automatic review chan. 4 root VCD va 2 raw log root
cung bi chan; cac file do con nguyen. Khong chay bang cong cu khac de vuot chan.
Receipt: results/source_archive/retired_sources.json va cleanup_proposal_outcome.json.

HANDOVER_CODEX.md da doi thanh PROJECT_STATE.md sau khi coordinator thoat; original
doc va coordinator source duoc giu trong source_archive. Persona da bo khoi doc trang
thai current. AI/tai lieu cu trong comment frozen RTL va raw archive chua sua, vi
doi byte se lam doi source identity / proof provenance. Day la gioi han cleanup ro rang,
khong la tuyen bo moi dau vet da bien mat.

## 9. Cong viec dang do

Fit chung seeds 1..10 da xong: 40 cap point/seed khop115 hardware fields, 56/56 additional fits da ghi nhan.
Common board seed2 giu cho ca bon config. Tham chieu simulation100 cap verified,100 SOF current da build/audit,
200 dong template chay vat ly hai luot con NOT_RUN. Folder output_files_board_matrix_6c4ccffd_seed2/ va INDEX.csv
giu hash va expected MCYCLE/MINSTRET. Khong dung SOF R14 cu thay the. Runner continuation da ket thuc READY_FOR_PHYSICAL_SESSION.

DM power12 kernel da khop hai STA doc lap tu GLS/SAIF co dinh; receipt gls_power_r14F_A_power_verification.json.
24 SAIF DM/SA2 deu thua mot chu ky20ns; exact-window capture va paired STA can lam lai, dau vao cu giu nguyen.
SA2 minimality die11.05mm2 dung P2: nom_tt setup-0.331932ns, hold-0.0579186ns, overflow16;
mot execution, can full-step1_r2 cung recipe truoc ung vien3325. SA2 final LEC chua proof,
DM full sequential LEC closure dang audit: symbolic gold reset-base235constant/28duplicate/4FSM
khong tu dong chung minh moi paired reset relation, clock edge va invariant tren dung input.
Clock/edge audit tren4 flat model DM da khop hai luot; joint invariant286 va sampled reset phase1716 nghia vu
cung chay kep, review doc lap PASS. BHT/UART baud/Icache hot-array unused default dong cuc bo261 classified
X/Z connect lines. Them49mainRAM defaults qua hai luot va reviewdoclap, tong310/358dong,48conmo;
selected B-data/whole-output definedness/RAMinit khong duoc claim. Bang97dong trong
results/lec_source_x_remaining_20261010/ la snapshot truoc mainRAMproof; current48=14PMUX+7mux+27moduleconnect.
source-model/paired reset/between-edge async/full sequential LEC van mo.
VC4 chua sign-off; candidate padding bat dau07:47+07 sau Windows free15,149MB,
WSL available23,171MB, dung08:07 tai postCTS nativeSignal11/P1MISSING. Stepcrash giu nguyen,
retrykhongdoi input batdau08:10 chi toi firstGRT, chua ketluanloimay; PROJECT_STATE.md va
results/vc4_postcts_crash_20261010.json ghi chi tiet. Client WSL foreground giu suot activeflow.
Update08:46+07: retry hoan tat firstGRT, p1 PASS overflow0; screen nom_tt setup+0.491ns,
hold-0.202ns tai9endpoint, skew hold-1.720ns. P2 FAIL smallhold da CONTINUE theo ECO; DRT chinh da xong
DRC0, antenna trong stepDRT van CPU-active;
receipt results/vc4_padding_initialgrt_20261010/receipt.json. Chua signoff/pairedPPA.
Job can song qua luc controlling session thoat van can terminal WSL owner giu mo.
Cac task/command
day du nam o PROJECT_STATE.md. Loi CoreMark/ACT4/test runner duoc ghi muc 9 NHAT_KY;
RTL frozen khong doi; cac verification runner duoc sua va kiem tra rieng.
