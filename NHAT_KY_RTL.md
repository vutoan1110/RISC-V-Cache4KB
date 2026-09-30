# Nhat ky sua RTL — dot 2026-09-24

File nay ghi moi thu trong dot sua RTL: sua cai gi, vi sao, anh huong toi dau,
do dac gi, loi gi gap phai va sua the nao. Doc tu tren xuong la theo thu tu thoi gian.

## Quy trinh ap dung cho dot nay

1. **RTL truoc, PD sau.** PD da dung han luc 09:35 (driver, OpenLane, watchdog deu da tat).
   PD chi chay lai khi RTL da sach va da dong bang.
2. **Moi thay doi RTL keo ca chuoi:** lint (moi CACHE_CONFIG x moi LINE_COUNT),
   directed regression, UVM, Embench 48 run, Quartus LE, roi moi toi PD. Moi phep do
   chay hai lan, chi nhan khi hai lan khop nhau (may co loi RAM da chung minh).
3. **Khi RTL da dong bang, PD co sua gi cung khong dong vao RTL.**
4. **Khong tat chuc nang nao de flow qua.** Neu mot cong kiem tra khong the dat, ghi ro
   so lieu va ly do, khong ha cong.
5. **Loi thi dao sau, co bang chung**, khong chay lai mu quang.
6. Kiem tra tien trinh moi 10 phut (treo / crash).

## Moc truoc khi sua

| Hang muc | Gia tri |
|---|---|
| Snapshot | `asic/backups/hdl_pre_rtlfix_20260924T093817Z.tar.gz` (hdl, tb, verification, firmware, scripts, wrapper ASIC) |
| Manifest RTL | `9cd02a066bc38a03ef1388f639198e42` (68 file) — trung voi moc da kiem chung chuoi LE |
| Embench tham chieu | `results/tagfix_1kb_p1/p2.csv`, `results/tagfix_4kb_p1/p2.csv` (23/09) |
| CoreMark tham chieu | `results/coremark_1kb.csv`, `results/coremark_4kb.csv` |

## Danh sach day du cac de xuat RTL, gom tu toan bo lich su

Nguon: transcript cac phien (17/09 - 24/09), `CHANGELOG_AND_ISSUES.md`, `DSE_RESULTS.md`,
`CLAUDE_AUTONOMY_LOG.md`, `asic/FLOW_JOURNAL.md`.

| # | De xuat | Nguon | Trang thai luc bat dau dot nay |
|---|---|---|---|
| R1 | Read-enable cho mang du lieu cache | 17/09 17:44 | `icache_data_ram.v`/`dcache_data_ram.v` da co `rd_en`; **`cache_dse_data_bank.v:35` chua** — doc moi chu ky |
| R2 | Tham so `PERF_COUNTERS_ENABLE` | 17/09 17:44 | da lam |
| R3 | `m_axi_bresp` bi bo qua trong `cache_axi_master.v` | 17/09 17:44 | **chua** — chi dung `bvalid && bready`, loi ghi AXI mat |
| R4 | UART khong xuat `tx_fifo_full` / `rx_fifo_empty` | 17/09 17:44 | **chua** — thanh ghi 0x10 chi co 5 bit |
| R5 | 2 latch `dlxtn_1` trong `rx_block.sv` (nhanh `default` thieu gan) | 24/09 | **chua** |
| R6 | regfile -> MLAB | 18/09 09:08 | khong kha thi: Cyclone IV E khong co MLAB. Phuong an M9K doc dong bo la doi pipeline |
| R7 | Tach duong toi han 54 tang logic (goc ss) | 23-24/09 | **chua** — doi pipeline |
| R8 | Noi `vccd1`/`vssd1` trong wrapper macro ASIC | 18/09 16:28 | chua; PDN da noi that qua `PDN_MACRO_CONNECTIONS` |
| R9 | Chi so 4 bit vao vector 8 bit trong `tx_block`/`rx_block` | 17/09 13:02 | da lam |
| R10 | `reset_n` vua dong bo vua bat dong bo (`SYNCASYNCNET`) | 17/09 13:02 | da lam |
| R11 | Cac loi be rong (`BRANCH_PREDICT_ENABLE`, baudrate, lcd) | 17/09 13:02 | da lam |
| R12 | Tag hot-line `[27:3]` cung trong `icache_dse_core.v` | CHANGELOG 9.2 | da lam |
| R13 | Copy eviction gate sai co (`IS_SA2` thay vi `VC`) | CHANGELOG 3.2 | da lam |
| R14 | AXI master ep can refill 16 byte | CHANGELOG 3.1 | da lam |
| R15 | Vong reset tag RAM 256 lan (`BLKLOOPINIT`) | 18/09 16:28 | da lam |

## Ke hoach thuc hien

Thu tu: R5 (va quet latch toan thiet ke) -> R1 -> R3 -> R4 -> R8. Moi muc: doc ky
FSM/logic lien quan, danh gia anh huong toi TB/UVM/firmware, sua, lint, smoke test.
Sau khi ca bon muc xong: chay **mot** lan full chain tren RTL cuoi, roi dong bang.

R6 va R7 doi pipeline, tuc la doi CPI cua moi kernel va vo hieu toan bo so lieu
nghien cuu. Hai muc nay khong phai sua loi ma la thay doi kien truc; ghi ro o day va
bao cao rieng, khong tu y lam.

---

## Tien trinh


### 09:40 — Quet latch toan thiet ke bang Yosys (cong cu moi: `scripts/latch_sweep.sh`)

**Vi sao can cong cu moi:** `lint_rtl.sh` co `LATCH` trong nhom loi nghiem trong nhung
van bao sach, trong khi netlist ASIC co 2 cell `dlxtn_1`. Ly do: Verilator chi bat LATCH
trong khoi `always_comb`, con khoi o `rx_block.sv:185` la `always @(*)`. Yosys suy latch
giong nhau cho ca hai kieu va in tung latch no tao ra, nen dem bang Yosys la dem dung.
Script elaborate du 8 to hop (CACHE_CONFIG 0..3 x LINE_COUNT 64/256) vi nhanh generate
khong duoc chon thi khong bao gio duoc kiem.

**Ket qua truoc khi sua:** 2 latch o moi to hop, 16 tong cong, **ca 16 deu o cung mot cho**:
```
rx_block.baud_rx_en  <- process rx_block.sv:185
rx_block.write_fifo  <- process rx_block.sv:185
```
Khong co latch nao khac trong toan thiet ke (tx_block, cache, AXI, core deu sach).

### 09:45 — R5: sua latch `rx_block.sv`

Nhanh `default` cua `case(current_state)` chi gan `rx_done`. Da them `write_fifo = 0` va
`baud_rx_en = 0`. Trang thai 2'b11 khong the dat toi (reset ve IDLE, `next_state` chi nhan
IDLE/RECEIVE/STOP), nen hanh vi o moi trang thai dat duoc **khong doi**.

**Ket qua sau khi sua:** `latch_sweep.sh` -> **0 latch tren ca 8 to hop**, script tra exit 0.

**Anh huong du kien toi phan con lai:** khong doi hanh vi -> Embench, CoreMark, directed
regression phai cho ket qua trung tung byte voi tham chieu. UART khong nam tren duong do
CPI, nhung firmware in qua UART nen neu UART hong thi harness se khong doc duoc ket qua.

### 10:05 — R1: read-enable cho `cache_dse_data_bank.v`

**Hien trang truoc khi sua:** `rd_word <= data_mem[rd_index]` khong dieu kien — 2 way x
LINE_WORDS bank M9K bi doc **moi chu ky**, ke ca khi CPU dang doi, dang refill, hay lenh
duoc phuc vu tu bo dem L0. `icache_data_ram.v`/`dcache_data_ram.v` (controller DM) da co
`rd_en` tu dot dong bo hoa cache; wrapper SRAM ASIC `cache_data_ram_sram4.v` cung da gate
`csb1` bang `rd_en`. Chi con bank cua DSE core (cau hinh SA2, DM_VC4, DM_DSE) chua gate.

**Phan tich de chung minh khong doi hanh vi (khong doan):**

I-cache (`icache_dse_core.v`): cac chu ky tieu thu `bank*_rd_line` la `ST_HIT_RESP`
(dong 260, 438), `ST_SWAP_WRITE` (446), `ST_EVICT_WRITE` (467). Chu ky ngay truoc chung
lan luot la `ST_LOOKUP`, `ST_SWAP_READ`, `ST_EVICT_READ` — deu khong phai IDLE. Ket qua
doc phat ra trong IDLE khong bao gio duoc dung.

D-cache (`dcache_dse_core.v`) **khac**: dong 450-453, khi store hit, `ST_LOOKUP` tinh
`store_merged_word` tu `bank*_rd_line` **ngay trong LOOKUP**, tuc dung ket qua doc phat
ra trong chu ky IDLE. Neu ap nguyen quy tac cua I-cache (`state != ST_IDLE`), moi lenh
`sb`/`sh` se tron byte vao du lieu cu — loi im lang. Da tranh duoc vi doc code truoc.
Dieu kien IDLE->LOOKUP (dong 419-437): moi store, va moi load truot L0.

**Ban sua:**
```
cache_dse_data_bank.v : them cong rd_en;  if(rd_en) rd_word <= data_mem[rd_index];
icache_dse_core.v     : bank_rd_en = (state != ST_IDLE) || (req_fire && !hot_hit);
dcache_dse_core.v     : bank_rd_en = (state != ST_IDLE) || (req_fire && !fast_load_main_event);
```
Dung cung mot dang than trong cho ca hai cache: giu doc o IDLE khi request sap vao LOOKUP.
Chi bo doc o chu ky ranh va chu ky L0 hit — dung noi ton dien ma khong ai dung ket qua.

Module chi duoc instance o 2 DSE core (4 instance); khong testbench nao instance truc tiep,
nen them cong khong gay TB. Quartus suy M9K co clock-enable dung nhu `icache_data_ram.v`.

**Kiem tra ngay:** `lint_rtl.sh` 8 to hop -> 0 canh bao nghiem trong, 0 loi elaborate,
canh bao cau truc giu nguyen 770/56/8 (khong phat sinh moi). `latch_sweep.sh` -> 0 latch.

**Anh huong du kien:** CPI cua moi kernel o moi cau hinh phai **trung tung chu ky** voi
tham chieu (ma tran Embench la phep thu). Cong suat FPGA cua SA2/DM_VC4/DM_DSE phai giam.
Design ASIC 4 KiB (DM) khong doi.

### 10:15 — R3: phan tich `m_axi_bresp` (chua sua, dang cho R16)

`cache_axi_master.v` la **bo dem ghi posted** (WB_DEPTH=2): D-cache nhan phan hoi ghi
ngay khi store duoc day vao buffer (`d_write_rsp_valid_q <= wb_push`), con `bresp` cua AXI
ve sau do nhieu chu ky (`wb_pop` khi `b_fire`). `d_write_rsp_error = 1'b0` va dong 150 ghi
chu "store hit is always in-range RAM". Hop dong nay **co y** va co test khang dinh:
`tb/axi_memory_tb.sv` T19 (tiem loi ghi, kiem store khong bao loi dong bo, RAM khong doi)
va UVM `wthru_agent.sv:118` (`d_write_rsp_error` luon bang 0, phan hoi sau dung 1 chu ky).

Vay **khong the** tra loi ghi ve dung lenh store ma khong bo posted write (doi CPI).
Cach dung cho kien truc posted la loi ghi **khong chinh xac (imprecise)**: chot co loi
sticky + dia chi ghi loi dau tien vao thanh ghi phan mem doc duoc. Cho dat: khoi sysmon
(`apb_performance_monitor`, APB `0x4000_0300`, ABI "S8" v1), offset trong tu `0xAC`.
UVM register model khang dinh `sysmon.ident == 0x53380001` -> neu tang phien ban ABI thi
phai sua `soc_reg_model.sv` va `gen_soc_periph_irq.py`.

### 10:25 — PHAT HIEN: ban sao SoC top cua ASIC da lech (nguon goc cua RTL thieu nhat quan)

`asic/soc_dm_4kb/soc_top_asic.v` tu ghi o dau file: *"byte-for-byte identical except the
axi_ram_32 instantiation ... this copy will silently go stale"*. `diff -w` voi
`hdl/soc_top.v`: **66 dong khac**:
- thieu 3 tham so `CACHE_LINE_WORDS`, `PERF_COUNTERS_ENABLE`, `L0_ENTRIES`; khong truyen
  `LINE_WORDS`/`L0_ENTRIES` xuong cache va `LINE_WORDS` cho `cache_axi_master` — chay dung
  chi nho gia tri mac dinh trung hop;
- dot don RTL (CHANGELOG 9.1) xoa 8 day probe khoi `soc_top.v`; ban ASIC **van giu ca 8**
  (`rts_n`, `data_addr`, `data_sel_*`, `axi_grant_source`, `apb_sel_unmapped`,
  `perf_counter_freeze_dbg`) -> day chinh la 71 canh bao UNUSEDSIGNAL cua `soc_top_asic.v`.

Nguyen nhan cau truc: RAM cache duoc thay bang **cung ten module** (`cache_data_ram_sram4.v`
dinh nghia `icache_data_ram`/`dcache_data_ram`, file goc bi loai khoi danh sach) — sach.
Rieng AXI RAM lai dung ten khac (`axi_ram_32_asic_macro`), buoc phai sao chep ca SoC top.
Cong va tham so cua hai module AXI RAM **giong het nhau** (da so tu dong).

Bon thu muc 1 KiB nghien cuu (`soc_dm_control`, `soc_dm_dse`, `soc_dse_vc1`,
`soc_vc4_check`) cung co ban sao rieng; khong phai design hien tai nen **khong dong vao**.

### 10:30 — PHAT HIEN: bo nho ASIC chua bao gio duoc mo phong

Dau file `axi_ram_32_asic_macro.v`: *"STATUS: written but NOT YET SIMULATED against
tb/axi_memory_tb.sv or any other testbench ... Do not treat this as verified"*.
`grep` toan bo `tb/`, `verification/`, `scripts/`: **khong testbench nao nap**
`axi_ram_32_asic_macro.v` hay `cache_data_ram_sram4.v` hay model SRAM. Toan bo chuoi
TB/UVM/Embench chay tren RAM hanh vi cua FPGA. He thong bo nho cua netlist ASIC 4 KiB
chua duoc kiem chuc nang lan nao — LVS/DRC khong kiem chuc nang, con EQY chua chay xong.
-> Phai lam **mo phong view ASIC** truoc khi dong bang RTL.

### 10:35 — PHAT HIEN: script EQY so voi netlist cua run cu

`eqy_soc_asic_top.eqy`, muc `[gate]`, ghi cung:
`.../runs/ch4kb/294-openroad-fillinsertion/soc_asic_top.nl.v` — netlist cua run ban cu.
Moi lan EQY trong `ch4kb_full` deu so RTL voi netlist **khong phai cua run dang chay**.
Ke ca neu EQY pass cung khong chung minh duoc gi. Se sua o pha PD (script phai lay
netlist cua chinh run do).

### 10:35 — `lint_asic.sh` chua tung chay tren `soc_dm_4kb`

