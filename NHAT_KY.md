# Nhat ky thiet ke: RTL, kiem chung, FPGA, ASIC

| muc | gia tri |
|---|---|
| Pham vi | ban nghien cuu `E:/Projects/RISCV-research` (RV32I + Zmmul, cache I/D 4 KiB, RAM chinh 16 KiB), 2026-09-16 .. 2026-10-15 |
| Trang thai du lieu den | 2026-10-15 07:45 (+07) |
| Cau truc | theo chu de (viet lai 2026-10-15 theo yeu cau chu du an: ngan hon, khoa hoc hon, khong trung lap); mot phien ban duy nhat |
| Ban cu theo gio | chi con trong git (commit `35ebf92` va truoc do); khong giu ban thu hai trong cay |
| RTL hien hanh | manifest `6c4ccffd` (227 file, `results/rtl_manifest.json`) |

## 0. Cach doc

- **Thoi gian.** Ngay dang YYYY-MM-DD. Gio khong ghi mui la gio dia phuong (UTC+7); gio lay tu log flow
  (`asic/gated_pd.log`, `asic/dse_pd.log`) ghi kem "UTC".
- **Nhan RTL.** [HT] = ket qua tren RTL hien hanh `6c4ccffd`. [LS] = lich su: chay tren RTL cu hon `6c4ccffd`
  (danh sach day du: `results/rtl_consistency_audit_20261014.md`). Thay doi RF/BHT cua `6c4ccffd` giu nguyen tung chu ky
  (k-induction + chuoi day du trung tung truong), nen ket qua [LS] du kien tai lap, nhung chua phai bang chung tren
  `6c4ccffd` cho toi khi chay lai. Moi PD/GLS/LEC truoc 2026-10-14 21:20 doc snapshot `asic/snapshots/rtl_r14`
  (manifest `3ea52396`) nen deu la [LS].
- **Do tin cay.** Moi so trong file nay da chay hai lan va so tung truong, tru khi ghi ro "mot luot", "sang loc" hoac
  "phat trien". So cuoi cung cua mot cau hinh nam o `RESULTS.md`.
- **Tai lieu lien quan.** Quy tac: `QUY_TRINH.md`. Trang thai va viec con lai: `PROJECT_STATE.md`. Phan bien:
  `REVIEW_RESPONSE.md`. Ten cu -> ten moi: muc 11.
- **Ghi su kien moi.** Su kien moi vao muc 8a (nhat ky tam theo thoi gian), roi duoc gop vao muc chu de o lan ra soat ke tiep;
  van de lap lai vao muc 9, don dep vao muc 10, ten moi vao muc 11.
- **So muc giu tuong thich.** Script, comment va tai lieu cu tham chieu "NHAT_KY section 8 / 9 / 10 / 11" va tieu de muc 8a; cac so
  do giu nguyen nghia o ban nay:

  | Tham chieu cu | Nghia cu | Vi tri trong ban nay |
  |---|---|---|
  | muc 8 | PD SA2 / DM_VC4, floorplan hanh lang, ly do tung knob | muc 8 (ASIC theo cau hinh); ha tang flow muc 6 |
  | muc 8a | RF/BHT vao M9K, conflict probe; noi script board ghi su kien | RF/BHT muc 1.2, conflict probe muc 2.7; muc 8a la nhat ky tam |
  | muc 9 | Van de da biet ("Loi may", "EQY va LEC", ...) | muc 9 (cung ten tung van de) |
  | muc 10 | Nhat ky don dep | muc 10 |
  | muc 11 | Bang doi ten | muc 11 |
  | muc 1-7 cu va tieu de theo ngay (vd. "NHAT_KY.md 2026-09-26", "NHAT_KY_RTL.md R9") | lich su theo ngay | tim theo ngay / ten ban trong muc 1 (RTL), 2 (kiem chung), 3 (FPGA / board), 7 (ASIC giai doan dau), 8 (ASIC) |

## 1. Cac ban RTL

### 1.1 Bang tong hop

Cot "Chuoi" la chuoi kiem chung kep tai thoi diem dong bang. Ma 8 ky tu la tong SHA-256 cua manifest
(`scripts/rtl_manifest.py`), tru hai dong 2026-09-18 la md5 cua cay `hdl/`.

| Ngay | Ten cu | Ma | Thay doi chinh | Chung minh | Chuoi | Trang thai |
|---|---|---|---|---|---|---|
| 2026-09-16 | ban sao | - | `LINE_WORDS` thanh tham so; sua 3 loi co san (muc 1.2) | 48/48 run trung tung chu ky ban dong bang | - | [LS] |
| 2026-09-17/18 | lint | md5 `bf24fbae` | Verilator -Wall ve 0 lop dung/sai; sua hot tag `[27:3]`, `bank_csb0` | - | 110 PASS, 48-run trung tung byte, UVM 8/8, AXI 8/8 | [LS] |
| 2026-09-18 | synccache | md5 `c9c96924` | tag RAM doc dong bo, valid tach rieng; D$ chi hot buffer tra trong chu ky request | 48-run: DM +0.021 % chu ky, cfg khac trung tung byte | 110 PASS | [LS] |
| 2026-09-19 | bo nho ASIC 4 KiB | - | wrapper macro `sky130_sram_1kbyte_1rw1r_32x256_8` (4 bank/cache), chan doc bank dang ghi | 48-run 1 / 4 KiB trung tung byte | 126 PASS (2026-09-23) | [LS] |
| 2026-09-22 | manifest dau | `9cd02a06` (68 file) | `scripts/rtl_manifest.py`, `scripts/run_fullchain_both.sh` | - | 126 PASS x2, UVM 20/20, 4 ma tran trung | [LS] |
| 2026-09-24 | rtlfix (R1..R16 cua dot) | `aa8e32f9` (170 file) | latch `rx_block`; read-enable bank DSE; loi ghi AXI posted; UART STATUS/RXDATA; mot SoC top; 3 loi bo nho ASIC | latch sweep 0 latch | 128 PASS x2; view ASIC 12/12 | [LS] |
| 2026-09-25 | rtlfix | `b82c2717` -> `c235dfb7` | `uart_apb` bo qua `pstrb` (APB4); xoa `rd_addr_q`; lint baseline 111 canh bao | - | 128 PASS x2, Embench/CoreMark trung, random 50/50, view ASIC = FPGA (33 truong) | [LS] |
| 2026-09-25 | R8 (sau goi R17) | `a0c425f8` | dong bo 2 flop cho `uart_rx` (FPGA) va reset/`key1_n`/`uart_rx` (ASIC) | TB moi: RTL cu 4 + 10 FAIL, RTL moi PASS | 129 PASS x2 | [LS] |
| 2026-09-25 | R7a+R7b+R8 | `358cb660` | bo cong dich fetch tach phan cao; mot bo nhan co dau 33x33; chan nguon macro | SAT miter + doi chung am; 20,025,600 phep nhan 0 sai | xanh, CPI khong doi | [LS] |
| 2026-09-26 | R9 | `ecf4fc03` | thanh ghi hoa giai ma (forwarding, load one-hot, lan byte) | checker mo phong 447,858,365 chu ky, 0 lech | xanh | [LS] |
| 2026-09-26 | R10 / fix1 / fix2, R11 | `b56fbd4e`, `2bffe7cc`, `d030ad12` | `hot_mvalid` (8 flop); `(* keep *)` bo dem perf chi duoi `__openlane__` | k-induction + doi chung am; equiv keep 1,256/1,256 va 5,281/5,281 | xanh | [LS] |
| 2026-09-26 | R12, R12b | `e21ef330`, `8b163675` | FPGA dung select ma hoa (-145 LE); ASIC giu one-hot | k-induction | xanh; Quartus 16/16 fit x2 | [LS]; RTL cua ban ky ten 8 KiB-RAM |
| 2026-09-29 | R14 | `535ec0f9` -> `1d584624` -> `3ea52396` (`9b868f10` sau khi bo kernel tu viet) | RAM chinh 8 -> 16 KiB, linker/stack/firmware, test `ramsweep` | - | `run_fullchain_r14.sh` luot 3: 0 loi | [LS]; snapshot `rtl_r14` cua moi PD toi 2026-10-14 |
| 2026-09-30 | R15 | `d409b09d` | core N-way (2/4 way, tree pseudo-LRU), CACHE_CONFIG 4 = SA4, 5 = SA2N | DM: 35,067 `$equiv`, 0 unproven | 0 FAIL; model cache EXACT 48/48 + 24/24 | [LS] |
| 2026-10-03 | R16 | `ea3ef852`, `c09143ea` | `CACHE_FAST_HIT` (mac dinh 0) | module 24/24; SoC DM 35,067 / SA2 36,741 / DM_VC4 37,441 `$equiv`, 0 unproven; doi chung am 1,824 unproven | 45 OK / 0 FAIL; 161 PASS x2 | [LS] |
| 2026-10-08 | RF/BHT M9K | `dcbf3495` -> **`6c4ccffd`** | RF va BHT vao M9K chi tren FPGA (`ifndef __openlane__`), read-ahead + bypass + valid | k-induction 3/3 PROVEN, 3/3 doi chung am co phan vi du | 0 loi; 178/178 x2; ACT4 43/43 x2 | **[HT] hien hanh** |

Snapshot RTL cho PD: `asic/snapshots/rtl_r14` (= `3ea52396`, dung den 2026-10-14), `rtl_r15`, `rtl_r16` (chi tong hop
doi chung), `rtl_rfbht` (= `6c4ccffd`, moi PD tu 2026-10-14 21:20; 44 file RTL trung cay song, sau do them 3 wrapper
SA2 / DM_VC4 thanh 47 file, SHA-256 trong `SNAPSHOT_ID.txt`).

### 1.2 Ghi chu tung ban

**2026-09-16 Ban sao nghien cuu.** Thiet ke da cong bo bi dong bang, nen thi nghiem chay tren ban sao giu nguyen bo cuc
(duong dan tuong doi cua `.qsf` / `config.json` van dung); 2026-09-18 ban sao chuyen ra `E:/Projects/RISCV-research`
(17 GB; lint, 110 test, hash RTL khong doi). `LINE_WORDS` thanh tham so; mac dinh trung ban dong bang (Quartus DM
15,188 LE / 8,356 reg / +0.629 ns / 51.62 MHz). Ba loi co san lo ra: (1) AXI master ep dia chi refill boi 16 byte (sai
voi line < 16 B); (2) ban sao eviction vao victim buffer gate theo `!IS_SA2` thay vi `IS_VC4`, nen cau hinh khong co
victim buffer van ton 8 chu ky moi conflict miss; (3) `axi_scoreboard.sv` mang dung gia dinh sai cua (1) - checker chung
gia dinh voi thiet ke khong bat duoc loi cua thiet ke. Loi do tham so hoa: ba lech do rong khong bao loi bien dich
(`wr_word` 3 bit / driver 2 bit, index 4 bit cat con 3, `read_beat_count_q` 3 bit), con tro thay the `VC_DEPTH` vuot mang;
tat ca da sua.

**2026-09-17 Lint (Verilator -Wall, khong file waiver).** WIDTHEXPAND/WIDTHTRUNC 28 -> 0, SYNCASYNCNET 3 -> 0, EOFNEWLINE 8 -> 0,
tin hieu chet 17 -> 0; con 98 canh bao cau truc co ly do. Loi that: `icache_dse_core` ghi hot tag bang `request_block[27:3]`
(o line 8 B mat bit tag cao). Lint ban dau chi elaborate CACHE_CONFIG 0; `lint_rtl.sh` nay quet moi cau hinh. Lint
OpenLane bat `bank_csb0` 2 bit noi vao `csb0` 1 bit trong `axi_ram_32_asic_macro.v`. Doi ten port `branch` -> `branch_en`
lam netlist ASIC 1 KiB +2,728 cell (muc 9 "Yosys nhay voi ten").

**2026-09-18 Tag RAM dong bo (`c9c96924`).** Tag doc dong bo (22 x 64 bit), valid tach rieng (64 flop to hop); DM giu hit
2 chu ky, miss them 1; DSE core khong doi. D-cache: noi long dieu kien hit tao duong doc tra du lieu block khac -> chi hot
buffer tra trong chu ky request; store miss mang chinh nay vo hieu ban sao trong hot buffer (loi tiem an co tu truoc);
lan do dau +12.045 % CPI la loi cai dat (L0 khong duoc nap) va suite 110/110 van xanh, tuc khong test nao kiem L0.
48-run (kernel tu viet, RAM 8 KiB): DM 1,463,306 -> 1,463,620 chu ky (CPI 1.2995 -> 1.2998); RTL `c9c96924` luu o
`results/rtl_state_synccache.md5`. Nhan dinh luc do rang thay doi nay "xoa confound controller" la sai (muc 9 "Confound controller").

**2026-09-18 Cache 4 KiB lan dau (chi doi `LINE_COUNT=256`).** Macro OpenRAM `test_sram_1rw1r_32x256_noperim` (`perimeter_pins False`,
`check_lvsdrc False`); giu 4 bank, doc line 128 bit mot chu ky, FSM khong doi. 48-run 4 KiB: DM 1,449,098 chu ky (-0.99 %), SA2
-0.93 %, DM_VC4 -0.85 %, DM_DSE -0.86 %; miss -11.2 / -13.8 / -3.2 / -11.2 %. DM_VC4 loi it nhat vi victim buffer va dung luong
cung khu mot loai conflict miss. Regression them quet `LINE_COUNT` 128/256 (126 PASS); UVM directed + periph PASS o 64 va 256.
View ASIC / FPGA cua cung diem: muc 2.4.

**2026-09-19 Bo nho ASIC 4 KiB.** Mang du lieu bang flop o 4 KiB la 65,536 flop: khong kha thi. Moi bank dung mot macro
1 KiB 32x256 (4 bank / cache, 12 macro tinh ca RAM chinh 8 KiB). Macro 1rw1r de cong 1 khong xac dinh khi cong 0 ghi cung
dia chi nen wrapper chan doc bank dang ghi; valid cua `icache_tag_ram` doi sang vector packed (BLKLOOPINIT o 256 line).
Tong hop 4 KiB: 1,036,877 um2 cell, 77,310 instance (1 KiB: 1,386,981 um2). Quyet dinh cung ngay: dua regfile vao MLAB khong
the tren Cyclone IV E (chi co M9K, doc dong bo) nen khong lam; RF/BHT giu flip-flop cho toi `6c4ccffd` (2026-10-08), ban giai
rang buoc doc dong bo bang read-ahead + bypass + valid.

**2026-09-24 Dot sua RTL (rtlfix, `aa8e32f9`).** Snapshot truoc dot: `hdl_pre_rtlfix_20260924T093817Z.tar.gz` (nay trong
`results/pd_run_archive/asic_experiments_20261007.tar.gz`). Latch `rx_block` (2 chan `dlxtn_1`; Verilator `--Werror-LATCH` bao 0 vi
khoi `always @(*)`). Read-enable cho `cache_dse_data_bank.v` (giu doc trong IDLE vi store hit D$ ghep byte tu ket qua doc
do; chu ky khong doi). Loi ghi AXI posted (`m_axi_bresp` bi bo qua): sticky `wr_err` + dia chi loi dau o sysmon `0xAC` / `0xB0`
(ghi 1 vao bit 0 cua `0xAC` de xoa), ident `0x53380001` -> `0x53380002`; test T19 cu PASS ma khong tiem loi, da viet lai. UART:
STATUS bit 5 `tx_fifo_full`, bit 6 `rx_fifo_empty`; test moi `tb_uart_apb` bat `RXDATA` khong tra byte vua nhan; nay `RXDATA` la
byte cu nhat chua doc, tu nap truoc tu FIFO (firmware khong nhan UART nen so lieu cu khong doi). Chan nguon macro trong wrapper
chua lam o dot nay (`PDN_MACRO_CONNECTIONS` noi chung, LVS dat; lam o `358cb660`). Mot SoC top cho ASIC (ban sao `soc_top_asic.v`
da lech 66 dong); wrapper RAM ASIC doi ten module thanh `axi_ram_32` (thay the theo ten module); `scripts/lint_asic.sh` doc
`VERILOG_FILES` tu `config.json` va coi MODDUP la loi (glob cu co 3 MODDUP van PASS). View ASIC lan dau: 1/12 kernel PASS; ba
loi RTL bo nho ASIC: (1) bien truoc khai bao (file chua tung qua Questa),
(2) dia chi ghi khong bypass khi AW va W cung chu ky (91/115 lenh ghi sai dia chi; netlist ASIC truoc do khong chay duoc
chuong trinh co store), (3) `cache_data_ram_sram4.v` khong giu gia tri doc (model OpenRAM tra X) -> chot 264 FF. Sau sua:
12/12 PASS. Ket qua PD cua `ch4kb_full` (RTL con loi) bi bo. Probe chan doan: `tb/diag/`.

**2026-09-25 `c235dfb7`.** `run_fpga_points.py` tu 6 so len 116 cot; lint OpenLane voi `ERROR_ON_LINTER_WARNINGS` true bat hai
loi that (`uart_apb.v` bo qua `pstrb`; `rd_addr_q` chet); 111 canh bao con lai vao `asic/soc_dm_4kb/lint_baseline.tsv` +
`scripts/lint_baseline_check.py`.

**2026-09-25 Bo dong bo dau vao (`a0c425f8`).** `uart_rx` di thang vao next-state cua `rx_block`; wrapper ASIC khong dong bo
gi va `set_false_path -from reset_n` lam recovery/removal khong duoc kiem. Them dong bo 2 flop, tach `reset_meta_q` /
`reset_sync_q` (lint_asic bat SYNCASYNCNET). SDC false path cho `key1_n` / `uart_rx` chi hop le sau khi da dong bo. Test moi
`tb/top_wrapper_sync_tb.sv`.

**2026-09-25 Fetch va bo nhan (`358cb660`).** Rang buoc: chi nhan sua RTL khong doi CPI, khong thi quay ve `a0c425f8`. Duong ASIC
dout SRAM (suon xuong) -> giai ma -> imm -> bo cong 32 bit -> `pc_next` trong nua chu ky. Phan cao cua tong chi co the la `pc_hi`,
`pc_hi+1`, `pc_hi-1` (tinh som); chi mot bo cong ngan phu thuoc `instr` (12 bit cho B, 12 + carry-select 8 cho J); chon bang AND-OR
de Yosys `opt_share` khong gop lai thanh bo cong 32 bit. Sau CTS nom_tt -0.788 -> +2.766 ns, +0.9 % dien tich cell. Ba bo nhan
32x32 thay bang mot bo nhan co dau 33x33 (FPGA: 24 -> 8 khoi nhan, cong suat bo nhan 6.22 -> 1.53 mW). Chan nguon macro trong hai
wrapper ASIC duoi `ifdef USE_POWER_PINS` (6 PINMISSING -> 0, netlist cong khong doi). Run `r7r8_358c` (timing: muc 7): hold 0 vi
pham o 9 goc; slew / cap tt 828 / 853; day 6.54 m; Magic DRC 0, KLayout DRC 0, LVS khop; antenna 469 net / 653 pin. Bai hoc:
`alu.v` bi sua 9 giay truoc khi mot thi nghiem doc no -> khong sua `hdl/` khi con flow co the doc.

**2026-09-26 Sua co trong tam cho goc ss (`ecf4fc03` -> `d030ad12`).** ss tren `r7r8_358c`: 2,820 endpoint truot, 70 % tu
`d_req_addr`; xau nhat -12.26 ns: `result_src_w` -> mux ghi nguoc -> forwarding -> ALU -> `d_req_addr` (ly do cua R9). Thanh ghi
hoa giai ma (`scripts/apply_r9.py`); cong lint baseline bi bo sot sau lan doi RTL truoc, chay bu (baseline 110). Sau R9
(`r9_ecf4`) duong xau nhat max_ss -7.575 ns: `pc_f` -> mux valid 256:1 cua I$ -> hot_hit -> stall -> chuoi 20 AND ->
`csr_minstret`. `hot_mvalid` bo mux 256:1 (checker mo phong `hot_mvalid` hong o cau hinh 8 dong, lat cat [-1:0], chi sua checker);
`(* keep *)` dua enable ra khoi chuoi carry (23 -> 3 cell). Quartus ton trong keep tung bit (+17 % LE) nen keep chi duoi
`__openlane__`. Ung vien so sanh hot tag theo tung entry: ABC dung lai sau hon, khong loi, khong ap dung. Bai hoc: o cau hinh
tong hop nay cau truc RTL chi giu duoc qua diem cat `(* keep *)`.

