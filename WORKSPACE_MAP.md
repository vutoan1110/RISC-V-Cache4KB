# Ban do workspace va pham vi ket qua

| muc | gia tri |
|---|---|
| Muc dich | trang vao de hieu du an theo chuc nang thay vi so phien ban |
| Pham vi | ban nghien cuu `E:/Projects/RISCV-research`; ban cong bo 1 KiB o thu muc khac chi doc; khong sua manuscript |
| Cap nhat lan cuoi | 2026-10-15 (kiem toan workspace goc: 2026-10-09) |
| Lien quan | quy tac `QUY_TRINH.md`; trang thai `PROJECT_STATE.md`; so lieu `RESULTS.md`; lich su `NHAT_KY.md` / `NHAT_KY_v2.md` |

## 1. Doc theo nhu cau

| Can biet | File can doc |
|---|---|
| He thong hien tai la gi, so lieu nao con dung, chay tren RTL nao? | trang nay, `RESULTS.md` (muc 0), `PROJECT_STATE.md` |
| Moi y phan bien da xu ly toi dau? | `REVIEW_RESPONSE.md`, `results/review_status_20261014.md`, `danh_gia.txt` |
| Gui dong nghiep tai lieu nao? | `results/colleague_materials_20261010.zip` (README / SOURCE_ORIGINS / SHA trong goi), trang bao cao `report_page/soc_report.html` |
| Chay / do / ky ten dung quy tac the nao? | `QUY_TRINH.md` |
| Vi sao chon knob / ung vien, loi cu debug the nao? | `NHAT_KY_v2.md` muc 4, 7 (ban goc `NHAT_KY.md` muc 8, 9); archive run |
| Chuc nang tung file nguon / script / Markdown? | `results/workspace_audit/SOURCE_CATALOG.md`, `source_catalog.json` |
| Moi file (ke ca ignored / build / binary) nam dau? | `results/workspace_audit/paths.jsonl`, `inventory.json` |
| Da xoa chinh xac gi va bang chung o dau? | `results/cleanup_deleted.txt`, `cleanup_execution.json`, `cache_cleanup.json`, `results/pd_run_archive/` |

Kiem ke truoc don (2026-10-09): 73,861 file, 11,891 thu muc, ~254.6 GiB byte logic; moi path duoc liet ke, symlink / reparse point khong
duoc theo ra ngoai workspace. Text nguon / config duoc doc de trich heading, symbol, docstring; code va raw bang chung quan trong duoc doi
chieu rieng. Quet ten file khong phai la da kiem chung moi byte cua binary, PDK, cong cu ben thu ba hay database PD. Danh muc tu dong la
chi muc, khong thay review logic. Inventory sau don (61,666 file) va ban truoc don duoc giu rieng.

## 2. Ban RTL hien tai va cac ten cu

Ten chuc nang dung trong bao cao: **SoC RAM 16 KiB, RF/BHT trong M9K tren FPGA, cache FAST_HIT tuy chon** = manifest `6c4ccffd`
(2026-10-08). Fingerprint manifest la khoa tra cuu bang chung, khong phai thu tu phien ban.

| Ten cu | Ngay | Thay doi co nghia | Con ap dung the nao |
|---|---|---|---|
| R14 (`3ea52396`) | 2026-09-29 | RAM chinh 8 -> 16 KiB; linker / stack / firmware va ramsweep theo RAM moi | snapshot `rtl_r14` cua moi PD DM / SA2 / VC4 toi 2026-10-14: ket qua do la lich su |
| R15 (`d409b09d`) | 2026-09-30 | core cache N-way, SA4 va SA2N doi chung | co trong RTL hien tai; ASIC chi DM / SA2 / VC4 |
| R16 (`ea3ef852`, `c09143ea`) | 2026-10-03 | `CACHE_FAST_HIT`: hit mang chinh tra o LOOKUP | mac dinh 0; diem FAST = 1 chi la thi nghiem kien truc, chua co ASIC FAST = 1 |
| rfbht (`dcbf3495` -> `6c4ccffd`) | 2026-10-08 | RF va BHT FPGA sang M9K, read-ahead + bypass + valid-reset | ban dang dung; giu nguyen tung chu ky, giam LE; snapshot PD `rtl_rfbht` tu 2026-10-14 |
| R17 trong ghi chu cu | 2026-09-25 | alias cua R8 (bo dong bo dau vao, `a0c425f8`) | khong phai ban sau R16 |
| R1..R16 trong dot 2026-09-24 | 2026-09-24 | so hang muc sua RTL cua mot dot cu | khong cung he so voi R14 / R15 / R16 |