Khong co `results/verilator_lint_asic_soc_dm_4kb.txt`. Neu chay nguyen trang, script nap
`hdl/cache/*.v` **va** `asic/soc_dm_4kb/*.v` -> hai dinh nghia `icache_data_ram` cung ten.
Se sua de lay dung danh sach file tu `config.json` (lint dung thu OpenLane tong hop).

### 10:45 — R16 (muc moi): gop ASIC ve MOT SoC top duy nhat

**Ban sua:**
- `asic/soc_dm_4kb/axi_ram_32_asic_macro.v`: doi ten module `axi_ram_32_asic_macro` ->
  `axi_ram_32` (cung co che thay the theo ten module ma `cache_data_ram_sram4.v` da dung).
- `asic/soc_dm_4kb/soc_asic_top.v`: instance `soc_top` (tu `hdl/soc_top.v`) thay vi
  `soc_top_asic`; **ghi ro** `CACHE_LINE_WORDS=4`, `PERF_COUNTERS_ENABLE=1`, `L0_ENTRIES=8`
  thay vi dua vao mac dinh.
- `config.json` `VERILOG_FILES`: `dir::soc_top_asic.v` -> `dir::../../hdl/soc_top.v`.
- `eqy_soc_asic_top.eqy` [gold]: cung doi sang `hdl/soc_top.v`.
- `soc_top_asic.v` chuyen vao `asic/backups/` (khong con trong thu muc design).
Tu nay FPGA, mo phong va ASIC dung **cung mot file** `hdl/soc_top.v`. Ban sao khong con
ton tai nen khong the lech nua.

**`scripts/lint_asic.sh`:** doi tu glob sang doc `VERILOG_FILES` cua `config.json`, va
them `MODDUP` vao nhom loi nghiem trong.
Bang chung vi sao can sua: chay voi glob cu tren `soc_dm_4kb` cho **3 MODDUP** (ba module
dinh nghia hai lan) ma script van in `[PASS]`.

**Ket qua lint ASIC sau khi sua:** MODDUP 3 -> **0**; 0 canh bao nghiem trong; 0 loi
elaborate. Con 2 `DECLFILENAME` (ten file khac ten module — co y, do la co che thay the).

### 11:05 — R3: bat loi ghi AXI posted (imprecise write error)

**RTL:**
- `cache_axi_master.v`: them `wr_err` (sticky), `wr_err_addr` (32 bit), `wr_err_clear`.
  Chot khi `wb_pop && m_axi_bresp != OKAY`, lay dia chi tu `addr_q` (addr_q chi doi khi
  ST_IDLE bat dau giao dich moi, nen luc wb_pop no van la dia chi cua lenh ghi dang duoc
  tra loi). Giu **loi dau tien**; loi moi trung chu ky voi lenh xoa thi loi thang, khong
  mat loi nao. `d_write_rsp_error` van = 0 (hop dong posted-write khong doi).
- `apb_performance_monitor.v` (sysmon): doc `0xAC = {31'b0, bus_wr_err}`,
  `0xB0 = bus_wr_err_addr`; ghi 1 vao bit0 cua `0xAC` de xoa. `PSLVERR` cho phep ghi `0xAC`
  (truoc day moi lenh ghi khac `0x04` deu bi SLVERR). Word nhan dang `0x5338_0001` ->
  **`0x5338_0002`** (ABI v2). Hai thanh ghi moi **khong** phu thuoc
  `PERF_COUNTERS_ENABLE` vi day la trang thai, khong phai bo dem.
- `performance_observability.v`, `soc_top.v`: noi day.

**Testbench / UVM da sua theo:**
- `tb/axi_memory_tb.sv`: noi cong moi; **T19 viet lai**. Phat hien khi viet: `axi_ram_32`
  lay mau `test_bresp_error` luc cap AW/W hoan tat, con T19 cu tat `cfg_b_error` ngay sau
  lenh store posted — neu ghi AXI chua toi RAM thi loi **khong he duoc tiem**, va kiem tra
  "RAM khong doi" chi dung vi chay qua som. Nghia la T19 cu co the pass ma khong kiem gi.
  T19 moi cho toi khi master ghi nhan loi (toi da 200 chu ky), roi kiem `wr_err=1`,
  `wr_err_addr=0x1000`, RAM khong doi, va xoa duoc.
- `tb/performance_counters_tb.sv`: TB tu lai `bus_wr_err`; test moi kiem ident
  `0x53380002`, `0xAC`=0 khi khong loi, `0xAC`=1 va `0xB0`=dia chi khi co loi, ghi 0 **khong**
  xoa, ghi 1 **co** phat xung xoa, va ca hai lenh ghi khong bi SLVERR.
- `verification/uvm/tb/tb_axi_top.sv`: noi `wr_err_clear=0` (khong de X).
- `soc_periph_test.sv:45`, `soc_reg_model.sv:99`, `gen_soc_periph_irq.py`: ident -> 0x53380002.
  Chay lai generator: `soc_periph_irq.hex` **giong het tung byte** — hang so chi dung de in
  thong bao, firmware doc ident tu phan cung.

### 11:10 — Smoke test R1 + R3 (Questa)

`results/smoke_r1r3.log`: tb_axi_memory, tb_performance_counters, tb_set_associative_cache,
tb_victim_cache, tb_dcache, tb_icache, tb_cache_configuration cfg 1/2/3.
**30 PASS, 0 FAIL, 0 Fatal, 0 Error.** Trong do co
`D-cache VC store swap and SB/SH/SW write-through merge` — chinh la duong store-merge
trong LOOKUP ma R1 se lam hong neu ap sai quy tac read-enable cho D-cache.
Day moi la smoke; full regression chay sau khi xong het cac muc RTL.

### 11:25 — R4: co FIFO cua UART trong thanh ghi trang thai

**RTL:** `uart_core.sv` them 2 cong ra `tx_fifo_full_o`, `rx_fifo_empty_o` (lenh `assign`
dat **sau** khai bao `tx_fifo_full`/`rx_fifo_empty` — du an da 3 lan dinh loi dung truoc
khi khai bao). `uart_apb.v`: khai bao tuong minh hai day; `STATUS 0x10` bit 5 =
`tx_fifo_full`, bit 6 = `rx_fifo_empty` (chi doc).

**Kiem anh huong:** firmware (`sw_baremetal/platform.h:36`) chi doc `UART_STATUS & 0x1` va
ghi `0x1` -> khong bi anh huong. Firmware khong bao gio doc `SYSMON_ID` (lien quan R3).
UVM register model khai bao `uart.status` rong 5 bit -> noi len 7; them tham so reset cho
`make_reg` (mac dinh 0) va dat `uart.status` reset = `0x40` vi RX FIFO rong luc reset.
Khong co test UVM nao kiem gia tri reset thanh ghi, nhung model phai dung.

**Test moi `tb/uart_apb_tb.sv` (module `tb_uart_apb`)**, them vao
`compile_active_design.do` va `run_full_regression.do`. Truoc do **khong co testbench nao
cham `uart_apb` o muc thanh ghi** (tb_axi_mmio dung slave APB hanh vi, tb_mmio_bypass chi
kiem dinh tuyen). Test dung loopback TX->RX nen chay qua ca duong `write_fifo` cua
`rx_block` ma R5 vua sua.

### 11:30 — LOI MOI do test moi bat duoc: `RXDATA` khong bao gio tra byte vua nhan

Lan chay dau cua `tb_uart_apb` tren RTL cu: moi thu dung (FIFO rong luc reset, TX FIFO
day sau 16 lan ghi, khung loopback nhan duoc, co FIFO doi dung) **tru** byte doc o `0x04`:
```
[FAIL] loopback byte 0x00, expected 0xa0 (first byte queued)
```
**Truy nguyen nhan (co bang chung, khong doan):**
- `uart_core.rx_data_o` = `read_data` cua RX FIFO (`uart_core.sv:84`).
- `fifo.sv:28-29`: `read_data` chi cap nhat khi `read && !empty`.
- `uart_apb.v` cu chot `rx_data_reg <= rx_data_o` **luc `rx_done`** — luc do chua co lenh
  doc FIFO nao, nen chot gia tri cu (0 sau reset). Byte vua nhan nam trong FIFO nhung
  khong bao gio len duoc `0x04`; lenh `CTRL[1]` pop FIFO nhung `rx_data_reg` khong cap nhat.

Tai lieu `docs/en/guides/07_CODE_WALKTHROUGH.md:3452` ghi `0x04 RXDATA = "The received
byte"`, `CTRL[1] = "read the RX FIFO"` — code khong lam duoc dieu do.
**Anh huong toi so lieu da do: khong.** Firmware khong bao gio nhan UART (grep
`UART_RXDATA` trong `sw_baremetal`: 0 lan dung); moi benchmark chi phat.

**Ban sua `uart_apb.v`:** `RXDATA` tra byte **cu nhat chua doc** o dau FIFO. Vi FIFO doc co
thanh ghi, `uart_apb` tu nap truoc: khi `rx_data_valid=0` va FIFO co du lieu thi phat mot
lenh doc; chinh xung `read_rx_fifo_pulse` (co thanh ghi) dong vai co "dang nap" nen khong
doc hai lan; canh sau `rx_data_valid <= 1`. `CTRL[1]` hoac ghi 1 vao `STATUS[4]` = tieu thu.
Bo `rx_data_reg`. Chon cach nay thay vi "chot byte luc rx_done" vi cach kia mat du lieu
khi nhan lien tiep nhieu byte (FIFO 16 byte thanh vo dung).

**Tranh chap thoi gian da chan:** neu phan mem ghi `CTRL[1]` dung chu ky lenh nap dang bay
(`rx_data_valid` con 0), lenh xoa dung sau trong khoi `always` se de len viec dat valid ->
byte vua lay khoi FIFO bi mat im lang. Da them dieu kien `&& rx_data_valid` cho ca hai
duong tieu thu.

**Test `tb_uart_apb` mo rong:** 3 khung lien tiep khong doc -> `RXDATA` van la A0, co byte
xep hang sau; tieu thu `CTRL[1]` -> A1; tieu thu `STATUS[4]` -> A2; hang doi rong; tieu thu
khi khong co byte la no-op.

**Ket qua `results/smoke_r4b.log`:** tb_uart_apb, tb_mmio_bypass, tb_soc_integration,
tb_axi_mmio -> **7 PASS, 0 FAIL, 0 Fatal, 0 Error.**

### 11:35 — R8: noi `vccd1`/`vssd1` trong wrapper — KHONG lam, va vi sao

Day khong phai loi. Trong OpenLane 2, chan nguon macro duoc noi o buoc PDN qua
`PDN_MACRO_CONNECTIONS = ['.*u_bank VPWR VGND vccd1 vssd1']`; log PDN co
`[INFO PDN-0001] Inserting grid: sram_macro_grid - ...u_bank` cho tung macro, va
`Netgen.LVS` + `Checker.LVS` deu OK trong `ch4kb_full` — LVS so layout voi netlist co
nguon, nen chan nguon macro da noi that. Noi trong RTL buoc phai dan cong nguon qua toan
bo cay RTL, trong khi chinh OpenLane chen chung vao netlist co nguon (`.pnl.v`); lam vay
co the gay trung lap nguon khi LVS. 2 canh bao `PINMISSING` la ket qua chuan cua flow.

### 11:45 — Kiem tra tinh tren RTL cuoi (truoc chuoi day du)

| Kiem tra | Ket qua |
|---|---|
| `latch_sweep.sh`, 8 to hop | **0 latch** |
| `lint_rtl.sh`, 8 to hop | 0 nghiem trong, 0 loi elaborate; UNUSEDSIGNAL 770 -> 746 |
| `lint_asic.sh soc_dm_4kb` | 0 nghiem trong, 0 MODDUP, 0 loi elaborate |

### 11:50 — Mo phong VIEW ASIC: lan dau tien bo nho ASIC duoc chay

**Ha tang moi:**
- `tb/compile_asic_view.do`: cung RTL va TB nhu `compile_active_design.do`, nhung thay
  `icache_data_ram.v`/`dcache_data_ram.v` bang `cache_data_ram_sram4.v`, thay
  `hdl/axi/axi_ram_32.v` bang `axi_ram_32_asic_macro.v`, them model SRAM cua OpenRAM
  (`-timescale 1ns/1ps` vi model khong co `timescale`). Thu vien rieng `work_asic` de
  khong de len `work` cua view FPGA.
- `axi_ram_32_asic_macro.v`: backdoor nap chuong trinh vao 4 macro (bank b giu word
  b*512..b*512+511, dung anh xa `word_addr[10:9]`), chi ton tai khi `ASIC_VIEW_SIM` —
  tong hop va lint khong thay.
- `scripts/run_ablation.py --asic-view`: ep CACHE_CONFIG 0, 256 line, `-gVERBOSE=0` (model
  SRAM mac dinh in moi lan truy cap).

**LOI RTL #1 do view ASIC bat duoc:** bien dich that bai ngay:
```
** Error: axi_ram_32_asic_macro.v(181): (vlog-2730) Undefined variable: 'wr_state'.
   ... 'WR_COMMIT', 'wr_bank_r', 'wr_strb_r', 'wr_bank_off_r', 'wr_data_r'
```
Khoi khai bao phia ghi (dong 249-262) nam **sau** khoi `always @(*)` (164-188) dung chung.
Yosys va Verilator chap nhan dung truoc khi khai bao, Questa thi khong — va day la bang
chung file nay **chua bao gio qua Questa**. Sua: chi doi khoi khai bao len truoc, logic
khong doi mot ky tu.

**Dac tinh model SRAM can luu y:** o moi canh len model gan `#(T_HOLD) dout = 32'bx`, chi
ghi lai khi co lenh doc. Tuc la theo model cua hang, macro **khong giu output** khi khong
doc. Comment trong `cache_data_ram_sram4.v` gia dinh "dout1 holds its previous value". Neu
controller dung `rd_line` sau mot chu ky khong doc, mo phong se ra X — day chinh la dieu
view ASIC phai kiem.

**Ket qua dau tien (crc32, DM, 4 KiB):** `result_pass=1 invariant_pass=1`,
`minstret=16925` trung view FPGA. Dang chay du 12 kernel -> `results/asic_view_4kb_p1.csv`.
Luu y: wrapper AXI RAM ASIC **bo qua moi hook do tre** (ke ca `ICACHE_MISS_PENALTY=2` ma
`soc_top` cap cho RAM FPGA), nen `mcycle` view ASIC **khac** view FPGA la dung; tieu chi la
moi kernel tu kiem PASS va `minstret` trung.

### 12:10 — View ASIC: lan chay dau 1/12 PASS, va 3 LOI RTL THAT trong bo nho ASIC

Lan chay dau 12 kernel o view ASIC: **chi crc32 PASS**, 11 kernel con lai treo (FAIL_TIMEOUT),
1 loi bat bien (insertsort), 1 crash Questa (sha256). crc32 qua duoc vi no **khong co lenh
store nao** (`d_read=0 d_write=0`). Moi kernel co truy cap du lieu deu hong.

Quy trinh dieu tra, tung buoc co bang chung (khong doan):
1. Module giam sat X (`tb/asic_view_x_monitor.sv`, sau nay tach thanh cac probe) dung lai o chu
   ky dau tien X den CPU: depthconv c63011, load `0x1F44` tra X tu duong nhanh L0.