**2026-09-26 RTL cuoi ban 8 KiB-RAM (`8b163675`).** DM_VC4 vuot 20,000 LE (20,002 .. 20,077) vi one-hot AND-OR khong dong goi
vao LUT4; FPGA dung select ma hoa (19,834 .. 19,893). ABC `fraig_restore` cham benh ly (~1 gio) tren dang ma hoa, nen ASIC
giu one-hot; netlist ASIC trung tung byte run r10A.

**2026-09-28 R13a / R13b (thu nghiem tren ban sao, khong vao `hdl/`).** Thu RTL cycle-exact cho goc ss: so sanh hot tag song
song, ban sao thanh ghi PC cho I-cache, bo so sanh nhanh dang prefix, mux forwarding rieng cho bo so sanh. PD te hon (max_ss
-9.930, nom_tt +1.194) -> khong port. Bien the nhan 2 tang (R13b, +1.03 % chu ky) khong chay PD. Ket luan: muc 9 "Goc ss".

**2026-09-29 R14: RAM chinh 16 KiB (`3ea52396`).** Gioi han so bai Embench chay duoc la RAM thong nhat (code + du lieu + stack
1 KiB), khong phai cache: trong 19 kernel Embench-IoT goc (commit `09c2ed8c`) 8 KiB vua 8 bai, 16 KiB 14, 32 KiB 18, 64 KiB 19;
chon 16 KiB (ASIC 8 macro 2 KiB). Thay doi (chuyen tu `RAM16K_CHANGES.md`):

| Nhom | File | Thay doi |
|---|---|---|
| RTL | `hdl/soc_top.v`, `hdl/board/de2_115_top.v` | `IMEM_DEPTH` / `DMEM_DEPTH` 1024 -> 2048 |
| RTL | `hdl/axi/axi_ram_32.v` | `DEPTH_WORDS` 2048 -> 4096 |
| RTL ASIC | `asic/soc_dm_4kb/soc_asic_top.v`, `axi_ram_32_asic_macro.v` | 4 -> 8 macro `sky130_sram_2kbyte_1rw1r_32x512_8`; bank/word suy ra tu tham so; kiem do sau luc elaborate |
| Phan mem | `sw/link.ld`, `sw/platform.h`, `sw/fix_hex.py`, `sw/Makefile`, `scripts/fpga/hex_to_mif.py` | 8K -> 16K; stack 0x3C00-0x3FFF; do sau MIF 4096 |
| Phan mem | `hdl/riscv_full.hex`, `hdl/riscv_full_byte{0..3}.mif` | sinh lai voi do sau 4096 |
| Cong cu | `scripts/rtl_manifest.py` | manifest phu ca `sw/` (truoc chi `sw_baremetal/`) |
| Test | `sw/main_ramsweep.c`, `sw/embench_ramsweep.{c,h}` | test moi `ramsweep` (word/byte/halfword, phu 8 bank RAM ASIC) |
| Test | `tb/benchmark_snapshot_tb.sv`, UVM (`tb_soc_top.sv`, `core_cfg.sv`, `native_mem_model.sv`, test smoke/random) | RAM 8192 -> 16384 byte |

Khong doi: cache, bo giai ma dia chi (cua so cacheable 64 KiB), pipeline, CPI. Xac minh: Embench/CoreMark trung tung byte ban
8 KiB (firmware build lai chi khac `auipc sp,0x2` -> `0x4`); view ASIC 8 bank = 4 bank ke ca chu ky. Hai loi checker bat duoc
(chi so word theo `addr[12:2]` co dinh; khoi nap ASIC view liet ke 8 bank theo ten). Sao luu: `backups/pre_ram16k_20260929/`.

**2026-09-30 R15: core N-way (`d409b09d`).** `hdl/cache/{d,i}cache_nway_core.v`; CACHE_CONFIG 5 (SA2 tren core N-way) chi de
kiem, phai trung SA2 tung truong. Netlist ASIC khac tung byte (Yosys nhay thu tu doc) nen tuong duong duoc chung minh thay vi
so byte.

**2026-10-03 R16: FAST_HIT.** Core DSE va N-way tra loi hit mang chinh ngay trong ST_LOOKUP. Ap bang
`scripts/r16_fasthit/apply_r16.py` (34 sua, moi neo dung mot lan). Kiem muc SoC phai doi ten `genblk1.g_dse` -> `g_dse` phia
gate (lan dau khong ghep duoc thanh ghi cache nao, Yosys len 16 GB). Test moi: do tre hit SA2 (1 / 0 chu ky), checker moi chu
ky co doi chung dot bien (`r16_word = 32'hdeadbeef`). Latch sweep / lint them truc FAST (33 to hop). Bang chung:
`results/fullchain_r16.log`, `asic/equiv/r16_eq/r16_eq_verdict.txt`.

**2026-10-08 RF/BHT vao M9K (`6c4ccffd`, ban hien hanh).** Muc tieu (A1): RF 1,386 LE va BHT 962 LE dang la flip-flop trong core
6,451 LE. Ap bang `scripts/apply_rf_bht_m9k.py` tu ban R16.
- RF: hai ban M9K (moi cong doc mot ban); dia chi doc = truong rs ma `instr_d` nhan tai canh (`instr_d_next`); RAM tra du lieu
  cu, lan ghi cua canh do duoc bypass tu ban sao dang ky; x0 = 0.
- BHT: hai ban M9K (doc fetch, doc update) dia chi theo dau vao D cua `pc_f` / `pc_e`; bit valid moi entry (flop, reset bat dong
  bo) giu nghia "reset dua entry ve 01"; update cua canh truoc bypass cho ca hai cong.
- Chung minh (`asic/equiv/rf_bht_m9k/`, Yosys `sat -tempinduct`): RF, BHT, giao thuc read-ahead: 3/3 PROVEN; doi chung am
  3/3 FAIL (bo bypass RF, bo kiem valid BHT, bo flush trong `instr_d_next`); mot dot bien bi loai khoi doi chung am vi tuong duong:
  bo `stall_pipe` khoi `pc_f_next` van chung minh duoc, vi `stall_f` da giu `pc_f` moi khi `stall_pipe` bat (dot bien van PROVEN
  phai kiem tuong duong truoc khi ket luan chung minh yeu). Checker chi mo phong canh mang moi, liveness bang
  `scripts/rf_bht_m9k/checker_mutation.sh`.
- TB: 74 truy cap truc tiep mang trong 7 TB + UVM chuyen sang macro `tb/rf_bht_backdoor.svh`; `tb/bht_tb.sv` viet lai (them
  BHT-7..10); `tb/regfile_tb.sv` moi (20,073 chu ky).
- Dong bang dau `dcbf3495`: 46 OK, 1 FAIL: lint_asic KHONG bo qua translate_off, nen checker chi mo phong cung phai qua lint_asic
  (checker BHT kiem `reset_n` trong `@(negedge clk)` bi SYNCASYNCNET). Sua: so sanh o canh len trong chinh cau truc reset bat dong
  bo cua mang tham chieu (doi `apply_rf_bht_m9k.py`, ap lai tu R16); dong bang lai `6c4ccffd` (chi khac `bht_2bit.v`, phan
  translate_off). Bang chung chuoi `dcbf3495`: `results/fullchain_rfbht_dcbf3495/`.
  Chuoi `6c4ccffd` (2026-10-08 21:17-21:56, 39 phut): 0 loi; 178/178 x2; UVM 5/5
  x2, AXI 3 kich thuoc line x2; Embench 72 + 72, FAST 60 + 60, CoreMark 6 + 5, random 50 seed, view ASIC, ramsweep deu trung
  R16 tung truong; ACT4 43/43 x2. Driver `scripts/run_fullchain_rfbht.sh` (lane song song, moi lane mot thu vien Questa: ~55 phut
  thay vi ~5 gio). Log: `results/fullchain_rfbht.log`.
- ASIC: view ASIC dong nhat token (3/3 file, doi chung am: view FPGA phai khac); tong hop DM tu snapshot `rtl_rfbht`
  (`dm_synth_rfbht_r1`) == `dm_synth_r16_r1` tung byte, sha256 `da06d38f`. Gioi han: day la dong nhat voi netlist tong hop R16,
  KHONG phai voi netlist PD R14 (sha256 tong hop `fc555d6b`); xem muc 8.4.

## 2. Cac bo kiem chung

### 2.1 Bang tong hop

| Bo | Noi dung va cach chay | Ket qua moi nhat | Ngay | RTL | Bang chung |
|---|---|---|---|---|---|
| Kiem tinh | `scripts/latch_sweep.sh` (Yosys, 33 to hop CACHE_CONFIG x LINE_COUNT x FAST_HIT), `lint_rtl.sh`, `lint_asic.sh`, lint baseline OpenLane | 0 latch, 0 canh bao moi | 2026-10-08 | [HT] | `results/fullchain_rfbht.log` |
| Regression TB | `tb/`, moi muc x2 | 178/178 PASS x2 (110 -> 126 -> 128 -> 129 -> 161 -> 178 qua cac ban) | 2026-10-08 | [HT] | nhu tren |
| UVM goc (frozen) | subset DM seed 1; UVM 5/5, AXI 3 kich thuoc line | PASS x2 trong chuoi | 2026-10-08 | [HT] | nhu tren |
| UVM bo sung | `scripts/verification/run_uvm_matrix.py`: 4 cache cfg x directed/periph/UART RX x seed 1/2/3 + AXI stress line words 2/4/8/16 x 3 seed = 48 ca/luot | 48/48 x2, moi truong scoreboard khop; doi chung sai byte (0xa4) bi bat | 2026-10-09 | [HT] | `results/uvm_cache_uart_20261009/verification.json` |
| ACT4 | riscv-arch-test `2e655961`, Spike tham chieu; 39 RV32I + 4 Zmmul | 43/43 x2, signature trung | 2026-10-02 (dau), 2026-10-08 (6c4ccffd) | [HT] | `verification/results/act4/` |
| Cua so kien truc 1 MiB | `scripts/verification/run_architecture_window.py`: ban sao TB index [19:2] + test nua tren (0x81000, thuc thi 0x90000) | 43 ACT4 + 1 test x2; ban cu bi alias (timeout) duoc doi chung bat | 2026-10-09 | [HT] | `results/architecture_window_20261009/verification.json` |
| Random differential | 50 seed, BP OFF vs ON cung core, hash trace (trace: `results/random_diff/`) | 50/50 x2; runner gate rc/PASS/Fatal/completion, raw rieng moi luot; 43 controls | 2026-10-09 | [HT] | `results/random_diff_checked_20261009/verification.json`, `results/verification_runner_controls_20261009/verification.json` |
| Spike doc lap | 50 seed x2 tien trinh Spike moi so voi 200 trace RTL da luu; adapter `processor_t` truc tiep (chi nap memory, PC 0, GPR / du lieu = 0 nhu TB; khong viet ngu nghia ISA), `libriscv.so` da cai (co SHA), isa RV32I_Zmmul; ly do khong dung Spike CLI: muc 2.8 | 100 exit 0, 200/200 khop, 7,105 retirement/luot, 300 doi chung trace sai bi bat | 2026-10-11 | [HT] | `results/spike_random_reference_20261011/receipt.json` |
| Embench-IoT | 12 kernel goc (`sw/embench_upstream/`, `fw/up_*.hex`) | base 72 + 72 dong, FAST 60 + 60 dong, trung tung truong | 2026-10-08 | [HT] | `results/rfbht_4kb_p{1,2}.csv`, `results/rfbhtf_4kb_p{1,2}.csv` |
| CoreMark ngan (-O2) | 6 base + 5 FAST, RAM mo phong 32 KiB, CRC tu observer APB TX | 22 mo phong, CRC e9f5/e714/1fd7/8e3a/e714 dung, 40 counter trung | 2026-10-09 | [HT] | `results/coremark_crc_checked_20261009/`, `results/coremark_canonical_checked_20261009/` |
| CoreMark sweep | 92 diem (49 base + 43 FAST) | 184 mo phong, CRC + 40 counter trung ca hai tham chieu cu; audit doc lap 241 input / 379 artefact | 2026-10-10 | [HT] | `results/coremark_sweep_crc_20261010/verification.json`, `results/coremark_sweep_crc_independent_audit_20261010/receipt.json` |
| CoreMark chuan (>= 10 s) | port -Os timer APB, 4 cfg x performance/validation x2 | 16/16 PASS, 108 truong/cap, 864 so sanh | 2026-10-11 | [HT] | `results/coremark_standard_apb_matrix_20261011/receipt.json` |
| View ASIC | RTL voi model OpenRAM, nap backdoor (`tb/compile_asic_view.do`, `run_ablation.py --asic-view`) | 12/12; trung view FPGA tru `mcycle` / i_wait / d_wait | 2026-10-08 | [HT] | chuoi |
| Conflict probe | `sw_metrics/conflict/`, 35 mau x 6 cfg x 4 KiB / 1 KiB | 390 cua so x2, moi cua so = model doc lap | 2026-10-08 23:46 | [HT] | `results/conflict_probe.csv` |
| Tham chieu board | 25 firmware x 4 cfg x 2 luot, thu vien rieng | 100 cap trung R14 moi truong | 2026-10-09 17:56 | [HT] | `results/board_reference_6c4ccffd_20261009_p{1,2}.csv` |
| Quet M1/M2 | dung luong / line / way / victim, ca hai FAST_HIT | 637 + 559 dong, p1 = p2 | 2026-10-06 | [LS] R15/R16 | `results/m2/` |
| Cross-validation (A3) | `scripts/cache_model.py`, `scripts/run_crossval.py` | 48/48, 24/24, 60/60 counter EXACT | 2026-10-06 | [LS] R16 | `results/crossval_r16_4cfg.csv`, `results/crossval_r16_fast.csv` |
| Retire vs minstret (A4) | monitor `scripts/metrics/overlap_mon.sv` | 24/24 kernel | 2026-09-30 | [LS] R14 | `results/a4_overlap/` |
| IRQ / chuyen ngu canh | `sw_metrics/irq`, view FPGA, 4 KiB, x2 | vao handler 5 chu ky; toi thieu 39; chuyen ngu canh 270 (DM) / 292 (DSE): chenh lech la chu ky ST_LOOKUP them cho 62 load/store cua thu tuc chuyen ngu canh | 2026-10-02 | [LS] R14/R15 | `results/irq_metrics.csv` |
| BP on/off (A8) | 12 kernel, 4 KiB | +6.48 .. +6.67 % chu ky khi tat BP | 2026-09-30 | [LS] R14 | `results/bp0_upstream_r14_4kb_p{1,2}.csv` |

Chay lai cac muc [LS] tren `6c4ccffd` bat dau 2026-10-15 (x2, uu tien thap tren Windows): M1/M2
`scripts/m2/rerun_m2_6c4ccffd.py` -> `results/m2_6c4ccffd/` (650 base + 572 FAST run moi luot); A8 / A3 / A4 / IRQ
`scripts/maintenance/rerun_review_sims_6c4ccffd.py` -> `results/review_sims_6c4ccffd/` (ket qua cu giu nguyen; `comparison.json`
o moi thu muc khi xong).

### 2.2 Ablation 1 KiB dau tien sai, da sua (2026-09-17) [LS]

CACHE_CONFIG 3 (DM tren controller 10 trang thai) do loi (2) cua muc 1.2 thuc chat la DM+VC4 tat lookup; moi so suy ra tu no
da vao ban thao bai bao va da duoc sua:

| dai luong | da bao cao | dung |
|---|---|---|
| chi phi controller | +10.25 % | +9.35 % |
| associativity | -1.16 % | -0.34 % |
| SA2 thang / hoa / thua | 11 / 1 / 0 | 3 / 8 / 1 |
| CPI cfg 3 | 1.4327 | 1.4210 |
| quet dung luong 512 B | -9.57 % | -3.52 % |
| line 64 B | -4.78 % | -1.39 % |

Khoang cach 8.98 % da cong bo gan nhu hoan toan do controller (phan tich day du o muc 2.6). Lo hong kiem chung lap theo: cfg 3
co unit test (regression 98 -> 100); UVM co 9 cho gia dinh burst 4 beat, nay dung tham so `LINE_WORDS` chung cho DUT va checker.
Mo hinh cache doc lap ban dau chi khop 4/5 kernel: `perf_counters` dang ky su kien mot chu ky truoc khi dem, nen cong clear/freeze
co hieu luc tu chu ky sau; mo hinh theo tung truy cap thi khop 36/36 run, 9 bo dem.

### 2.3 Do sau L0 cua I-cache: giu 8 entry (2026-09-18) [LS]

Tham so hoa do sau L0 ban dau sai (lat cat tag van `[27:3]`); ca 48 run L0 = 4 sai firmware. Sau sua: L0 = 4 tiet kiem 730 LE
(-5.0 %) nhung truot 50 MHz (-0.297 ns) va +6.42 % chu ky (L0 = 2: +15.45 %; mont64 +19.21 %, md5sum +15.33 %, fdct 0.00 %).
Giu 8 entry. So "-721 LE, slack tot hon" bao truoc do la fit tren RTL loi, da huy. Quy tac rut ra: sau moi lan tham so hoa do
rong, grep moi dang hard-code cu va doi hoi 0 ket qua.

### 2.4 View ASIC va view FPGA

View ASIC retire dung cung dong lenh, moi bo dem kien truc va cache trung, nhung `mcycle`, I-wait, D-wait thap hon vi wrapper
RAM ASIC khong co hook do tre cua RAM FPGA (`ICACHE_MISS_PENALTY=2`): RAM 8 KiB 1,436,264 / 1,449,098 chu ky (-0.89 %), CPI
1.2755 / 1.2869; RAM 16 KiB, Embench goc: DM -4.18 %, SA2 -3.67 %, DM_VC4 -3.23 %. GLS cua moi netlist ky ten tai lap `mcycle`
view ASIC tung chu ky; board so voi view FPGA (INDEX), khong so voi GLS. CPI chip va EPI dung chu ky view ASIC (mot cot EPI cu
tron hai view, sai toi 12 %, da sua `asic/gls/power_csv.py`).

### 2.5 Benchmark

- **Embench-IoT goc (2026-09-29).** `sw/embench_upstream/` (`make MODE=upstream BENCH=<bai> SCALE=<n>`), thay doi duy nhat trong
  nguon goc la hook `LOCAL_SCALE_FACTOR_OVERRIDE`; khung bao ket qua tu viet (khong chep `support/` GPL-3.0); 9/12 bai GPL-3.0 nen
  chi o cay nghien cuu. SCALE cho ~130k-350k chu ky moi lan do sau mot vong lam nong; khong phai diem Embench chinh thuc.
  12 kernel vua 16 KiB: aha-mont64, crc32, depthconv, edn, huffbench, matmult-int, md5sum, nettle-sha256, slre, statemate,
  tarfind, ud (nettle-aes, sglib-combined vuot 15 KiB). Ban vong lap goc cho board: `fw_board/upfull_*.hex`. 2026-09-30: xoa 52
  file kernel tu viet (git giu lich su).
- **CoreMark RAM 32 KiB.** Ban -O2 rv32i_zmmul can .text 13,952 + .rodata 2,445 + .data 24 + .bss 2,020 + stack 1,024 = 19,465 byte
  > 16 KiB; `sw/coremark/coremark_link.ld` dat stack o 32 KiB. Quyet dinh chu du an 2026-10-08: giu RAM mo phong 32 KiB, moi so
  CoreMark ghi "mo phong, RAM 32 KiB". `M1_M2_REPORT.md` tung ghi nham "RAM 16 KiB", da sua.
- **Loi do luong CoreMark (2026-10-09).** `sw/main_coremark.c` dat PASS chi tu counter invariant, khong dung CRC; `core_main.c`
  in CRC loi qua UART nhung tra hang so. Runner hien tai gate CRC tu observer APB TX thu dong (khong sua firmware/TB/RTL), tu
  choi CRC sai/thieu truoc CSV/PASS (15 controls). Cua so counter van la ca chuong trinh, khong phai diem chinh thuc.
- **Sweep 92 diem (2026-10-10).** `scripts/verification/run_coremark_sweep_crc.py` kiem tham so elaborate thuc
  (I/D/line/victim/FAST/RAM/L0/predictor), 36 controls truoc khi chay; SA4_256B_L16 bi loai (4 set khong du index cho L0 8 entry).