Gia tri truoc / sau M9K (seed 2): DM 15,440 -> 12,815 LE; RF 1,386 -> 52 LE; BHT 962 -> 636 LE; them 4 M9K cho RF / BHT. Chi tiet va
pham vi fit: `RESULTS.md` muc 4. SA4 / cache 8 KiB chua fit lai; khong tron so LE cu vao bang PPA cua bon diem 4 KiB.

SoC: pipeline 5 tang RV32I + Zmmul, forwarding / stall / redirect, BHT 256 entry x 2 bit, cache I/D, AXI4 burst, posted-write buffer 2
entry, MMIO AXI-Lite -> APB, UART, timer, LED / HEX / LCD, bo dem chu ky / su kien va snapshot. RAM chinh thong nhat 16 KiB (khong phai
hai RAM rieng). D-cache write-through / no-write-allocate. Tap CSR / timer IRQ / mret co gioi han; khong co synchronous exception day
du hay DIV/REM.

Profile nghien cuu: moi cache 4 KiB = 256 line x 16 B, RAM 16 KiB, FAST_HIT = 0 cho bon diem board / ASIC chinh. HDL chung van mac dinh 64
line = 1 KiB; QSF va wrapper chot profile, nen chi doc default trong `soc_top.v` se hieu sai diem dang do.

| CACHE_CONFIG | Ten | Cau truc |
|---:|---|---|
| 0 | DM | direct mapped, I$ FSM 5 state / D$ 7 state |
| 1 | SA2 | 2 way tren DSE, I$ 10 state / D$ 11 state |
| 2 | DM_VC4 | direct mapped + 4 victim entry tren DSE |
| 3 | DM_DSE | direct mapped tren DSE de tach chi phi controller |
| 4 | SA4 | 4 way tren N-way, tree pseudo-LRU |
| 5 | SA2N | 2 way tren N-way de doi chung SA2; khong thuoc bon diem board chinh |

## 3. RTL va PD da khop toi dau? (2026-10-15)

| Cau hoi | Ket luan va bang chung |
|---|---|
| Cay hien tai co doi sau dong bang? | `--check`: 227 file IDENTICAL (2026-10-14); khong rewrite manifest |
| Netlist tong hop cua `6c4ccffd` bang netlist nao? | bang tong hop R16 tung byte (sha256 `da06d38f`); KHAC tong hop R14 cua PD cu (`fc555d6b`); M9K chi tren FPGA |
| Layout ASIC nao chay tren `6c4ccffd`? | chua co layout ky ten; DM va SA2 dang chay (tu 2026-10-15 00:18 UTC); moi layout ky ten hien co doc `rtl_r14` (lich su) |
| DM RTL -> netlist routed (R14)? | LEC anh xa thanh ghi x2 voi gold `rtl_r14`, cac tien de (reset bat dong bo, gia tri khong xac dinh, bat bien, clock) da dong 2026-10-13/14; PD sign-off hai luot |
| SA2 RTL -> netlist routed (R14)? | LEC day du hai luot (2026-10-14), moi doi chung am; PD sign-off hai luot; GLS 12 kernel |
| DM_VC4? | chua ky ten; LEC phan tong hop xong hai luot (2026-10-14); chu du an hoan, se xay lai tren `6c4ccffd` |
| Hai view co cung MCYCLE? | khong: ASIC RAM wrapper khong co hook do tre FPGA. GLS doi chieu view ASIC; board doi chieu view FPGA |