2. Bat thoi diem X lot vao L0: c62997, ngay sau beat refill cuoi.
3. Vet tung chu ky mang du lieu: beat refill thu 1 duoc ghi vao cache voi `wd=xxxxxxxx` —
   du lieu **tu RAM chinh ve da la X**. Cache khong co loi o cho nay.

**LOI #2 (nghiem trong nhat) — `axi_ram_32_asic_macro.v`, dia chi ghi thieu bypass:**
```
wire [10:0] wr_word_addr = aw_addr_q[12:2];     // dia chi DA CHOT
wr_data_r <= w_have_q ? w_data_q : s_axi_wdata;  // du lieu CO bypass
```
Khi AW va W den cung chu ky (truong hop thuong gap), `aw_addr_q` chua cap nhat nen lenh ghi
di vao **dia chi cua lenh ghi truoc**. Bang chung mo phong (probe so dia chi AW voi dia chi
commit):
```
write #1 accepted at 00000cf0 but committed to 00000000   <- de len lenh dau cua chuong trinh
write #2 accepted at 00000cf4 but committed to 00000cf0
total writes 115, committed to the wrong address 91
```
**Tuc la SoC ASIC da di PD khong chay duoc bat ky chuong trinh nao co lenh store.**
RAM FPGA `hdl/axi/axi_ram_32.v` co bypass nay tu dau (`selected_awaddr`). Sua: them
`wr_sel_addr = aw_have_q ? aw_addr_q : s_axi_awaddr`. Sau sua: moi lenh ghi dung dia chi.

**Mot huong sai, ghi lai trung thuc:** truoc khi tim ra loi #2, toi da doan wrapper cache
thieu "giu gia tri" va them thanh ghi giu cho `cache_data_ram_sram4.v`. Vet cho thay X den
tu RAM chinh chu khong phai cache, nen toi **hoan tac** ban sua do vi chua co bang chung.
Toi cung dat checker bao loi khi X lot vao L0 — sau do chung minh day la **bao dong gia**:
view FPGA vang cung co y het 14 lenh store X (prologue luu thanh ghi chua khoi tao — regfile
khong reset) va cung co X trong L0, va van PASS. Da go hai luat X khoi checker; checker cuoi
cung (`tb/asic_view_checker.sv`) chi giu bat bien ghi dung dia chi.

4. Sau sua loi #2: 11/12 PASS, edn van treo. Diff vet retire kien truc (bo vong poll UART vi
   so vong poll phu thuoc thoi gian) -> lech that dau tien: PC `0x858` `lw s2,0(a1)`,
   `a1=0xC74`, FPGA doc `fffffb9c`, ASIC doc X.
5. Probe RAM chinh cho word 797 (`0xC74`): ghi `fffffb9c` c59990, beat refill c60490 tra
   **dung** `fffffb9c`. RAM chinh khong co loi.
6. Probe tung lenh load `0xC74` o ca hai view:
```
FPGA c63386 LD -> L0 rdata=fffffb9c  hot0=ffffc132_ffffde39_fffffb9c_0000048b
ASIC c62814 LD -> L0 rdata=xxxxxxxx  hot0=xxxxxxxx_xxxxxxxx_xxxxxxxx_0000048b
```

**LOI #3 — `cache_data_ram_sram4.v` khong giu gia tri doc:** word 0 (`0x48b`) la gia tri vua
store, ba word con lai le ra la dong cu. `dcache_controller.v` tat doc o `ST_WRITE_REQ` (comment
ghi ro "those are the ones that hold") roi khi store commit ghep word vao `data_rd_line`
(`store_line_next`) de nap L0. RAM FPGA giu `rd_line` tu lan doc o LOOKUP; model SRAM cua hang
cho `dout1 = X` sau moi canh khong doc. Sua: moi bank chot gia tri da doc, `rd_line` = `dout1`
o chu ky ngay sau lenh doc, con lai = gia tri doc gan nhat. Khong them chu ky tre. Chi phi:
33 FF + mux 32 bit moi bank x 4 bank x 2 cache = 264 FF (se do trong PD).
Day chinh la ban sua da hoan tac o buoc truoc — lan nay co bang chung truc tiep.

**LOI #1** (da ghi o 11:50) — thu tu khai bao trong `axi_ram_32_asic_macro.v`, Questa khong
bien dich duoc.

### 12:40 — View ASIC sau 3 ban sua: 12/12 PASS va tuong duong kien truc tuyet doi

`results/asic_view_4kb_p1.csv`: **12/12 PASS**. So voi view FPGA DM/256
(`results/tagfix_4kb_p1.csv`): **moi truong kien truc** (minstret, d_read, d_write,
branches, taken, not_taken, predictions, correct, mispredict, load_use, control, trap) **va
moi bo dem cache** (i_access, i_main, i_miss, d_main, d_miss, axi_read) **trung khit tren ca
12 kernel**. Chi `mcycle` khac (ASIC nhanh hon 0.1-6%) vi wrapper khong mo phong
`MISS_PENALTY=2` ma RAM FPGA duoc cap.

| kernel | mcycle ASIC | mcycle FPGA |
|---|---:|---:|
| crc32 | 17,565 | 17,619 |
| depthconv | 3,504 | 3,919 |
| edn | 116,159 | 116,569 |
| fdct | 209,849 | 210,299 |
| huffbench | 339,818 | 340,910 |
| insertsort | 128,194 | 128,795 |
| matmult | 40,938 | 42,163 |
| md5sum | 64,135 | 68,153 |
| mont64 | 85,071 | 85,408 |
| sha256 | 101,425 | 104,884 |
| tarfind | 169,181 | 169,444 |
| wikisort | 160,425 | 160,935 |

**He qua cho PD:** netlist `ch4kb_full` duoc tong hop tu RTL con loi #2 va #3 — ket qua PD do
khong dung duoc cho design cuoi. PD se chay lai tu dau sau khi RTL dong bang.

**Cong cu chan doan da viet** (giu lai, co the dung lai): `tb/asic_view_checker.sv`,
`tb/x_origin_probe.sv`, `tb/retire_trace_dump.sv`, `tb/addr_watch_probe.sv`,
`tb/ram_r_probe.sv`, `tb/ram_word_probe.sv`, `tb/dcache_line_probe.sv`.

### 13:00 — Don dep, dong bang RTL, khoi chay chuoi day du

- Sua comment cua chinh toi bi Verilator hieu la pragma (`// Verilator accept ...` ->
  `%Error-BADVLTPRAGMA`); dong nay cung se lam hong buoc lint dau tien cua OpenLane.
- `tb_directed_isa` them tham so `TB_LINE_COUNT` (mac dinh 64, giu nguyen regression) va
  nhanh `ifdef ASIC_VIEW_SIM` doc word 1027 tu macro. Chay o view ASIC @256: **6/6 PASS**
  (217 lenh retire, Zmmul, thu tu/noi dung retire, chan nhanh sai, bat bien bo dem,
  assertion AXI 1329 chu ky).
- `scripts/rtl_manifest.py` mo rong: truoc chi bam `hdl/` + `tb/` (68 file), **bo sot**
  UVM (`verification/`), anh firmware (`fw/`) va file Verilog cua thiet ke ASIC. File cau
  hinh PD (`config.json`, `soc.sdc`, `*.cfg`, `*.eqy`) co y **khong** nam trong dong bang RTL.
- Cac probe chan doan chuyen vao `tb/diag/` (co README); monitor cu da bi thay the.

**RTL DONG BANG: 170 file, aggregate `aa8e32f9d9e0afe996c54de65f57e73a`.**

Chuoi day du: `scripts/run_fullchain_rtlfix.sh` (log `results/fullchain_rtlfix.log`):
static (latch, lint FPGA, lint ASIC) -> regression x2 -> UVM 5 test x 64/256 x2 -> UVM AXI
line 8/32/64 B x2 -> Embench 1 KiB/4 KiB x2 so voi tham chieu truoc sua -> CoreMark x2 so
tham chieu -> random diff 50 seed x2 so tham chieu -> view ASIC x2 + so voi view FPGA +
directed ISA view ASIC. Moi thu duoc ky vong **trung tung byte** voi tham chieu vi moi ban
sua deu trung tinh ve chu ky voi benchmark.

Song song: Quartus `scripts/run_le_rtlfix.sh 1` (9 diem x 4 seed, ~10 phut/fit, roi cong
suat), sau do luot 2 de thuc thi kep.

| Moc | Ket qua |
|---|---|
| Dong bang | IDENTICAL, 170 file |
| latch_sweep | 0 latch, 8 to hop |
| lint_rtl | 0 nghiem trong, 8 to hop |
| lint_asic | 0 nghiem trong, 0 loi elaborate |
| Regression luot 1 | **128 PASS**, 0 FAIL (truoc 126; +tb_uart_apb, +sysmon ABI v2) |

### 13:15 — Chuan bi PD (khong dong vao RTL): EQY so dung netlist cua chinh run

Doc `openlane-local/openlane/steps/yosys.py` (dong 309-311): khi dat `EQY_SCRIPT`, OpenLane
**chep nguyen van** file, khong co co che chen netlist cua run hien tai. Vi vay script tuy
bien buoc phai ghi cung duong dan, va no tro vao `runs/ch4kb/294-.../soc_asic_top.nl.v` —
netlist cua run cu. Sua o tang cong cu PD:
- `yosys.py`: thay `@NETLIST@` bang netlist cua run (`state_in[NETLIST]`) va `@PDK_FORMAL@`
  bang model PDK formal cua chinh buoc do. Backup `backups/yosys.py.20260924T165607Z`.
- `eqy_soc_asic_top.eqy` [gate]: `read_verilog -formal -sv @PDK_FORMAL@ @NETLIST@`.
  [gold] da doi sang `hdl/soc_top.v` o R16.
Van de EQY chet im lang sau `combine` (7/7 lan o `ch4kb_full`) se dieu tra khi PD moi
toi buoc do, tren netlist moi.

| Moc chuoi day du | Ket qua |
|---|---|
| Regression luot 2 | **128 PASS**, 0 FAIL; hai luot khop 128 = 128 |
| UVM 64 line luot 1 | 5/5 PASS |
| Quartus luot 1 | dang chay (dm seed 2) |

### 2026-09-25 00:10 — Pham vi thu hep: CHI 4 KiB

Ong yeu cau khong lam cache 1 KiB nua. Chuoi dang chay co cac buoc 1 KiB (Embench 1 KiB x2,
CoreMark 1 KiB) va Quartus bat dau bang 5 diem 1 KiB (dm, sa2, dm_vc4, dm_dse, dm_nopc) — loi
cua toi, dua vao ca hai chi vi tham chieu cu co san ca hai. Da dung het (ke ca cac vong `bash`
cha va tien trinh python/vsim/quartus mo coi con sinh tien trinh moi), xoa ket qua Quartus
1 KiB dang do.

Giu lai nhung gi da xong va hop le: dong bang, kiem tra tinh, regression x2 (128/128), UVM
x2, UVM AXI x2, va `rtlfix_1kb_p1.csv` (48/48 trung tham chieu) nhu bang chung da co —
khong lam them gi o 1 KiB.

Tiep tuc:
- `scripts/run_fullchain_rtlfix_4kb.sh`: Embench 4 KiB x2 (so tham chieu), CoreMark 4 KiB x2,
  random diff x2 (chi loi, khong co cache), view ASIC x2 + so view FPGA + directed ISA.
- `scripts/run_le_rtlfix.sh`: chi `dm_4kb sa2_4kb vc4_4kb dse_4kb` x 4 seed, x2 luot, cong suat.

### 2026-09-25 00:15 — BANG KE HOACH: moi thu se chay (chi 4 KiB)

Trang thai: XONG / DANG CHAY / CHO. Moi phep do chay 2 lan va phai khop nhau.

**A. Kiem chung RTL da dong bang (170 file, `aa8e32f9...`)**

| # | Viec | Tieu chi dat | Trang thai |
|---|---|---|---|
| A1 | Kiem dong bang manifest | IDENTICAL | XONG |
| A2 | Quet latch bang Yosys, 8 to hop | 0 latch | XONG — 0 |
| A3 | Lint FPGA (Verilator), 8 to hop | 0 canh bao nghiem trong | XONG — 0 |
| A4 | Lint ASIC `soc_dm_4kb` | 0 nghiem trong, 0 loi elaborate | XONG — 0 |
| A5 | Directed regression x2 | 0 FAIL, hai luot khop | XONG — 128/128 x2 |
| A6 | UVM 5 test @256 line x2 | 5/5 | XONG — 5/5 x2 |
| A7 | UVM AXI @ line 8/32/64 B x2 | PASS | XONG |
| A8 | Embench view FPGA 4 KiB, 12 kernel x 4 cau hinh = 48 run, x2 | trung tung byte voi tham chieu truoc sua | DANG CHAY |
| A9 | CoreMark 4 KiB x 4 cau hinh, x2 | trung tham chieu | CHO |
| A10 | Random differential 50 seed, x2 (chi loi) | 50/50 MATCH, trung tham chieu | CHO |
| A11 | View ASIC (macro SRAM that) Embench 12 kernel x2 | 12/12 PASS, trung view FPGA moi truong kien truc | CHO |
| A12 | View ASIC directed ISA | 6/6 PASS | CHO |

**B. FPGA (Quartus), 4 diem 4 KiB: `dm_4kb`, `sa2_4kb`, `vc4_4kb`, `dse_4kb`**

| # | Viec | Tieu chi | Trang thai |
|---|---|---|---|
| B1 | 4 diem x 4 seed = 16 fit, luot 1 (~10 phut/fit, ~2.7 gio) | LE, reg, slack, Fmax | DANG CHAY (dm_4kb seed 2) |
| B2 | Cong suat 4 diem (Power Analyzer, fit seed 2) | mW do that | CHO |
| B3 | Luot 2: lai 16 fit + cong suat | trung luot 1 tung so | CHO |

**C. PD (OpenLane 2, Sky130) — chi bat dau khi A xong; tu day RTL khong doi**

| # | Viec | Tieu chi | Van de da biet can xu ly |
|---|---|---|---|
| C1 | Full flow tu buoc 1, tag moi, netlist tu RTL da dong bang | chay het 78 buoc | — |
| C2 | Lint + tong hop + cac checker tong hop | 0 loi, 0 latch trong netlist | kiem lai `dlxtn` = 0 |
| C3 | Floorplan, PDN, dat macro (luoi 4x3), placement, CTS | 0 vi pham power grid | — |
| C4 | Global route + RepairAntennas + detailed route | `Checker.TrDRC` = 0 | antenna con 532 net o run cu |
| C5 | STA hau dinh tuyen, RCX, IR drop | setup/hold o tt | run cu: setup tt -0.30 ns; slew/cap/fanout |
| C6 | Magic DRC, KLayout DRC, XOR | 0 | run cu: Magic 4,187 (mot luat `nwell.4`, 0% trong macro) |
| C7 | LVS (Netgen) | khop | — |
| C8 | Yosys.EQY (script da sua de so dung netlist cua run) | tuong duong | run cu: chet im lang sau `combine` 7/7 lan |
| C9 | Trich PPA hau dinh tuyen, so voi run truoc | bang PPA | chi phi 264 FF cua ban sua SRAM wrapper |