- **CoreMark chuan (2026-10-11).** Port cu chi bat timer, ma `apb_timer.v` mac dinh CMP = 40 va dung tang COUNT khi cham CMP;
  port moi `coremark_standard_apb_port.c` dat CMP = 0xffffffff truoc interval, khong IRQ. Hai build doc lap khop byte
  (`results/coremark_standard_apb_build_pair_20261011.json`; image 14,032 + stack 1,024 = 15,056 byte, linker van dat stack o
  32 KiB). Tieu chi nhan: CRC dung, interval >= 500,000,000 tick, delta timer = delta canh clock = thoi gian / 20 ns, moi truong
  hai luot khop. Ket qua (RESULTS muc 3.2): 76.389218 / 79.495077 / 73.561270 / 68.496689 iteration/s (DM / SA2 / DM_VC4 /
  DM_DSE). Screening CSR khong dung de chot diem vi datapath ghi CSR khi doc mcycle.

### 2.6 Quet thiet ke M1/M2 (2026-10-06) [LS R15/R16]

Dung luong 256 B .. 8 KiB, line 8 / 16 / 32 B, 1 / 2 / 4 way, victim 2 / 4 / 8, ca hai FAST_HIT, 12 kernel + CoreMark, moi diem
x2. Rieng controller ton +4.33 % (256 B) .. +10.83 % (8 KiB) GM chu ky (+9.83 % o 4 KiB); cung controller (FAST), SA2 nhanh hon
DM_DSE o moi dung luong (-7.43 % .. -0.18 %), DM_VC4 cham hon (+5.99 % .. -0.01 %) vi ban sao eviction noi tiep refill. Hieu
ung theo kernel lon ca hai chieu (4 KiB: nettle-sha256 +16.15 % voi SA2, statemate -8.86 %). Ket luan "DM thang set-associative"
la ket qua cua controller. Bao cao: `results/m2/M1_M2_REPORT.md`.

### 2.7 Conflict probe mo rong (2026-10-08) [HT]

Probe cu chi doc N dong cua MOT set; o 4 KiB stride 1024 cua no khong con dung do. Probe moi (`sw_metrics/conflict/`, ngoai
manifest): dong (s, k) o 0x0C00 + k x SPAN + s x 16, 35 thi nghiem (tuan hoan, nhieu set, ngau nhien xorshift32, RMW, chi ghi);
firmware tu kiem so truy cap; `model_windows.py` chay lai trace D$ qua model doc lap. Ket qua: SA2 giu 2 dong/set o moi set;
DM_VC4 giu 2 dong/set chi toi 4 set (victim buffer 4 entry dung chung), ngau nhien giam dan 90 / 84 / 76 / 65 % (5 / 6 / 8 / 16
set); DM giu N = 2 trong mot set nho L0 2 entry (98.4 %), DM_DSE 0 %; 1 KiB: DM_VC4 tuan hoan N <= 5 -> 100 %, N = 6 -> 66.7 %,
N >= 7 -> 0 %, ngau nhien N = 8 -> 59 % (sap do round-robin gap thu tu tuan hoan, khong do dung luong). Victim hit ~19-22 chu
ky/truy cap, hit mang chinh ~10-14. Loi khi chay: GCC shrink-wrap luu s0 sau khi mo cua so (sua `-fno-shrink-wrap`); bang UART
vuot gioi han 20M chu ky cua TB (nang 40M); script bi sua khi dang chay nen luot do bi bo va chay lai toan bo.

### 2.8 Loi trong cong cu kiem chung tu viet (tong hop)

| Ngay | Cong cu | Loi | Sua / quy tac |
|---|---|---|---|
| 2026-09-17 | `make` firmware | khong build lai, 12/13 kernel "khac nhau" | `make clean` |
| 2026-09-18 | `pd_retry.sh` | sap xep step theo chuoi, chay lai 20 step; `final/` khong phai dau hieu xong | dau hieu xong = `state_out.json` / metric |
| 2026-09-18 | `verify_double.py` | lap chi muc theo `kernel` (so 12/48 dong) van VERIFIED; pass 2 Quartus VERIFIED khi khong fit nao chay | khoa ghep day du; dem dong `[PASS] 1 fit(s)` |
| 2026-09-25 | runner | `echo "$(date) ... rc=$?"` in rc cua `date` | lay rc cua chinh cong cu |
| 2026-10-02 | ACT4 (cau hinh chay) | file cau hinh CRLF va `$HOME` khong duoc mo rong: lan chay dau khong chay duoc | chay tu ban sao LF, file trong repo giu nguyen |
| 2026-10-09 | CSV comparator | chi so cot giao nhau | fail khi thieu schema/field/key/metric (43 controls, gom doi chung mat cot va hai metric rong); du lieu Embench / board cu da so lai full header / field: chua thay ket qua sai |
| 2026-10-09 | random runner | chi gate hash, ghi de raw; trace bi cat van PASS | gate rc/PASS/Fatal/completion, raw rieng moi luot |
| 2026-10-09 | manifest hex random differential | generator Windows ghi hex CRLF nhung hash trong manifest tinh tren text LF truoc khi ghi | checker kiem hash text LF, receipt luu them SHA256 byte file thuc; khong so hash byte tren dia voi manifest; khong sua generator / RTL |
| 2026-10-09 | ACT4 TB | `tb/architecture_signature_tb.sv` cap 1 MiB nhung index [18:2] alias moi 512 KiB | runner sinh ban sua rieng, TB frozen giu nguyen |
| 2026-10-09 .. 11 | preflight cua harness (CoreMark CRC, GLS pass 2, helper board PowerShell) | regex tim thu vien compile bat nham `vlog -work`; GLS pass 2 sai ten lib `1p80V` thay `1v80`; PowerShell `$Pass:` bi hieu la bien co scope | parse target Tcl thuc; sua ten lib; dung `${Pass}:`. Ca ba bi preflight fail-closed chan truoc khi co output: loi tat dinh cua harness, khong phai loi may hay phep do |
| 2026-10-10 | `scripts/metrics/build_upfull_fw.sh` | tiep tuc khi `make` loi, co the exit 0 voi hex cu | `set -euo pipefail`, `exit 1` |
| 2026-10-11 | tham chieu Spike | Spike CLI FAIL vi debug device 0..0x1000 trung chuong trinh RAM o dia chi 0; stdout / stderr gop qua WSL tung mat dong commit dau | adapter `processor_t` truc tiep (muc 2.1); runner tach raw stdout / stderr va kiem HALT + exit 0 |

Quy tac chung: PASS chi tu artefact ma cong cu ghi khi thanh cong; kiem tra kep can hai artefact tao doc lap.

## 3. FPGA va board

### 3.1 Dien bien FPGA (Cyclone IV E EP4CE115, Quartus 20.1, Slow 1200 mV 85 C, 50 MHz)

| Ngay | RTL | Diem / seed | Ket qua | Ghi chu |
|---|---|---|---|---|
| 2026-09-16 | ban dong bang | DM 1 KiB, seed 2 | 15,188 LE / 8,356 reg / +0.629 ns / 51.62 MHz | moc ban cong bo [LS] |
| 2026-09-17 | sau lint | DM 1 KiB | 15,192 LE / +0.774 ns / 52.01 MHz; 4 seed 15,141..15,289 LE, +0.550..+0.774 ns | [LS] |
| 2026-09-18 | `c9c96924` | DM 1 KiB | 14,596 LE / 8,015 reg / 0.000 ns; 4 seed 14,596..14,672 LE; 272.25 mW (core dynamic 105.08) | tu day bao cao dai 4 seed [LS] |
| 2026-09-18 | `c9c96924` | 4 diem 1 KiB seed 2 | dm 14,596 / 0.000; dm_dse 15,007 / +1.097; sa2 16,211 / +0.309; dm_vc4 18,033 / +0.708 ns | controller 10 trang thai +411 LE [LS] |
| 2026-09-18 | `c9c96924` | dm vs dm_nopc | bo dem hieu nang ton 2,702 LE (18.5 %), 2,038 reg (25.4 %), 11.06 mW tong, 10.88 mW core dynamic | [LS] |
| 2026-09-25 | `c235dfb7` | 4 KiB, 4 seed x2 | DM, DM_DSE dat ca 4 seed; SA2 truot 2/4, DM_VC4 1/4 | [LS] |
| 2026-09-25 | `a0c425f8` | 4 KiB | moi cfg co it nhat 1 seed truot (DM seed 2 -0.924 ns); Slow 0C dat | bien Slow 85C chi ~+-1 ns [LS] |
| 2026-09-25 | `358cb660` | DM seed 2 | -0.924 -> +1.340 ns; bo nhan 24 -> 8 khoi 9 bit | [LS] |
| 2026-09-26 | `e21ef330` | DM_VC4 | 20,002..20,077 -> 19,834..19,893 LE | [LS] |
| 2026-09-30 | R15 | seed 2 x2 | SA4 4 KiB 21,821 LE (Fmax 50.95 MHz); 8 KiB: DM 16,812, DM_DSE 19,364, SA2 23,629, DM_VC4 22,262, SA4 28,891 LE | `results/fpga_points_r15_p{1,2}.csv` [LS] |
| 2026-09-30 .. 10-06 | R14..R16 (RF/BHT flop) | 4 KiB, 4 seed x2 | dm 15,440-15,546 LE / 8,430 reg / 26 M9K; dse 16,989-17,063; sa2 19,360-19,474; vc4 19,810-19,875 | `results/fpga_points_r14_p{1,2}.csv` [LS] |
| 2026-10-03 | R16 FAST_HIT | seed 2 x2 | SA2 +456 LE, Fmax 53.71 -> 51.65 MHz; DM_VC4 +115; DM_DSE +345; SA4 +881; slack xau nhat +0.639 ns | `results/le_r16_compare.log` [LS] |
| 2026-10-08 | R16 | A1 theo module (`scripts/le_breakdown.py` doc report fit da luu, khong chay lai Quartus) | DM 15,440 LE: core 6,451 (RF 1,386, BHT 962), I$ 2,439, D$ 1,896, observability 2,356 | `results/a1_le_breakdown_r16.md` [LS] |
| 2026-10-08 | `dcbf3495` | dm seed 2 (sang loc) | 15,440 -> 12,815 LE (-17.0 %), reg 8,430 -> 7,198, M9K 26 -> 30, slack 0.778 -> 0.870, Fmax 52.02 -> 52.27 | tong hop trung `6c4ccffd` |
| 2026-10-09 | `6c4ccffd` | 4 diem x 4 seed x2 | DM 12,810-12,842; DM_DSE 14,308-14,364; SA2 16,675-16,739; DM_VC4 17,130-17,139 LE; Fmax 51.96-55.52 | `results/fpga_points_rfbht_p{1,2}.csv` [HT] |
| 2026-10-09 23:28 | `6c4ccffd` | 4 diem x seed chung 1..10 x2 | 40 cap khop 115 truong phan cung; 56/56 fit bo sung | `results/fpga_common_seeds_continued_20261009_ppa.{json,md}` [HT] |

A1 sau M9K (`results/a1_le_breakdown_rfbht.md`): RF 1,386 -> 52 LE, BHT 962 -> 636 LE, core 6,451 -> 3,818 LE; uoc luong cong suat
khoi CPU core 39.68 -> 28.08 mW (DM, seed 2).

**Dinh chinh do FPGA (2026-09-25).** Truoc do cong suat Quartus chi chay mot lan, tren seed chay cuoi (so cong suat cu khong phai
cua tung seed); tu do chay sau moi fit va luu report rieng tung seed. Report Quartus dung CRLF lam regex khong khop; cong "thieu
truong la FAIL" bat duoc truoc khi chay that. `scripts/fpga_seed_summary.py`: bang 4 seed, thieu seed hay truong la FAIL.

**Phuong phap seed (2026-10-09 14:23).** Phuong an chon seed tot nhat rieng cho tung cau hinh
(`results/board_6c4ccffd_20261009_seed_comparison.md`, da xoa 2026-10-15, con trong git) bi rut lai TRUOC khi refit / build SOF nao. Phuong phap moi: cung bo seed
1..10 cho bon cau hinh, so sanh ghep cap theo seed, hai luot doc lap; board dung seed 2 chung cho ca bon. Ma tran
`paired10_6c4ccffd_20261009` bat dau 14:33; seed 1/3/4 giu nguon goc rfbht, seed 5..10 va seed 2 refit hai lan. Kiem phuong phap
5/5 (`results/board_seed_method_validation_20261009.json`). Hai lan ngat: phien Windows dung ~15:33 (khong PID, khong ket luan
FAIL; archive `results/board_preparation_interrupted_20261009_1541/EVIDENCE.json`: 8 fit + 38 case tham chieu da xong), va guard
bo nho 6,000 MB dung o 51/56 fit (Windows con 5,384 MB). Continuation `scripts/fpga/continue_common_seed_preparation.py` doi bo nho,
chay 5 fit con lai tuan tu va hoan tat 23:28; audit doc lap 2026-10-10 (`results/fpga_common_seeds_completion_audit_20261010`).

### 3.2 Chuan bi board (2026-10-09 .. 2026-10-12) [HT]

- Tham chieu mo phong: `scripts/fpga/prepare_board_reference.py`, 200 case = 25 firmware x 4 cfg x 2 luot, moi luot compile thu vien
  rieng; 100 cap trung R14 moi truong (`results/board_reference_6c4ccffd_20261009_p{1,2}.csv`, `_inputs.json`, 34 hash). Khong dung
  `BENCHMARK_FAST_UART` (doi `mcycle` mot so kernel). Tham chieu R14 dung de so: `results/upstream_r14_4kb_p1.csv`, `results/ramsweep_r14_p1.csv`,
  `results/upfull_r14_4kb_p1.csv`.
- SOF: builder cu `scripts/fpga/build_board_matrix_r14.py` hard-code RTL 3ea52396 nen viet builder moi `scripts/fpga/build_board_matrix.py`; no chi nhan fit seed 2 chung da VERIFIED + tham chieu da chay kep; moi SOF = fit + MIF
  firmware qua `quartus_cdb --update_mif` + `quartus_asm`, khong fit lai; MIF chuan duoc khoi phuc. Ket qua: 100 SOF trong
  `output_files_board_matrix_6c4ccffd_seed2/`, INDEX.csv (hash + expected MCYCLE/MINSTRET), template 200 dong NOT_RUN; builder 11/11
  va audit 5/5 controls (`results/board_builder_guard_validation_20261009.json`, `results/board_preparation_audit_validation_20261009.json`).
- Readiness 2026-10-11 (`results/board_20261012/readiness.json`): checklist cu ghi RS-232, nhung SOF da fit dung UART JP5 GPIO 3.3 V
  LVTTL (TX = GPIO[0]/AB22, RX = GPIO[1]/AC15, USB-TTL CP2102, GND chung); da sua checklist va QUY_TRINH E. Baud that: divider 433
  >> 4 = 27 -> 28 x 16 = 448 clock/bit = 111,607 baud tai 50 MHz (-3.1 % so voi 115,200; dac tinh tu ban cong bo). Firmware boot
  ngay, khong cho KEY1: mo Hercules / log truoc khi nap. `program_board_case.ps1` chi lap ke hoach tru khi co `-Program`;
  `check_board_uart.py` so 28 truong UART.
- Kiem lai 2026-10-13 14:40 (moi kiem x2): manifest IDENTICAL; 4 project point chi khac CACHE_CONFIG 0/1/2/3, tham so trung top PD;
  hash SOF / firmware trung INDEX; 81 vi tri chan trung board cong bo.

### 3.3 Phien board 2026-10-13 (mot luot vat ly) [HT]

- Thiet bi: DE2-115, USB-Blaster USB-0 (chip ID 020F70DD), CP210x COM3, Hercules 3.2.8 (ban sao `tools/hercules`, nguon cong bo
  khong doi), 115200/8N1/handshake OFF.
- Noi day: CP2102 RXD -> JP5 chan 1 (TX AB22), RX AC15 = JP5 chan 2, GND = JP5 chan 12. Firmware in boot va full report truoc LEDR
  A5 roi lap, khong phat lai: mat capture thi can reset tay. Log UART dau (case 1, ramsweep DM) 0 byte vi HideReceived cua Hercules
  dang bat (tat bang command 38); menu Hercules doi vi tri khi doi NVT, nen doc trang thai checkbox theo command ID trong dung
  submenu, khong theo index. Hai diem nay can giu cho 58 case con lai.
- Pham vi (chot 16:10): chi pass 1 cho 100 case = 4 ramsweep + 48 Embench ban ngan + 48 Embench full iteration; pass 2 giu trong
  CSV voi `NOT_SCHEDULED_SINGLE_PASS_SCOPE`. Moi case dung cho xac nhan hien thi truoc case tiep theo. Ngoai le nay chi cho phep do
  vat ly; verification / Quartus / PD / power van chay hai luot. Helper `program_board_case.ps1` / `record_board_case.py` tu choi
  pass ngoai `scheduled_passes`; `hercules_case_ui.py --wait-done` cho dong DONE truoc khi flush log.
- Da do 42 case (15:22 - 17:24), moi case nap SOF moi mot lan, native exit 0; moi log UART du (boot .. DONE, RESULT=PASS) khop 28
  truong voi tham chieu. Kiem tra doc lap (`results/board_20261013_independent_check/`): 42/42, 25 bo dem + D_ACCESS trung CA HAI
  luot tham chieu RTL, VERIFY_CODE (gia tri tra ve cua kernel, khong phai ma loi) trung giua 4 cau hinh cua moi kernel, HEX = MCYCLE
  o moi case co doc hien thi (41 case co doc hien thi xac nhan). Bang chung: `results/board_20261013/` (`session.json`, `runlist.csv`,
  `results.csv`, `programming/`, `uart/`).

MCYCLE do tren board (hex, view FPGA), case 1-42 theo thu tu hang roi cot:

| workload (ban ngan) | DM | SA2 | DM_VC4 | DM_DSE | MINSTRET |
|---|---|---|---|---|---|
| ramsweep | 0003D520 | 0003D521 | 00041769 | 0003D521 | 00028073 |
| aha-mont64 | 00023DE3 | 00024837 | 00024837 | 00024837 | 00021C81 |
| crc32 | 00026CC2 | 0002E4DE | 0002E4DE | 0002E4DE | 0001CC5E |
| depthconv | 00023400 | 0002AB11 | 0002AB11 | 0002AB11 | 0001AC47 |
| edn | 00022301 | 000236C1 | 00023ECB | 00023EDB | 0001D78B |
| huffbench | 000540B8 | 000594EB | 00059A98 | 0005975B | 0003A5EB |
| matmult-int | 000223B2 | 0002332E | 0002468C | 00024B30 | 00014467 |
| md5sum | 0001F857 | 00022D91 | 00022FA5 | 00022CF1 | 000171BC |
| nettle-sha256 | 000231AE | 0002B143 | 0002C072 | 00025BCE | 0000F24D |
| slre | 00027DA6 | 0002F1AB | 0002F17B | 0002F18B | 00015A66 |
| statemate | 00021B5F | 00020925 | chua do | chua do | 0000A7EF |

So dem: 4 ramsweep + 9 kernel day du x 4 + statemate x 2 = 42. Con 58: 10 ban ngan (statemate DM_VC4 / DM_DSE, tarfind x 4, ud x 4)
va 48 ban full iteration. depthconv DM_VC4 va DM_DSE trung moi counter (victim hit I/D = 0/0, I miss 3, D miss 837, MCYCLE 174,865):
hai cau hinh dung chung controller DSE va victim probe to hop trong ST_LOOKUP; ramsweep phan biet ro (DM_VC4 D victim hit 16,
MCYCLE 268,137; DM_DSE 0, 251,169) (`results/board_20261013/cache_comparison_depthconv.json`). Moi so board la mot lan thuc thi vat
ly; ket qua cung cua cac lan khoi dong lai sau reset tay khong tinh la lan do thu hai.

## 4. LEC (tuong duong RTL - netlist da ky ten)

### 4.1 Phuong phap

- **EQY goc cua OpenLane khong bao gio xong tren thiet ke nay** (2026-09-23 .. 28): thieu make/grep trong shell nix `--pure`; crash
  `read_ids` Python; gioi han that: tong hop ma hoa lai 4 FSM sang one-hot, EQY ghep theo ten va cat tai net to hop, mot partition
  (`d_req_write`, ~16,700 flop) can hon 23 GB. Tot nhat 795/876 partition (chay doc lap); voi grep tren PATH: 10 partition roi FAIL
  o `LCD_EN`. Day la that bai cua cong cu goc, khong phai bang chung khong tuong duong.
