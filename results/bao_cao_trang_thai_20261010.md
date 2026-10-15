# Bao cao trang thai du an, 2026-10-10

Snapshot khi lap bao cao: 2026-10-10T08:15:36+07:00. Day la ban tong hop de doc ket qua va tim bang chung; chua phai ket qua T6 cuoi. Trang thai job dai co the doi sau snapshot; [PROJECT_STATE.md](../PROJECT_STATE.md) va receipt duoc dan duoi day la noi theo doi tiep.

## 1. Ban RTL dang dung va y nghia cac ten cu

Ten chuc nang: **SoC RAM 16 KiB, RF/BHT trong M9K tren FPGA, FAST_HIT tuy chon**. Core RV32I + Zmmul co pipeline 5 tang, predictor 2 bit, AXI/AXI-Lite/APB, UART, timer va bo dem hieu nang. Cau hinh nghien cuu chinh dung I-cache va D-cache 4 KiB, line 16 B. Bon diem vat ly la DM, SA2, DM_VC4 va DM_DSE; SA4/SA2N la cac diem kien truc bo sung.

| Ten lich su | Chuc nang duoc them | Quan he voi ban dang dung |
|---|---|---|
| R14 | Tang RAM 8 -> 16 KiB, sua linker/stack/firmware va ramsweep | Snapshot PD van giu ten nay; khong phai RTL moi nhat |
| R15 | Cache N-way, SA4 va SA2N doi chung | Con trong source hien tai |
| R16 | CACHE_FAST_HIT: tra main-array hit ngay LOOKUP, bo mot chu ky cua DSE/N-way | Mac dinh 0; FAST=1 la thi nghiem rieng, chua co ASIC build |
| Sau R16, 2026-10-08 | RF/BHT FPGA sang M9K, read-ahead, bypass va valid-reset | Ban hien tai; giu nguyen tung chu ky benchmark |