**D. Ho so**
- Nhat ky nay (`NHAT_KY_RTL.md`) cap nhat sau moi moc; `asic/FLOW_JOURNAL.md` cho PD.
- Ban giao cuoi: moi thay doi, moi so do, moi loi va cach sua.

**Can ong quyet (chua lam):** R6/R7 (doi pipeline -> doi toan bo CPI);
`ERROR_ON_LINTER_WARNINGS` (dang False).

### 2026-09-25 00:40 — Quyet dinh cua ong va phan loai lint

**Quyet dinh:** R6 bo. R7 theo thu tu: (a) sua o PD, (b) neu tt van truot thi noi clock;
chua dong RTL. Lint: bat `ERROR_ON_LINTER_WARNINGS=True` truoc de xem loi that, sua cai sua
duoc, ghi lai cai bat kha khang, roi moi chuyen `False`.

**Chay lint dung cua OpenLane voi True** (tag nhap `lintcheck`, buoc 1-4):
`[E] 112 Lint warnings found` -> flow dung o buoc 4; loi lint = 0.

**Phan loai tung canh bao** (kiem code va kiem testbench co doc qua tham chieu phan cap
hay khong, khong doan):

| Nhom | So | Ket luan |
|---|---:|---|
| Day debug/retire trace `soc_top.v` (mcause_dbg, retire_*, bo dem cache/AXI...) | 63 | co y — TB/UVM/Embench doc |
| Bit khong dung theo thiet ke: bit dia chi khong giai ma (PADDR, addr), offset trong line (refill addr), nua thap phep nhan (MULHU/MULHSU), bit index BHT, 16 bit cao dia chi write buffer, part-select `count_max`, bit cao `exclusive_cycle_sum` cua checker mo phong | 22 | co y |
| `branch_mispredict_e`, `branch_recovery_pc` (datapath) | 2 | alias cua `mispredict_e`/`recovery_target_e`; `tb/branch_predictor_tb.sv` doc -> day quan sat, **khong phai loi nhanh** |
| Cong ra de ho co chu dich (7 o soc_top), cong macro khong dung (dout0/dout1), chan nguon macro vccd1/vssd1 (PDN noi, LVS da khop), tham so giu cung giao dien (DEPTH_WORDS, MEMFILE, LINE_COUNT), tin hieu giao thuc AXI ma wrapper ASIC khong kiem (arsize, arburst, awlen, awsize, awburst, wlast — master chi phat dung mot kieu burst) | 21 | co y |
| `bht_index_f`, `bht_state_f`, `snapshot_sequence` — cong debug khong ai doc | 3 | de ho cong chi doi sang PINCONNECTEMPTY, khong giam duoc |
| **`rd_addr_q` trong `axi_ram_32_asic_macro.v`** — thanh ghi chi duoc ghi, khong bao gio doc | 1 | **logic chet — SUA** |
| **`pstrb` trong `uart_apb.v`** — bo qua hoan toan byte strobe | 1 | **LOI THAT — SUA**: vi pham APB4; mot lenh ghi byte vao `CFG` se de ca 3 byte con lai |

Firmware hien tai ghi UART bang lenh word nen loi `pstrb` chua anh huong so do nao; nhung
day la loi giao thuc that. Ca hai ban sua deu la thay doi RTL -> dung chuoi dang chay,
sua, dong bang lai, chay lai chuoi day du.

### 2026-09-25 00:55 — Sua 2 muc lint, dong bang lai, chay lai tu dau

**`uart_apb.v` — ton trong `pstrb` (APB4):** TXDATA, CTRL va W1C cua STATUS nam o byte 0 nen
chi tac dong khi `pstrb[0]`; CFG cap nhat tung byte. Bang chung A/B voi test moi trong
`tb_uart_apb` (ghi byte 1 cua CFG; 16 lan ghi TXDATA khong strobe byte 0):
```
RTL cu : [FAIL] byte-1 write to CFG gave 0xffffffff, expected 0x0000ffc3
         [FAIL] unstrobed TXDATA writes push nothing (FIFO bi day)
         [FAIL] RXDATA ... 0xee, expected 0xa0   (7 loi)
RTL moi: [PASS] UART byte strobes, status FIFO bits, TX FIFO full, loopback frames, RX order
```
Firmware ghi UART bang lenh word (`pstrb=1111`) nen khong doi hanh vi hien tai.

**`axi_ram_32_asic_macro.v` — bo thanh ghi chet `rd_addr_q`** (chi ghi, khong bao gio doc).

**Lint OpenLane voi True sau sua: 111** (112 - `rd_addr_q` - `pstrb` + `s_axi_araddr` bits:
truoc day `rd_addr_q` chot ca 32 bit nen che cac bit cao; thuc te chi `[12:2]` co nghia voi
RAM 8 KiB — cung loai co y nhu `wr_sel_addr`). **Ca 111 deu co ly do thiet ke.**
Theo quyet dinh cua ong: `ERROR_ON_LINTER_WARNINGS` ve `False`, va thay bang cong chat hon:
- `asic/soc_dm_4kb/lint_baseline.tsv`: 111 canh bao da phan loai (file, lop, tin hieu).
- `scripts/lint_baseline_check.py <verilator-lint.log>`: fail neu co **bat ky** canh bao moi.
  Chay tren log vua roi: `111 accepted, 111 found, 0 new`.

**Kiem tra tinh tren RTL moi:** latch 0; lint_rtl 0 nghiem trong; lint_asic 0 nghiem trong.

**RTL DONG BANG LAI: 170 file, aggregate `b82c2717dc826ed7f147582eb8f11150`.**
Chuoi day du (chi 4 KiB) va Quartus chay lai tu dau vi `hdl/uart_apb.v` doi.

### 2026-09-25 00:35 — Yeu cau moi: Embench, Quartus, PD phai do DU thong so, moi cau hinh

Ong yeu cau: "chay bao nhieu cau hinh cung phai do het khong chua mot cai gi". Kiem tra lai
cac script do va tim thay 5 lo hong:

| # | Cho | Lo hong | Sua |
|---|---|---|---|
| M1 | `run_fpga_points.py` | chi lay 6 so: LE, comb, regs, mem bits, setup slack va Fmax **chi o corner Slow 85C** | lay toan bo: tai nguyen chi tiet (LE theo loai, LUT 4/3/2, LAB, M9K, mult 9-bit, pin, global clock, interconnect, fan-out), map LE; setup/hold/recovery/removal/MPW slack + TNS o **ca 3 corner** (Slow 85C, Slow 0C, Fast 0C); Fmax 2 corner cham; multicorner; so duong unconstrained; power day du (tong/dong/tinh/IO, theo loai khoi, theo mien clock, dong nguon VCCINT/VCCIO/VCCA/VCCD, theo module: core, icache, dcache, AXI, sysmon, UART...) — **116 cot**. Truong nao khong doc duoc -> fit do tinh la FAIL, khong de o trong |
| M2 | `run_le_rtlfix.sh` | power chay **mot lan sau vong seed** -> do tren fit seed 4 (seed chay cuoi), trong khi chu thich noi seed 2. Ca 3 seed con lai khong co power | power (quartus_asm + quartus_pow) chay **ngay sau moi fit**, moi point x seed co power rieng |
| M3 | `run_fpga_points.py` | report moi seed ghi de vao cung `results/fpga_points/<point>/` -> chi con report cua seed chay cuoi | luu rieng `results/fpga_points/<tag>/<point>/s<seed>/` (ca .qsf da dung); xoa report cu truoc map de khong bao gio doc nham report cua fit truoc |
| M4 | `run_ablation.py`, `run_coremark.py` | CSV bo `axi_write` (co trong dong snapshot) | module chung `scripts/snapshot_fields.py`: doc **moi** cap key=value, thieu truong nao la FAIL |
| M5 | `tb/benchmark_snapshot_tb.sv` | sysmon co 37 thanh ghi snapshot, harness chi in 28. Thieu: icache_hit, icache_miss, dcache_read_hit/miss, dcache_write_hit/miss, control_redirect_event, trap_event, last_mcause (+ snapshot_sequence) | in du; them kiem tra bat bien moi (i_access = hit+miss, d_read = hit+miss, d_write = hit+miss, branches = taken+not_taken, predictions = correct+mispredict) trong Python |

**Kiem tra parser M1 tren report that** (fit dm_4kb seed 2 luc 00:35): doc du 116 cot; gia tri
multicorner khop min cua 3 corner (setup 0.426 = Slow 85C; hold 0.125, removal 1.337, MPW 9.198 =
Fast 0C) — dung nhu dinh nghia. Loi gap khi viet: report Quartus dung CRLF nen regex bang
khong khop (tat ca cot timing = None) -> them buoc chuan hoa xuong dong; gate "truong nao thieu la
FAIL" da bat duoc loi nay truoc khi chay that.

**Dung Quartus pass 1 cu de chay lai voi M1-M3.** `TaskStop` chi giet shell cha; vong lap bash va
python con song, va lenh kill truc tiep bi he thong tu choi. Them co huy hop tac
`results/.abort_fpga_sweep` (moi lan goi fit/power kiem tra truoc khi chay) -> vong lap tu thoat
ma khong fit nao bi giet giua chung.
**Su co phu:** fit dm_4kb seed 2 cua vong cu xong (00:35:28) nhung `quartus_sta` fail 3 lan lien,
log rong, ngay sau TaskStop. Bang chung: chay lai `quartus_sta` tren cung database -> rc=0 sau 4 s.
Ket luan: loi moi truong do giet shell cha, khong phai loi design. Ghi vao dau
`run_le_rtlfix.sh`: muon dung sweep thi dung co huy, khong giet shell.

**Quartus pass 1 chay lai 00:39** voi M1-M3 (4 point 4 KiB x 4 seed, moi fit kem power).

**M4/M5 chua ap:** chuoi xac minh (b82c2717) dang o stage 5 va stage 8 se compile lai testbench;
sua testbench giua chung se tron du lieu hai phien ban. Doi chuoi xong -> ap M4/M5 -> dong
bang lai (chi `tb/` doi, RTL khong doi — se chung minh bang diff manifest) -> chay lai TOAN BO
chuoi voi du 38 truong. Ket qua Quartus van hop le vi Quartus khong doc `tb/` (se chung minh
bang diff manifest chi gom file `tb/`).

### 2026-09-25 00:50 — Yeu cau: do du thong so cho CA 4 SEED

Sau M1-M3, moi fit (moi point x moi seed) da co du 116 cot, ke ca power rieng. Them:
- `scripts/fpga_seed_summary.py <csv>`: bang day du **seed 1/2/3/4** cho tung truong cua tung
  point, kem min / max / mean / spread (max - min), va mot bang so sanh giua cac cau hinh
  (trung binh 4 seed [min, max]) de moi khac biet giua cau hinh duoc dat canh nhieu seed cua
  chinh truong do.
- Cong kiem tra (exit 1): moi point phai co dung 4 seed 1-4, va moi seed phai du ca 116 truong.
  Thieu seed hay thieu mot truong la FAIL.
- Chay cho pass 1 va pass 2. Voi pass 2 se goi ngay trong `run_le_rtlfix.sh` (chinh file do
  sau khi pass 1 xong; khong sua script bash dang chay vi bash doc script tung doan).

### 2026-09-25 00:46 — Quartus pass 1: crash router lan thu 1 cua dm_4kb seed 2 (tu thu lai)

`quartus_fit` chet voi `*** Fatal Error: Access Violation at 0X00007FFCBF242B77`, stack
`l_run_heap_expansion_algorithm <- l_route_to_target <- l_route_net <- aa_route_alg_route_all_nets`
(router song song cua fitter). Day la loi ngau nhien da do truoc day (~8 % so lan fit, ca
`quartus_fit` va `quartus_map`, nguyen nhan: RAM may loi — xem memory "machine-memory-fault").
`run()` trong `run_fpga_points.py` tu thu lai toi da 3 lan; lan 2 dang chay. Log lan 1 luu tai
`asic/evidence/quartus_crash_20260925/dm_4kb_s2_attempt1_fit.log`. Chi chap nhan fit khi pass 2
tai lap dung tung truong (Double-Execution).

### 2026-09-25 01:01 — Chuoi tren b82c2717: 0 loi. Ap M4/M5, dong bang lai c235dfb7, chay lai

**Ket qua chuoi tren b82c2717 (01:00:52, 0 failure):** latch 0; lint_rtl 0; lint_asic 0;
regression 128 PASS x2; UVM @256 5/5 x2; UVM AXI 6/6; Embench 4 KiB 48 lan x2 va trung khop
tham chieu truoc sua; CoreMark 4 lan x2 va trung khop tham chieu; random diff 50/50 MATCH x2 va
trung khop tham chieu ke ca hash; ASIC view 12/12 x2 = FPGA view tren 18 truong; directed ISA
tren ASIC view 6/6.

**Ap M4/M5:**
- `tb/benchmark_snapshot_tb.sv`: dong BENCHMARK_SNAPSHOT them 10 truong (i_hit_ev, i_miss_ev,
  d_rd_hit, d_rd_miss, d_wr_hit, d_wr_miss, control_ev, trap_ev, mcause, snap_seq). Chi them
  doi so cho `$display`, khong doi hanh vi.
- `run_ablation.py`, `run_coremark.py`: dung `snapshot_fields.py` (38 truong + 8 bat bien);
  log rieng moi file output (`results/ablation_logs/<ten csv>/`) de pass 2 khong ghi de log pass 1.
- `run_fullchain_rtlfix.sh` stage 8: so ASIC view voi FPGA view tren **moi** truong tru cac
  lop chu ky phu thuoc do tre bo nho (truoc: 18 truong, nay: 31 truong); giu load_use,
  control, trap nhu truoc de khong lam yeu phep so.

**Chay thu (wikisort, DM va DM_VC4):** du 38 truong; bat bien moi dung
(i_hit_ev + i_miss_ev = 122,051 + 55 = 122,106 = i_access; d_rd 18,592 + 17 = 18,609;
d_wr 13,379 + 66 = 13,445); mcycle 160,935 khong doi so voi truoc sua.

**Dong bang lai:** 170 file, aggregate `c235dfb70c4429412b5aaf18672f93f2`. Diff manifest voi
b82c2717: **chi** `tb/benchmark_snapshot_tb.sv`. Quartus khong doc `tb/` (0 lan xuat hien trong
hai file .qsf) -> Quartus pass 1 dang chay van hop le cho c235dfb7. Ban manifest cu luu tai
`results/rtl_manifest_b82c2717.json`.

**Chuoi day du chay lai 01:05 tren c235dfb7.**

### 2026-09-25 01:36 — CHUOI RTL XANH tren c235dfb7. Bat dau PD full flow.

**Chuoi day du tren c235dfb7 (01:03 -> 01:35:57), 0 failure:** latch 0; lint_rtl 0; lint_asic 0;
regression 128 PASS x2 va hai lan khop; UVM @256 5/5 x2; UVM AXI 6/6; Embench 4 KiB 48 lan x2,
du 38 truong, 8 bat bien dung tren ca 4 cau hinh, trung khop tham chieu truoc sua; CoreMark 4 lan
x2, trung khop tham chieu; random diff 50/50 x2, trung khop tham chieu ke ca hash; ASIC view 12/12
x2 = FPGA view tren **33 truong** (truoc la 18); directed ISA tren ASIC view 6/6. Manifest van
IDENTICAL o cuoi chuoi.