- **Chuoi LEC anh xa thanh ghi tu viet** (`asic/equiv/lec/`): RTL == RTL + `fsm` (Yosys `equiv_make -encfile` / `equiv_induct`) == N1
  (trang thai tong hop truoc `abc -fast`, replay trung tung byte buoc 06) == netlist cuoi. Flop chi co o gold: chung minh hang (diem
  bat dong lon nhat), ban sao, hoac input tu do. Output con lai sau SAT tung output (32 bit `d_req_addr` + 2 kiem ban sao, deu sau bo
  nhan) dong bang chung minh dai so `macc_alg.py`: tich == signed33(A) x signed33(B) mod 2^64 o ca hai phia, noi bang `&cec`. Moi
  buoc chay hai lan va so hash; doi chung am: ma hoa FSM sai, spec nhan unsigned / tich rieng phan sai, netlist and2 -> or2. Macro
  SRAM la hop den hai phia (GLS phu phan nay). `&acec` tung bao "NOT EQUIVALENT" sai hai lan: chi tin khi bao equivalent.
- **Bo nhan va flop chi o gold.** SAT tung output khong dong duoc bo nhan vi `maccmap` nhom tich rieng phan theo trang thai tien
  trinh Yosys (40 % nut ben trong khong co doi tac); cach lam: chup mang o dung cach nhom cua synthesis (`techmap -max_iter 1`),
  kiem 5 techmap cell bang SAT, roi noi bang `&cec`. 235 flop chi o gold phai chung minh hang bang SAT: lay mau ngau nhien tung
  xep nham mot flop. Ban sao do `opt_merge` duoc trich tu RTL va tu kiem.
- **SEC ABC** (`asic/equiv/sec/`): cat 12 SRAM, ep reset o chu ky 0; doi chung am bat duoc o frame 0 va frame 19 (gioi han 19 chu
  ky, muc 4.2).
- **Gioi han.** Tuong duong tuan tu khong anh xa thanh ghi khong kha thi o kich thuoc nay voi cong cu mo nguon. Chung minh voi gold
  `rtl_r14` khong phai chung minh cho layout `6c4ccffd`.

### 4.2 Dien bien

| Ngay | Doi tuong | Ket qua | RTL | Bang chung |
|---|---|---|---|---|
| 2026-09-27 | DM 8 KiB final_A | `fsm` 4 FSM, 36,303 `$equiv`; SEC ABC gioi han 19 chu ky (khong gioi han: UNDECIDED); LEC anh xa: 19,881 output, 0 phan vi du, 235 flop hang, bo nhan 1,128 don thuc (~2 s) | [LS] 8b163675 | `asic/equiv/lec/`, `asic/equiv/sec/` |
| 2026-09-28 | DM 8 KiB final3_A/B | N1 == netlist ca hai: equivalent | [LS] | |
| 2026-10-09 | DM 16 KiB r14F_A/B | buoc A: 19,458 / 19,090 bit flop, 20,124 output, 235 hang, 28 ban sao, 34 output bo nhan dong; buoc B: 19,090 / 19,087, 20,096 output, 0 phan vi du; luot 2 trung hash; NegB 184 SAT | [LS] rtl_r14 | `run_lec_r14.ps1`, `run_lec_r14_mul.ps1`, `run_lec_r14_pass2.ps1` |
| 2026-10-09 | SA2 replay N1 | replay 1 hook (`SYNTH_PY=synthesize_n1only.py`) trung tung byte buoc 06 (`46e3066895914f1a`); 4 hook khac (77,157 vs 77,562 cell); chuan bi front end 77 input + 24 artefact | [LS] | `asic/equiv/lec/synth_replay_r14/sa2_rsztf_r1_n1only/`, `results/completion_preparation_20261009/sa2_lec_20261009/` |
| 2026-10-10 | DM: thu hep pham vi | legacy chi lay mau reset va bo clock khoi D-function; khong con claim full LEC vo dieu kien; `scripts/verification/lec_reset_base.py` chi chung minh reset gold; cong thuc raw-frontend khong gioi han chuan bi, chua chay | [LS] | `results/lec_proof_scope_20261010.md`, `results/dm_raw_frontend_preparation_20261010/` |
| 2026-10-10 | DM sub-proof | reset base 235 hang / 28 ban sao / 4 FSM x2; clock 4 mo hinh phang x2; AXI 6 cofactor (36,864 phep gan/luot); ALU 14 case CNF; bat bien dong thoi 286 nghia vu; pha reset 1,716 nghia vu; review doc lap moi muc | [LS] | muc 4.3 |
| 2026-10-10 | DM definedness | BHT, UART baud, I$ hot-array, RAM chinh: 310 / 358 dong X/Z connect dong cuc bo, 48 con mo | [LS] | muc 4.3 |
| 2026-10-13 | DM + SA2 premises | `asic/equiv/lec/arst_audit.py`: reset bat dong bo: DM 19,087 bit (7,519 co reset + 11,568 khong), SA2 20,462 (8,074 + 12,388), 0 sai khac; clock SA2; one-hot DM chung minh lai | [LS] | `results/lec_arst_audit_20261013/`, `results/lec_clock_audit_sa2_20261013/`, `results/lec_dm_inv_20261013{,_p2}/` |
| 2026-10-14 | DM + SA2 undefined | `run_xsens.ps1`: DM 1,401 nguon -> 20,124/20,124 UNSAT; SA2 1,552 -> 21,489/21,489; thay the viec dong tung dong X | [LS] | |
| 2026-10-13/14 | SA2 day du | `fsm` 38,300 cell; A: 20,803 gold / 20,465 cap, 338 chi gold = 231 hang + 18 ban sao + 89 tu do; 21,489 output; B1/B2: 20,462 cap, 21,471 output, 0 SAT; hai luot (p1, p2b) 39 doi tuong trung (`PASS1_EQUALS_PASS2`); NegFSM 10 unproven; NegB 60 SAT | [LS] rtl_r14 | `asic/equiv/lec/run_lec_sa2.ps1`, `results/lec_sa2_20261013/p1`, `p2b`, `results/lec_sa2_20261013/pass_comparison.json` |
| 2026-10-14 | DM_VC4 phan tong hop | lan a dung (8 macro way 1 khong doc -> `asic/equiv/lec/sram_align.py`, doi chung `NegAlign`); lan b (`results/lec_vc4_20261014b`) dung (thu tu input AIGER lech 771 vi tri: Yosys `write_aiger` xep theo thu tu khai bao); lan c dung (kiem t1 qua chat); lan d: hai luot tron, `fsm` 39,000 cell, 21,828 / 21,093 bit flop, 735 chi gold = 364 hang + 18 ban sao + 353 tu do, 22,117 output 0 SAT, X 1,796 nguon UNSAT | [LS] | `results/lec_vc4_20261014d/pass_comparison_goldn1.json` |
| 2026-10-15 | LEC tren `6c4ccffd` | chuan bi `scripts/verification/prepare_lec_6c4c.py`, `scripts/maintenance/run_lec_6c4c_goldn1.sh` (commit `d0d2a35`); chua co ket qua ghi nhan | [HT] | |

Moi tuong duong cua netlist N-way / FAST_HIT so voi netlist PD (khac tung byte do Yosys nhay ten) duoc chung minh muc SoC (muc 1.1)
thay vi so byte.

### 4.3 Bang chung sub-proof DM (2026-10-10) [LS]

| Sub-proof | Ket qua | Receipt |
|---|---|---|
| Reset base gold | 235 hang, 28 ban sao, 4 nhom FSM; 2 doi chung duong + 24 am | `results/dm_reset_base_structural_20261010_p{1,2}.json`, `results/lec_reset_base_controls_20261010.json` |
| Clock / canh | 4 mo hinh phang, canh len, `clk` vo huong | `results/dm_lec_clock_audit_20261010/receipt.json` |
| AXI one-hot | 6 cofactor, BDD + vet can 36,864 phep gan/luot | `results/dm_onehot_boolean_20261010_verification.json`, `results/dm_axi_exhaustive_audit_20261010_receipt.json` |
| ALU one-hot | 14 case CNF chinh xac (4,958 bien / 12,142 menh de moi case), review replay 28 proof / 73,296 buoc resolution | `results/dm_alu_onehot_cnf_20261010_verification.json`, `results/lec_onehot_cnf_independent_review_20261010.json` |
| Bat bien dong thoi | 286 nghia vu (235 hang + 28 ban sao + 23 ma hop le); review 266 structural + 40 CNF, 74,938 buoc | `results/dm_joint_invariant_20261010_verification.json`, `results/lec_joint_invariant_independent_review_20261010.json`, `results/lec_joint_reset_base_independent_review_20261010.json` |
| Pha reset | 1,716 nghia vu/luot (1,696 structural + 20 CNF); TypeError o lan review dau, retry nguyen lenh PASS | `results/dm_reset_phase_20261010_verification.json`, `results/lec_reset_phase_independent_review_20261010.json`, `results/lec_reset_phase_review_execution_20261010.json` |
| Definedness BHT | 257 dong; review doc lap 256 dia chi doc, 1,024 / 2,048 ca update | `results/lec_source_definedness_20261010_verification.json`, `results/bht_read_default_definedness_20261010_verification.json`, `results/bht_definedness_independent_review_20261010.json` |
| UART baud | default PMUX 16 bit (20832/10416/5207/433) | `results/uart_baud_default_definedness_20261010_verification.json`, `results/uart_baud_definedness_independent_review_20261010.json` |
| I$ hot-array | 3 PMUX, 24 index tu do, 1,224 bit du lieu symbolic | `results/icache_hot_default_definedness_20261010_verification.json`, `results/icache_hot_definedness_independent_review_20261010.json` |
| RAM chinh | 49 default, 392 ca bank, 98 loi selector/du lieu thuc | `results/ram_bank_default_definedness_20261010_verification.json`, `results/ram_bank_definedness_independent_review_20261010.json` |
| Khoi tao mo hinh | 11,560 trang thai chua reset duoc phan loai, khong gan 0 | `results/lec_model_initialization_audit_20261010.md` |

Ban do 97 dong X con mo truoc proof RAM: `results/lec_source_x_remaining_20261010/` (sau do con 48 = 14 PMUX + 7 mux + 27 module
connect). Muc nay duoc thay the ngay 2026-10-14 boi chung minh `run_xsens` (moi output doc lap voi moi gia tri khong xac dinh).

## 5. Cong suat theo hoat dong

Phuong phap (`asic/gls/`): GLS netlist sau fill (model cell chuc nang, model OpenRAM) cho 12 kernel; cua so tu `sysmon_clear_start()`
toi `sysmon_freeze_snapshot()`; SAIF -> `saif_to_pins.py` (gan net vao chan; OpenSTA 2.6 `read_saif` bo qua net phang; chay Python
phia Windows) -> OpenSTA voi lib / SPEF RCX / SDC cua buoc STAPostPNR, goc nom_tt_025C_1v80. Kiem truoc khi tin so: vectorless phai tai
lap so cua flow; bao cao ty le "unknown". `power__total` cua flow la goc max_ff, khong phai tt.

| Ngay | Doi tuong | Ket qua | Ghi chu |
|---|---|---|---|
| 2026-09-25 | r8_a0c4 crc32 | 116.15 mW (vectorless 102.96) | so dau tien [LS] |
| 2026-09-27/28 | DM 8 KiB final_A / final3 | 111.03-116.02 / 110.61-115.43 mW; EPI final3 2,379-3,637 pJ | [LS] |
| 2026-10-02 | DM r14F_A, STA luot 1 | 114.81-122.99 mW (TB 119.45), unknown 5.38 % | [LS] |
| 2026-10-09 08:14 UTC | SA2 ecomaxmin_r1 | GLS 12/12 (`results/gls_power_sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/`); hai phien OpenSTA doc lap tu cung SAIF: 127.45-131.75 mW (TB 129.64), EPI GM 4,317 pJ, unknown 4.42 % | `_power_p1.csv`, `_power_p2.csv`, `_power_verification.json` [LS] |
| 2026-10-09 17:03 | DM r14F_A: thieu bang chung luot 2 (dinh chinh) | `results/gls_power_r14F_A/` chi co 12 report power va vectorless luot dau, khong co `.power.p2.rpt` hay receipt chay kep -> RESULTS / REVIEW_RESPONSE danh dau cong suat va EPI DM chua du bang chung | chuan bi Pass 2 (hash 12 pin-SAIF, netlist, SPEF, dau vao): `results/dm_activity_power_second_pass_preparation_20261009.json`; chay xong 2026-10-10 (hang duoi) [LS] |
| 2026-10-10 02:00 | DM STA luot 2 | 13 phien moi (12 kernel + vectorless), moi nhom/nguon trung luot 1 | `results/dm_activity_power_second_pass_20261010.json` [LS] |
| 2026-10-10 14:22 | Audit cua so | 24 SAIF DM/SA2 dai `(mcycle+1) x 20 ns`; cot `win_t*_ns` thuc chat la ps; STA van tai lap voi dau vao cu | `results/embench_gls_evidence_audit_20261010/receipt.json` |
| 2026-10-10 14:29 | Kiem bien bo dem | 2 compile rieng, N=1/2/17 moi luot, 6 doi chung mo phong: observer cu `freeze_q` cho count N nhung wall time (N+1) x 20 ns -> nguyen nhan SAIF cu dai `(mcycle+1) x 20 ns`; observer `counter_freeze` thuc + khoang dong doc lap +1 cho count N, wall time N x 20 ns; nguon `perf_counters` / `apb_performance_monitor` trung byte snapshot PD. Chi la kiem bien nguon, khong phai GLS mapped / cong suat | `results/embench_gls_evidence_audit_20261010/counter_boundary_controls/receipt.json` |
| 2026-10-10 19:37 | Observer freeze moi | 65 nghia vu/design (DM, SA2) x2; review replay 252 chung chi CNF / 340,338 buoc | `results/mapped_counter_freeze_checked_20261010/` |
| 2026-10-10 .. 13 | DM exact-window | screening `up_ud` (`results/gls_exact_dm_ud_screen_20261010/receipt.json`, SINGLE_SCREEN_NOT_RESULT); luot 1 12/12 (`results/gls_exact_dm_full_p1_20261011/receipt.json`, 2026-10-11 06:48); luot 2 (`results/gls_exact_dm_full_p2_20261011/receipt.json`): TypeError chuyen doi Windows, retry moi (cap `results/gls_exact_dm_full_pair_retry_20261011.json`; thu muc cong suat du kien `results/activity_power_exact_dm_20261011/`, `results/activity_power_exact_dm_retry_20261011/` khong ra ket qua; cap goc `results/gls_exact_dm_full_pair_20261011.json`), Errno22 doc lib qua UNC, noi tiep tu tien to native (`results/gls_exact_dm_p2_continuation_20261012/`); STA dung o guard bo nho, roi access violation 2026-10-13 05:29; chay ghim CPU 2 xong 14:56: 114.81-122.99 mW (TB 119.45), EPI GM 3,608 pJ, lech <= 0.005 mW so voi SAIF cu | `results/activity_power_exact_dm_20261013/receipt.json` [LS] |
| 2026-10-14 | SA2 exact-window | hai GLS (`results/gls_exact_sa2_full_p{1,2}_20261014`, cap `results/gls_exact_sa2_full_pair_20261014.json`, 03:25 UTC) + 26 OpenSTA; 127.45-131.75 mW (TB 129.64), EPI GM 4,317 pJ; lech <= 0.005 mW | `results/activity_power_exact_sa2_20261014/receipt.json` [LS] |

Ket luan: chu ky thua 20 ns trong SAIF cu khong anh huong dang ke (DM va SA2 deu lech <= 0.005 mW). Moi so tren deu tren layout R14
nen la [LS]; can lam lai GLS + cong suat tren layout `6c4ccffd` duoc chap nhan.

## 6. Ha tang flow PD va cong cu chan doan

### 6.1 Ha tang flow: phan them vao openlane-local va gate scripts

Moi phan them mac dinh tat (tru khi ghi khac) va chi bat qua config; chi sua khi khong co flow chay.

| Ngay | Phan them | Muc dich / bang chung |
|---|---|---|
| 2026-09-22 | `set_thread_count 1` trong `antenna_check.tcl` / `antenna_repair.tcl` | race OpenMP trong `boost::polygon` (8 crash); `OMP_NUM_THREADS=1` khong co tac dung |
| 2026-09-24 | `yosys.py`: `@NETLIST@` / `@PDK_FORMAL@` cho EQY | script EQY tro vao netlist cua run cu |
| 2026-09-25 | Magic `drc.tcl` (GDS cell chuan + macro truu tuong, `MAGIC_DRC_USE_GDS true`), `read.tcl` | 4,187 loi `nwell.4` la hien vat view LEF; noi bo macro do KLayout kiem |
| 2026-09-26 | `asic/run_pd_mk.sh` them GNU make, grep vao PATH | shell nix `--pure` khong co make/grep cho EQY |
| 2026-09-27 | `DRT_ANTENNA_REPAIR_ITERS` / `_MARGIN` (vong sua antenna sau detailed route trong `drt.tcl`) | OpenLane 2.3.10 chi sua antenna tren global route; 140 -> 1 net, roi 0/0 |
| 2026-09-27/28 | `LAYERS_RC`, `LAYERS_RC_SCOPE` | uoc luong RC thap hon RCX 1.93-2.37x (muc 9) |
| 2026-09-28 | `OpenROAD.MacroPinBuffers`, `OpenROAD.PostRouteHoldECO` | buffer chan macro; ECO hold tren RCX + DRT tang dan + vong antenna; loi tat dinh da sua khi viet: thieu bien RCX, `global_route -start_incremental` segfault trong tien trinh moi, `detailed_placement` lat lai huong moi cell da route (giu cell cu FIRM), access point cua master cu sau khi doi kich thuoc (chay `pin_access` truoc GRT). Cung dot: clock goc la day 2.5 mm khong buffer vi uoc luong RC thap -> `CTS_CLK_MAX_WIRE_LENGTH 800` (gia tri nay DM 16 KiB-RAM va SA2 con ke thua, muc 8.2) |
| 2026-09-30 | `SYNTH_OPT_DFF_SAT` | DM_VC4 giu 4 macro chet cua way 1 D$; voi SAT con 8 macro |
| 2026-10-03 | flow co cong `asic/run_gated_pd.sh`, `asic/drt_watch.sh`, `asic/fp_tools/gate_check.py` | dung som khi that bai; nguong o QUY_TRINH D |
| 2026-10-06/07 | hieu chinh nguong drt_convergence; `grt_repair_overflow` doc route lai tu dau trong RepairAntennas | nguong dau dung nham run SA2 dang hoi tu |
| 2026-10-07 | `DRT_DRC_REPORT_ITER_STEP` | bao cao DRC moi 5 vong de chan doan |
| 2026-10-08 | ECO hop phap hoa voi padding 0; `POST_ROUTE_ECO_SETUP` (+ `_MARGIN`, `_MAX_BUFFER_PCT`, `POST_ROUTE_ECO_CORNERS`), `POST_ROUTE_ECO_HOLD` | DPL-0033 do padding sau route; ECO setup chi dung SPEF |
| 2026-10-09 | `G5_UNLIMITED_LATE_PHASE=1`, `P2_INITIAL_GRT_FALLBACK=1` | khong gioi han sau vong 40 (`results/drt_watch_rule_alignment_20261009/`); doc p2 khi tat sua design sau GRT (34 controls, `results/gate_p2_no_repair_20261009/verification.json`) |
| 2026-10-11 | `HOLD_AFTER_DRT=1` | giu truoc P4 de kiem tai nguyen (`results/gated_resume_phase_hold_20261011.json`) |
| 2026-10-12 | `P4_RESOURCE_WAIT=1` (`asic/run_resource_gated_resume.sh`) | doi Windows / WSL >= 15,000 MiB truoc sign-off |
| 2026-10-13 | `DRT_SAVE_MAIN_ROUTE`, `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION` | giu `main_route.odb`; cho nghen trong vong sua antenna (GRT-0232) |
| 2026-10-13 | `POST_ROUTE_HOLD_ECO_RCX_CORNER_2`, `P2_MIN_HOLD` | ECO hold hai luot trong mot buoc (trung tung byte quy trinh nhanh: `asic/soc_sa2_4kb/eco2pass_check_20261013/`); nguong hold p2 khai bao luc khoi dong (`asic/fp_tools/check_p2_min_hold_20261013.sh`) |
| 2026-10-14 | `G5_ANT_ROUND_RULES=1` (`drt_watch.sh`) | luat rieng cho cac lan goi detailed_route sau vong sua antenna |

### 6.2 Cong cu chan doan PD (chi doc)