Proof: `asic/equiv/r16_eq/r16_eq_verdict.txt` (29 check, 0 FAIL) va cac .status SoC; `asic/rf_bht_m9k_asic_checks.log`;
`asic/equiv/rf_bht_m9k/run_live.log`; `asic/equiv/lec/`; `results/asic_ppa_verified_subset_20261010.md` / `.json`;
`results/rtl_consistency_audit_20261014.md`. Gate DRC / LVS / antenna va tung corner phai PASS truoc khi dung PPA; corner ss bao cao, khong
gate; cong suat SAIF dung nom_tt, khong lay `power__total` (max_ff) lam power tt.

Manifest khong phu top SA2 / VC4 va adapter `asic/dse_sram`, cung khong phu SDC / config / .do / fw_board / sw_metrics. Receipt
`results/workspace_audit/asic_input_provenance.json` luu 42 input moi design va SHA (2026-10-09); tu 2026-10-14 cac wrapper SA2 / VC4 duoc
dong bang trong snapshot `rtl_rfbht` (47 file). Hash quan sat khong tu chung minh lich su; proof va resolved input cu van la bang chung goc.

## 4. Kiem chung va gioi han (tren `6c4ccffd`)

| Hang muc | Da xac nhan | Chua duoc ket luan |
|---|---|---|
| Regression | 178 PASS moi luot, x2 | PASS count khong thay cho coverage |
| UVM | 48 ca bo sung x2 (4 cache cfg, seed 1/2/3, UART RX hai byte, AXI stress 4 line size); doi chung sai byte bi bat | functional coverage, chua code coverage; bo UVM frozen cu la subset DM |
| Embench base / FAST | 72 / 60 dong moi luot, moi cot khop; 144 / 120 raw log khop CSV | 12 kernel vua RAM 16 KiB; khong phai official score; khong suy ra PPA ASIC FAST_HIT = 1 |
| ACT4 | 43/43 x2 qua adapter 1 MiB da sua; them test nua tren x2 va doi chung alias | unprivileged I / Zmmul |
| Random differential | 50 seed x2 voi gate rc / completion / full trace; Spike doc lap 2026-10-11 khop 200/200 trace | Spike chi phu tap RV32I / Zmmul sinh ra, khong MMIO / IRQ / cache / timing |
| Tham chieu board | 100 ca x2, moi counter khop R14; 42 ca vat ly da do (2026-10-13), khop ca hai luot tham chieu | 58 ca chua do; mot luot vat ly |
| CoreMark | 92 diem sweep x2 (184 mo phong), CRC + 40 counter khop, audit doc lap; ma tran chuan 16/16 | cua so ca chuong trinh / RAM 32 KiB; khong official score; SA4_256B_L16 khong hop le voi L0 = 8 |
| Mo phong cu (M1/M2, A3, A4, A8, IRQ) | ket qua R14 / R15 / R16 giu nguyen | dang chay lai x2 tren `6c4ccffd` (2026-10-15) |

Embench harness: warm-up ngoai cua so, chi do `benchmark()`, `verify_benchmark(result)` AND voi counter invariant, report / UART ngoai cua
so. Firmware mo phong thuong giam iteration; `fw_board/upfull_*` la iteration goc. Khong build canonical voi `BENCHMARK_FAST_UART`.
Coverage tong trong `verification/uvm/out/` ngay 2026-09-18 la lich su; bang chung hien tai la `results/uvm_rfbht*` va
`results/uvm_cache_uart_20261009/`. Loi runner / CRC / memory index / manifest: `NHAT_KY_v2.md` muc 2.8 va 7.

## 5. Chuc nang thu muc