**=> RTL SACH. Tu day PD khong duoc dong vao RTL** (theo yeu cau cua ong).

**PD full flow tu buoc 1**, tag moi `rtlfix_c235`, RTL dong bang c235dfb7:
`TAG=rtlfix_c235 TO=Misc.ReportManufacturability MAX=200 bash ch4kb_run.sh` (WSL),
log driver `asic/pd_rtlfix_c235.log`. Chay song song voi Quartus pass 1 (may 32 nhan, WSL 23 GB;
Quartus o phia Windows). Cau hinh PD giu nguyen trang thai cuoi trong FLOW_JOURNAL (Incident
52-56). Day la lan chay baseline tren RTL cuoi; cac muc PD con no (antenna, EQY, setup ss,
slew/cap/fanout, 2,648 net unannotated, Magic nwell.4) se xu ly bang thay doi PD, co bang chung,
tren du lieu cua lan chay nay. Sau buoc 1 se chay `lint_baseline_check.py` tren log Verilator.
So lieu PD se lay bang `scripts/pd_metrics.py` (292 metric + 9 corner x truoc/sau PnR).

**Quartus sa2_4kb:** seed 2 setup slack Slow 85C = **-0.034 ns** (Fmax 49.92 MHz < 50 MHz,
truot timing o corner cham nhat); seed 1 = +0.358 ns (Fmax 50.91). Phu thuoc seed; se bao cao
ca 4 seed.

**PD rtlfix_c235, buoc 1-11 (01:37-01:5x):**
- Lint (buoc 01): `lint_baseline_check.py` -> `111 accepted, 111 found, 0 new, 0 no longer present`;
  lint error 0, timing construct 0.
- Synthesis (buoc 06): **0 cell latch** trong netlist gate (`grep sky130_fd_sc_hd__dl(x|r)` = 0).
  Run truoc co 2 cell `dlxtn_1` (Incident 54) -> ban sua R5 `rx_block.sv` da co hieu luc tren
  netlist ASIC. Post-synthesis: 78,007 cell, dien tich 1,051,728.69 um^2, 0 cell chua map,
  0 loi synth check.

### 2026-09-25 02:55 — Quartus pass 1 XONG: 16/16 fit, 0 loi, du 4 seed x 115 truong

Bang day du: `results/fpga_seed_summary_rtlfix_p1.md` (moi truong x seed 1-4, min/max/mean/spread).
Cong day du: PASS (4 point x 4 seed, 115 truong moi fit, khong o trong). Tom tat (trung binh 4 seed
[min, max]):

| Truong | dm_4kb | dse_4kb | sa2_4kb | vc4_4kb |
|---|---:|---:|---:|---:|
| LE | 15,406 [15,371; 15,446] | 16,894 [16,853; 16,935] | 19,369 [19,329; 19,394] | 19,830 [19,811; 19,859] |
| Registers | 8,420 | 8,710 | 9,107 | 10,495 |
| M9K | 18 | 18 | **28** | 18 |
| Setup slack Slow 85C (ns) | 0.659 [0.241; 1.053] | 0.643 [0.496; 0.721] | **0.043 [-0.398; 0.358]** | **0.326 [-0.003; 0.592]** |
| Fmax Slow 85C (MHz) | 51.72 [50.61; 52.78] | 51.66 [51.27; 51.87] | 50.12 [49.02; 50.91] | 50.84 [49.99; 51.53] |
| Power tong (mW) | 275.5 [272.9; 278.3] | 293.9 [289.0; 298.9] | 302.5 [299.1; 305.3] | 305.1 [300.4; 310.9] |
| Power dong loi (mW) | 108.3 | 126.4 | 134.8 | 137.4 |

**That bai phai noi ro:** o 50 MHz, corner Slow 85C, **SA2 4 KiB truot timing 2/4 seed** (seed 2
-0.034 ns, seed 4 -0.398 ns) va **DM+VC4 4 KiB truot 1/4 seed** (seed 4 -0.003 ns). DM va DM-DSE
dat ca 4 seed. VC4 chi con du 141-189 LE so voi ngan sach 20,000. Nhieu do seed: LE ~60-80,
Fmax ~0.6-2.2 MHz, power ~5-10 mW — khac biet giua cau hinh phai lon hon muc nay moi tinh.
Power la uoc luong vectorless cua Quartus ("Low confidence"), khong phai do bang mo phong.

**Quartus pass 2 bat dau 02:56** (cung 16 fit, so sanh tung truong voi pass 1).

### 2026-09-25 04:40 — PHAT HIEN RTL MOI (R8): dau vao bat dong bo khong duoc dong bo hoa

**Tu dau ra:** STA ky ten cua PD (rtlfix_c235 buoc 58) bao hold vi pham o goc ss/min_ss/max_ss
(13-20 endpoint, **0 reg-to-reg**). Truy tung duong trong `max_ss_100C_1v60/min.rpt`: moi duong deu
bat dau tu **cong vao `uart_rx`** (6 duong dau, -1.17 ns) va **`key1_n`** (-1.04 ns). SDC dang coi hai
chan nay la dong bo voi `clk` (`set_input_delay`), nhung chung la tin hieu ngoai bat dong bo.

**Kiem tra RTL (bang chung, khong doan):**
- `hdl/rx_block.sv`: `rx` dung THANG trong logic trang thai ke (dong 73 `if(~rx && count_tick == 15 ...)
  next_state = RECEIVE`), lay mau du lieu (130), parity (150) va to hop `baud_rx_en` (190). Khong co
  flop dong bo nao. Mot tin hieu bat dong bo vao logic next-state co the lam cac bit trang thai thay
  hai gia tri khac nhau -> nguy co metastability va chuyen trang thai sai.
- `hdl/board/de2_115_top.v` (FPGA): co dong bo reset (bat bat dong bo, nha dong bo, 2 flop) va `key1_n`
  (2 flop), **nhung khong dong bo `uart_rx`**.
- `asic/soc_dm_4kb/soc_asic_top.v` (ASIC): **khong dong bo gi ca** — `reset_n`, `key1_n`, `uart_rx` noi
  thang vao `soc_top`. Reset nha bat dong bo, va `soc.sdc` lai `set_false_path -from reset_n` nen kiem
  tra recovery/removal cua reset chua bao gio duoc thuc hien. `key1_n` vao thang mux `PRDATA`
  (`apb_display_regs.v:58`).

**Sua (R8), theo dung khuon da co trong wrapper FPGA:**
- `de2_115_top.v`: them dong bo 2 flop cho `uart_rx` (reset ve 1 = UART ranh).
- `soc_asic_top.v`: them dong bo reset (giong FPGA), `key1_n` va `uart_rx` (2 flop moi cai).
- `soc.sdc`: `set_false_path -from` `key1_n`, `uart_rx` — chi dung SAU khi da co dong bo (duong do vao
  flop dau cua bo dong bo, la CDC chu khong phai duong duoc dinh thoi). Voi reset: false path tu chan
  `reset_n` nay chi con toi 2 flop dong bo; moi flop khac nhan reset tu flop dong bo nen recovery/
  removal duoc dinh thoi that.
- `soc_top` va moi TB dung `soc_top` truc tiep KHONG doi -> regression/UVM/Embench phai giu nguyen.
- Test moi cho logic moi: TB rieng kiem tra do tre 2 chu ky cua dong bo `uart_rx`/`key1_n`, gia tri
  reset, va reset nha dong bo cho ca hai wrapper.

**Thu tu (khong tron du lieu):** chua ap ngay vi (1) Quartus pass 2 dang map `de2_115_top.v`, va
(2) buoc EQY (73) cua run PD hien tai doc `soc_asic_top.v` tu dia lam "gold" — doi file bay gio se
so RTL moi voi netlist cu. Ap khi ca hai xong, roi dong bang lai va chay lai TOAN BO chuoi
(regression, UVM, Embench, CoreMark, random diff, ASIC view, Quartus x2, PD full flow).

**R8 — test moi va thi nghiem A (tren RTL CU, 04:50):** `tb/top_wrapper_sync_tb.sv` (2 top:
`tb_de2_115_top_sync` trong `work`, `tb_soc_asic_top_sync` trong `work_asic`). Hai wrapper chua tung
duoc mo phong truoc day (khong script compile nao co `de2_115_top.v` hay `soc_asic_top.v`). Test kiem
tra tren tin hieu ma `soc_top` nhan: reset thap khi reset_n thap; nha reset dung o canh len thu hai
(khong truoc); `uart_rx`/`key1_n` toi `soc_top` dung sau 2 canh, bang 1 khi vua ra reset; reset bat
khong can canh clock. Ket qua tren RTL cu (thu vien rieng `work_sync`, khong dung vao `work`):
```
de2_115_top : 4 FAIL  — uart_rx di thang (0 do tre) ; reset va key1_n PASS (da co dong bo)
soc_asic_top: 10 FAIL — reset nha ngay khong can canh ; uart_rx va key1_n di thang
```
=> Test bat dung loi R8 o ca hai wrapper. Da them vao `compile_active_design.do`,
`compile_asic_view.do`, `run_full_regression.do` (tb_de2_115_top_sync) va stage 8 cua
`run_fullchain_rtlfix.sh` (tb_soc_asic_top_sync x2). Regression se tang 128 -> 129 PASS sau khi ap R8.
Cho Quartus pass 2 va buoc EQY cua PD xong moi ap RTL.

### 2026-09-25 04:56 — Quartus pass 2 VERIFIED (freeze c235dfb7)

`verify_double.py fpga_points_rtlfix_p1.csv fpga_points_rtlfix_p2.csv`: **16 dong, 16 giong het,
0 lech** tren ca 115 truong (tai nguyen, timing 3 corner, power). Bang 4 seed pass 2:
`results/fpga_seed_summary_rtlfix_p2.md`, cong day du PASS. Ket qua Quartus tren c235dfb7 da duoc
xac nhan bang hai lan chay doc lap. (Se phai chay lai sau R8 vi `de2_115_top.v` doi.)

### 2026-09-25 05:40 — AP R8, thi nghiem B, dong bang lai