| Cong cu | Dung de | Them ngay |
|---|---|---|
| `asic/fp_tools/guide_demand.py` | ban do nhu cau dinh tuyen tu guide, hieu hai guide | 2026-10-07 |
| `asic/fp_tools/region_cells.py`, `net_probe.py` | thanh phan cell trong o; chan / guide cua net | 2026-10-07 |
| `asic/fp_tools/pin_hotspots.py` | du bao diem nong DRT (mat do chan / 100 um2, o 20 um); DM hoi tu nhanh o max ~29, SA2 can 54 vong o max 32 | 2026-10-08 |
| `asic/fp_tools/clock_detour.py`, `clock_layers.py` | chieu dai guide clock so voi HPWL; chieu dai than clock theo lop | 2026-10-09 |
| `asic/fp_tools/grt_skew_screen.sh` | skew ngay sau GRT dau cua mot run (WSL) | 2026-10-09 |
| `asic/sta_query/` | truy van STA tren run da ky (nap dung lib / SPEF / SDC cua STAPostPNR) | 2026-09-26 |
| `asic/gls/gls_power_csv_rebuild.sh` | dung lai CSV cong suat GLS | 2026-10-09 |

## 7. ASIC giai doan dau: 1 KiB va 4 KiB toi RTL dong bang (2026-09-18 .. 2026-09-25) [LS]

- **Moc 1 KiB `sync_final` (2026-09-18, `asic/soc_dm_control/runs/sync_final`, ten moi `dm_c1k_baseline`).** Tag dong bo lam ASIC
  lon hon (+2.9 % cell; khong co macro vua mang tag nen tag van la flop). Hai run dung o GRT-0118: bon macro 2 KiB xep mot cot,
  cell chen trong dai 955 um; xep bon goc thi qua. CheckAntennas segfault do LEF OpenRAM khong co thuoc tinh antenna (them
  `ANTENNAGATEAREA 0.126` / `ANTENNADIFFAREA 0.4455`). Ket qua: die 1800 x 2900 = 5.22 mm2, 186,877 cell, DRC 0, 7.30 m day; hold
  +0.0919 ns, setup tt/ff +2.80 .. +5.68, ss -13.26 ns (8,846 path); 196.4 mW nom_tt vectorless. Do lai voi SDC dung: setup tt +3.16,
  hold tt -0.048 / ss -0.123 / ff -0.146 ns (`asic/evidence/sdc_recheck_1kb_research/`).
  Chi tiet: dien tich instance 2,720,150 um2 (macro 1,138,150 + cell 1,582,000), util 53.35 % (cell 39.94 %); 27,642 cell tuan tu,
  6,603 diode; max cap 658, max slew 4,730; 196.4 mW = internal 108.6 + switching 87.7 (to hop 86.3, tuan tu 58.3, clock 40.6, macro
  11.2); ReportDisconnectedPins 44 chan = 44 tie cell `conb_1`, 0 critical. Moc 1 KiB chua tung dat 0 antenna: 1,848 net / 2,736 pin
  truoc repair -> 498 / 643 sau (910 diode); `sync_final` 501 net sau repair (cong sign-off hien nay doi 0).
- **Floorplan 12 macro 4 KiB (2026-09-19).** Phuong an: hai cot (hanh lang 990 um) bo; dai ngang 2600 x 2500 chong lan 26 um;
  2800 x 2400 sach (6.72 mm2, util 57.2 %). GlobalPlacement crash 3/3 trong resizer timing-driven (tat dinh) -> `PL_TIME_DRIVEN
  false`; DPL-0036 -> density 48 -> 40 roi `PL_MAX_DISPLACEMENT_Y 100 -> 500`, `X 500 -> 1000` (util cell chi 28 %, gioi han dich
  chuyen moi la rang buoc). `GRT_OVERFLOW_ITERS 20` va `GRT_ALLOW_CONGESTION` khong tac dung, bo. Die 2800 x 2400 -> 2800 x 2900:
  +35.6 % tai nguyen met1 sau derate, util 57.2 -> 46.4 %; 12 macro chiem 40 % die nen khong kich thuoc nao dat ca util 60-70 % lan
  routability. Nguyen nhan that cua nghen: kenh thoat chan (khe 18 / 33.5 / 41.5 um cho 216 / 401 / 175 chan, trong khi dai trong
  1552 um khong co chan; ban 1 KiB co 138 / 171.5 um cho ~144 chan, ~11 lan track/chan); `macro_placement_channels.cfg` chia lai
  chieu cao trong (300 / 450 / 450 / 445.4 um): kenh xau nhat 49 -> 661 track met3.
- **So post-route 4 KiB dau (2026-09-23).** Detailed routing 99,784 -> 0 trong 9 vong, 8.20 m day; setup nom_tt -1.005 ns, hold truot 9
  goc (-1.436, TNS -59.0), skew -4.128 ns; cong suat 173.7 mW (1 KiB 233.7). `MAX_SLEW/CAP_VIOLATION_CORNERS` la `['']` nen checker
  khong kiem goc nao (10,914 slew / 1,744 cap): dat `['*tt*']`. Run thu hai bat cac co che sua nhung duoc tiep tuc tren database
  da detailed route (GRT-0226) nen so khong dung duoc; ba gia thuyet truoc do deu sai.
  Dien tich instance 4 KiB post-route dau 3,944,670 um2 (1 KiB 2,720,150). Antenna 4 KiB: 2,139 -> 465 net (9,579 diode) sau
  `set_thread_count 1` (2026-09-22, muc 6.1); 2026-09-23 con 429 net, 94.5 % tren cell thuong.
- **SDC (2026-09-24).** `set clocks [create_clock ...]`: `create_clock` khong tra ve gi nen uncertainty, transition va moi I/O delay
  bi bo (muc 9). Tu day: thay doi tu tong hop tro di phai chay full flow tu buoc 1.
- **RTL dong bang dau (2026-09-25):** `rtlfix_c235` nom_tt -0.272 / max_tt -0.477, ss -11.75; `r8_a0c4` (die 8.12 mm2, 195,518 cell)
  nom_tt -0.569 / max_tt -0.827, DRC 0, LVS khop, antenna 578, 102.96 mW (154.34 mW cua run truoc la hien vat cua `reset_n` chua dong
  bo); GLS 12/12 (`results/gls_r8_a0c4.csv`). Bon thi nghiem PD chi doi resizer / margin / placement: -0.63 .. -1.01 ns (suy giam
  GRT -> RCX ~0.65-0.7 ns lon hon moi bien resizer tao duoc, nen chi doi PD khong dong tt); clock 21.5 ns bo (50 MHz bat buoc). Kham
  pha tong hop (buoc 35, sau CTS): AREA 0 -0.788, AREA 1 -0.177, AREA 2 -0.394, AREA 3 +4.326, DELAY 0..4 +0.13 .. +2.64 ns; AREA 3
  dung o GRT-0118 (`buffer -c -N 8` viet cung); AREA 3 + `DESIGN_REPAIR_REMOVE_BUFFERS` route duoc (+4.553 ns sau GRT) nhung tren
  RTL `358cb660` lai nghen GRT; DELAY 1 nghen; gate cloning khong co loi (giu tat) -> chon tong hop phai co tieu chi routability.
  Sau RTL `358cb660`: `r7r8_358c` nom_tt +2.190 / max_tt +1.974 (lan dau dat tt), ss -11.20 / -12.26.
- **Driver PD (2026-09-25).** `asic/pd_driver.py` thay `ch4kb_run.sh` (resume tu buoc bi gate tat lam RepairAntennas chay lai tren
  database da sua, xem muc 9 "Bay trang thai run OpenLane"): danh sach buoc theo gating cua `classic.py`, kiem chuoi
  `state_in == state_out` cua buoc truoc, cach ly thu muc step do dang, chi thu lai crash native.

## 8. ASIC theo cau hinh (sky130A, sky130_fd_sc_hd, OpenLane 2.3.10 ban sao `asic/openlane-local`, chu ky 20 ns)

### 8.1 DM

| Ngay | Run (ten cu) | Thay doi | Ket qua | Nguyen nhan / ghi chu |
|---|---|---|---|---|
| 2026-09-26 | r9_ecf4, r10A | RTL `ecf4fc03`, `d030ad12` | tt +2.878 / +1.721; max_ss -7.575 / -9.518 | bien dong PD giua netlist ~1 ns (tt), vai ns (ss): mot lan chay khong phan dinh duoc mot thay doi RTL ~2 ns |
| 2026-09-26 | mau mat do 38 / 40 / 42 | RTL `8b163675`, cung netlist; diode heuristic > 250 um, GRT hold margin 0.1, setup truoc hold, setup margin 2.0 | chon 42 (`config_FINAL.json`): max_tt +1.960, max_ss -8.335; dai bien dong do placement tt 0.25 ns, max_ss 1.26 ns | quy tac chon ghi truoc: max_tt, max_ss, dien tich; dai 0.25 / 1.26 ns la thuoc do de danh gia mot thay doi PD; ba lan chay doc lap (mau 42, final_A, final_B) trung moi chi so STAPostPNR va hash netlist / DEF |
| 2026-09-27 | final_A / final_B (`dm_ram8k_grid2800x2900_heurdiode_r1/_r2`) | ky ten dau 8 KiB-RAM | DRC/LVS/XOR 0, hold 0, IR drop 0.43 mV; nom_tt +2.112 / max_tt +1.960, nom_ss -7.436 / max_ss -8.335; antenna 140 net / 159 pin; 1.453 mm2 / 212,196 cell; 102.24 mW vectorless (`power__total` flow 115.73 mW la goc max_ff) | antenna chi sua tren global route; bi thay the; golden v1 (ghi chu duoi bang) |
| 2026-09-27 | final2_A (`..._drtant_rc2`) | + `LAYERS_RC` | nom_ss -8.973 / max_ss -9.518, 3 hold max_ff | loai |
| 2026-09-28 | **final3_A / final3_B** (`dm_ram8k_grid2800x2900_drtant_r1/_r2`) | `config_FINAL3.json`: bo diode heuristic + sua antenna sau DRT (5 vong, margin 10) | KY TEN, golden: 302 metric trung, netlist `326cc257`, DEF `2f31dfab`; antenna 0/0; 1.400 mm2 / 192,005 cell; nom_tt +2.086 / max_tt +1.960; nom_ss -7.413 / max_ss -8.311 | final3_B chay lai tu buoc 1 mot lan va tiep tuc hai lan sau crash ngau nhien; bang chi tiet `results/FINAL_METRICS.md` trong git truoc 2026-10-07 [LS] |
| 2026-09-28 .. 30 | x_E1..x_E6, X1..X4, f3_H1/H2 | buffer chan macro, clock goc, hold ECO, AREA 3, gioi han day, hold margin, mat do 55 | khong nang golden (f3_H2: +2.442 / +2.312 tt, max_ss -9.023, cell 1.2835 mm2; max_ss xau hon final3 0.71 ns) | goc ss can pipeline moi (muc 9 "Goc ss") |
| 2026-09-29 | r14_A, r14_E6 .. E16 | RAM 16 KiB, die 3665 x 2900 (+31 %) | E6: max_tt -0.162 (duong dout RAM -> mux bank -> mux nap D$ ~5 mm trong nua chu ky); bang knob duoi day | E16 = cau hinh ky ten |
| 2026-09-29 .. 10-02 | **r14F_A / r14F_B** (`dm_grid3665x2900_r1/_r2`) | `config_R14_FINAL.json` | KY TEN 2026-10-02: 319 metric trung, netlist cuoi sha256 `83f38f7e...` ca hai (buoc 55 / 56); so: RESULTS 4.1, `results/asic_compare_dm_r14.md` | phien ket thuc 2026-09-30 ~23:38 UTC giet ca hai; resume 2026-10-02 bang `run_resume_retry.sh` (r14F_A tu Magic streamout, r14F_B tu buoc 47); khong nang golden vi la diem thiet ke khac (RAM gap doi), bao cao rieng; khong nam trong golden nao, chi trong workspace (muc 10) [LS] |
| 2026-10-06/07 | dmuA / dmuB (`dm_corr3400x3325_f220_r1` / `dm_corr3400x3400_f220_r1`) | floorplan hanh lang chung | sign-off sach, mot luot (ss max -8.754 / -10.043) | doi chung cung die; xoa 2026-10-15 sau archive [LS] |
| 2026-10-14 | `dm_grid3665x2900_r3` | lan chay tron theo quy tac Q (snapshot `rtl_r14`) | OpenLane segfault ngay sau buoc 40 (khong state_out), STAMidPNR-3 khong chay -> STOP after P2 | ngau nhien, khong phai loi thiet ke |
| 2026-10-14 | `dm_grid3665x2900_r4` | nhu r3 | P1 PASS (+2.164 / +0.184), P2 PASS (overflow 0, +1.725 / +0.186); dung o cong DRT 14:11 UTC (co hop tac) khi PD chuyen sang `6c4ccffd` | netlist/metric trung r14F_A toi buoc 42 (r14F_A STAMidPNR-3 +1.756 / +0.201), nhung DEF buoc 41 co 2 buffer (`wire10760`, `wire10761`) lat S/FS -> RepairAntennas 350 net / 6,249 diode (r14F_A 322 / 6,262), layout tach nhanh |
| 2026-10-14 | `dm_grid3665x2900_rtl6c4c_r1` | `config_R14_FINAL_rtl6c4c.json` (chi doi `VERILOG_FILES` sang `rtl_rfbht`) | p1 FAIL: STAMidPNR-2 setup nom_tt +0.307 < `P1_MIN_SETUP` 0.5 | 71,006 cell (R14 70,441), tong hop `da06d38f`; duong xau nhat RAM bank[3] -> refill bank du lieu D$ (nua chu ky) |
| 2026-10-15 | `dm_grid3665x2900_rtl6c4c_r2` | `P1_MIN_SETUP=0 P2_MIN_SETUP=0` khai bao luc khoi dong; gate sign-off giu nguyen | dang chay (`asic/sequence_heavy_20261015g.sh`, 00:18 UTC) | [HT] |

Ghi chu cac hang DM 8 KiB-RAM (2026-09-27 .. 30) [LS]:
- **Golden.** v1 `E:/Projects/RISCV-research_GOLDEN_20260927` (2026-09-27, final_A / B, 19,373 file) hard-link ca `transcript`
  va vsim ghi de tai cho -> v2 `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928` (22,656 file, sha256 tung file, `--diff` /
  `--restore`) chi hard-link artefact bat bien. Quy tac tu 2026-09-28: chup golden truoc moi thay doi; moi thi nghiem chay tag
  moi, khong resume vao run da ky ten.
- **Ket qua tung knob tren final3 (hang x_E / X; STAPostPNR, tu trang thai sau GPL cua final3_A).** Gioi han day 800 um -> slew /
  cap nom_tt 536 / 439 nhung 1 vi pham hold; buffer chan macro + clock goc + hold ECO: slew 80, hold +0.061 nhung tt giam 0.5 ns
  (cay clock moi doi skew co loi cua duong nua chu ky); AREA 3 + go buffer: max_ss -8.339 (khong doi), day +22 %, DRV x5, 30 vi
  pham hold -> AREA 3 khong phai loi giai goc ss; `repair_design` sau route tren SPEF: max_ss -12 .. -13 ns (doi kich thuoc hang
  nghin cell) -> giu tat; buffer tang truoc: slew 47 (44 chan SRAM).
- **f3_H1 / f3_H2.** f3_H1 (final3 + bien hold 0.02 + hold ECO tren RCX): cell 1.3996 -> 1.2153 mm2 (-13.2 %), hold sach, nhung
  max_ss -10.930 (xau 2.6 ns) -> khong nang golden. f3_H2 (final3 + mat do 55 + bien hold 0.03 / ECO 0.02 + cum CTS 8, xong
  2026-09-30 12:30 UTC) bo sung cho hang tren: nom_ss -8.248, hold +0.021 (0 vi pham), 180,453 cell, slew / cap nom_tt 1,250 / 706,
  antenna 0, route DRC 0. Cung cong thuc bien 0.03 / ECO 0.02 trong ban 16 KiB-RAM ky ten bo ~172,000 um2 buffer hold (cell
  1.3696 mm2; muc 9 "Buffer hold").

Quet knob DM 16 KiB-RAM tu trang thai sau global placement (2026-09-29, STAPostPNR, mot lan moi bien the) [LS]:

| knob (cong don) | max_tt / nom_tt | max_ss | cell mm2 | ghi chu |
|---|---|---|---:|---|
| resizer chi tt + ff | -0.486 / -0.268 | -12.92 | 1.578 | loai |
| cap margin 20 / 10 | +1.145 / +1.275 | -9.474 | 1.519 | |
| + GRT cap margin 50 | +1.197 / +1.322 | -8.284 | 1.545 | slew / cap 110 / 310 |
| + day toi da 1000 um | +1.510 / +1.654 | -8.804 | 1.545 | loai |
| + cum CTS 8 | +1.699 / +1.800 | -8.357 | 1.541 | fanout 2,366 -> 1,379 |
| + bien hold 0.03 / ECO 0.02 | +1.197 / +1.342 | -8.397 | 1.372 | buffer hold 18,259 -> 1,032 |
| + mat do 55 % | +1.766 / +1.910 | -8.117 | 1.514 | tot nhat tt, ss, cong suat, day |

`config_R14_FINAL.json` = mat do 55 + bien hold 0.03 / ECO 0.02 + cum CTS 8 tren nen GRT cap margin 50. Dinh chinh 2026-10-14: ma
netlist cuoi DM dung la sha256 `83f38f7e...`; ma `7ae150fe` ghi truoc day khong khop file nao con lai.

Thac dien tich (2026-09-30, DEF sau fill + liberty): final3 1,399,590 um2 trong do buffer hold 189,693 (19,019 cell, 13.6 %); ban
16 KiB-RAM thi nghiem E10 1,544,690 um2 (+84,449 buffer "wire" do `LAYERS_RC`, +22,982 tap).

### 8.2 SA2