| Thu muc / nhom file | Chuc nang | Cach quan ly |
|---|---|---|
| `hdl/` | RTL core, cache, bus, RAM, ngoai vi, bo dem, board top | current, manifest khoa |
| `tb/` | unit / directed / integration bench, compile / regression | current; `diag/` la probe loi cu |
| `verification/assertions, coverage, directed, random, diff` | assertion, functional coverage, ISA test, random generator, ISS / trace reference | giu nguon |
| `verification/uvm/{intf,env,seq,test,tb}` | interface / driver / monitor / scoreboard / ISS / coverage, test / sequence, DUT adapter | current; `out/` tron current va legacy |
| `verification/architecture` | ACT4 linker / target / Spike / signature | TB frozen co gioi han; runner duy tri sinh ban sua |
| `verification/results` | raw log / signature / summary kiem chung | bang chung |
| `sw/` | harness / platform / linker / firmware C/S | current; `embench_upstream/`, `coremark/` la nguon ben thu ba / port |
| `fw/`, `fw_board/` | hex canonical cho mo phong; 12 Embench iteration goc cho board | giu firmware va hash |
| `sw_metrics/{irq,conflict}` | IRQ / chuyen ngu canh va conflict probe / model | ngoai manifest, co receipt |
| `scripts/` | build / run / parser / checker / metric | `fpga/` (seed chung, tham chieu, SOF, audit), `m2/` (sweep), `metrics/`, `verification/`, `maintenance/` (inventory, archive, hang doi, chay lai), `rf_bht_m9k/`, `r16_fasthit/` (lich su, khong ap len cay hien tai) |
| `quartus/`, `point_*.qpf/.qsf`, `db/`, `incremental_db/` | QSF / SDC / chan DE2; bon project point + fit database co seed | giu: con can cho SOF seed 2 |
| `output_files_*_4kb/` | report / database / SOF cua fit point | khong prune truoc fit receipt / SOF build |
| `output_files_board_matrix_6c4ccffd_seed2/` | 100 SOF hien hanh, INDEX.csv | board hien hanh |
| `output_files_board_matrix_r14/`, `output_files_de2_115_*/` | SOF RTL cu | legacy, khong dung de bao cao RTL hien tai |
| `asic/soc_dm_4kb/`, `soc_sa2_4kb/`, `soc_vc4_4kb/` | wrapper / config / SDC / macro / run tung thiet ke | run ky ten R14 khoa; config `_rtl6c4c` cho RTL hien tai |
| `asic/soc_dm_control/` | moc cache 1 KiB `sync_final` | bat buoc giu |
| `asic/dse_sram/` | adapter bank du lieu cache sang OpenRAM | input that cua SA2 / VC4; trong snapshot `rtl_rfbht` |
| `asic/snapshots/` | RTL co dinh cho PD va equivalence (`rtl_r14`, `rtl_r15`, `rtl_r16`, `rtl_rfbht`) | khong doi ten / sua duong dan baked vao state |
| `asic/openlane-local/`, `eqy-local/` | cong cu ben thu ba co sua cuc bo | thay doi theo QUY_TRINH D |
| `asic/equiv/` | chung minh RTL, k-induction, doi chung am, replay tong hop, LEC tu viet | giu input / verdict / raw log; Fatal cua doi chung am co the la PASS |
| `asic/gls/` | mo phong netlist, chuyen SAIF, cong suat OpenSTA | giu SAIF / SPEF / NL / raw power / receipt |
| `asic/fp_tools/`, `fp_explore/` | chan doan floorplan / nghen / chan / clock / DRC va sang loc | khong phai ket qua ky ten |
| `asic/sta_query/` | truy van timing / DRV / clock tren run da ky | mot so query gan voi net / cell cua run cu |
| `asic/pd_exp/` | thi nghiem PD theo co che | legacy |
| `report_page/` | nguon trang bao cao (Version 9, 2026-10-14) | sua roi dang lai cung URL |
| `results/` | CSV cap, raw log, bao cao, receipt chung minh | phan loai theo RTL / profile / phuong phap / trang thai |
| `results/m2/`, `results/m2_6c4ccffd/` | sweep thiet ke (lich su; chay lai tren `6c4ccffd`) | giu CSV cap |
| `results/report_page/` | trang bao cao cu (`bao_cao_soc_v5.html`) | lich su, khong coi la ket qua hien hanh |
| `results/pd_run_archive/` | config / metric / report / log / step list cua run da xoa | giu de debug sau khi xoa binary |
| `results/source_archive/` | helper / coordinator / tai lieu goc, ZIP script legacy va coverage UVM | khong phai driver hien hanh |
| `results/workspace_audit/` | catalogue moi path / nguon, provenance, cleanup | bang chung quan ly workspace |
| `evidence_runs/`, `backups/pre_ram16k_20260929/` | bang chung thi nghiem cu; ban truoc khi tang RAM | giu provenance, khong merge |
| `work*` | thu vien Questa, tai tao tu nguon | 22 thu muc idle da xoa 2026-10-09 |
| `.git/` | lich su git | commit chi khi chu du an yeu cau |