- `hdl/board/de2_115_top.v`: them `uart_rx_sync_q` (2 flop, reset 2'b11), `soc_top.uart_rx <= soc_uart_rx`.
- `asic/soc_dm_4kb/soc_asic_top.v`: them dong bo reset (`reset_sync_q`, bat bat dong bo / nha o canh
  thu hai), `key1_sync_q`, `uart_rx_sync_q` — giong het wrapper FPGA; `soc_top` nhan ban da dong bo.
- `asic/soc_dm_4kb/soc.sdc` (file PD, ngoai manifest): `set_false_path -from [get_ports {key1_n uart_rx}]`
  kem chu thich: chi hop le vi R8 da co dong bo (test chung minh); chu thich reset_n cap nhat.
**Thi nghiem B (RTL moi):** `tb_de2_115_top_sync` PASS; `tb_soc_asic_top_sync` PASS
(RTL cu: 4 va 10 FAIL). Test phan biet dung ca hai chieu.
**Dong bang moi:** 171 file (them `tb/top_wrapper_sync_tb.sv`), diff so voi c235dfb7 = dung 3 file
tren. Ban cu luu `results/rtl_manifest_c235dfb7.json`.
**Bao cao dung ve may:** WSL van hong bo nho (probe 4/16 hong sau khi khoi dong lai WSL; mot lan
ket qua in ra DUNG nhung phep so sanh da cho ket qua sai -> may tinh toan sai, khong chi mot o nho
hong); Windows 12/12 sach hom nay. Chuoi xac minh chay phia Windows (Questa, Quartus) va moi so do
hai lan; PD (WSL) se duoc doi chieu bang lan chay thu hai.

### 2026-09-25 05:50 — lint_asic bat duoc SYNCASYNCNET trong bo dong bo reset moi; sua cau truc

Chuoi tren ca481b2c: stage 1 `lint_asic` **FAIL** — `%Warning-SYNCASYNCNET: soc_asic_top.v:50:11 Signal
flopped as both synchronous and async: 'soc_asic_top.reset_sync_q'` (lop "correctness"). Nguyen nhan: toi
viet bo dong bo reset bang mot vector 2 bit, bit 0 la du lieu dong bo cua bit 1, bit 1 lai la reset bat
dong bo cho moi flop -> cung mot tin hieu dung ca hai cach. **Khong tat canh bao.** Sua cau truc: tach
thanh hai thanh ghi rieng `reset_meta_q` (chi la du lieu) va `reset_sync_q` (chi dung lam reset) — cung
hai flop, cung hanh vi. `lint_asic` chay lai: **0 correctness, PASS**. Chi sua wrapper ASIC; wrapper
FPGA (khong qua Verilator lint, da chay tren board) giu nguyen -> Quartus pass 1 dang chay van hop le.
**Dong bang moi** (khac ca481b2c dung `soc_asic_top.v`). Chuoi dang chay se bao manifest CHANGED o cuoi
nen khong tinh; se chay lai TOAN BO chuoi tren dong bang moi ngay khi no xong.

### 2026-09-25 06:10 — Chuoi trung gian (bat dau tren ca481b2c) — KHONG TINH; chay lai tren a0c425f8

Ket qua (log luu `results/fullchain_ca481b2c_partial.log`): stage 1 lint_asic FAIL (SYNCASYNCNET, da sua
thanh a0c425f8); regression **129** PASS x2; UVM 5/5 x2; UVM AXI 6/6; Embench 48 x2 = tham chieu;
CoreMark x2 = tham chieu; random diff 50/50 x2 = tham chieu; ASIC view = FPGA view 33 truong; directed
ISA 6/6; **tb_soc_asic_top_sync PASS x2** (tren ban tach thanh ghi). Loi thu hai: ASIC view lan 2
`mont64/DM rc=211` — vsim chet im lang ngay sau `run -all` (11 s, khong BENCHMARK_SNAPSHOT, "Errors: 0").
Chay lai dung mo phong do 3 lan: ca 3 rc=0, mcycle=85,071, giong het lan 1 -> **crash khong tat dinh
cua trinh mo phong (phia Windows)**, khong phai loi thiet ke.
Chuoi nay khong tinh vi dong bang doi giua chung. Chay lai TOAN BO tren **a0c425f8**.

**Quartus pass 1 (R8), dm_4kb 4 seed:** setup slack Slow 85C = seed 2 **-0.924**, seed 1 **-0.086**,
seed 3 +0.221, seed 4 +0.717 ns (truoc R8: 0.426/0.241/0.915/1.053). Duong toi han (seed 2, 8 duong xau
nhat) deu trong datapath cua core (`upper_m`/`instr_w`/`valid_w` -> `alu_result_m`), KHONG qua bo dong bo
moi. **Ket luan phai noi thang: timing DM o Slow 85C / 50 MHz khong ben vung** — them 2 flop o cho khong
lien quan da doi placement va lam 2/4 seed truot. Quartus dung `de2_115_top.v` (khong doi tu ca481b2c) nen
ket qua nay hop le cho a0c425f8.

### 2026-09-25 06:30 — CHUOI XANH tren a0c425f8 (R8). RTL SACH. Bat dau PD full flow `r8_a0c4`.

Chuoi day du (05:58 -> 06:29), **0 failure**, manifest IDENTICAL dau-cuoi (log: `results/fullchain_a0c425f8.log`):
latch 0; lint_rtl 0; **lint_asic 0**; regression **129** PASS x2 (them tb_de2_115_top_sync); UVM @256 5/5 x2;
UVM AXI 6/6; Embench 48 x2 = tham chieu truoc sua; CoreMark x2 = tham chieu; random diff 50/50 x2 = tham chieu
(ca hash); ASIC view 12/12 x2 = FPGA view tren 33 truong; directed ISA 6/6; **tb_soc_asic_top_sync PASS x2**.

**PD full flow tu buoc 1**, tag `r8_a0c4`, driver `asic/pd_driver.py` (log `asic/pd_driver_r8_a0c4.log`).
Khac run rtlfix_c235: (1) RTL R8 (wrapper ASIC co dong bo reset/key1_n/uart_rx), (2) `soc.sdc` false path cho
`key1_n`, `uart_rx`, (3) Magic DRC tren GDS that voi macro truu tuong (Incident 61). Khong doi gi khac, de run
nay la baseline sach cho cac thi nghiem antenna / timing sau do.

### 2026-09-25 07:19 — Quartus pass 1 tren R8 (a0c425f8): 16/16 fit, 0 loi, cong day du PASS

Bang day du `results/fpga_seed_summary_rtlfix_p1.md`. Trung binh 4 seed [min, max]:

| Truong | dm_4kb | dse_4kb | sa2_4kb | vc4_4kb |
|---|---:|---:|---:|---:|
| LE | 15,460 [15,418; 15,505] | 16,877 [16,837; 16,915] | 19,344 [19,302; 19,411] | 19,876 [19,861; 19,906] |
| Registers | 8,422 (+2 so voi truoc R8) | 8,712 | 9,109 | 10,497 |
| Setup slack Slow 85C (ns) | -0.018 [**-0.924**; 0.717] | 0.359 [**-0.064**; 0.840] | 0.024 [**-0.480**; 0.422] | -0.110 [**-1.491**; 0.594] |
| Seed truot o Slow 85C | **2/4** | **1/4** | **2/4** | **1/4** |
| Setup slack Slow 0C (ns) | 1.76 [0.811; 2.473] | 2.14 | 1.73 | 1.69 [0.358; 2.368] |
| Fmax Slow 85C (MHz) | 50.00 [47.79; 51.86] | 50.93 | 50.08 | 49.81 [46.53; 51.53] |
| Power tong (mW) | 280.3 | 292.7 | 307.3 | 303.0 |

**That bai phai noi thang:** o 50 MHz, goc Slow 85C, **moi cau hinh deu co it nhat mot seed truot timing**
sau R8 (truoc R8: DM va DSE dat 4/4). R8 chi them 2 flop tren duong UART; duong toi han khong di qua do
(da kiem: datapath core -> alu_result_m). Nghia la margin o Slow 85C chi ~+/-1 ns va thay doi theo bat ky
nhieu nao cua placement — ket qua "dat timing" truoc day cho DM/DSE la may man cua placement, khong ben.
O Slow 0C moi cau hinh dat ca 4 seed (min +0.358 ns). VC4 chi con du 94-139 LE so voi ngan sach 20,000.
Quartus pass 2 chay tiep de xac nhan tung truong.
**Quartus pass 2 (R8), dm_4kb seed 2 (07:30):** lan thu 1 that bai `rc=2` (khong ro cong cu nao — `run()` ghi de
log moi lan thu nen **log cua lan that bai da mat**; lo hong bang chung cua toi). Lan thu 2 cho ket qua giong het
pass 1 (LE 15,505, slack -0.924 ns). Da sua `run_fpga_points.py`: moi lan thu that bai giu log thanh
`<ten>.attemptN.failed.log` (hieu luc tu fit ke tiep, khong doi so do).

### 2026-09-25 09:21 — Quartus pass 2 tren R8 (a0c425f8) VERIFIED

`verify_double.py` pass 1 vs pass 2: **16 dong, 16 giong het, 0 lech** tren ca 115 truong. Bang 4 seed pass 2:
`results/fpga_seed_summary_rtlfix_p2.md` (cong day du PASS). Ket qua Quartus tren R8 (bang o muc 07:19, ke ca cac
seed truot timing o Slow 85C) da duoc xac nhan bang hai lan chay doc lap. Lan thu that bai duy nhat (dm_4kb s2,
pass 2, rc=2) da duoc lan thu 2 thay the bang ket qua giong het pass 1.

### 2026-09-25 10:00 — PD r8_a0c4 (RTL a0c425f8): 71/77 buoc, dung o EQY vi phan cung

So lieu day du: `results/pd/r8_a0c4/` (`summary.md`, `corners.csv`, `metrics_final.csv` 304 key, `metrics_stages.csv`),
ghi ro INCOMPLETE (tu buoc 71-checker-lvs). Tom tat:
- **Dien tich:** die 8.12 mm^2; cell 4.12 mm^2 = cell chuan 1.46 + 12 macro 2.66; utilization 51.7 % (cell chuan 27.5 %);
  195,518 cell chuan (19,067 tuan tu, 33,234 buffer sua timing, 3,249 buffer clock, 6,821 diode). Sau synthesis:
  77,791 cell, 1.047 mm^2.
- **Timing (RCX that, 9 corner):** hold 0 vi pham o CA 9 corner; setup tt **-0.569 ns (3 endpoint)**, max_tt -0.827,
  min_tt -0.412; ss -11.3 .. -13.4 ns; ff +2.9 .. +3.3. Slew/cap vi pham o moi corner (tt: 1,304 / 1,012).
- **Power (vectorless, do tin cay thap):** nom_tt 102.96 mW (internal 84.04, switching 18.63, leakage 0.30).
- **IR drop:** VPWR xau nhat 0.43 mV, VGND 0.39 mV (chua co VSRC_LOC_FILES; power vectorless).
- **Signoff:** Magic DRC **0** (che do GDS, Incident 61), KLayout DRC **0**, XOR 0, LVS **"Circuits match uniquely"**,
  illegal overlap 0, routing DRC 0. **Antenna sau routing: 578 net / 802 pin (chua dat).**
- **EQY: khong hoan thanh** — 3/3 lan chet vi bo nho hong (Incident 64). Khong tat EQY.
- Cac muc con mo: R7 (tt setup) -> thi nghiem E1/E2 dang chay; antenna -> thi nghiem sau; slew/cap.

### 2026-09-25 16:15 — Quyet dinh moi cua ong: THU R7 va R8; khong kha thi thi ve ban chuan a0c425f8

Loi ong: "cu lam thu R7 va R8 nhung neu khong kha thi quay ve phien ban chuan cho toi la duoc. Luc ay chap nhan va
se tien hanh cai thien ben PD". Truoc do (14:30) ong da huy phuong an noi clock: ASIC bat buoc 50 MHz.
**Ghi chu dat ten:** muc "PHAT HIEN RTL MOI (R8)" luc 04:40 (dong bo dau vao bat dong bo) bi toi dat TRUNG ten voi R8
trong bang (noi vccd1/vssd1). Tu day goi muc dong bo la **R17**; **R8** la muc vccd1/vssd1.
**Moc quay ve:** RTL `a0c425f8` (manifest `results/rtl_manifest_a0c425f8.json`), snapshot
`asic/backups/hdl_pre_r7r8_20260925T091632Z.tar.gz`, ket qua chuoi cu `results/archive_a0c425f8/` (41 file).
Nguyen tac tu dat cho R7: **khong doi CPI** (hanh vi tung chu ky giu nguyen) — chuoi co san se bat moi thay doi CPI
(Embench 48 run phai trung tham chieu tung byte). Moi sua doi CPI (pipeline bo nhan, v.v.) KHONG lam.

**R7a — duong fetch ASIC (datapath.v):** duong toi han ASIC (Incident 68): SRAM icache ra du lieu o CANH XUONG ->
`instr` -> `is_jal_f` -> mux imm -> **bo cong 32 bit** `pc_f + imm` -> `pc_next` -> `pc_f`, trong NUA chu ky.
Viet lai cung gia tri: tren cac bit rieng cua imm, moi bit cua b_imm/j_imm la dau `instr[31]` nen phan cao cua
tong chi co the la `pc_hi`, `pc_hi+1`, `pc_hi-1` — tinh tu `pc_f` (co som). Chi phep cong thap cho `instr`: 12 bit
(B), 12 bit + carry-select 8 bit (J). Hai dich tinh song song, `is_jal_f` chon sau cung. Cac phep chon viet dang
AND-OR, khong dung `?:`, vi Yosys `opt_share` (dang bat trong OpenLane) gop cac cell cung loai co chung dau vao
khi chung lai cung mot `$mux` — se dung lai dung cau truc cu.
**Chung minh HINH THUC (khong chi mo phong):** `asic/equiv/r7_target.v` (chep nguyen van doan RTL tu datapath.v) +
`r7_target.ys`: Yosys `miter -equiv` + `sat -verify -prove-asserts`, moi pc_f x moi instr (2^64):
`SAT proof finished - no model found: SUCCESS!` (3,336 bien, 8,889 menh de). Doi chung am (lat 1 bit ket qua J):
`ERROR: Called with -verify and proof did fail!` -> phep chung minh co y nghia.

**R7b — bo nhan (alu.v):** duong toi han FPGA (Quartus, Slow 85C, dm_4kb s2 -0.924 ns) la forwarding
(`upper_m`/`instr_w`/`valid_w`) -> ALU -> `alu_result_m`; ALU co **ba bo nhan 32x32** (ss, uu, su) trong mot chu ky EX.
Pipeline bo nhan = doi CPI -> KHONG lam. Sua khong doi CPI: **mot bo nhan co dau 33x33**, bit thu 33 cua moi toan hang
la bit dau khi lenh coi no co dau, 0 neu khong; tich 66 bit chua dung ket qua 64 bit cua moi bien the; MUL (word
thap) khong phu thuoc dau. Giam 2/3 logic nhan, toan hang forward chi lai mot mang thay vi ba. Tac dung len timing
FPGA: chua biet — se do bang Quartus. Mien 32x32 qua kho cho SAT -> bang chung mo phong: `asic/equiv/tb_alu_equiv.sv`
so `hdl/alu.v` voi `asic/equiv/alu_old.v` (ban cu) tren ca 16 ma alu_ctrl: 40x40 gia tri bien x 16 + ngau nhien:
**20,025,600 phep so, 0 sai khac**. Doi chung am (MULHSU coi b co dau): bat sai ngay (`op=13 a=1 b=ffffffff`).
Loi cua toi luc lam: lan sua dau quen doi cac nhanh `case` sang `product` (vlog bao 3 loi undefined) -> sua ngay.

**R8 — chan nguon macro (2 wrapper ASIC):** `supply1 vccd1; supply0 vssd1;` cuc bo + noi `.vccd1/.vssd1` vao macro,
chi duoi `ifdef USE_POWER_PINS` (synthesis khong dinh nghia -> netlist cong khong doi; PDN/LVS van do OpenLane noi
qua PDN_MACRO_CONNECTIONS). Khong dan cong nguon len qua soc_top vi RTL phia tren dung chung voi FPGA.
A/B Verilator `-DUSE_POWER_PINS`: wrapper cu **6 PINMISSING**, moi **0**; cac lop canh bao khac giu nguyen.
`lint_asic.sh`: PASS, 0 correctness.

**Su co trong luc lam (toi):** toi sua `alu.v` 9 s truoc khi buoc synthesis cua thi nghiem `syn_R7A0` bat dau. Log
synthesis cho thay no doc ban alu.v CU (`process alu.v:33`, `$ternary alu.v:44` = so dong ban cu; ban moi la 38/49),
nen syn_R7A0 = R7a + ALU cu (dung "chi R7a"); se doi chieu them bang so cell. Bai hoc: khong sua `hdl/` khi con flow
co the doc no.
**Dong bang moi `358cb660`** (171 file): khac a0c425f8 dung 4 file `hdl/datapath.v`, `hdl/alu.v`,
`asic/soc_dm_4kb/cache_data_ram_sram4.v`, `asic/soc_dm_4kb/axi_ram_32_asic_macro.v`. Chuoi day du x2 dang chay
(`results/fullchain_358cb660.log`). Tiep theo: Quartus 4 diem x 4 seed x 2 luot; PD full flow tu buoc 1.

**16:40 — R7a do tren PD (thi nghiem `syn_R7A0`, config PD baseline AREA 0, tu buoc 1 toi buoc 35 sau CTS):**
| | a0c425f8 (r8_a0c4) | R7a |
|---|---:|---:|
| setup nom_tt (ns) | -0.788 | **+2.766** |
| arrival duong xau nhat (ns) | 22.909 | 19.412 |
| so tang logic | 42 | 36 |
| dien tich cell chuan (um^2) | 1,242,320 | 1,253,080 (+0.9 %) |
| HPWL global placement | 3.45e9 | 3.46e9 (nhu baseline -> khong nguy co nghen nhu AREA 3) |
| cell sau synthesis | 77,791 | 78,162 (+371: cac bo cong song song) |
Xac nhan syn_R7A0 chi co R7a: so cell +371 (bo 2 bo nhan se giam hang nghin) va so dong trong log synthesis.
Duong xau nhat van bat dau o bank[1] icache (duong nua chu ky), ket thuc o flop khac. **R7a kha thi.**
Chuoi day du tren 358cb660: tang 0-2 OK (0 latch, lint 0, regression 129 = 129). Quartus luot 1 (`TAG=r7r8`,
16 fit) khoi chay 16:41 — script `run_le_rtlfix.sh` nay nhan `TAG` de khong ghi de ket qua a0c425f8.

### 2026-09-25 18:20 — CHUOI XANH tren 358cb660 (R7a + R7b + R8). RTL SACH.

`results/fullchain_358cb660.log`, **0 failure**, manifest IDENTICAL dau-cuoi: latch 0; lint_rtl 0; lint_asic 0; regression
129 = 129 x2; UVM @256 x2; UVM AXI 6/6; **Embench 48 x2 trung tham chieu truoc sua (va trung a0c425f8)**; CoreMark x2
trung tham chieu; **random diff 50/50 MATCH, trung ca hash** (kiem truc tiep MUL/MULH/MULHSU/MULHU ngau nhien so voi mo
hinh tham chieu); ASIC view 12/12 x2 = FPGA view 12 x 33 truong; directed ISA 6/6; tb_soc_asic_top_sync x2.
=> **R7/R8 khong doi CPI; moi so lieu nghien cuu (Embench, CoreMark) giu nguyen gia tri.**
Ket qua a0c425f8 luu o `results/archive_a0c425f8/`; manifest `results/rtl_manifest_358cb660.json`.

**Quartus luot 1 (TAG r7r8) — 2 fit dau, dm_4kb, so voi a0c425f8 cung seed:**
| seed | setup Slow 85C | Fmax Slow 85C | LE | mult 9-bit |
|---|---|---|---|---|
| 2 | -0.924 -> **+1.340** | 47.79 -> **53.59** | 15,505 -> 15,425 | 24 -> 8 |
| 1 | -0.086 -> **+1.275** | 49.79 -> **53.40** | 15,465 -> 15,380 | 24 -> 8 |
Cong suat khoi nhan (seed 2): 6.22 -> 1.53 mW. Hai seed truoc day truot cua DM nay deu dat. 14 fit con lai + luot 2 dang chay.
**PD:** full flow tu buoc 1, tag `r7r8_358c`, config PD baseline (AREA 0, 20 ns, khong doi gi). Driver cho RAM WSL
available >= 8 GB (cac thi nghiem pha 2 tren RTL cu dang chiem 23 GB) roi moi chay; stdout ra file rieng.

### 2026-09-26 00:40 — Goc ss: quyet dinh cua ong — SUA CO TRONG TAM, KHONG DOI CPI

Ong yeu cau "fix not 2 loi chua dat" (goc ss; antenna/slew/cap/EQY). Do day du goc ss (r7r8_358c, max_ss_100C_1v60):
**2,820 endpoint truot** (reg-reg), xuat phat: `d_req_addr` 1,987 (70 %), `instr_w` 628, `if_req_addr` 173,
`result_src_w` 32; ket thuc o gan nhu moi thanh ghi pipeline (src_a_e/src_b_e, immext_e, if_req_addr, CSR, mcycle,
regfile 992 ...). Xau nhat -12.26 ns: `result_src_w` -> mux ghi nguoc (trich load) -> forwarding W->EX -> ALU ->
`d_req_addr` (128 cell, ~32 ns o ss). Ti le tre ss/tt ~1.8x -> moi duong phai <= ~11 ns o tt (hien ~18 ns).
Hoi 1: ong cho phep doi CPI. Toi hoi lai kem so lieu day du (dong ss = thiet ke lai core ~8 tang); **ong chon: sua co
trong tam, KHONG doi CPI** (nhu R7) + PD tot nhat (SS1/SS2), bao trung thuc Fmax dat duoc o ss.

**23:36 — Quartus luot 1 tren 358cb660 dung som (co huy hop tac `results/.abort_fpga_sweep`), sau fit dang chay (dse s1):**
13-14/16 fit xong, deu DAT Slow 85C: dm 4/4 (min +1.246), sa2 4/4 (min +0.747), vc4 4/4 (min +1.132), dse s2 +0.928.
Ly do: RTL chuyen sang R9 (sua trong tam cho goc ss, khong doi CPI); ban cuoi se chay du 16 fit x 2 luot. Cac thi nghiem
PD ss (SS2/SS3) da tro sang ban chup RTL `asic/snapshots/rtl_358cb660/` (42 file, trung hash manifest) de hdl/ duoc sua.

### 2026-09-26 00:10 — R9: sua co trong tam cho goc ss, KHONG doi CPI — dong bang ecf4fc03

Phan tich (do tren r7r8_358c): duong ss xau nhat `result_src_w` -> mux ghi nguoc -> forwarding -> ALU -> d_req_addr;
nhom `instr_w` (628 duong) di qua so sanh rd_w trong hazard unit va giai ma load o W; nhom `d_req_addr` (70 %) gom vong
M->EX (alu_result_m = d_req_addr -> forward_result_m -> ALU) va duong tag dcache -> hit -> stall_pipe -> enable.
**R9 (`scripts/apply_r9.py`):** dua giai ma ra khoi duong toi han len tang truoc, dang ky voi DUNG enable/flush/reset:
- R9a `forward_a_e/forward_b_e` thanh thanh ghi: next = flush_e ? 00 : f(instr_d rs, instr_e rd, reg_wr_e, instr_m rd,
  reg_wr_m) — chung minh quy nap trong dau file script; hazard_unit bo 8 cong forwarding.
- R9b tang W: one-hot kieu load {LHU,LBU,LH,LB}, lan byte, result_src dang ky o M->W.
- R9c tang M: is_upper_m / is_link_m dang ky o E->M.
- controller xuat them `reg_wr_e`, `result_src_m` (von la thanh ghi noi bo); riscv_core noi.
**Checker tuong duong trong datapath.v** (`ifndef __openlane__` + translate_off, mau co san cua du an): tinh lai moi
giai ma cu moi chu ky, `$fatal` khi lech, in `R9_EQUIV ... N cycles checked, 0 mismatches` o `final`. Loi cua toi: ban
dau dung `if(reset_n && ...)` trong khoi dong bo -> lint_asic bao SYNCASYNCNET (reset dung ca dong bo lan bat dong bo)
-> sua thanh khoi reset bat dong bo. Lan dau ap script: hazard_unit.v la CRLF, riscv_core.v lan CRLF/LF -> script
that bai an toan (diem neo khong khop), sua ham edit() thu ca hai kieu xuong dong; chay thu tren ban sao truoc.
**Kiem tra:** latch 0 (8 to hop); lint_rtl 0; lint_asic 0; Questa bien dich/elaborate core 0 loi; regression 129/129
PASS, checker R9 chay trong 13 testbench, 0 lech. Quartus luot 1 cua 358cb660 da dung (co huy) truoc khi sua hdl/;
cac thi nghiem PD dang chay deu da qua synthesis hoac dung ban chup.
**Dong bang `ecf4fc03`** (171 file, khac 358cb660 dung 4 file hdl/controller.v, datapath.v, hazard_unit.v,
riscv_core.v). Chuoi day du x2 (`results/fullchain_ecf4fc03.log`) + PD `r9_ecf4` (config baseline, toi STAPostPNR,
cho RAM) dang chay. Ket qua 358cb660 luu `results/archive_358cb660/`.

**00:50 — Cong lint baseline (lo hong quy trinh cua toi, da bu):** sau R7/R8 toi KHONG chay `lint_baseline_check.py` tren
log Verilator buoc 1 cua r7r8_358c. Chay bu: r8_a0c4 111/111/0 moi; r7r8_358c 3 moi / 6 mat; r9_ecf4 5 moi / 6 mat.
Phan loai tung canh bao moi: `alu.v product` [65:64] = bit mo rong dau cua tich 33x33, moi ket qua lay [63:0];
`b_imm_f`/`j_imm_f` bit cao = ban sao dau, R7a doc thang instr[31]; `load_byte_offset_w`[0] va `result_src_w` sau R9b
chi con checker tuong duong (mo phong, an khoi lint OpenLane boi __openlane__) doc — giu de checker so voi thanh ghi
that. Mat: product_su/uu (R7b), 4 PINMISSING (R8). Baseline cu luu `asic/soc_dm_4kb/lint_baseline_a0c425f8.tsv`; ban moi
co chu thich. r9_ecf4: **110 accepted, 110 found, 0 new, 0 gone**.
**Chuoi ecf4fc03 (den 00:40):** latch 0, lint 0/0, regression 129 x2, UVM 5/5 x2, AXI 6/6, **Embench 48 x2 = tham chieu
truoc sua**, CoreMark x2 = tham chieu; checker R9 trong moi log Embench: tong 367,771,004 chu ky kiem, 0 lech.

### 2026-09-26 00:46 — CHUOI XANH tren ecf4fc03 (R9). RTL SACH, CPI KHONG DOI.

`results/fullchain_ecf4fc03.log`, **0 failure**, manifest IDENTICAL dau-cuoi: latch 0; lint_rtl 0; lint_asic 0; regression
129 = 129 x2; UVM 5/5 x2; AXI 6/6; **Embench 48 x2 trung tham chieu truoc sua**; CoreMark x2 trung tham chieu; **random
diff 50/50 MATCH trung ca hash**; ASIC view 12/12 x2 = FPGA view 12 x 33 truong; directed ISA 6/6; bo dong bo x2.
Cong lint baseline OpenLane: 110/110, 0 moi. **Checker R9: 447,858,365 chu ky trong 278 lan mo phong, 0 dong "R9
equivalence broken" trong moi log.** Luu y trung thuc: dong `final` cua checker in co dinh "0 mismatches" va Questa van
chay `final` sau `$fatal`, nen bang chung dung la KHONG co dong "R9 equivalence broken" (mot lech se in dong do va lam
test FAIL) — da kiem: 0. Sua cau chu o lan doi RTL ke tiep (khong doi RTL chi vi mot chuoi in ra mo phong).

### 2026-09-26 — R10: sua co trong tam lan 2 cho goc ss, KHONG doi CPI — dong bang b56fbd4e

**Bang chung (STA ky ten r9_ecf4, max_ss; cong cu truy van moi `asic/sta_query/`, nap dung lib/SPEF/SDC cua flow, tai
lap dung -7.575 ns):** duong xau nhat `pc_f[9]` -> mux valid 256:1 cua icache (11.1 -> 18.1 ns, **7 ns**) -> hot_hit
(21.1) -> stall_pipe (24.1) -> retire_event (24.9) -> **chuoi ripple 20 cong AND** (24.9 -> 34.9) -> `csr_minstret`.
Cung duong qua nhanh so sanh hot tag (chan B/C/D cua and4 hop hit) ngan hon **2.2 ns** (-5.3 vs -7.575). 265/2,657
endpoint vi pham la bo dem: ABC dat enable tre (retire, counter_clear/freeze tu ghi APB) o **GOC** chuoi carry ripple
(perf `pipe_fill_drain`: 26 cong, ~13 ns). dcache khong doc mux valid trong hot hit (hot buffer 2 muc tu du).
**Thi nghiem Yosys nho (`asic/equiv/r10_keep/`):** voi bo dem 64 bit + enable sau 32 tang logic, `(* keep *)` tren gia tri
tang tao diem cat that (luoi `q_inc` ton tai sau anh xa, enable chi con qua 2 o mux); module don le khong tai lap duoc
chuoi (ABC tu dat enable cuoi) — nen `keep` la de CO DINH hinh dang, khong dua vao lua chon cua ABC.
**R10 (`scripts/apply_r10.py`, chay thu tren ban sao truoc; lap luan day du trong dau script):**
- R10a icache_controller: `hot_mvalid` (8 flop) = ban sao bit valid cua dong ma moi hot entry dang giu. Dat 1 khi fill
  (lookup hit: lookup_valid_q=1 va khong co ghi tag giua IDLE va LOOKUP; refill_success: tag RAM cung dat 1), theo moi ghi
  valid cua tag RAM vao dung dong do (chi hot entry `miss_hot_index` co the giu dong `miss_index`, khi cac bit chi so con
  lai trong hot_tag khop). Bat bien: hot_mvalid[e] == valid_bits[dong cua e] => hot_hit moi == hot_hit cu MOI chu ky.
  `tag_valid_rd` van nuoi `lookup_valid_q` (co thanh ghi, khong tren duong stall).
- Checker R10a trong icache.v (nhanh g_dm_baseline, `ifndef __openlane__` + translate_off): moi chu ky kiem ca bat bien
  (8 entry) lan hot_hit so voi dang cu; `$fatal` khi lech; `final` in `R10_EQUIV ... N cycles matched`.
- R10b: `(* keep *) wire [31:0] X_inc = X + 32'd1` cho 36 bo dem perf va `csr_minstret` — cung ham logic (X + 1'b1 trong
  ngu canh 32 bit), chi doi hinh dang netlist. KHONG ap cho load_stall_count / control_redirect_count / retire_order_q:
  synthesis dang xoa chung (khong dung), luoi keep se lam song lai. 2 bo dem victim hang 0 o DM, van gap lai nhu cu.
- Sua cau chu checker R9: "N cycles checked, 0 mismatches" -> "N cycles matched" (dung ca khi `$fatal` da chay).
**Kiem tra tinh:** latch 0 (8 to hop); lint_rtl 0 canh bao dung dan (khong canh bao nao tren tin hieu moi); lint_asic 0.
**Dong bang `b56fbd4e`** (171 file; khac ecf4fc03 dung 4 file: datapath.v, perf_counters.v, cache/icache.v,
cache/icache_controller.v). Chuoi day du x2 dang chay (`results/fullchain_b56fbd4e.log`); OpenLane lint+synthesis
`syn_R10` dang chay de kiem cong lint baseline va hinh dang netlist truoc PD.

### 2026-09-26 02:45 — LOI CUA TOI trong checker R10a: regression dung o test 54 -> fix 1 (chi checker)
Chuoi b56fbd4e buoc 2: `54 PASS, 2 FAIL/Fatal/Error` x2. Nguyen nhan (log `results/regression_rtlfix_p1.log`): Questa vopt
tu choi `tb_cache_event_accounting` (icache 8 dong) — `icache.v(114): part-select [-1:0] into u_controller.hot_tag`.
Voi LINE_COUNT=8, INDEX_WIDTH = 3 = so bit chi so L0 nen checker cat `hot_tag[e][INDEX_WIDTH-L0B-1:0]` = [-1:0].
Controller KHONG loi (nhanh generate `g_hot_li_none` da xu ly truong hop nay); chi checker mo phong. Do-file co
`onerror quit` nen 75 test con lai khong chay. lint_rtl chi quet 64/256 dong nen khong bat duoc. Cau hinh nho nhat voi
controller DM trong moi tb la 8 dong (quet `tb/*.sv`, `run_full_regression.do`), nen guard `$fatal` INDEX_WIDTH < L0B
khong bao gio ban.
**Fix 1 (`scripts/apply_r10_fix1.py`):** checker dung lai dia chi block 28 bit `{hot_tag[e], e}` roi lay
`[INDEX_WIDTH-1:0]` — hop le moi INDEX_WIDTH >= L0B. Logic thiet ke KHONG doi (khoi nam trong `ifndef __openlane__`
+ translate_off).
**Kiem ban sao (scratch, thu vien Questa rieng de khong dung chuoi dang chay):** regression day du **129/129 PASS, 0
loi**, checker R10a chay trong 11 testbench, 0 lech. **Doi chung am:** tat nhanh cap nhat `hot_mvalid` theo ghi valid
cua tag RAM -> `tb_icache` bao ngay `R10a equivalence broken at 425000 ... invariant 0` (checker co hieu luc; 3 tb khac
khong cham truong hop nay — bat bien nhay hon ket qua cuoi). Embench FPGA view cua chuoi b56fbd4e dang chay: checker R10a
khop ~3.2–3.6 trieu chu ky moi kernel DM, 0 lech.
Se ap fix 1 vao hdl/ SAU khi chuoi b56fbd4e ket thuc (khong sua hdl/ giua chuoi), dong bang lai va chay LAI TOAN BO chuoi.
PD R10A/R10B khoi chay tren snapshot `asic/snapshots/rtl_r10f1` = hdl/ hien tai + fix 1 (42 file, chi icache.v khac).

### 2026-09-26 03:10 — R10a CHUNG MINH HINH THUC (k-induction), khong chi mo phong
`asic/equiv/r10a_fv/` (`gen.py` sao chep RTL song — doi ten module, THEM cong fv_* chi de lo tin hieu noi co san, khong
sua logic; `run.sh`). Harness noi controller + tag RAM y nhu `icache.v` g_dm_baseline, moi dau vao tu do (ke ca reset,
refill, data line). Lap luan: thiet ke cu = thiet ke R10a voi hot_hit tinh theo cong thuc cu va khong co hot_mvalid
(thanh ghi nay khong nuoi gi khac), nen hot_hit moi == cong thuc cu o MOI trang thai dat duoc => hai thiet ke cho vet
giong het voi cung dau vao. Ba assert: A1 hot_mvalid[e] == valid_bits[dong cua e]; A2 ST_LOOKUP -> lookup_valid_q ==
valid_bits[miss_index]; A3 hot_hit == hot_valid[h] && valid_bits[request_index] && tag khop.
`sat -tempinduct -prove-asserts` (async2sync, memory_map, reset o buoc 1 cua base case):
- **256 dong (4 KiB): base case + induction step proven, SUCCESS o k = 1** (3/3 assert duoc nap).
- **8 dong (INDEX_WIDTH = so bit L0, truong hop da lam vo checker): SUCCESS.**
- **Doi chung am** (bo cap nhat hot_mvalid theo ghi valid): induction that bai toi k = 8 -> "proof failed" (chung minh
  khong rong); ban mo phong cua cung dot bien da cho phan vi du that o 425 ns (tb_icache).
**R10b cung duoc chung minh hinh thuc** (`asic/equiv/r10b_eq/eq.sh`, yosys equiv_make + equiv_simple/equiv_induct,
`-D__openlane__` nen checker bi loai ca hai phia): perf_counters cu (snapshot 358cb660, khong doi tu do) vs moi:
**1,256/1,256 o $equiv proven**; datapath cu (datapath song dao nguoc dung 2 dong R10b) vs moi, lam phang cung
alu/extend/regfile/branch/hazard_unit/bht: **5,281/5,281 proven**. Doi chung am (`eq_neg.sh`): doi mot bo dem thanh +2
-> 32 o khong chung minh duoc, `equiv_status -assert` bao loi (dung 32 bit bi doi).

### 2026-09-26 03:22 — Chuoi b56fbd4e: 2 loi (chi regression, loi checker da biet); ap fix 1 -> DONG BANG 2bffe7cc
`results/archive_b56fbd4e/`: latch/lint 0; regression 54 PASS + 2 loi x2 (checker, xem 02:45); UVM 5/5 x2; AXI 6/6;
**Embench 48 x2 trung tham chieu truoc sua; CoreMark x2 trung; random diff 50/50 trung ca hash; ASIC view = FPGA view
12 x 33 truong; directed ISA 6/6; bo dong bo x2.** Checker: 120 dong EQUIV, tong 401,502,954 chu ky khop, 0 dong
"equivalence broken". => CPI khong doi voi R10.
Ap `scripts/apply_r10_fix1.py` vao hdl/ -> **dong bang `2bffe7cc`** (171 file). Snapshot PD `asic/snapshots/rtl_r10f1`
trung tung byte voi cay song (42 file) => R10A/R10B/R10C dang chay dung RTL cuoi. Chuoi day du x2 chay lai tren
2bffe7cc (`results/fullchain_2bffe7cc.log`).

### 2026-09-26 04:04 — CHUOI XANH tren 2bffe7cc (R10 + fix 1). RTL SACH, CPI KHONG DOI.
`results/fullchain_2bffe7cc.log`, **0 failure**, manifest IDENTICAL dau-cuoi: latch 0; lint_rtl 0; lint_asic 0; regression
**129 = 129 x2**; UVM 5/5 x2; AXI 6/6; **Embench 48 x2 trung tham chieu truoc sua**; CoreMark x2 trung; **random diff 50/50
trung ca hash**; ASIC view 12/12 x2 = FPGA view 12 x 33 truong; directed ISA 6/6; bo dong bo x2. Cong lint baseline
OpenLane (syn_R10, cung logic): 110/110, 0 moi. Bang chung hinh thuc: R10a k-induction SUCCESS (256 va 8 dong), R10b
equiv 1,256/1,256 + 5,281/5,281, deu co doi chung am. Tiep: Quartus x2 (TAG=r10, dang chay luot 1), PD R10A/B/C.
Checker trong log cua chuoi 2bffe7cc: R10a 48 dong / 80,144,012 chu ky khop (chi cau hinh DM co controller nay; SA2/VC4
dung icache_dse_core, khong doi); R9 126 dong / 321,397,692 chu ky; 0 dong "equivalence broken".

### 2026-09-26 04:10 — R10 fix 2: keep cua R10b CHI cho ASIC (Quartus tra +17 % LE) -> DONG BANG d030ad12
**Do duoc (Quartus luot 1 tren 2bffe7cc, TAG r10):** dm_4kb seed 2 **18,063 LE** vs 15,425 (r7r8, 358cb660) = +2,638 (+17 %);
seed 1 17,918 vs 15,380; seed 3 18,005 vs 15,357. Quartus ton trong `keep` nen moi bit tang thanh mot bien LCELL rieng,
cong khong con gop voi thanh ghi. sa2_4kb (19,346) va vc4_4kb (19,798) se vuot ngan sach 20,000 LE -> DUNG sweep bang co
`results/.abort_fpga_sweep` (fit dang chay xong; 12 fit con lai bo qua — "12 failure(s)" cua runner la cac fit bi bo qua,
khong phai loi fit). Luu `results/archive_2bffe7cc/`.
**Fix 2 (`scripts/apply_r10_fix2.py`):** thuoc tinh chi phat ra khi co `__openlane__` (macro cuc bo `R10B_KEEP`, `undef` ngay
sau cum khai bao). Quartus/Questa/lint_rtl khong dinh nghia __openlane__ -> khong keep; OpenLane lint/synth/EQY co.
**Bang chung PD van hop le:** OpenLane toi Yosys.Synthesis tren snapshot `rtl_r10f2` (= cay song sau fix 2):
`soc_asic_top.nl.v` **trung tung byte** voi netlist synthesis cua r10A (sha256 79aba67f…, 13,965,031 byte). Lint OpenLane
chi khac so dong; cong baseline 110/110, 0 moi. => R10A/R10B (snapshot f1) dung cho RTL cuoi; R10C chuyen sang f2.
**Dong bang `d030ad12`** (171 file). Chuoi day du x2 va Quartus luot 1 (TAG r10f2) dang chay.

### 2026-09-26 04:40 — R11 (ung vien): so sanh hot tag theo tung entry roi chon one-hot — KHONG AP DUNG
Dong co: Incident 77 (duong ss xau nhat r10A qua nhanh so sanh hot tag, 15.2 ns sau pc_f). `scripts/apply_r11.py` (chi
chay tren scratch + snapshot `asic/snapshots/rtl_r11cand`; cay song KHONG doi, van d030ad12). Tuong duong tuan tu
controller cu/moi (`asic/equiv/r11_eq/eq.sh`): SUCCESS o INDEX_WIDTH 6 / 8 / 3 (~2,090 o $equiv, 0 unproven).
**Do cau truc (OpenLane synth `syn_R11cand` vs r10A):** do sau pc[4..6] -> hit 13 -> 8, NHUNG pc bit cao -> hit 6 -> 14;
tong hit 13 -> 14, access 15 -> 16, duong pc_f -> pc_f 39 -> 42. ABC (AREA 0, muc tieu delay long = 20 ns o tt) dung bo so
sanh 25 bit tung entry thanh chuoi sau; cau truc RTL khong duoc giu ngoai diem cat keep. => Khong co loi -> bo.
Bai hoc: o cau hinh synth nay, sua cau truc RTL chi co tac dung chac chan khi co diem cat (keep) dat dung cho — nhu R10b
(enable tre ra khoi chuoi carry, 23 -> 3 cell). Doi hinh dang ben trong mot khoi to hop thi phu thuoc ABC.

### 2026-09-26 18:05 — R12: tra lai logic FPGA ma R9b ton (vc4_4kb vuot 20,000 LE) — DONG BANG e21ef330
**Phat hien (Quartus luot 1 TAG r10f2, d030ad12):** vc4_4kb 20,002 / 20,077 / 20,026 / 20,039 LE (4 seed) > 20,000 — dac ta
(docs/en/guides/01_RTL_QUARTUS_QPF_QSF_SOF.md): "LE over 20,000 ... is still a FAIL". r7r8 (358cb660): 19,742–19,817.
Luot 1 bi dung giua chung o dse_4kb (phien Claude ket thuc: `fork: Resource temporarily unavailable`), khong phai loi fit.
**Do (map-only A/B tren thu muc guong, khong dung hdl/):** vc4 map 22,555 (358cb660) -> 22,744 (hien tai); toan bo tang nam
trong logic rieng cua datapath (+216 LUT; hazard_unit -21, controller -8) = R9. Chon mot hot AND-OR cua R9b khong dong goi
duoc vao LUT4 nhu mux tren select ma hoa (Quartus khong biet la one-hot): result_w (4 x 32) va load_byte (4 x 8). Bien the
V2 (hai mux do tren select 2 bit co san) -> map 22,599; **fit vc4 seed 2 = 19,855 LE (+145), setup Slow-85C +1.194 ns**.
**R12 (`scripts/apply_r12.py`, chay thu tren ban sao):** result_w = mux tren result_src_w; load_byte = case tren
load_byte_offset_w; bo 2 thanh ghi chet rsel_w / ld_lane_w. Giu ld_kind_w (phan R9b co loi cho ASIC). Dung vi:
rsel_w reset 0001, `if(!stall_pipe) <= onehot(result_src_m)`; result_src_w (controller) reset 00, `if(!stall_pipe) <=
result_src_m`, khong flush; tuong tu ld_lane_w / load_byte_offset_w.
**Chung minh hinh thuc (`asic/equiv/r12_fv/`):** k-induction tren RTL TRUOC R12 o muc riscv_core (controller + datapath,
moi dau vao tu do): A1 rsel_w == 1 << result_src_w, A2 ld_lane_w == 1 << load_byte_offset_w -> **SUCCESS (k = 1, 2/2
assert)**. Doi chung am (rsel_w[2] dung ==3): base case tim ra phan vi du that o do dai 6 ("model found for base case:
FAIL!"). Checker R9 von da so result_w / rd_data_final voi dung cac cong thuc ma hoa nay (>400 trieu chu ky, 0 lech).
**Kiem tra tinh:** latch 0; lint_rtl 0; lint_asic 0. **Dong bang `e21ef330`** (171 file, chi datapath.v khac d030ad12).
Chuoi day du x2 va Quartus luot 1 (TAG r12) dang chay. PD phai chay lai tren e21ef330 (netlist doi).

### 2026-09-26 18:43 — CHUOI XANH tren e21ef330 (R12). RTL SACH, CPI KHONG DOI.
`results/fullchain_e21ef330.log`, **0 failure**, manifest IDENTICAL dau-cuoi: latch 0; lint_rtl 0; lint_asic 0; regression
129 = 129 x2; UVM 5/5 x2; AXI 6/6; Embench 48 x2 trung tham chieu truoc sua; CoreMark x2 trung; random diff 50/50 trung
ca hash; ASIC view 12/12 x2 = FPGA view 12 x 33 truong; directed ISA 6/6; bo dong bo x2. Checker R9/R10a: 174 dong,
401,541,704 chu ky khop, 0 dong "equivalence broken". Quartus luot 1 (TAG r12): dm_4kb 4/4 seed dat (LE 15,529–15,584,
setup Slow-85C +0.235..+1.661 ns); cac diem con lai dang chay. Cong lint baseline OpenLane se chay trong run PD R12.

### 2026-09-26 20:30 — R12b: ASIC giu R9b one-hot (ABC treo voi dang ma hoa), FPGA giu R12 — DONG BANG 8b163675
Xem FLOW_JOURNAL Incident 80. `scripts/apply_r12b.py`: `ifdef __openlane__` quanh rsel_w/ld_lane_w va hai bieu thuc
result_w/load_byte. Tien xu ly: nhanh ASIC == d030ad12 (757 dong ma), nhanh FPGA == e21ef330 (805 dong ma). Netlist OpenLane
trung tung byte r10A (79aba67f). latch 0; lint_rtl 0; lint_asic 0; lint baseline 110/110. Dong bang `8b163675`; chuoi x2 dang
chay. Luu y trung thuc: mo phong (Questa, khong __openlane__) chay nhanh FPGA; nhanh ASIC da duoc mo phong day du o chuoi
d030ad12 (0 loi, checker R9 so tung chu ky) va duoc chung minh tuong duong nhanh FPGA bang k-induction.

### 2026-09-26 20:57 — CHUOI XANH tren 8b163675 (R12b) — RTL CUOI. CPI KHONG DOI.
`results/fullchain_8b163675.log`, 0 failure, manifest IDENTICAL dau-cuoi: latch/lint 0; regression 129 x2; UVM 5/5 x2; AXI
6/6; Embench 48 x2 = tham chieu truoc sua; CoreMark x2 =; random diff 50/50 = ca hash; ASIC view = FPGA view 12 x 33; ISA 6/6.
Quartus chinh thuc (TAG r12b) luot 1 + 2 dang chay. Luot kiem tra so bo r12 (16/16 fit dat, vc4 margin +107..+166 LE).

### 2026-09-26 21:00 — Quy tac moi cua ong (PD_metrics.pdf) — ghi nhan
1. 20,000 LE la muc tieu MEM tu dat, khong phai dat/truot; van toi thieu LE / dien tich std-cell va can nhac tang dien tich
   voi loi ich slack / CPI / cong suat do duoc. (R12 van dung huong: -145 LE, cung ham.)
2. May loi khong sua duoc luc nay: loi ngau nhien ro rang (Python SIGSEGV, WHEA, OOM ngau nhien) DUOC chay lai; chay kep la
   la chan chong hong du lieu am tham. Loi xac dinh cua EDA/thiet ke van phai sua ky thuat.
3. Don workspace BAT BUOC (xem FLOW_JOURNAL Incident 81).
4. Bao cao post-PD: ghi ro corner cho moi WNS/TNS/Fmax, tach corner ky ten timing voi corner do cong suat, ghi ro cong suat
   uoc luong hay tu hoat dong that, DRC/LVS la cong dat/truot truoc bang PPA, bang theo cau hinh kem hit rate / CPI.

### 2026-09-26 22:59 — Quartus luot 1 tren 8b163675 (TAG r12b): 16/16 dat, TRUNG TUNG TRUONG voi luot r12
`results/fpga_points_r12b_p1.csv`, 0 failure. dm_4kb 15,529–15,584 LE (setup S85C min +0.235 ns); sa2_4kb 19,438–19,527
(+0.460); vc4_4kb 19,834–19,893 (+1.194; truoc R12: 20,002–20,077); dse_4kb 16,869–17,027 (+0.374). So voi luot kiem tra
so bo r12 (e21ef330, chay truoc do): 0 truong khac tren 16 fit (tru thoi gian chay) => nhanh FPGA cua R12b trung R12, va
day cung la mot lan tai lap doc lap. Luot 2 chinh thuc dang chay.

### 2026-09-27 01:48 — Quartus luot 2 tren 8b163675: VERIFIED, 16/16 trung tung truong voi luot 1
`results/le_r12b_p2.log`: "[VERIFIED] 16 row(s) compared, 16 identical, 0 mismatched, 0 unpaired", 0 failure. Phia FPGA cua
RTL cuoi HOAN TAT (4 diem x 4 seed x 2 luot; them luot kiem tra so bo r12 cung trung tung truong).