Cung seed 2, DM giam tu 15,440 xuong 12,815 LE; RF 1,386 -> 52 LE, BHT 962 -> 636 LE. Day la giam tai nguyen FPGA, khong phai giam CPI. SA4 va cac diem cache 8 KiB chua fit lai bang M9K. R17 trong mot ghi chu cu thuoc he alias khac, khong phai ban sau R16 FAST_HIT. Chi tiet: [ban do RTL va alias](../WORKSPACE_MAP.md#2-ban-rtl-hien-tai-va-cac-ten-cu), [RESULTS muc 3](../RESULTS.md). Manifest hien tai gom 227 file; check chi-doc cho ket qua IDENTICAL.

## 2. Doc file/folder nao de hieu workspace

| Noi | Chuc nang |
|---|---|
| hdl/, tb/, verification/ | RTL, testbench directed, UVM, ACT4 va infrastructure kiem chung |
| sw/, fw/, fw_board/, sw_metrics/ | Source/harness, firmware routine, firmware original iteration cho board, test IRQ |
| scripts/, quartus/, point_* | Runner/generator, constraint va bon project FPGA; database seed 2 can giu de tao lai SOF |
| asic/soc_*/, snapshots/ | Wrapper/recipe/run PD va RTL snapshot co dinh |
| asic/equiv/, gls/, fp_tools/, sta_query/ | Proof/replay, GLS/SAIF/power, chan doan routing va timing |
| results/ | Bang CSV hai luot, report, receipt, archive bang chung va danh sach da xoa |

Chuc nang tung Markdown/source/script nam trong [SOURCE_CATALOG.md](workspace_audit/SOURCE_CATALOG.md); moi path, ke ca ignored/build/binary, co trong [inventory.json](workspace_audit/inventory.json) va [paths.jsonl](workspace_audit/paths.jsonl). [Snapshot bo sung](workspace_audit/completion_20261009/CURRENT_DIGEST.md) va [current_state.md](workspace_audit/completion_20261009/current_state.md) tach cac dot kiem chung cu/moi. Kiem ke binary la metadata, khong dong nghia da doc hay kiem chung moi byte database/PDK/tool.

Cac file vao chinh: [WORKSPACE_MAP.md](../WORKSPACE_MAP.md) giai thich folder/RTL/alias; [RESULTS.md](../RESULTS.md) chua so lieu; [REVIEW_RESPONSE.md](../REVIEW_RESPONSE.md) doi chieu tung y phan bien; [QUY_TRINH.md](../QUY_TRINH.md) la quy tac; [NHAT_KY.md](../NHAT_KY.md) giu lich su va bai hoc debug, nhat la muc 9.

## 3. RTL va PD khop toi dau?

RTL hien tai tai FAST_HIT=0 co proof RTL-to-RTL voi snapshot PD. Thay doi M9K chi tren FPGA; view ASIC va tong hop DM truoc/sau thay doi giu byte-identical. GLS phai so voi ASIC-view RTL; board phai so voi FPGA-view, vi wrapper RAM hai view co do tre khac nhau.

**Full sequential RTL-to-netlist LEC con OPEN.** DM giu bang chung legacy mapped SAT/CEC/algebra hai luot va negative controls. Dot moi da chung minh gold reset base cho 235 constant, 28 duplicate va 4 nhom FSM hai luot; audit clock/positive edge tren bon flat model cung khop hai luot. Chua dong paired reset relation cua N1/netlist cuoi, exact-input invariant/reachability bridge va source-to-model abstraction. Cac sub-proof nay khong tu dong la full-chip LEC, va khoang trong proof khong la bang chung RTL sai. SA2 moi co preparation va N1 replay byte-exact; SA2/DM_VC4 chua co final LEC. Xem [proof scope](lec_proof_scope_20261010.md) va [clock receipt](dm_lec_clock_audit_20261010/receipt.json).

Them [audit khoi tao/model](lec_model_initialization_audit_20261010.md): cac bit tag, register array va SRAM read khong reset phai co quan he trang thai symbolic duoc chung minh. Mot so default-X chi la model mux va da co check Boolean cuc bo; khong suy so luong X thanh loi thiet ke hay full proof.

## 4. UVM, Embench, CoreMark va board

- **UVM:** 48 ca moi pass, hai luot khop scoreboard; bon cache config, seed 1/2/3, directed/peripheral/IRQ/UART RX hai byte va AXI stress line words 2/4/8/16. Wrong-byte controls bi bat. Day la functional coverage; khong la full code coverage hay ma tran SA4/FAST_HIT. [Receipt](uvm_cache_uart_20261009/verification.json).
- **Embench:** 12 upstream kernel vua RAM 16 KiB; base 72 dong/pass, FAST 60 dong/pass, moi truong khop. Sweep 637/559 dong va conflict probe 390 window co doi chieu hai luot/model. Khong la full upstream suite hay official score. Original iteration da duoc mo phong lai tren RTL hien tai trong 100 cap firmware/config board-reference; khong dung BENCHMARK_FAST_UART. [Bang tong hop](unified_metrics.md), [M1/M2](m2/M1_M2_REPORT.md).
- **ACT4/random:** 43 selected RV32I/Zmmul cases + mot upper-half probe = 44 cap sau sua adapter; khong la full privileged compliance. Random 50 cap la predictor OFF/ON cung core, khong phai oracle ISA doc lap. [ACT4](architecture_window_20261009/verification.json), [random](random_diff_checked_20261009/verification.json).
- **CoreMark:** 11 diem current da qua numeric CRC va 40 counters trong hai luot, them canonical DM pair. RAM 32 KiB, window gom initialization/reporting, ITERATIONS=1; khong chay tren chip 16 KiB va khong la official score. Sweep CRC mo rong **92 diem (49 base + 43 FAST), moi diem hai luot, dang IN_PROGRESS**; chua cong bo VERIFIED cho sweep day du. [Current receipt](coremark_crc_checked_20261009/verification.json), [live sweep receipt](coremark_sweep_crc_20261010/verification.json).

**FPGA:** bon config deu dung seeds 1..10 chung; 40 cap fit khop 115 truong ngoai runtime. So sanh trong cung seed, khong chon seed tot nhat rieng. Fmax nam 51.02..56.18 MHz tai Slow 1200 mV 85 C; power la Quartus default toggle-rate estimate, khong phai do tren board. [PPA muoi seed](fpga_common_seeds_continued_20261009_ppa.md).

**Board seed 2 chung:** 100 SOF cho 25 workload x 4 config da build/audit, canonical MIF restore PASS. INDEX co expected MCYCLE/MINSTRET va hash. Template 200 dong hai pass deu NOT_RUN; chua co so quan sat/anh/UART hay power board. [INDEX](../output_files_board_matrix_6c4ccffd_seed2/INDEX.csv), [checklist](../output_files_board_matrix_6c4ccffd_seed2/SESSION_CHECKLIST.md).

## 5. ASIC: gate truoc PPA, snapshot chua final T6

**DM/SA2 PASS o ca hai full flow:** route/Magic/KLayout DRC, moi LVS difference, XOR, overlap, critical disconnected pins va antenna nets/pins deu 0; setup moi tt/ff va hold ca 9 corner deu dat. Moi design khop 319 non-runtime metrics, netlist/DEF byte-identical, SPEF chi khac DATE. ss setup bao cao, khong gate; SRAM Liberty chi TT.

| Chi tieu | DM | SA2 |
|---|---:|---:|
| Die, mm2 | 10.6285 | 11.5600 |
| Std-cell area, mm2 | 1.3696 | 1.4711 |
| Routed wire, m | 6.585 | 9.274 |
| Setup max_tt_025C_1v80, ns | +1.708 | +0.838 |
| Hold min_ff_n40C_1v95, ns | +0.021 | +0.020 |
| Setup max_ss_100C_1v60, ns, chi bao cao | -7.365 | -7.917 |
| Activity total, nom_tt_025C_1v80, mW, mean 12 kernels | 119.453 | 129.644 |
| Activity dynamic, cung power corner, mW, mean | 119.016 | 129.207 |
| Leakage, cung power corner, mW | 0.437 | 0.437 |

Power dung GLS -> SAIF -> OpenSTA voi sign-off RCX SPEF; hai STA doc lap tu cung preserved activity khop moi power group/origin. Khong tuyen bo hai GLS moi. Power/EPI dung ASIC-view cycles; CPI Embench cua bang kien truc dung FPGA-view. Chi tiet moi corner, buffer class va per-kernel: [verified subset](asic_ppa_verified_subset_20261010.md).

**DM_VC4 chua sign-off.** Ung vien unpadded cu that bai convergence DRT. Ung vien padding-only moi tren die 12.24 mm2 bi native signal 11 o post-CTS repair truoc P1, trong sta::PathVisitor::visitEdge; cause undetermined, chua du bang chung ket luan loi may/OOM. Step crash da giu; diagnostic retry khong doi input bat dau tu completed step 36, dung gated driver toi first global route de kiem P1. Day van la mot execution bi ngat, khong phai ket qua PPA. [Crash receipt](vc4_postcts_crash_20261010.json); [gia thuyet](vc4_padding_hypothesis_20261009.md).

## 6. Don dep va goi gui dong nghiep

Da archive/doi chieu hash roi xoa 17 run PD khong con dependency; xoa 22 library Questa idle. Tong **85,424,751,170 byte logic = 79.558 GiB**, khong dong nhat voi dung luong disk thuc reclaim do NTFS/hardlink. [PD cleanup receipt](workspace_audit/cleanup_execution.json), [cache cleanup receipt](workspace_audit/cache_cleanup.json), [danh sach da xoa](cleanup_deleted.txt). Run locked/signed-off, raw report, CSV, recipe va bai hoc debug duoc giu.

final_B da archive 6 input, giu 562 evidence va migrate 14 reader; xoa folder bi automatic approval review chan nen source van nguyen. Mot so source/doc cu va golden-helper rename cung bi chan; originals co ZIP archive nhung chua xoa/rename. Khong lap lai bang cong cu khac. Cac ten nam trong snapshot/manifest/raw proof khong doi tuy tien vi se pha provenance. [final_B outcome](final_b_dependency_migration_20261009/cleanup_outcome.json), [retired-source receipt](source_archive/retired_sources.json).

[Goi dong nghiep](colleague_materials_20261010.zip) gom **121 file**, 114 ban sao nguon, khoang 3.27 MB ZIP; SHA/CRC/roundtrip va manifest PASS. [README](colleague_materials_20261010/README.md) neu cach doc va gioi han; [SOURCE_ORIGINS](colleague_materials_20261010/SOURCE_ORIGINS.csv) map ten mota sang file goc; [package receipt](colleague_materials_20261010_package_receipt.json) giu ket qua integrity. ZIP la snapshot bat bien, chua gom ket qua cac job dang chay sau do.

Bai TeX goc 1 KiB duoc copy nguyen va **chua sua theo research**. Nam PDF goi tu bai goc con thieu: fig_cacheorg.pdf, fig_soc.pdf, fig_cyclecat.pdf, fig_le.pdf, fig_fmax.pdf; cac anh PNG/JPG hien co va bibliography inline da kem. Khong tu tao asset thay the. [Missing assets va dong TeX](colleague_materials_20261010/original_published_1kb/MISSING_ASSETS.md).

Bo sung sau snapshot: [goi bieu do research](paper_figures_20261010.zip), 24 file, 911,092 byte ZIP. Hai figure co PDF/SVG/PNG, anh render PDF da kiem tra bo cuc, CSV input hai pass va portable verifier. Figure FPGA dung cung seeds 1..10; figure Embench tach controller DM/DM_DSE va to chuc SA2/VC4 tren cung DSE. Power FPGA la Quartus vectorless, Typical 1.20 V, ambient 25 C voi junction tu tinh 26.6..26.8 C. ZIP membership/CRC/SHA/roundtrip PASS; khong thay nam PDF thieu cua bai goc. [Receipt](paper_figures_20261010_package_receipt.json).

Phan con phai dong: CRC toan sweep sau khi hai pass verified; DM full sequential LEC va SA2/DM_VC4 final LEC; VC4 sign-off + full flow lap lai + power; SA2/VC4 minimality; bang T6 ba design cuoi; phien board vat ly hai luot. M3/related work, A5/caption va minor manuscript van thuoc cong viec viet bai; bai bao goc chua bi chinh sua.