## 6. Vai tro file RTL chinh

File cap trong cung dong co cung vai tro cho I$ va D$. Danh muc tung path / symbol / fingerprint: `SOURCE_CATALOG.md`.

| File duoi `hdl/` | Chuc nang |
|---|---|
| `soc_top.v` | ghep CPU / cache / AXI RAM / MMIO / ngoai vi / instrumentation |
| `board/de2_115_top.v` | chan board, reset / KEY / RX synchronizer, profile tham so |
| `riscv_core.v`, `riscv_core_native.v` | controller / datapath, adapter request / response |
| `datapath.v` | thanh ghi pipeline / PC / forwarding / CSR / IRQ / retire, RF / BHT read-ahead |
| `controller.v`, `maindec.v`, `aludec.v` | dieu khien pipeline, giai ma opcode va ALU / Zmmul |
| `alu.v`, `branch.v`, `extend.v`, `hazard_unit.v` | ALU / bo nhan chung, so sanh nhanh, immediate, stall / flush |
| `regfile.v` | 2 cong doc; FPGA M9K + bypass, ASIC cai dat cu |
| `predictor/bht_2bit.v` | bo dem du doan; FPGA M9K + valid + bypass, ASIC mang cu |
| `cache/icache.v`, `dcache.v` | chon controller theo CACHE_CONFIG / FAST_HIT |
| `cache/icache_controller.v`, `dcache_controller.v` | DM lookup / refill / L0, D$ store-through |
| `cache/icache_dse_core.v`, `dcache_dse_core.v` | SA2 / VC4 / DM_DSE; lookup, victim swap / evict / refill |
| `cache/icache_nway_core.v`, `dcache_nway_core.v` | N-way 2/4 way, tree pseudo-LRU |
| `cache/icache_tag_ram.v`, `dcache_tag_ram.v` | tag doc dong bo, valid reset rieng |
| `cache/icache_data_ram.v`, `dcache_data_ram.v`, `cache_dse_data_bank.v` | mang du lieu DM; bank du lieu tung way |
| `axi/cache_axi_master.v` | phan xu refill I$/D$, burst, FIFO posted-write |
| `axi/axi_ram_32.v` | RAM FPGA thong nhat, MIF theo byte lane, nap mo phong |
| `axi/native_axi_lite_master.v`, `axi/axi_lite_to_apb.v` | MMIO CPU -> AXI-Lite -> APB |
| `bus/soc_address_decoder.v` | bo nho thap va trang UART / display / timer / monitor |
| `perf_counters.v`, `performance_observability.v`, `apb_performance_monitor.v` | phan loai chu ky / bank su kien, clear / start / freeze / snapshot |
| `apb_timer.v`, `apb_display_regs.v` | timer / COUNT / IRQ; thanh ghi LED / HEX / LCD / KEY |
| `uart_apb.v`, `uart_core.sv`, `fifo.sv`, `baudrate_gen_block.sv`, `rx_block.sv`, `tx_block.sv` | UART: thanh ghi, FIFO, baud, RX / TX |
| `hex7seg_decoder.v`, `lcd_1602_hex.v` | giai ma HEX, LCD |
| `riscv_full.hex`, `riscv_full_byte0..3.mif` | du lieu khoi tao canonical |