| Ngay | Run | Thay doi | Ket qua | Nguyen nhan / ghi chu |
|---|---|---|---|---|
| 2026-09-30 | wrapper `asic/dse_sram/cache_dse_data_bank_sram.v` | SA2: 2 lane/macro (128 set/way; lane 2j hang 0-127 doc cong 1, lane 2j+1 hang 128-255 doc cong 0 khi khong ghi), 4 macro/cache | view ASIC 12 kernel x2 = view FPGA (33 truong), shadow 0 lech | tong hop SA2 1,051,715 um2 (+7.6 % so voi DM 977,837 um2). Ca SA2 va DM_VC4: doc trong khi ghi cung chi so chan doc lane do, giu lan doc truoc; shadow chi mo phong so `rd_line` voi mo hinh bank thanh ghi moi chu ky (`$fatal` khi lech) |
| 2026-10-02 | sa2F_A/B (luoi DM) | knob DM, mat do 55 / 42 | GRT-0118, overflow 67,971 | nhu cau day gap doi DM, HPWL +32 %; nghen o suc chua kenh |
| 2026-10-02 | luoi rong wide4211x3331 (14.03 mm2) | die x1.15 | route duoc, STAMidPNR-3 nom_tt -17.573 | than clock dai -> skew lon -> 5,884 cell tre hold |
| 2026-10-06 | sang loc hop nhat | lat hang macro tren (FS), khe 220 um | overflow 3,588 -> 1,530 -> 0 | SA2 dung ca cong 1 (dout1 canh tren) va bus cong 0 (canh duoi) |
| 2026-10-06/07 | sa2uA (`sa2_corr3400x3325_f220_r1`, 11.305) | floorplan hop nhat | P2 +0.234 (duoi bien +0.3, cho tiep); DRT dung vong 30 (173 > 150) | |
| 2026-10-06 .. 08 | sa2uB (`sa2_corr3400x3400_f220_r1`, 11.56) | | DRT bi dung vong 23 (luat cu); chay lai 64 vong: 0 o vong 54 (5 h 43 m); antenna sau DRT 833 net -> 1,576 diode -> route lai tu 48,176; dung 2026-10-08 07:06 (136 vi pham, bi ap dao) | tu vong 25 moi vi pham trong o ~640 x 310 um hanh lang: cay buffer fanout + flop `replace_way` D$ |
| 2026-10-07 | `sa2_corr3400x3400_f220_capm20_fo16_r1` (nhanh) | cap margin 50 -> 20, max fanout 8 -> 16 | buffer sua DRV dau 19,987 -> 13,508; buffer resizer sau GRT 24,304 -> 17,791 (-27 %); cell -1.1 %; P2 +0.671 / +0.159 | qua p2 (11.56 mm2): sua DRV sau GRT chi con 4,208 vi pham cap (11,274 voi cap 50), chen 477 buffer (4,416); GRT 21.25 -> 21.55 % (cap 50 + fanout 8: 22.23 -> 22.95 %); cell chuan STAMidPNR-3 1,473,170 um2 / 213,514 cell so voi 1,524,290 / 223,278 (-3.4 %) |
| 2026-10-07 | `sa2_corr3400x3100_f220_capm20_fo16_r1` (10.54) | die | P2 FAIL: overflow 17, setup -1.287 (26), hold -0.192 (74) | skew setup 0.737 -> 2.088 ns tu placement sang GRT; `clknet_1_0_1_clk` guide ~4.9 mm |
| 2026-10-07/08 | `sa2_corr3400x3250_f220_capm20_fo16_r1` (11.05) | die | P2 +0.220; DRT vong 14 (483) khi tat may 2026-10-08 07:57; xoa 16:26 | |
| 2026-10-08 | `sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1` (10.54) | padding 1 site/ben, `PL_TIME_DRIVEN`, clock met3-met5 | P2 +0.280 / +0.025; ECO dung DPL-0033 (sua); sign-off max_tt -0.571 (21 endpoint, TNS -6.07) | duong doc nua chu ky SRAM way 1 I$, net slew 1.0-1.3 ns |
| 2026-10-08 | `..._seco_r1`, `..._secott_r1` (nhanh sau buoc 46) | ECO setup sau route | max_tt -0.573 khong doi; secott treo route lai 2 h 25 m, dung 20:06 UTC | `estimate_parasitics` truoc `read_spef`; SRAM mot .lib TT (STA-1140) |
| 2026-10-09 | `..._pad1_tdp_clkm3_rsztf_r1` (10.54) | `RSZ_CORNERS` nom_tt, nom_ff | P1 22 phut (truoc 43), P2 +0.153; dung truoc DRT (du bao max_tt ~ -0.7) | resizer duoi theo goc ss khong dong duoc (muc 9) |
| 2026-10-09 | `sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1` (11.56) | chi doi die | P2 +1.057, hold -0.206 (19) -> CONTINUE; DRT 38 phut; sign-off: chi hold nom_ff -0.023 / min_ff -0.027 (4) | ECO hold gan MOT extraction (max_*) cho moi goc |
| 2026-10-09 | `..._rsztf_ecomin_r1` | ECO tren min_* | max_ff -0.116, nom_ff -0.044 (te hon) | |
| 2026-10-09 | **`..._rsztf_ecomaxmin_r1`** | ECO thu hai min_* sau ECO max_* (nhanh sau buoc 47) | KY TEN SACH 03:04 UTC; buoc 52 crash CPython (`'cell' object has no attribute 'name'`), chay lai buoc do | |
| 2026-10-09 | **`..._rsztf_r2` -> `..._rsztf_ecomaxmin_r2`** | lan chay thu hai (full flow tu buoc 1 01:37 UTC, nhanh sau buoc 47) | KY TEN SACH 05:14 UTC; netlist / DEF trung tung byte (sha256 `08901143` / `07a82698`), SPEF trung tru `*DATE`, 319/319 metric | [LS]; khong tuan thu quy tac Q (muc 8.4) |
| 2026-10-10/11 | `sa2_corr3400x3250_..._rsztf_r1` / `_r2` (11.05) | chi hinh hoc | P2 FAIL x2 (15:01:55 va 20:35:09): setup -0.331932 (10), hold -0.0579186 (4), overflow 16; 568 truong trung | duong nua chu ky I$ way1/bank1 `dout1[25]` -> `if_req_addr[31]` (arrival 23.654978 > required 23.323046 ns) |
| 2026-10-11 .. 13 | `sa2_corr3400x3325_..._rsztf_r1` (11.305) | chi hinh hoc | P2 PASS (+0.762128 / +0.045411, overflow 0); DRT 01:08:19.415, route DRC 0, antenna 0/0; P4: ECO 326 endpoint / 197 buffer, DRT tang dan dung o 24 vi pham vong 13-18, SIGSEGV vong 19 (`checkMetalSpacing_short_skipFixed`); DONG FAILED 2026-10-13 | die 11.56 cung buoc: 794 -> 0 trong 4 vong; khong quy loi may |
| 2026-10-13/14 | `..._rsztf_cts25_r1` .. `_r5` (E1) | `CTS_SINK_CLUSTERING_SIZE` 8 -> 25 | r1 SIGSEGV `pdr::primDijkstra` (buoc 41); r2 MemoryError (buoc 51, canh DRT DM_VC4); r3 SIGSEGV checkantennas (buoc 43); r4 Tcl panic (buoc 34); moi buoc loi chay lai rieng deu qua. r5: P1/P2 trung (STAMidPNR-3 +0.959 / +0.182), DRT + ECO route DRC 0, SIGSEGV buoc 51, sign-off chay lai tu buoc 51 (phat trien) | ly do E1: cay clock SA2 3,391 clkbuf + 1,939 dummy load (0.0703 mm2) so voi DM 2,819 + 1,088; cong suat clock 43.10 vs 33.02 mW. Ket qua sign-off cua r5 chua ghi trong tai lieu; log `asic/gated_queue_20261013_sa2cts25_vc4antcong.log` |
| 2026-10-14/15 | `..._rsztf_eco2_rtl6c4c_r1` | E0 (`_rsztf.json` + CORNER_2 + `P2_MIN_HOLD`) + snapshot `rtl_rfbht` | buoc 16 ManualMacroPlacement FAIL | tu R15/R16 macro cache la `u_soc.u_{i,d}cache.genblk1.g_dse.*`; sua bang `macro_placement_u2fg_rtl6c4c.cfg` (chi 8 ten, toa do trung, 16/16 kiem voi netlist) |
| 2026-10-15 | `..._rsztf_eco2_rtl6c4c_r2` | nhu tren + `P1_MIN_SETUP=0` | dang chay (`asic/sequence_heavy_20261015g.sh`) | [HT] |

Bang die SA2 voi cap 20 + fanout 16 (setup nom_tt STAMidPNR-2 -> STAMidPNR-3): 11.56 +1.754 -> +0.671; 11.05 +1.529 -> +0.220; 10.54
+1.521 -> -1.287. Phan tich PPA SA2 so voi DM (2026-10-13, doc du lieu da luu, moi phep tinh x2): cong suat theo hoat dong 129.64 vs
119.45 mW, chenh chu yeu o clock 43.10 vs 33.02 mW va tuan tu 41.50 vs 38.71 mW, macro 37.87 nhu nhau; SA2 co 14,184 diode antenna
(DM r14F_A 7,360), 12,619 trong do do sua antenna o GRT (`RUN_ANTENNA_REPAIR` true, margin 30), sau DRT chi chen them ~1,550.
Dien tich cell tu DEF cuoi (khong tinh fill / decap / tap): SA2 1.3423 mm2 / 113,040 cell, DM hanh lang dmuB 1.2472 mm2. CTS ca
hai dung `CTS_SINK_CLUSTERING_SIZE` 8 (mac dinh OpenLane 25) va `CTS_CLK_MAX_WIRE_LENGTH` 800 ke thua tu config DM cu, chua tung
toi uu; OpenROAD `edf00dff` co `clock_tree_synthesis -dont_use_dummy_load` (`cts.tcl` chua noi). Huong thu cho SA2 ghi 2026-10-13
(moi lan mot thay doi, full flow + ECO hai luot; tu 2026-10-14 PD tren `6c4ccffd`, muc 8.4): tat sua antenna o GRT; clustering
8 -> 16 / 25; bo dummy load; bo padding o 11.56; max fanout 16 -> 24. Den 2026-10-15 moi thu clustering 25 (E1).

### 8.3 DM_VC4

| Ngay | Run | Thay doi | Ket qua | Nguyen nhan / ghi chu |
|---|---|---|---|---|
| 2026-09-30 | wrapper DSE SRAM | 1 lane/macro (cong 1 doc, cong 0 ghi), 4 macro/cache | tong hop 1,077,811 um2 (+10.2 %) | 4 macro chet cua way 1 D$: Yosys khong chung minh duoc flop `refill_way` la hang (Quartus thi bo); `SYNTH_OPT_DFF_SAT` (mot luot `opt` voi SAT sau `share`) bo 4 macro chet, DM / SA2 +0.08 % / +0.22 %; doc khi ghi, shadow va moc DM: muc 8.2 |
| 2026-10-02 | vc4F (luoi DM), luoi rong | | GRT-0118; luoi rong overflow 34,086 | moi tuyen doc phai qua khe giua hang macro (macro chan met1-met4); hai cum flop tag 5,120 flop o nga ba kenh; day trong cum tag DM 231 / SA2 1,142 / VC4 1,516 mm |
| 2026-10-03 | vong 3200x3190; tang 3260x3400; hanh lang U2 3400x3400 | floorplan | vong: nom_tt -1.093 (refill nua chu ky, 55 repeater 8.02 ns); tang: +1.809 nhung overflow 233,074; U2: +1.724, overflow 1,560 (15 vong); hanh lang hep hon ~1,057 um that bai (957 um: overflow 51,831 sau 50 vong GRT); xoay macro OpenRAM 90 do lam hong luoi nguon (chan nguon macro met4 nam ngang) | core DSE doc valid/tag o hai chi so (`live_index`, `request_index`) - cau truc RTL |
| 2026-10-06/07 | vc4uA / vc4uB (11.305 / 11.56) | floorplan hop nhat | route lai trong RepairAntennas: overflow 19,114 / 11,485 (gioi han 2,000) | sua DRV sau GRT chen +4,643 buffer. Dien tich o 11.305 mm2 (2026-10-06): core 11.137 mm2, macro 3.802 mm2 (34 %), cell chuan 1.32 / 1.44 / 1.47 mm2 (DM / SA2 / DM_VC4), chi chiem ~20 % phan core ngoai macro: gioi han la dinh tuyen qua hanh lang (macro chan met1-met4), khong phai cho dat cell; nho hon nua phai doi hinh hoc macro / vi tri chan hoac cau truc truy cap tag cua core DSE (RTL), ngoai pham vi PD |
| 2026-10-07 | corr3600x3400 (12.24) / corr3800x3400 (12.92) | die rong hon | overflow 5,774 / 10,627; dung 22:42 | `guide_demand.py` tren `after_grt.guide` (corr3600x3400_f220): buoc sua DRV sau GRT (`LAYERS_RC` ~2x LEF + `GRT_DESIGN_REPAIR_MAX_CAP_PCT` 50, mac dinh OpenLane 10) gap 1,270 vi pham slew + 11,363 cap, chen 4,671 buffer (wire +2,808, max_cap +1,863) vao hai cum tag (x ~1450-2300, y ~1550-2000 um) da ~82 % track; vung 850 x 450 um co 17,992 cell (3,757 flop, 3,809 mux2, 5,747 buffer resizer); GRT di vong: met1 +31 %, met2 +25 %, met3 +19 %, 6,163 net moi 528,975 track x gcell. Truoc khi sua, DM_VC4 da can nhieu day hon SA2 cung die (corr3400x3400_f220): met1 +24 %, met2 +22 %, met3 +68 %, met4 +20 %. 14,503 buffer fanout tu `MAX_FANOUT_CONSTRAINT` 8 |
| 2026-10-07 | `vc4_corr3400x3400_f220_capm20_fo16_r1` | fanout 16 | P1 FAIL overflow 1,272 | cay fanout it buffer hon nhung nhanh dai tren met1/met2; DM_VC4 giu fanout 8 |
| 2026-10-07 | `vc4_corr3400x3400_f220_capm20_r1` | cap 20 | P2 FAIL: 17,135 diode o sua antenna GRT, overflow 3,934, setup -5.329 | |
| 2026-10-08 | `..._capm20_antm10_r1` | `GRT_ANTENNA_MARGIN` 10 | P2 FAIL: ~11,087 diode, setup -2.099, hold -0.568; ResizerTimingPostGRT ~3 h (1,400 vong duoi theo ss) | |
| 2026-10-08/09 | `..._capm20_antoff_r1` | tat sua antenna o GRT | P2 FAIL: overflow 66 -> 1,185 o ResizerTimingPostGRT, setup -2.673 | chinh buoc sua timing sau GRT gay tac |
| 2026-10-09 | `..._antoff_rsztf_r1`, `..._nogrtt_r1` | resizer tt/ff; tat sua timing sau GRT | P1 +2.061; nogrtt: route khoe (overflow 22) nhung P2 setup -0.896, hold -3.902 | skew hold -1.545 -> -5.460 ns: net clock detour qua met1/met2 nghen. Cac lan truoc, buoc sua timing sau GRT 'sua' cac vi pham gia do skew nay (hold -7.8 ns, 2,746 buffer) va chinh no lam no overflow |
| 2026-10-09 | `..._nogrtt_clkm3_r1`, `..._clkm3_pad1_r1` | clock met3; + padding | P2 FAIL (-1.076 / -3.192; -0.190 / -1.157). pad1 (1 site / ben): o nong sau GPL 3,035 -> 2,516 cell; GRT dau VAN hard benchmark (overflow cuoi 11, day +2.6 %); skew hold -4.77 -> -2.69 ns, setup 4.56 -> 2.24 ns (so voi clkm3); overflow sau sua DRV 60 | `clknet_2_1_1_clk` (HPWL ~670 um) guide ~7.7 mm; moi run 11.56 mm2 chay GRT-0103 "Extra Run for hard benchmark" (SA2/DM khong): diem nong tren hang D$ ~175 / 256 track (SA2 ~5) = victim buffer D$. clkm3: `clknet_4_7_0_clk` 1.4 -> 7.1 mm sau sua DRV sau GRT, tre clock dich 7.82 ns so voi nguon 3.49 ns: detour cua router, khong phai chuyen lop. Sau padding cua so nong nhat chuyen sang x 1932-2208, y 1822-1987 um (cum tag D$ o mep hanh lang, 2,277 cell, 806 buffer fanout / max_cap): padding giup nhung chua du o 11.56 mm2 |
| 2026-10-09 | `..._pad1_grtit150_grtscr_r1`, `..._clkm4_pad1_grtscr_r1` (sang loc) | 150 vong GRT; clock met4-met5 | GRT-0103 van chay; skew -3.79; clock met4-met5 van 22 mm tren met3 (dai lop khong giu chat khi thieu cho) | GRT-0103 bat o vong 20 khi overflow > 200 (OpenROAD `edf00dff`). Ma nguon (`GlobalRouter.cpp` / `FastRoute.cpp`): clock va tin hieu route chung mot luot; net clock non-leaf (`isNonLeafClock`) co dai lop rieng, FastRoute chi cong capacity trong dai do, nen doi lop clock khong phai don bay. Skew ngay sau GRT dau (`grt_skew_screen.sh`; hold skew / hold nom_tt / so endpoint): SA2 ky ten -1.92 / -0.126; DM_VC4 3600 cu -2.00 / -0.364 / 162; 3800 cu -3.77 / -2.209; 3500 padding -2.66 / -1.250; 3400 padding + clock met4-met5 -3.79 / -2.133. Skew khong giam deu theo die: vai net than clock detour quanh khe giua hai hang macro D$ o mep hanh lang |
| 2026-10-09 | `corr3500x3400` pad1 | die 11.90 | P2 FAIL: +0.548, hold -1.926 (1,675 endpoint) | skew hold -3.37 |
| 2026-10-09 | `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_r1` | 3600, truoc GRT giong `vc4_corr3600x3400_f220_r1`; chon vi hold 162 endpoint -0.364 nam trong tam ECO hai luot (SA2: 112 endpoint -0.38 sau DRT, 139 buffer) | GRT dau trung tung byte (khong GRT-0103; day 11.94 m, P1 +1.168); P2 FAIL hold -2.030 (1,863), skew hold -3.41 ns, setup -0.535 | `OpenROAD.RepairDesignPostGRT` (`repair_design_postgrt.tcl`) chen 368 buffer vao 2,289 net, hop phap hoa roi chay lai TOAN BO global route; 744 net clock route lai, `clknet_2_2_0_clk` 1.1 -> 4.6 mm. Moi lan GRT toan bo la mot lan boc tham cho than clock DM_VC4 -> `RUN_POST_GRT_DESIGN_REPAIR` false (nogrtd, J1) |
| 2026-10-09 | `vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1` (J1) | tat sua DRV sau GRT (`config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd.json`) | P2 "MISSING p2 data" -> CONTINUE 06:20 UTC; rui ro setup nom_tt sau GRT chi +0.046 (nua chu ky RAM bank[4] dout0 -> I$ bank[2] din0, slew 0.87 ns); DRT 161,333 / 95,248 / 89,365 vi pham sau 3 vong dau (SA2 r2: 103,892 / 48,827 / 45,440 roi 5,822 / 1,289 / 308; DM r14F_A: 114,374 / 62,655 / 58,640 roi 12,993); watchdog dung o vong 10 (5,689 > 5,000) 14:28 | 4,089 marker o x 1500..1600, y 1800..2000 um (`results/vc4_corr3600x3400_drt_diagnosis_20261009.json`, `results/vc4_corr3600x3400_drt_region_20261009.log`) |
| 2026-10-10/11 | `vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1` | + padding (`results/vc4_padding_hypothesis_20261009.md`) | SIGSEGV post-CTS (giu `crashed-37`), retry khong doi qua; P1 +1.51761 / +0.181665; screen GRT dau va P2: setup +0.491013, hold -0.202347 (9 endpoint), skew hold -1.719956 -> CONTINUE; DRT chinh DRC 0 o vong 45 (18.5 h); antenna sau DRT 2,243 net / 3,211 pin, 5,978 diode, fatal GRT-0232 (2026-10-11 03:19) | `results/vc4_postcts_crash_20261010.json`, `results/vc4_postdrt_antenna_failure_20261011.json`. Pha im lang >10 h sau DRT chinh: probe CPU chi doc 2026-10-10 19:53 (perf_event_open, TID 669, 20 Hz, 98 mau, mat 0, khong ptrace / signal) cho moi PC trong `grt::FastRouteCore::mazeRouteMSMD` = maze route cua GRT trong vong sua antenna, khong phai treo; suy luan 'antenna check im lang' truoc do khong duoc stack / PC ung ho (SA2 ky ten: buoc 46 mat 36m45.497s / 34m32.522s); `results/vc4_cpu_sampling_20261010/receipt.json`, `results/vc4_postdrt_antenna_comparison_20261010.json` |
| 2026-10-13/14 | `..._pad1_antoff_nogrtt_nogrtd_antcong_r1` | `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`, `DRT_SAVE_MAIN_ROUTE` | DRT chinh 0; vong antenna khong con GRT-0232 nhung route lai 59,810 -> 8,323 o vong 13: watchdog FAIL | 2,916 net vi pham o buoc GRT (ty le toi 21.5x so voi DM 481 / SA2 653 sau route), tap trung o net dai toi chan SRAM (din0 / csb0) va mux du lieu victim |
| 2026-10-14 | V2 `..._pad1_antgrt10_nogrtt_nogrtd_antcong_r1` | sua antenna o GRT bien 10 (sang loc tren trang thai sau GRT cua `antcong_r1`, 10 vong, `asic/soc_vc4_4kb/screen_antgrt10_20261014/`: 3,428 -> 1,015 -> 227 -> 54 -> 13 -> 7 -> 6 -> 4, 9,225 diode, overflow 0 (23.3 %), day 12.27 -> 12.45 m) | DRT chinh 0 o vong 31 (42 phut); antenna sau DRT 1,031 net / 1,453 chan; vong sua 1 chen 2,295 diode, route lai 78,513 -> 1,389 (vong 16) -> 2,063 (vong 17): watchdog FAIL | `main_route.odb` (`asic/soc_vc4_4kb/screen_ant_postdrt_v2_20261014/`): moi vi pham la PAR side-area (met3 885, met2 307, met1 194, met4 93); cong mux2 521 / a221o 238 / a22o 230; 837 / 1,031 net do resizer tao; dai trung vi 731 um (p90 1,138); 538 / 1,027 net co 5-8 chan (cay buffer fanout, MAX_FANOUT 8); 1,020/1,453 chan trong vung logic giua cot macro I$ va D$: dout1 cua ca 4 macro moi cache quay vao kenh 220 um |
| 2026-10-14 | `screen_drt_replay_v2_20261014` (sang loc) | chay lai buoc DRT cua V2 khong watchdog | route chinh trung tung vong (flow tat dinh); route lai 225 o vong 43-44, giam 1-3 %/vong: khong hoi tu trong 64 vong | |
| 2026-10-14 | V3 (`..._antcong_r2`) | V2 + luat watchdog antenna | P1/P2 trung V2; dung truoc DRT 08:31 UTC (co abort) | tai hien tat dinh se that bai |
| 2026-10-14 | V4 `vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1` | die 3800 (12.92) | P1 +1.263, P2 +0.476; antenna sau sua GRT 821 net (V2 742); DRT tu 10:33 UTC; dung boi chu du an 14:01 UTC | be rong die khong phai don bay |
| 2026-10-14 | V5 `..._antcong_mwl500` | `DESIGN_REPAIR_MAX_WIRE_LENGTH` 500 | P2 FAIL: 23,680 buffer, setup -1.068, hold -1.882; antenna 873 net | chieu dai day khong phai don bay |