Adapter ASIC: `axi_ram_32_asic_macro.v` dung 8 macro 2 KiB cho RAM; `cache_data_ram_sram4.v` dung 4 macro 1 KiB moi cache;
`cache_dse_data_bank_sram.v` dong goi set / word theo to chuc cache; `soc_asic_top.v` tung design chot profile va synchronizer.

## 7. Markdown: tai lieu duy tri va tai lieu bang chung

| File | Chuc nang / pham vi | Cap nhat |
|---|---|---|
| `README.md` | cua vao, cau hinh, trang thai tong quan, layout, lenh tai lap | 2026-10-15 |
| `PROJECT_STATE.md` | trang thai, job dang chay, nhat ky trang thai, viec theo thu tu (thay `HANDOVER_CODEX.md`) | 2026-10-15 |
| `RESULTS.md` | so lieu da kiem chung va dang cho, nguon goc RTL, goc / phuong phap | 2026-10-15 |
| `REVIEW_RESPONSE.md` | phan bien M1..M3 / A1..A9 va phan con lai | 2026-10-15 |
| `QUY_TRINH.md` | quy tac rang buoc, moc thoi gian quy tac, thu tu thuc thi | 2026-10-15 |
| `NHAT_KY.md` | lich su duy nhat theo ngay | 2026-10-15 07:46 |
| `NHAT_KY_v2.md` | lich su viet lai theo chu de (de xuat thay the) | 2026-10-15 |
| `WORKSPACE_MAP.md` | trang nay | 2026-10-15 |
| `CLOUD_TASKS.md` | viec chi-van-ban cho phien cloud | 2026-10-15 |
| `CODEX_PROMPT.md` | instructions cu 2026-10-09; khong la quy tac hien hanh; xoa bi tool review chan | lich su |
| `report_page/README.md` | nguon trang bao cao | 2026-10-15 |
| `tb/diag/README.md` | probe view ASIC cu, khong regression | lich su |
| `sw/embench_upstream/README.md` | nguon upstream / scale / licence | 2026-09-29 |
| `asic/evidence/MAGIC_NAMESPACE_COLLISION.md` | bang chung bat buoc giu cua hai ban sua Magic / OpenRAM | dong bang |
| `asic/pd_log.md` | log START / DONE / STOP cua launcher, khong bien tap | tu dong |
| `asic/fp_explore/fp_summary_20261006.md` | sang loc floorplan / GRT, khong phai ket qua ky ten | 2026-10-06 |
| `results/m2/M1_M2_REPORT.md`, `M1_M2_analysis.md` | confound controller, DSE, gioi han; phan tich sinh tu sweep | 2026-10-06 (lich su R15/R16) |
| `results/a1_le_breakdown_r16.md`, `a1_le_breakdown_rfbht.md` | LE theo module truoc / sau M9K | 2026-10-08 |
| `results/asic_compare_dm_r14.md`, `asic_compare_dm_sa2_20261009.md` | bang generator DM / DM+SA2 (subset) | 2026-10-02, 2026-10-09 |
| `results/asic_ppa_verified_subset_20261010.md` (`_20261009.md` lich su) | subset PPA du bang chung DM / SA2 | 2026-10-10 |
| `results/unified_metrics.md` | bang hop nhat CPI / hit / PPA | 2026-10-10 |
| `results/rtl_consistency_audit_20261014.md` | ket qua nao chay tren RTL nao | 2026-10-14 |
| `results/review_status_20261014.md`, `extensions_vs_published_1kib_20261014.md` | trang thai 20 diem phan bien; 38 muc mo rong | 2026-10-14 |
| `results/bao_cao_trang_thai_20261010.md` | snapshot bao cao trang thai | 2026-10-10 |
| `results/fpga_seed_summary_*.md` | bang seed (r12b, r14 lich su; rfbht 4 seed; common seeds) | 2026-10-09 |
| `results/board_6c4ccffd_20261009_seed_comparison.md` | chon best seed theo cfg: DA RUT LAI (thay bang seed chung) | lich su |
| `results/vc4_padding_hypothesis_20261009.md`, `pd_minimality_preflight_20261010.md` | ke hoach thi nghiem PD (R14) | lich su |
| `results/cleanup_proposal_20261009.md` | de xuat truoc don; ket qua o `cleanup_proposal_outcome.json` | lich su |
| `results/lec_*_20261010.md` va cac receipt LEC | sub-proof LEC DM (Boolean) | 2026-10-10 |
| `results/workspace_audit/SOURCE_CATALOG.md` | entry tu dong tung source / config / Markdown | 2026-10-09 |

## 8. Ket qua don va nhung gi con giu

- 2026-10-09: 17 run PD da xoa sau khi so SHA archive / source, metric gop va step list; 22 thu vien Questa idle da xoa. Tong
  85,424,751,170 byte logic (~79.558 GiB); disk reclaim co the khac vi hardlink NTFS. Moi thu muc xoa co receipt / log.
- 2026-10-14: 43 thu muc PD that bai / dung / sang loc (~125 GB) da archive text va xoa (`results/pd_run_archive/20261014/`).
- 2026-10-15: dmuA / dmuB da xoa sau archive.
- Giu: run ky ten / khoa, run nguon, doi chung tong hop, moc 1 KiB, golden, SOF, CSV cap, raw log, proof. `final_B`: 6 input LEC / replay da
  archive dung byte va 14 reader da doi duong dan, nhung lenh xoa bi tool review chan nen folder van con. 20 file nguon / tai lieu /
  coverage cu da ZIP va kiem SHA, nhung xoa ban goc + doi ten golden helper bi chan; 4 VCD va 2 log goc cung bi chan. Khong dung cong cu
  khac de vuot chan (`results/source_archive/retired_sources.json`, `cleanup_proposal_outcome.json`).
- Ten Rxx trong path bat bien duoc giu vi resolved / state / proof co duong dan tuyet doi; ten chuc nang va alias dung cho nguoi doc; r1 /
  r2 la luot do lap, khong phai so phien ban. Comment trong RTL frozen con ten tai lieu cu; sua se doi danh tinh nguon nen khong sua.

## 9. Cong viec dang do

Trang thai chi tiet, job dang chay va lenh: `PROJECT_STATE.md` (muc 3-6). Tom tat 2026-10-15: PD DM va SA2 tren `6c4ccffd` dang chay
(lan thu hai); mo phong cu dang chay lai x2 tren `6c4ccffd`; LEC / cong suat se lam lai tren layout `6c4ccffd` duoc chap nhan; DM_VC4 hoan;
con 58 ca board.

## Lich su tai lieu

| Ngay | Thay doi |
|---|---|
| 2026-10-09 18:40 .. 20:36 | tao sau kiem toan workspace va don 17 run |
| 2026-10-10 | cap nhat trang thai VC4 / LEC |
| 2026-10-15 07:46 | commit `2d4202d` |
| 2026-10-15 | viet lai: muc 3 / 4 cap nhat theo trang thai 2026-10-15 (LEC SA2 xong, Spike, board 42 ca, PD tren `6c4ccffd`); muc 7 them cot cap nhat va cac tai lieu moi; muc 9 thay doan trang thai cu 2026-10-10 bang tro toi PROJECT_STATE |