Antenna DM_VC4 so voi DM / SA2 (vong sua sau route: net vi pham -> diode -> route lai): DM r14F_A 481 -> 1,051 -> ~21k, hoi tu;
SA2 653 -> 1,453 -> ~33k, hoi tu; DM_VC4 V2 1,031 -> 2,295 -> 78,513, dinh tre. Sang loc bien antenna o GRT 10 / 20 / 30 %:
9,225 / 11,611 / 15,107 diode nhung con 742 / 753 / 641 net vi pham sau sua GRT, trong khi GRT tu bao 4 / 6 / 8: sau khi sua,
vong 'extra iterations to remove overflow' route lai va sinh vi pham moi, nen bien khong phai don bay. Muc tieu cho DM_VC4:
<= ~650 net vi pham sau route. OpenROAD `edf00dff` chi sua antenna bang diode (khong chen jumper), nen giai phap phai den tu
floorplan / diode.

Ket luan DM_VC4 (2026-10-14): bien antenna o GRT, be rong die va gioi han chieu dai day deu khong giam duoc vi pham antenna; nguyen
nhan cau truc la chan doc cua ca hai cache huong vao vung giua. Chu du an hoan DM_VC4 (2026-10-14 21:20); se xay lai tren
`6c4ccffd` voi floorplan rieng (chan doc tranh dai giua) va can doi ten macro nhu SA2.

### 8.4 Quy tac Q va lan chay tron; PD tren `6c4ccffd`

- **Quyet dinh 2026-10-07 (toi, chu du an).** DM khoa o dm_grid3665x2900_r1 / _r2 (10.63 mm2, GRT cap margin 50); SA2 va DM_VC4
  toi uu rieng theo PPA (die nho nhat con route duoc, it buffer / day nhat; gioi han cung va bang cuoi o QUY_TRINH muc A); DM tren
  hai floorplan hanh lang (dmuA / dmuB, muc 8.1) chi con la doi chung cung die. Thay ke hoach 2026-10-06 (chay ca hai floorplan
  hanh lang cho ca ba thiet ke, 6 flow).
- **Tu danh gia 2026-10-08.** ~10 gio chay 8 run sang loc (5 truot cong); 3 run bo truoc khi chay, 1 bo sai (DM_VC4 fanout 8 +
  cap 20 bo luc 16:10 do suy tu SA2, chua co so lieu DM_VC4; chay lai la `vc4_corr3400x3400_f220_capm20_r1`, muc 8.3); thu - sai
  bang knob toan cuc chi doi loi sang cho khac; moi so SA2 / DM_VC4 toi luc do la so sang loc, chua toi uu. Chu du an: hon 100 loi
  o vong 50 van co the ve 0 o vong 64 (SA2 B 70 o vong 44 -> 0 o vong 54) nen bo gioi han sau vong 40 (cai dat
  `G5_UNLIMITED_LATE_PHASE=1`, muc 6.1); mot run duoc dung theo GIA TRI (bi bien the khac ap dao, vd. SA2 B cap 50 + fanout 8
  dung 07:06, muc 8.2), khong theo so vong.
- **Minimality (2026-10-10).** Cau hinh die nho chi doi 3 truong hinh hoc (`DIE_AREA`, `CORE_AREA`, `MACRO_PLACEMENT_CFG`) tu recipe
  nguon (SA2 3250 / 3325: recipe ky ten 3400 x 3400; DM_VC4 3500 pad1 moi: recipe 3600 x 3400 pad1). Run VC4 corr3500x3400 pad1 cu
  (2026-10-09, muc 8.3) doi them 4 knob (antenna margin 30 -> 10, resizer tt/ff, clock toi thieu met3, sua design sau GRT bat) nen
  KHONG dung lam chung minh die nho nhat. Cap moi chi hop le sau khi recipe nguon duoc chap nhan; luc do chua chay PD. Preflight
  6 config: 16 macro + halo 10 um vua, 17 doi chung am, 36 kiem cu phap PASS; `results/pd_minimality_preflight_20261010.json`.
- **Thu tu cong viec 2026-10-13 (chu du an).** Lam TUAN TU, uu tien cho bai viet: (1) kiem lai chuan bi board so voi thiet ke hien
  tai, chay board (muc 3.3); (2) PD SA2 / DM_VC4 toi uu rieng, KHONG chep thong so / ket qua cua DM (config DM ky ten chi tam chap
  nhan); (3) LEC SA2 / DM_VC4; (4) bao cao cac muc `danh_gia.txt` da giai quyet; (5) liet ke day du phan mo rong so voi ban 1 KiB.
- **Quy tac Q.** 2026-10-13: khong chay tiep tu buoc FAIL. 2026-10-14 (chu du an sua): khi phat trien duoc sua va chay tiep tu buoc
  loi; khi moi thu da qua, BAT BUOC mot lan chay tron tu buoc 1 (tag moi, khong resume / nhanh / CONTINUE, nguong khai bao luc khoi
  chay); chi lan chay tron do (va lan chay kep khi can) la ket qua. Kiem toan 2026-10-14: DM r14F_A/B (resume sau ket thuc phien) va
  SA2 ecomaxmin (nhanh sau buoc 47, CONTINUE qua p2, resume buoc 52) khong tuan thu khi thuc hien; netlist cuoi tai lap tung byte o
  lan chay thu hai, nhung moi thiet ke can mot lan chay tron moi.
- **Quyet dinh 2026-10-14 21:20.** PD doc `asic/snapshots/rtl_rfbht` (= `6c4ccffd`); truoc do moi config doc `rtl_r14` (`3ea52396`),
  chi duoc bien minh bang chung minh R14 == R16 (FAST_HIT 0) va thay doi RF/BHT chi FPGA. Wrapper SA2 / DM_VC4 nam ngoai manifest
  duoc dong bang vao snapshot (47 file). Moi ket qua PD/GLS/LEC tren `rtl_r14` tro thanh [LS].
- **Ghi chu tong hop.** Tong hop `6c4ccffd` = R16 (`da06d38f`), khac tong hop R14 cua PD (`fc555d6b`): netlist DM `6c4ccffd` co
  71,006 cell (R14 70,441), nen layout R14 khong the coi la layout cua `6c4ccffd`.
- **Trang thai 2026-10-15 07:45.** DM `dm_grid3665x2900_rtl6c4c_r2` va SA2 `..._eco2_rtl6c4c_r2` dang chay qua
  `asic/sequence_heavy_20261015g.sh` (mot pha nang mot luc). DM_VC4 hoan.

## 8a. Su kien moi (nhat ky tam theo thoi gian)

Su kien sau 2026-10-15 07:45 ghi o day theo dang `### YYYY-MM-DD HH:MM <chu de>` (moi su kien mot lan), roi duoc gop vao muc chu
tuong ung (1-8, 9-11) o lan ra soat tai lieu ke tiep. `scripts/fpga/record_board_case.py --sync-tracking` tu ghi su kien board vao
cuoi muc nay (tim tieu de muc 8a va muc 9); khong doi ten hai tieu de do va khong viet lai
chuoi tieu de cua chung o noi khac trong file (script lay lan xuat hien dau tien).

## 9. Van de da biet

Moi van de ghi mot lan; cac muc khac chi tham chieu ten muc.

**Loi may.** Tren may tram da ghi nhan crash native ngau nhien va mot so ket qua Python sai khong lap lai (probe
`python3 asic/parse_ids_probe.py --synth 300000`); nguyen nhan chua xac dinh, Intel Processor Diagnostic Tool 4.5 PASS 2026-10-13
(`results/health_20261013_recheck/ipdt_4.5/`). Thuc hanh: chay kep quyet dinh ket qua; crash ngau nhien duoc chay lai; cong cu Python
phia Windows chay ghim mot CPU; probe truot khong du de dung cong viec. Lech huong N/FN (2026-09-25) va S/FS (2026-10-14) cua cell
giua hai lan chay la hanh vi phu thuoc dia chi cua OpenROAD, chua xac dinh nguyen nhan; doi chieu PD dung netlist + metric, khong dung
hash ODB/DEF.

**OpenRAM suon xuong.** Macro OpenRAM dua `dout` ra o suon xuong (`timing_type falling_edge`), nen moi duong dout -> flop suon len chi co
nua chu ky (10 ns). DM 8 KiB: vong fetch -0.569 / -0.827 ns, sua RTL cycle-exact cho +2.190. SA2 / DM_VC4: core DSE ghi moi beat refill
tu dout RAM thang vao macro lane trong cung nua chu ky, nen hang RAM phai sat macro lane; SA2 o die nho truot o duong doc way 1 I$.
Nguon ngoai (tra cuu 2026-09-26): dynamatic PR #42 (dout suon xuong; doc+ghi cung dia chi khong xac dinh - wrapper du an da chan hoac
khong the xay ra).

**Uoc luong RC.** Resizer dung dien dung don vi tu tech LEF, khong co thanh phan ghep: tren 2,072 net, uoc luong placement thap hon RCX
2.37x (trung vi 2.13x), global route 1.93x (net dai 2.1-2.2x). He qua: slew / cap song sot qua flow va uoc luong ss lac quan ~4 ns.
`LAYERS_RC` k = 2.0 (C = 2 x dien tich / canh trong tech LEF, R = RPERSQ / w_min, bang lay tu ORFS sky130hd; OpenLane 2.3.10 doc
`LAYERS_RC` trong `set_rc.tcl` nhung khong khai bao bien, khai bao trong openlane-local) giam sai so con 1.19x / 0.96x; ca hai lan
global placement timing-driven doc `set_rc.tcl` nen full flow doi placement tu buoc 23 (max_ss -8.311 -> -9.518, 3 hold): khong dung
cho sign-off; chi trong `repair_design` (`LAYERS_RC_SCOPE`) thi slew/cap 213/402 voi +4.1 % cell. Thi nghiem tu trang thai final_A
(2026-09-27; vi pham cap o 738 driver cell chuan va 106 dout SRAM): `LAYERS_RC` k=2: slew 757 -> 201, cap 807 -> 406 nhung tt giam
0.2 ns, max_ss -8.615, 1 vi pham hold; them cap margin: hold +0.082, tt +1.755; `LAYERS_RC` + GRT hold 0.15: 2 vi pham hold. Vi pham
cap song sot vi `repair_design` dat repeater theo cay Steiner ngan hon route that, va diode antenna chen sau do. Nguon ngoai (tra cuu
2026-09-26): ORFS #3969 (uoc luong RC).

**Buffer hold.** Bien hold 0.1 ns o PL / GRT sinh 18-19k `dlygate4sd3_1` trong khi chi ~50 endpoint vi pham that (8 KiB-RAM: 19,019
buffer = 13.6 % cell). Bien 0.03 + hold ECO 0.02 tren RCX: con 1,032 buffer, hold van sach (cau hinh ky ten 16 KiB-RAM).

**Knob resizer / repair_design.** Do tren r10A (2026-09-26): setup truoc hold (`PL_RESIZER_FIX_HOLD_FIRST` false) +0.25 ns tt / +0.7
ns ss (README OpenROAD, tra cuu 2026-09-26: setup truoc hold); setup margin 2.0 +0.41 / +0.52 ns; dem day dai giam slew / cap 31 / 58 %
nhung hai timing. 2026-09-23: `repair_design` khong co tuy chon fanout, cell vi pham fanout la buffer do chinh no chen (fanout 26-31 so
voi gioi han 8) nen fanout khong giam. Diode heuristic va `HeuristicDiodeInsertion`: muc "Antenna".

**Job nen va ket thuc phien.** Job khoi tu phien terminal chet khi phien ket thuc (WSL2 tat VM khi khong con client `wsl.exe`;
`setsid` / `nohup` khong giup; tach qua WMI / Task Scheduler bi chinh sach quyen tu choi). Mat mat: 2026-09-26, 2026-09-30 04:50 va
23:38, 2026-10-07 01:17. Job can song qua phien thi chu du an chay tu terminal WSL cua minh.

**Bo nho WSL 24 GB.** Do thuc te: flow truoc DRT 5-8 GB, DRT ~10.5 GB (VC4 toi 12.4), Magic WriteLEF 12-13 GiB, KLayout 8 GiB, ECO
~10 GB. P4 cua mot run canh DRT cua run khac khong vua (SA2 E1 r2 MemoryError 2026-10-14); may ao WSL tat 2026-10-03 08:22 khi chay
DRT + resizer + 2 sang loc + 2 kiem hinh thuc song song. Kiem hinh thuc muc SoC va EQY (~13 GB) chay mot minh.
2026-10-08 21:30: chuoi 9 lane + Quartus + 2 flow PD lam RAM trong Windows xuong 1.6 GB, CPU 100 %; dung Quartus bang co abort sau
fit dang chay, chay lai Quartus x2 sau chuoi. Quy tac: khi 2 flow PD chay, khong chay Quartus cung luc voi chuoi nhieu lane.

**Yosys nhay voi ten.** Ket qua Yosys / ABC phu thuoc ten va thu tu doc (doi ten mot port: +2,728 cell, +2.8 %); chenh lech < ~3 %
khong quy duoc cho thiet ke. Generate `g_nway` doi ten core DSE thanh `genblk1.g_dse` (kiem muc SoC phai doi ten phia gate; PD can ten
macro moi tu R15/R16). ABC `fraig_restore` co the cham benh ly; replay voi hook co the khac tung byte du cung logic. `write_aiger` xep
input/output theo thu tu khai bao day, ABC ghep theo vi tri.

**Confound controller.** DM dung controller 5 trang thai; SA2 / DM_VC4 / DM_DSE dung core DSE 10 trang thai, hit mang chinh ton them mot
chu ky (ST_IDLE -> ST_LOOKUP -> ST_HIT_RESP / ST_CPU_RESP). O 4 KiB controller +9.83 %, to chuc cache SA2 -0.26 % / SA4 -0.07 % / DM_VC4
+1.03 %. Voi FAST_HIT = 1 set associative nhanh hon DM o moi dung luong; DM_VC4 van cham hon vi eviction noi tiep refill. FPGA:
controller sau hon +444 LE (1 KiB, 4 seed). Nhan dinh 2026-09-18 rang tag dong bo "xoa confound" la sai.

**SDC create_clock.** `set clocks [create_clock ...]` lam `set_clock_uncertainty 0.25`, `set_clock_transition 0.15` va moi I/O delay
bi bo im lang (sua 2026-09-24). Do lai: 1 KiB nghien cuu setup tt +3.412 -> +3.162, hold tt +0.202 -> -0.048, ss +0.483 -> -0.123, ff
+0.104 -> -0.146 ns; 1 KiB cong bo setup tt +2.944 -> +2.694, ss -10.933 -> -11.183, hold tt +0.302 -> +0.052, ss +0.657 -> -0.231, ff
+0.186 -> -0.064 ns; endpoint khong rang buoc 121 -> 46 (4 KiB: 161 -> 86 -> 84, ca 84 do hang so dieu khien). Bang chung:
`asic/evidence/sdc_recheck_1kb_{research,published}/`; SDC ban cong bo giu nguyen.
SDC loi bo 72 / 78 cong ra khong duoc kiem; moi timing ASIC truoc 2026-09-24 lac quan dung bang uncertainty (0.25 ns). Phep do lai
hop le vi SDC cu chay lai tren netlist 1 KiB da luu tai lap metric da cong bo den 4 chu so.

**Magic namespace collision.** Hai loi doc lap cua cac buoc Magic voi macro OpenRAM va hai ban sua (`read.tcl`; `.magicsafe.gds`),
chung minh tung hinh: `asic/evidence/MAGIC_NAMESPACE_COLLISION.md`. `MAGIC_CAPTURE_ERRORS` luon true.
Log XOR KLayout cua `.magicsafe.gds` chua tung la file (phat hien khi don workspace 2026-09-19); bang chung dung lai bang
`asic/prove_magicsafe_equivalence.py` (so tung hinh: 412 hinh bi bo tren dung 5 layer chu thich, 34 layer con lai giong het).
2026-09-23: macro 1 KiB chua co `.magicsafe.gds` nen Magic WriteLEF hong 31 lan; tao va chung minh nhu macro 2 KiB, XOR Magic/KLayout
= 0. Magic DRC tren GDS: 42,198,750 vi pham, mot luat li.3, mau 100 % nam trong vien macro; KLayout DRC 0, TritonRoute 0 -> giu
`ERROR_ON_MAGIC_DRC` true, Magic DRC chay tren DEF (`MAGIC_DRC_USE_GDS false`), KLayout kiem toan bo GDS ke ca trong macro (2026-09-25
doi sang GDS cell chuan + macro truu tuong, muc 6.1).

**Liberty OpenRAM.** Macro chi co Liberty TT, nen ss / ff dung timing TT cho macro; macro OpenRAM cham hon ~10 % o SS 1.8 V so voi TT
nen STA ss / ff qua SRAM lac quan. Chi `addr0` / `addr1` / `wmask0` co `max_transition` 0.04 ns (OpenRAM issue #298, tra cuu
2026-09-26; `din` / `csb` / `web` 0.5 ns; do 10-90 %, bang 0.030 ns theo quy uoc 20-80 % cua thu vien cell); buf_8 chi dat khi cach
chan ~8 um, halo cat row 10 um giu buffer >= 12 um nen con 44-70 chan vuot 0.1-5.6 ps. `dout` max_capacitance 0.0276 pF. Bao cao theo
loai, khong sua bang dien tich lon. Dinh chinh: cau "khong the dat voi day that" trong bao cao cu da duoc thay bang phan tich buf_8 /
halo.

**Bay cong suat.** `power__total` cua OpenLane la goc max_ff (8 KiB-RAM: 115.5 mW). Vectorless phu thuoc hoat dong gia dinh cua dau vao
(`reset_n` chua dong bo lam switching +~37 mW: 154.34 -> 102.96 mW). `read_saif` bo qua net phang; chan trong vong phan hoi khong lan
truyen; Questa giu DURATION tong khi `power reset`. Cong suat macro SRAM lay tu Liberty TT, khong phu thuoc hoat dong.

**Antenna.** LEF OpenRAM khong co du lieu antenna lam CheckAntennas segfault (them `ANTENNAGATEAREA` / `ANTENNADIFFAREA`). Diode
heuristic 90 um lam te hon (101,367 diode); 250 um giam ~74 % nhung diode bi tinh la tai, gay 3,276 / 3,277 vi pham fanout. Vong sua sau
DRT (openlane-local) dat 0/0 tren DM va SA2; tren DM_VC4 vong route lai sau sua antenna khong hoi tu (muc 8.3). Tag `antoff` khong co
nghia sua sau DRT tat. Thong diep abort/crash chung cua driver khong phai nguyen nhan: doc log native.
final_A (2026-09-27): antenna 140 net la 100 % PAR tren met1-met3. Diode heuristic 90 um them +3.5 % dien tich;
`HeuristicDiodeInsertion` can `DIODE_ON_PORTS both`, `GPL/DPL_CELL_PADDING 4/2` (ghi trong docstring) - 19 lan hong truoc khi dat
(2026-09-23).

**Bay trang thai run OpenLane.** (1) Khong xoa thu muc step da xong cua run con resume (`state_in.json` tro bang duong dan tuyet doi);
(2) resume lay `state_out.json` moi nhat tim de quy (resume qua buoc bi gate tat lam antenna repair chay lai tren database da sua); (3)
config chi doc luc bat dau; (4) `state_out.json` cua STAMidPNR mang metric ss / ff cu tu STAPrePNR; (5) thu muc step ton tai truoc khi
step chay va flow bi cat ngan cung ghi `final/`: thanh cong la `state_out.json` hoac metric; (6) step resume duoc danh so sau so lon
nhat hien co; (7) OpenLane ghi noi `error.log` qua cac lan resume: chi xet phan cua lan thu hien tai; crash "unexpected error" khong ghi
gi vao `error.log` nen phai xet ma tra ve (`asic/run_resume_retry.sh`); (8) run co buoc cuoi (EQY goc) hong thi khong co `final/`:
artefact ky ten (netlist, DEF, GDS, SPEF, report) nam trong thu muc step tuong ung; tim o do, khong ket luan run khong co dau ra.

**Bay knob padding.** Padding 1 site moi ben phai dat `GPL_CELL_PADDING` / `DPL_CELL_PADDING` = 2, vi script OpenLane chia doi bang
phep chia nguyen; gia tri 1 la KHONG padding. Moi run tag pad1 (vd. `sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1`, DM_VC4
pad1) dung gia tri 2 (muc 8.2, 8.3).

**Khong sua script dang chay.** Bash doc script theo offset; file nguon sua trong luc flow doc cung bi doc nua chung (`alu.v`
2026-09-25). Viet file moi; dung bang co huy hop tac (`asic/.abort_*`, `results/.abort_*`). Runner phai bao ma tra ve cua chinh cong
cu. `pgrep -f` trong `bash -c` co the khop chinh no (2026-10-14).

**Ghim CPU tren Windows.** Mat na `start /affinity` la HEX (`20` = CPU 5; `32` = CPU 1, 4, 5); `cmd /c "start /wait ..."` tra 0 bat ke
ma thoat cua chuong trinh con, phai dung `cmd /v:on /c "start /wait /b /affinity <mask> "" ... & exit !ERRORLEVEL!"` (2026-10-14).

**Goc ss.** CPI khong doi nen ss duoc bao cao, khong sua: 8 KiB-RAM nom_ss -7.413 / max_ss -8.311 (2,511 endpoint, ~35 MHz); DM
16 KiB-RAM -6.897 / -7.365 (TNS -11,439); DM hanh lang 11.305 mm2 -8.292 / -8.754. Phan ra 2,557 endpoint max_ss: trung binh 15.8 ns
logic (22.6 cell) + 7.8 ns repeater + 0.5 ns day; 1,504 endpoint la PC -> hit I$ -> stall -> enable RF/BHT. STA what-if: moi vong
toi han bi cat lai lo vong ke o -4 .. -8 ns; cac thay doi cycle-exact (R13a) va AREA 3 khong doi max_ss; dong ss can pipeline moi
(fetch 2 tang voi du doan o decode, execute 2 tang, stall dang ky, cay reset co pipeline).

**Resizer duoi theo goc ss.** Chan doan 2026-10-09: moi buoc resizer chay o ba goc (tt, ss, ff) voi bien setup 2.0 ns; ss khong cau
hinh nao dong o 20 ns (WNS -9 .. -10 ns, ~7,600 endpoint), nen resizer chen / phong to buffer hang gio vao cum tag (DM_VC4
ResizerTimingPostGRT ~3 gio, 1,400 vong), ton dien tich / cong suat, gay tac ma khong giup goc bi gate (tt / ff). Sua: `RSZ_CORNERS` =
nom_tt, nom_ff cho moi buoc resizer (ke ca ECO sau route); ss van bao cao o sign-off. SA2 10.54 mm2: P1 22 phut (truoc 43), it hon
~1,100 cell; P2 24 phut (truoc 76) (muc 8.2).

**Verilator va latch.** `--Werror-LATCH` bao 0 voi `always @(*)`; `design__inferred_latch__count` khong phai bang chung. Dung
`scripts/latch_sweep.sh` va dem cell `dlxtn` / `dlxtp` trong netlist cong.

**Pham vi kiem chung va provenance.** UVM frozen la subset DM seed 1 (bo sung 48 ca, chua SA4/FAST_HIT; coverage functional). Manifest
chi phu top ASIC cua DM; top SA2/VC4 va `asic/dse_sram` co hash rieng (`results/workspace_audit/asic_input_provenance.json`) va tu
2026-10-14 nam trong snapshot `rtl_rfbht`. Ten Rxx khong du de chon ket qua (R17 tung la alias cua R8); comment trong RTL frozen con
ten tai lieu cu, khong sua de giu manifest IDENTICAL.

## 10. Nhat ky don dep

Danh sach tung muc da xoa: `results/cleanup_deleted.txt`. Bang chung run da xoa (resolved.json, metric cuoi, log loi / canh bao, flow
log, danh sach buoc): `results/pd_run_archive/<run>/`.

| Ngay | Da xoa | Dung luong | Ghi chu |
|---|---|---:|---|
| 2026-09-19 | run that bai; roi step lap lai cua bao retry trong hai run con lai | 24.6 GB; 61 -> 13 GB | vong hai lam hong resume (muc 9 "Bay trang thai run") |
| 2026-09-24 | 697 thu muc step that bai (khong `state_out.json`) | 31 GB | 5 log dai dien o `asic/evidence/failed_steps_20260924/` |
| 2026-09-26 | 5,074 file nhi phan tai tao duoc cua 30 run loi thoi | 157.1 GB | giu log / report / metric |
| 2026-09-26 | 47 run loi thoi va trung gian | ~112 GB | |
| 2026-09-27 | 159 muc: run netlist cu, mau mat do khong chon, scratch EQY | 68.6 GB | |
| 2026-09-27 | 177 file trung gian chung minh tuong duong | 7.47 GB | 2 dau vao chung minh dai so giu dang gzip |
| 2026-09-28 | run tham do antenna / RC, run RC hieu chinh bi loai | 43.9 GB | |
| 2026-09-30 | 15 run bi thay the | 101.3 GB | chu du an tu xoa (`results/cleanup_20260930_deleted.txt`) |
| 2026-10-07 | san pham build tai tao duoc o goc (db Quartus, thu vien Questa, VCD) | ~5 GB | |
| 2026-10-07 | 77 run PD loi thoi / that bai / sang loc | 198 GB | |
| 2026-10-07 | goc `asic/`: 68 script mot lan, 178 log console, thu muc thi nghiem | ~5.7 GB | `results/pd_run_archive/asic_{console_logs,experiments}_20261007.tar.gz` |
| 2026-10-07 | tai lieu trung lap (gop vao NHAT_KY, QUY_TRINH, RESULTS, REVIEW_RESPONSE, README) | - | git giu ban goc |
| 2026-10-07 | 84 config, 45 floorplan cua thi nghiem da xoa run; 3 thu muc thiet ke 1 KiB khong dung | 45 MB | `results/pd_run_archive/asic_1kb_designs_20261007.tar.gz` |
| 2026-10-08 | golden v1 `E:/Projects/RISCV-research_GOLDEN_20260927` (final_A / B, muc 8.1) | ~12 GB | theo yeu cau chu du an; ~20 GB khac la hard link chung voi FINAL3; con mot golden `RISCV-research_GOLDEN_FINAL3_20260928` (DM 8 KiB-RAM); moc DM 16 KiB-RAM dang khoa (r14F_A / B = dm_grid3665x2900_r1 / _r2) KHONG nam trong golden nao, chi trong workspace |
| 2026-10-09 | 17 run PD da archive + 22 thu vien Questa idle | 79.558 GiB logic | giu 2 run co dependency; 20 file nguon/coverage va 6 file goc bi tool review chan, chua xoa; `results/workspace_audit/` |
| 2026-10-09 | final_B CHUA XOA | 0 | 6 input + 562 file bang chung da kiem, 14 reader doi duong dan; xoa bi chan; `results/final_b_dependency_migration_20261009/cleanup_outcome.json` |
| 2026-10-14 | 43 thu muc PD that bai / dung / sang loc | ~125 GB | `scripts/maintenance/archive_and_delete_failed_pd_20261014.sh`; archive `results/pd_run_archive/20261014/`, log `results/pd_run_archive/archive_and_delete_20261014.log` |
| 2026-10-14 | worktree + nhanh `worktree-agent-ae25d606b11a3137d` + thu muc `.claude/` trong repo da cong bo (chi doc): CHUA XOA | 0 | lan goi phien cloud phu dau tien loi khi tao worktree (repo o dia e: / E:) va de lai; lenh go bi bo loc an toan tu choi, da dua lenh go cho chu du an (chua xac nhan da go) |
| 2026-10-15 | dmuA / dmuB | - | sau khi archive bang chung text (chu du an) |

Luon giu: tai lieu duy tri, log (log cu nen lai), CSV chuan da chay kep, moc 1 KiB `asic/soc_dm_control/runs/sync_final`, bang chung
Magic, SOF board, run ky ten, golden snapshot.

## 11. Bang doi ten

Ten cu van con trong log, commit, ten thu muc va comment script. Khong doi ten tren dia nhung gi run con giu (duong dan tuyet doi
trong `state_in` / `resolved.json`); ten moi dung cho tai lieu va run / file moi.

| ten cu | ten moi / muc | loai |
|---|---|---|
| HANDOVER_CODEX.md | PROJECT_STATE.md | tai lieu trang thai (doi 2026-10-09) |
| CODEX_PROMPT.md | instructions lich su (2026-10-09), thay bang PROJECT_STATE.md + QUY_TRINH.md | da xoa 2026-10-15, con trong git |
| CLOUD_TASKS.md | PROJECT_STATE.md muc 1 (quy tac phien cloud) va nhat ky trang thai | gop 2026-10-15 |
| make_golden_snapshot2.py | de xuat golden_snapshot.py | chua doi ten: tool review chan |
| dmuA / dmuB | dm_corr3400x3325_f220_r1 / dm_corr3400x3400_f220_r1 | run DM hanh lang |
| sa2uA / sa2uB | sa2_corr3400x3325_f220_r1 / sa2_corr3400x3400_f220_r1 | run SA2 |
| vc4uA / vc4uB | vc4_corr3400x3325_f220_r1 / vc4_corr3400x3400_f220_r1 | run DM_VC4 |
| u2fg33, "phuong an A" | corr3400x3325_f220 (11.305 mm2, hang cache tren FS, khe 220 um) | floorplan |
| u2fg, "phuong an B" | corr3400x3400_f220 (11.56 mm2) | floorplan |
| U2 khac (u2a, u2s1..s5, u2f, u2fh, u2fg3/35/4, u2ng3/35, u2nm3, u2r1, u2b) | corr<W>x<H>_<n/f><khe> | floorplan sang loc (`asic/fp_explore/fp_summary_20261006.md`) |
| wide, ring1, ring2, strata1, channels, column, four-corner | wide4211x3331, ring3200x3190, ring3700x3400, strata3260x3400, bands2800x2900, c1k_column1800x2900, c1k_corners1800x2900 | floorplan cu |
| r14F_A / r14F_B, `config_R14_FINAL.json`, `macro_placement_grid_r14.cfg` | dm_grid3665x2900_r1 / _r2, grid3665x2900 | DM 16 KiB-RAM ky ten 2026-10-02 |
| final3_A / final3_B, `config_FINAL3.json` | dm_ram8k_grid2800x2900_drtant_r1 / _r2 | DM 8 KiB-RAM ky ten 2026-09-28, golden |
| final_A / final_B / r12b_d42, `config_FINAL.json` | dm_ram8k_grid2800x2900_heurdiode_r1 / _r2 / _r3 | ky ten 8 KiB-RAM dau |
| final2_A | dm_ram8k_grid2800x2900_drtant_rc2 | bi loai |
| sync_final (soc_dm_control) | dm_c1k_baseline | moc 1 KiB |
| r14_A, r14_E7 .. r14_E16 | dm_grid3665x2900 + knob (muc 8.1); E16 = cau hinh ky ten | thi nghiem |
| x_E1 .. x_E6, x_E3R, x_E3R2, x_E5b, x_E4_A, X1 .. X4 | thi nghiem tren final3 (muc 8.1) | thi nghiem |
| f3_H1 / f3_H2 | dm_ram8k_grid2800x2900_hold002 / _dens55_hold003_cts8 | thi nghiem |
| sa2F_A/B, vc4F_A/B, vc4R1F_A, vc4S1, <cfg>U2<fp>[G50] | SA2 / DM_VC4 tren luoi DM, luoi rong, vong, tang, hanh lang (muc 8.2, 8.3) | thi nghiem |
| E0 | SA2: `_rsztf.json` + `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` + `P2_MIN_HOLD` chay mot flow (`..._eco2`) | cong thuc |
| E1 | SA2 `..._rsztf_cts25` (CTS clustering 25) | cong thuc |
| V2 / V3 / V4 / V5 | DM_VC4 `..._pad1_antgrt10_nogrtt_nogrtd_antcong_r1` / `_r2` / `vc4_corr3800x3400_..._antcong_r1` / `..._antcong_mwl500` | cong thuc |
| J1, J2, J3; T1 .. T12 | ma job / viec trong PROJECT_STATE.md | quy uoc noi bo |
| quy tac P / Q / M / H (trong log) | P: probe suc khoe khong du de dung cong viec; Q: 2026-10-13 khong chay tiep tu buoc fail, sua 2026-10-14 (muc 8.4); M: khong dung job dang chay de lay bo nho, khong lach lenh bi tu choi; H: DRV bao cao theo loai | quy tac (QUY_TRINH) |
| G1, G2, G3, G4, G5, G6 | grt_overflow, cts_tt_slack, grt_repair_overflow, grt_tt_slack, drt_convergence, signoff | cong flow |
| asic/snapshots/rtl_r14, rtl_r15, rtl_r16 | RTL 2026-09-29 "RAM 16 KiB", 2026-10-02 "core N-way", 2026-10-06 "FAST_HIT" | snapshot PD |
| asic/snapshots/rtl_rfbht | RTL `6c4ccffd` (2026-10-08) + 3 wrapper SA2/DM_VC4 | snapshot PD hien hanh |
| R1 .. R16 cua 2026-09-24 | cac muc cua dot rtlfix (muc 1.2) | muc cong viec |
| R8 (sau goi R17), a0c425f8 | bo dong bo dau vao | ban RTL |
| R7a + R7b + R8, 358cb660 | bo cong dich fetch, bo nhan 33x33, chan nguon macro | ban RTL |
| R9 (ecf4fc03), R10 / fix 1 / fix 2 (b56fbd4e, 2bffe7cc, d030ad12), R11 | sua co trong tam cho goc ss | ban RTL |
| R12 (e21ef330), R12b (8b163675) | RTL cuoi ban 8 KiB-RAM | ban RTL |
| R13a / R13b | thu RTL cycle-exact / nhan 2 tang (2026-09-28) | thu nghiem |
| R14 (535ec0f9, 1d584624, 3ea52396; 9b868f10) | RAM chinh 16 KiB | ban RTL |
| R15 (d409b09d) | core N-way (SA4) | ban RTL |
| R16 (ea3ef852, c09143ea), *_fast, r16f | FAST_HIT; diem FAST_HIT = 1 co hau to `fast` | ban RTL |
| rfbht (dcbf3495, 6c4ccffd) | RF/BHT trong M9K tren FPGA | ban RTL hien hanh |
| rtlfix / c235dfb7 (b82c2717, aa8e32f9) | dot sua RTL 2026-09-24 .. 25 | ban RTL |
| dedup / synccache / tagfix / sanitized | trang thai RTL 2026-09-17 .. 18 | ten file ket qua cu |
| Entry 1 .. 33 (`CLAUDE_AUTONOMY_LOG.md`) | cac muc 2026-09-16 .. 18 (tim theo ngay trong muc 1, 2, 3, 7) | tieu de cu |
| Entry 34 .. 35, Incident 83-90 | ky ten 8 KiB-RAM dau, final_A / final_B (muc 8.1) | tieu de cu |
| `PD_incident_report.md` A, B1-B4, C1-C11, D1-D5, E1-E3, F, G1-G8, Incident 33-38 | muc 7 (2026-09-18 .. 19); B3 / B4: ghi chu bang chung Magic (muc 9 "Magic namespace collision") | tieu de cu |
| `asic/FLOW_JOURNAL.md` log 2026-09-22 .. 24, Incident 52-56 | muc 7 (2026-09-22 .. 24), ha tang muc 6.1 | tieu de cu |
| Incident 57-61 | PD dau tren RTL dong bang (muc 7, 2026-09-25) | tieu de cu |
| Incident 62-70 | bo dong bo dau vao (muc 1.2 `a0c425f8`; muc 7 `r8_a0c4`) | tieu de cu |
| Incident 71-75 | bo cong dich fetch / bo nhan (muc 1.2 `358cb660`; muc 7 `r7r8_358c`) | tieu de cu |
| Incident 76-81 | sua ss 2026-09-26 va RTL cuoi `8b163675` (muc 1.2; muc 8.1 r9_ecf4, r10A) | tieu de cu |
| Incident 82 | chon cau hinh PD cho `8b163675` (muc 8.1, mau mat do) | tieu de cu |
| Incident 91-92 | antenna sau DRT, final3 (muc 8.1; muc 9 "Antenna") | tieu de cu |
| Incident 93 | thu nghiem tren final3 2026-09-28 (muc 8.1, x_E / X) | tieu de cu |
| Incident 94-95 | ket qua r14F, thac dien tich (muc 8.1) | tieu de cu |
| Incident 96 | muc 8 | tieu de cu |
| Incident 97 | muc 9 "Job nen va ket thuc phien" | tieu de cu |
| hau to _A / _B cua run | _r1 / _r2 (lan chay kep); A / B trong "phuong an A / B" la floorplan | quy uoc |
| TAG Quartus / CSV rtlfix, c235dfb7, r7r8, r10, r10f2, r12, r12b, r14, r15, r16, r16f | giu cho file cu; do moi dung ten theo ngay | ten file ket qua |

## 12. Bao cao va ban giao (moc thoi gian)

| Ngay | San pham | Duong dan |
|---|---|---|
| 2026-09-27 | bao cao ban giao 8 KiB-RAM (sau gop vao RESULTS.md) | `results/FINAL_METRICS.md` (git) |
| 2026-10-09 06:40 UTC | ban giao `HANDOVER_CODEX.md` (nay `PROJECT_STATE.md`); trang bao cao; danh sach dung luong run | `results/report_page/bao_cao_soc_v5.html`, `results/cleanup_candidates_20261009_sizes.txt` |
| 2026-10-09 18:40 | kiem toan workspace (73,861 file, 254.6 GiB), ban do chuc nang | `WORKSPACE_MAP.md`, `results/workspace_audit/` |
| 2026-10-09 17:57 | bang hop nhat CPI / hit / PPA | `results/unified_metrics.md` (`scripts/metrics/unified_table.py`) |
| 2026-10-10 07:51 | goi tai lieu viet bao cho dong nghiep (121 file, ZIP kiem CRC / SHA) | `results/colleague_materials_20261010.zip` |
| 2026-10-10 08:25 | bao cao trang thai de doc (snapshot; da xoa 2026-10-15 vi bi PROJECT_STATE / RESULTS thay the, con trong git) | `results/bao_cao_trang_thai_20261010.md` |
| 2026-10-10 08:39 | figure research (PPA FPGA seed chung, Embench controller) | `results/paper_figures_20261010.zip`, `results/paper_figures_20261010_package_receipt.json` |
| 2026-10-14 01:00 | ban nhap trang thai phan bien (20 diem) va danh sach 38 muc mo rong so voi ban 1 KiB (gop vao `REVIEW_RESPONSE.md` 2026-10-15) | `results/review_status_20261014.md`, `results/extensions_vs_published_1kib_20261014.md` (con trong git) |
| 2026-10-14 21:30 | trang bao cao Version 9 (tieng Viet) | `report_page/soc_report.html` |

## Lich su tai lieu

| Ngay | Thay doi |
|---|---|
| 2026-09-16 .. 2026-10-07 | lich su nam rai rac trong `CLAUDE_AUTONOMY_LOG.md`, `PD_incident_report.md`, `asic/FLOW_JOURNAL.md`, `RAM16K_CHANGES.md` |
| 2026-10-07 | gop thanh `NHAT_KY.md` duy nhat (commit `507c3fb`), them muc don dep (`480508d`) |
| 2026-10-15 07:46 | `NHAT_KY.md` cap nhat toi trang thai 2026-10-15 (commit `2d4202d`) |
| 2026-10-15 | viet lai theo chu de (CLOUD_TASKS Task 1, ban nhap `NHAT_KY_v2.md`, commit `45ee690`); bang board 42 case thay 42 muc rieng; danh dau [HT]/[LS]; loi may ghi trung tinh |
| 2026-10-15 | chu du an: thay han ban theo gio, chi giu mot phien ban; so muc 8 / 8a / 9 / 10 / 11 giu tuong thich voi script va tai lieu cu |
| 2026-10-15 | ra soat do day du so voi ban theo gio (104 ung vien, 61 muc giu lai sau loc doc lap): bo sung chi tiet so lieu, co che, quyet dinh va bay vao muc 1.2, 2, 3, 4, 5, 6, 7, 8.1-8.4, 9, 10, 11; moi so cua muc de xuat da doi chieu co mat |
