# Nhat ky thiet ke: RTL, kiem chung, FPGA, PD

Lich su duy nhat cua ban nghien cuu `E:/Projects/RISCV-research`, tu 2026-09-16. Moi su kien ghi mot lan. Van de lap
lai nhieu lan (loi may, OpenRAM suon xuong, EQY, ...) nam o muc 9 va duoc tham chieu tu cac muc ngay. Quy tac va
quy trinh chay: `QUY_TRINH.md`. So lieu hien hanh: `RESULTS.md`. Tra loi phan bien: `REVIEW_RESPONSE.md`.

## 0. Cach doc

- Tieu de: `### YYYY-MM-DD <chu de>`. Tham chieu cheo ghi ngay va chu de.
- Moi muc: thay doi gi, vi sao, so lieu, bang chung (duong dan). Bang so cuoi cung cua mot cau hinh nam o `RESULTS.md`.
- Ten run, ten cau hinh va ten ban RTL dat theo noi dung (`QUY_TRINH.md` muc I). Ten cu (r14F_A, Incident 96, R16,
  E14, ...) van con trong log, commit va ten thu muc; muc 11 anh xa ten cu sang ten moi.
- Log flow (`asic/dse_pd.log`, `asic/gated_pd.log`) ghi gio UTC.

## 1. 2026-09-16 .. 2026-09-18: ban sao nghien cuu, cache 1 KiB, tag RAM dong bo

### 2026-09-16 Ban sao nghien cuu va tham so hoa LINE_WORDS

- Thiet ke da cong bo bi dong bang; phan bien doi hoi thi nghiem phai sua thiet ke. Ban sao giu nguyen bo cuc thu muc
  cua repo (duong dan tuong doi trong `.qsf` / `config.json` van dung), Quartus va OpenLane ghi ket qua vao ban sao.
  Ngay 2026-09-18 ban sao chuyen ra ngoai repo cong bo thanh `E:/Projects/RISCV-research` (17 GB, doi ten cung o dia;
  file duy nhat co duong dan tuyet doi, `asic/run_pd.sh`, chuyen sang tu suy ra duong dan; lint, 110 test, hash RTL
  khong doi sau khi chuyen).
- RTL: `LINE_WORDS` thanh tham so (icache/dcache_dse_core, cache_axi_master, cache_dse_data_bank, soc_top,
  de2_115_top). Gia tri mac dinh bang ban dong bang: 48/48 run trung tung chu ky, Quartus DM trung ca bon so
  (15,188 LE / 8,356 reg / +0.629 ns / 51.62 MHz).
- Ba loi co san trong ban dong bang, lo ra khi kich thuoc line thanh bien:
  1. AXI master ep dia chi refill ve boi 16 byte (`addr_q <= {addr[31:4], 4'b0}`): sai voi line < 16 B.
  2. Ban sao eviction vao victim buffer gate theo `!IS_SA2` thay vi `IS_VC4`: cau hinh DM khong co victim buffer van
     ton 8 chu ky cho moi conflict miss de nap mot buffer khong bao gio doc.
  3. `axi_scoreboard.sv` mang dung hai gia dinh sai cua (1). Checker chung gia dinh voi thiet ke thi khong bat duoc loi
     cua thiet ke.

### 2026-09-17 Ablation 1 KiB: so lieu dau tien sai, da sua

- `CACHE_CONFIG=3` (DM tren controller 10 trang thai) do loi (2) o tren thuc chat la DM+VC4 tat lookup. Moi so suy ra
  tu no sai va da duoc dua vao ban thao bai bao; da sua sau do:

  | dai luong | da bao cao | dung |
  |---|---|---|
  | chi phi controller | +10.25 % | +9.35 % |
  | associativity | -1.16 % | -0.34 % |
  | SA2 thang / hoa / thua | 11 / 1 / 0 | 3 / 8 / 1 |
  | CPI cfg 3 | 1.4327 | 1.4210 |
  | quet dung luong 512 B | -9.57 % | -3.52 % |
  | line 64 B | -4.78 % | -1.39 % |

  Ket luan con dung: associativity khong doi gi tren 8/12 kernel va thua o matmult; khoang cach 8.98 % da cong bo gan
  nhu hoan toan do controller (phan tich day du: 2026-10-06 M1/M2).
- Loi do chinh dot sua nay gay ra, da sua:
  - Ba lan lech do rong khong bao loi bien dich: port `wr_word` 3 bit voi driver 2 bit (khong bank nao duoc ghi; canh
    bao `vopt-2241` bi coi la vo hai), index 4 bit bi cat con 3 bit o 16 word (alias, treo), `read_beat_count_q` 3 bit
    khong du cho burst 16 beat.
  - Mo rong bo dem beat vo dieu kien len 4 bit ton 10 LE va 0.66 ns, DM xuong -0.032 ns. Lam do rong co dieu kien thi
    tra lai dung 15,188 LE / +0.629 ns.
  - Ban sua `VC_DEPTH` dau tien de `vc_valid` / `vc_hit_vec` theo `VICTIM_ENTRIES`; con tro thay the co the vuot mang
    o do sau 1. Nay moi do rong theo `VC_DEPTH`, con tro wrap ro rang.
  - Mo hinh cache doc lap can luat `skip_after_clear` va chi khop 4/5 kernel. Nguyen nhan that: `perf_counters` dang
    ky su kien mot chu ky truoc khi dem, nen cong clear/freeze co hieu luc la cua chu ky sau. Mang cong cua phan cung
    theo tung truy cap trong trace thi khop 36/36 run, ca 9 bo dem.
  - Kiem tra firmware bao 12/13 kernel khac nhau vi `make` khong build lai (moi hash "da build" giong nhau); co
    `make clean` thi 13/13 giong.
- Lo hong kiem chung da lap: cfg 3 chua co unit test (them vao `cache_configuration_tb`, ky vong thrash nhu cfg 0;
  regression 98 -> 100 PASS); moi truong UVM co 9 cho gia dinh burst 4 beat (scoreboard, coverage, refill agent,
  assertions), nay dung mot tham so `LINE_WORDS` tren `tb_axi_top` cho ca DUT va checker, smoke/stress PASS o
  8/16/32/64 B; guard `LINE_WORDS` them vao 4 module va da chung minh guard bao loi o 1, 3, 32.

### 2026-09-17 Dot lint RTL (Verilator -Wall, khong file waiver)

- Lop dung/sai ve 0: WIDTHEXPAND/WIDTHTRUNC 28 -> 0, SYNCASYNCNET 3 -> 0, EOFNEWLINE 8 -> 0, tin hieu chet 17 -> 0.
  Con 98 canh bao cau truc moi cau hinh (61 debug tap / retire trace doc qua tham chieu phan cap tu testbench va co-sim;
  phan con lai dung theo cau truc: bit dia chi khong giai ma, nua thap cua tich cho MULHU, `m_axi_bresp`).
- Loi that lo ra: `icache_dse_core` ghi hot tag bang `request_block[27:3]` o 1/3 cho; o line 8 B mat bit tag cao nhat
  (hai line khac nhau co the bao hot hit). Questa `vopt-2697` bat duoc khi regression quet `LINE_WORDS`.
- Loi phuong phap cua lint: ban dau chi lint `CACHE_CONFIG=0`, khong elaborate DSE core (0 canh bao; cfg 1 co 17).
  `lint_rtl.sh` nay quet ca bon cau hinh. Nhanh DM baseline cung hard-code line 16 B, nay bao loi ro rang.
- Lint cua OpenLane (top `soc_asic_top`) bat `bank_csb0` khai bao 2 bit noi vao `csb0` 1 bit trong
  `axi_ram_32_asic_macro.v` (chi bit 0 duoc noi, chay dung do may man); sua o ca 4 thu muc design.
- Bo `-Wno-DECLFILENAME -Wno-VARHIDDEN`: VARHIDDEN chi do port `branch` cua module `branch`, doi ten `branch_en`.
  Ngoai le duy nhat duoc ghi ten trong script: `de2_115_top.reset_sync_q` (bo dong bo reset 2 flop).
- Sau lint: 110 PASS, 48-run giong tung byte, UVM 8/8, UVM AXI 8/8. Moc Quartus moi (seed 2, hai project, trung nhau):
  15,192 LE / 8,356 reg / +0.774 ns / 52.01 MHz; bon seed 15,141..15,289 LE (dai 148), +0.550..+0.774 ns.
- Doi ten port `branch_en` lam netlist ASIC 1 KiB tang 2,728 cell (+2.8 %) ma logic khong doi: muc 9, "Yosys nhay
  voi ten".

### 2026-09-18 Tag RAM dong bo cho ca bon cache (1 KiB)

- Moc: RTL md5 `bf24fbae` (sau lint + gop `is_branch_e`), 110 PASS.
- Quyet dinh kien truc: tag RAM doc dong bo (bo nho vat ly that) thay cho tra tag to hop 0 chu ky. Chi phi thuc te
  nho hon du doan: data RAM von da dong bo; DM giu hit 2 chu ky (ST_IDLE + ST_LOOKUP thay ST_HIT_RESP), miss them 1
  chu ky; DSE core da co ST_LOOKUP nen khong doi.
- Cau truc: `tag_mem` doc dong bo (22 x 64 bit), bit valid tach rieng va giu to hop (64 flop, xoa dong loat khi reset,
  doc ngay trong chu ky request). Fast path DM bo dieu kien main tag, giong DSE core.
- D-cache: (a) noi long dieu kien hit lam duong doc thu hai tra du lieu cua block khac; chi hot buffer (so sanh du 28 bit
  dia chi block) duoc tra loi trong chu ky request, main hit di qua ST_LOOKUP. (b) Test moi (store sau khi block bi
  day khoi mang chinh) lo loi tiem an co tu truoc: store miss mang chinh khong vo hieu ban sao trong hot buffer; nay vo
  hieu khi store miss. (c) Lan do dau +12.045 % CPI la loi cai dat (read hit van qua ST_CPU_RESP, L0 khong con duoc nap
  khi doc); suite 110/110 van xanh voi L0 chet, tuc khong test nao kiem L0 co duoc dung.
- Ket qua 48-run 1 KiB: DM 1,463,306 -> 1,463,620 chu ky (+0.021 %, CPI 1.2995 -> 1.2998); SA2, DM_VC4, DM_DSE giong
  tung byte. RTL `c9c96924` (`results/rtl_state_synccache.md5`).
- Nhan dinh luc do rang thay doi nay "xoa confound controller" la sai (DM_DSE van chay controller khac DM): xem
  2026-10-06 M1.
- Questa tu choi dung truoc khai bao, Verilator thi chap nhan: lint khong thay duoc mot lan bien dich Questa.

### 2026-09-18 PERF_COUNTERS_ENABLE va gia cua bo dem tren FPGA

- Tham so `PERF_COUNTERS_ENABLE` (mac dinh 1) nam trong dieu kien dem; bang 0 thi bo dem thanh hang so va flop bi xoa.
  Bang 1: 48/48 giong tung byte.
- Quartus seed 2, DM 1 KiB, tag dong bo so voi tag to hop: 14,596 / 15,192 LE, 8,015 / 8,356 reg, bit nho 84,736 /
  83,328 (ca hai mang tag 2 x 22 x 64 bit nam trong M9K), slack 0.000 / +0.774 ns, cong suat 272.25 mW (core dynamic
  105.08 mW, vectorless).
- Gia cua bo dem (dm so voi dm_nopc): 2,702 LE (18.5 %), 2,038 reg (25.4 %), 11.06 mW tong, 10.88 mW core dynamic.
- Bon seed: tag dong bo 14,596..14,672 LE so voi 15,141..15,289 (khong chong lan, trung binh -586); slack trung binh
  -0.114 ns, do trai 0.224 -> 0.924 ns, seed 2 la diem xau nhat (0.000). Quy tac tu day: bao cao dai bon seed, khong
  chi seed ghim.
- Bang bon diem cung RTL (seed 2): dm 14,596 LE / 0.000 ns; dm_dse 15,007 / +1.097; sa2 16,211 / +0.309; dm_vc4 18,033
  / +0.708. Controller 10 trang thai ton +411 LE (+2.8 %) va khong cham hon; SA2 +1,204 LE, VC4 +3,026 LE so voi
  dm_dse (mot seed; so bon seed: `RESULTS.md`). Tag dong bo giam khoang 2,000 LE o moi cau hinh DSE.

### 2026-09-18 ASIC 1 KiB sau tag dong bo: lon hon va nghen global routing

- So voi tag to hop: 102,041 / 99,132 cell (+2.9 %), 1,386,981 / 1,354,452 um2. Tren sky130 khong co macro vua mang tag,
  nen tag van la flop va con them thanh ghi dau ra (nguoc chieu voi FPGA). Uoc tinh ~1,070 cell la nhieu thu tu mapping,
  ~1,839 la logic that.
- Hai run dung o global routing (GRT-0118) voi density 48 va 40. Nguyen nhan la floorplan: bon macro 2 KiB xep mot cot
  ben trai, cell chen trong dai 955 um (51 % util trong dai, 27 % toan chip). Xep bon goc (die giu 1800 x 2900) thi
  global routing qua lan dau tien ke tu khi doi tag. Khong dung `GRT_ALLOW_CONGESTION`.
- CheckAntennas segfault: LEF macro OpenRAM khong co thuoc tinh antenna (59 chan vao). Them `ANTENNAGATEAREA 0.126` /
  `ANTENNADIFFAREA 0.4455` lay tu thu vien cell (muc 9 "Antenna"); buoc check khong duoc bo qua. Sau sua: 1,848 net /
  2,736 pin vi pham truoc repair, 498 / 643 sau repair (910 diode).
- Run `sync_final` (1 KiB, bon goc) qua detailed routing voi 0 vi pham; buoc ReportDisconnectedPins chet ngau nhien.
  Probe Python thuan (khong OpenROAD) cung sai ket qua tren may nay: day la loi phan cung (muc 9 "Loi may"). Bon ban
  va script cua buoc do sua loi that (vd. `PortStats` la `@dataclass` khong co field nao) nhung khong phai nguyen nhan.

### 2026-09-18 Cache 4 KiB va macro OpenRAM 32x256

- OpenRAM tren may co mot macro da build: `test_sram_1rw1r_32x256_noperim` (32 bit x 256 word, co GDS/LEF/LIB, tao voi
  `perimeter_pins False`, `check_lvsdrc False`). Voi `LINE_COUNT=256` moi bank du lieu la dung 256 x 32: giu bon bank,
  van doc ca line 128 bit trong mot chu ky, FSM khong doi.
- 48-run 4 KiB (khong doi RTL, chi tham so): DM 1,449,098 chu ky (-0.99 %), SA2 -0.93 %, DM_VC4 -0.85 %, DM_DSE -0.86 %;
  miss -11.2 / -13.8 / -3.2 / -11.2 %. DM_VC4 giam miss it nhat vi victim buffer va dung luong cung khu conflict miss.
- Kiem chung 4 KiB: regression them quet `LINE_COUNT` 128/256 cho bon cau hinh (126 PASS); `tb_soc_top` nhan
  `CACHE_LINE_COUNT`, UVM directed + periph PASS o 64 va 256.
- Y nghia so sanh bon diem (giu ca 1 KiB va 4 KiB): 0 vs 3 = chi phi controller; 3 vs 1 va 3 vs 2 = to chuc cache tren
  cung controller; 0 vs 1, 0 vs 2 bi confound.

### 2026-09-18 Do sau L0 cua I-cache: giu 8 entry

- Tham so hoa do sau L0 lam sai: chi so hep lai nhung lat cat tag van co dinh `[27:3]`, o 4 entry bit 2 khong thuoc truong
  nao, buffer tra sai line. Ca 48 run L0=4 sai ket qua firmware; ban sua dau chi bat 4/6 cho (khac khoang trang). Quy
  tac: sau moi lan tham so hoa do rong, grep moi dang hard-code cu va doi hoi 0 ket qua. O 8 entry ban sua la no-op
  (8/8 run giong).
- Gia (bon seed, cong suat o seed 2): L0=4 13,896 LE trung binh (-730, -5.0 %), 7,403 reg, worst slack -0.297 ns (truot
  50 MHz), 270.19 mW (-2.06); chu ky 48-run +6.42 % (L0=2: +15.45 %). Hieu ung theo kernel la bac thang: mont64 +19.21 %,
  md5sum +15.33 %, fdct 0.00 %. Ket luan: giu 8 entry. So "-721 LE, slack tot hon" bao truoc do la mot fit tren RTL loi,
  da huy; hai dong LE cua RTL loi da xoa khoi `results/fpga_points.csv`.

## 2. 2026-09-18 .. 2026-09-24: moc 1 KiB tren ASIC, chuyen 4 KiB sang ASIC

### 2026-09-18 Moc 1 KiB post-route (run sync_final)

- `asic/soc_dm_control/runs/sync_final`, giu lai lam moc 1 KiB. Die 1800 x 2900 um = 5.22 mm2; dien tich instance
  2,720,150 um2 (macro 1,138,150 + cell 1,582,000), util 53.35 % (cell 39.94 %); 186,877 cell (27,642 tuan tu, 6,603
  diode); 0 vi pham DRC, 7.30 m day.
- Timing 9 goc RCX, chu ky 20 ns: hold 0 vi pham moi goc (+0.0919 ns); setup tt/ff dat (+2.80 .. +5.68 ns); ss truot
  -13.26 ns (8,846 path), can khoang 33 ns. Max cap 658, max slew 4,730. Cong suat nom_tt 196.4 mW (internal 108.6,
  switching 87.7; to hop 86.3, tuan tu 58.3, clock 40.6, macro 11.2).
- ReportDisconnectedPins qua sau khi thu lai (44 chan = 44 tie cell `conb_1`, 0 critical).
- Cac so nay lac quan vi loi SDC phat hien 2026-09-24 (muc 9 "SDC create_clock"): kiem lai bang SDC dung, hold tt cua
  ban 1 KiB nghien cuu tu +0.202 xuong -0.048 ns.
- Phan sign-off con lai cua 1 KiB dung lai khi 4 KiB thanh cau hinh chinh.

### 2026-09-18 Loi trong cong cu tu viet (retry, kiem tra kep)

- `pd_retry.sh` sap xep thu muc step theo chuoi ("99-..." sau "126-...") nen chay lai 20 step da xong; doc moi `$1 $2`,
  bo qua `--from`. Thu muc `final/` khong phai dau hieu hoan thanh (run cat ngan cung ghi `final/`). Thu muc step ton tai
  truoc khi step chay; dau hieu dung la `state_out.json` hoac metric.
- `verify_double.py` lap chi muc theo `kernel` nen chi so 12/48 dong ma van in VERIFIED; nay khoa ghep, trung khoa la
  loi cung. Pass 2 cua Quartus 4 KiB in VERIFIED khi khong fit nao chay (vong cho het han roi van chay tiep, moi fit bi
  khoa dong thoi tu choi): hai CSV gia da xoa, vong cho nay dung khi het han. Guard thay the bao FAIL nham khi hai
  snapshot giong het vi moi fit tai lap dung; nay dem dong `[PASS] 1 fit(s)` thay vi so file. Ket qua dung: 16/16 dong
  4 KiB giong tung truong.
- Cac loi nho: sua script dang chay (bash doc theo offset), sweep thieu `--compile`, `run_power.py` ghi de thay vi gop,
  `run_fpga_points.py --list` hong. Ba bao cao PASS sai (grep dem, "da sua upstream", `final/`).
- Quy tac rut ra: PASS chi tu artefact cong cu ghi khi thanh cong; kiem tra kep can hai artefact duoc tao doc lap va
  phai chung minh dieu do.

### 2026-09-19 RTL bo nho 4 KiB cho ASIC

- Mang du lieu cache bang flop o 4 KiB la 65,536 flop (2 x 4 x 256 x 32): khong kha thi. Macro PDK
  `sky130_sram_1kbyte_1rw1r_32x256_8` vua dung mot bank: 4 bank moi cache, 8 cho I va D, cong 4 macro 2 KiB cua RAM chinh
  = 12 macro. Doc dong bo cua macro trung chu ky voi RTL hien co.
- D-cache doc va ghi cung mot hang trong `ST_REFILL_DATA` (moi beat refill). Macro 1rw1r de cong 1 khong xac dinh khi
  cong 0 ghi cung dia chi, nen wrapper chan doc dung bank dang ghi; mot bo dem chi-mo-phong do so lan xung dot. Bo dem nay
  ban dau co BLKSEQ/PROCASSINIT (lint bat), da sua.
- `icache_tag_ram` reset bit valid bang vong lap tren mang unpacked: Verilator cua OpenLane bao BLKLOOPINIT o 256 line
  (o 64 line khong lo). Doi sang vector packed nhu `dcache_tag_ram`; 48-run 1 KiB va 4 KiB giong tung byte.
- Regfile vao MLAB khong the tren Cyclone IV E (chi co M9K, doc dong bo): khong lam.
- Tong hop 4 KiB: cell 1,036,877 um2, 77,310 instance (1 KiB: 1,386,981 um2, -25.2 %); 0 latch, 0 loi lint.

### 2026-09-19 Floorplan 12 macro va global routing 4 KiB

- Floorplan dau: hai cot (hanh lang 990 um, hep hon dai 955 um da hong o 1 KiB, bo), dai ngang 2600 x 2500 (chong lan 26
  um), dai ngang 2800 x 2400 (sach, 6.72 mm2, util 57.2 %). Kiem tra chong lan va bien core nam trong script sinh file.
- Cac chan: GlobalPlacement crash 3/3 trong resizer timing-driven (tat dinh) -> `PL_TIME_DRIVEN false` (tuy chon chat
  luong dat cell, resizer sau GRT van chay); DPL-0036 voi 3 cell do RepairDesign chen -> density 48 -> 40 roi
  `PL_MAX_DISPLACEMENT_Y 100 -> 500`, `X 500 -> 1000` (util cell chi 28 %, gioi han dich chuyen moi la rang buoc);
  ABC segfault 13 lan (loi may) -> dung lai netlist da thanh cong.
- Global routing: 43 lan crash (loi may), khong lan nao GRT-0118. `GRT_OVERFLOW_ITERS 20` va `GRT_ALLOW_CONGESTION`
  da thu va bo vi khong co tac dung. Die 2800 x 2400 -> 2800 x 2900 tang 35.6 % tai nguyen met1 sau derate (util 57.2 ->
  46.4 %, duoi muc 60-70 %: voi 12 macro chiem 40 % die khong co kich thuoc nao dat ca hai). Mot lan chay 244 phut bi
  dung o gioi han dat truoc.
- Nguyen nhan that: kenh thoat chan. Chan tin hieu cua macro nam o canh tren/duoi; khe giua cac hang macro la 18 / 33.5 /
  41.5 um cho 216 / 401 / 175 chan, trong khi dai trong 1552 um khong co chan nao. Ban 1 KiB co 138 / 171.5 um cho moi
  ~144 chan (gap khoang 11 lan so track tren moi chan). `macro_placement_channels.cfg` chia lai chieu cao trong
  (300 / 450 / 450 / 445.4 um): kenh xau nhat tu 49 len 661 track met3 cho 401 chan.

### 2026-09-19 Don workspace lan dau va hau qua

- Xoa 24.6 GB; log duoc trich dan chep sang `asic/evidence/`, metric cua run bi xoa vao `evidence_runs/`. Hai phat hien:
  `ablation_l0_4.csv` suyt bi xoa nhung chua 48 dong hop le (giu); log XOR KLayout cua `.magicsafe.gds` chua tung la
  file, nen dung lai bang chung bang `asic/prove_magicsafe_equivalence.py` (so tung hinh: 412 hinh bi bo tren dung 5
  layer chu thich, 34 layer con lai giong het; `asic/evidence/MAGIC_NAMESPACE_COLLISION.md`).
- Vong hai bo cac step lap lai cua bao retry (sync_final 27 -> 11 GB, synth4kb 7.8 -> 2.4 GB; tong 61 -> 13 GB) va lam
  hong kha nang resume cua ca hai run: `state_in.json` tro toi file trong thu muc step cu bang duong dan tuyet doi (muc 9
  "Bay trang thai run OpenLane"). 1 KiB khong mat gi (`final/` tu du); 4 KiB phai chay lai tu tong hop.
- May khong con tong hop duoc: 27 lan, 26 log khac nhau, chet o 9 pass khac nhau trong khi Yosys tat dinh. Netlist cua
  `synth4kb` (cau hinh chi khac `DIE_AREA`, Yosys khong doc) duoc ghep vao run moi bang `graft_synthesis.py` (sha256
  `6f16a7ee`): tu day thiet ke vat ly 4 KiB dung netlist cua mot run truoc.
- Treo im lang o STAMidPNR: luong doc output cua OpenLane chet vi IndexError khong the xay ra (bo nho hong), luong chinh
  cho mai. `hang_watchdog.sh` ban dau do CPU cua tien trinh Python cha (ranh theo thiet ke) nen giet nham
  RepairDesignPostGPL dang chay 99.8 %; sua thanh cong CPU ca cay tien trinh. Quy tac: watchdog phai do tien trinh dang
  lam viec.

### 2026-09-22 RepairAntennas 4 KiB: race trong vung OpenMP

- 8 lan crash trong `boost::polygon` duoi `__kmpc_fork_call`: `antenna_repair.tcl` khong goi `set_thread_count`, va
  OpenROAD tu dat so luong luong nen `OMP_NUM_THREADS=1` khong co tac dung. Them `set_thread_count 1` vao
  `antenna_repair.tcl` va `antenna_check.tcl` (openlane-local) thi qua; antenna 2,139 -> 465 net (9,579 diode).
- Moc 1 KiB cung chua tung dat 0 antenna (501 net sau repair, 6,603 diode).
- Danh sach yeu cau cua phan bien (`danh_gia.txt`) duoc kiem ke va theo doi tu ngay nay: `REVIEW_RESPONSE.md`.

### 2026-09-22 Chuoi kiem chung kep va manifest RTL

- `scripts/rtl_manifest.py` ghi sha256 cua 68 file RTL / TB / UVM / firmware (tong `9cd02a06`), `--check` chung minh
  nguon khong doi. `scripts/run_fullchain_both.sh`: regression x2, UVM x2 o 64 va 256 line, Embench x2 o hai dung luong,
  so pass 1 voi pass 2 va voi ma tran chuan. Ket qua 2026-09-23: 126 PASS x2, UVM 20/20, bon ma tran 48-run giong tung
  byte, ke ca so voi ma tran chay 4 ngay truoc (37 phut cho ca chuoi).
- CoreMark (can RAM lon hon 8 KiB, chay rieng bang `scripts/run_coremark.py`) va random differential 50 seed (50/50
  khop, trace luu trong `results/random_diff/`) chay xong 2026-09-23. 43.7 % chu ky CoreMark la MMIO (in diem qua UART).

### 2026-09-23 4 KiB: detailed routing DRC 0 va so post-route dau tien

- Detailed routing 9 vong ve 0 (99,784 -> 0), 8.20 m day, 872,648 via. `Checker.TrDRC` = 0 xac nhan; giu
  `GRT_ADJUSTMENT 0.2`.
- ResizerTimingPostGRT chet 6 lan o 6 ham khac nhau (loi may), chay lai. ReportDisconnectedPins qua khoang 1/40 lan;
  tang ngan sach retry len 300. Watchdog co lo: mot lan chay quay 12 gio o 99.9 % CPU khong ghi gi; quy tac moi la khong
  co output VA RSS doi < 8 MiB trong 30 cua so 60 s (ban 5 phut da dung nham Magic.WriteLEF hai lan, buoc nay im lang
  ~4 phut va len 8 GiB).
- So post-route dau tien (4 KiB so voi 1 KiB): dien tich instance 3,944,670 / 2,720,150 um2, cong suat 173.7 / 233.7 mW
  (-26 %, bank du lieu thanh macro); setup nom_tt -1.005 ns; hold truot o ca 9 goc (xau nhat -1.436 ns, TNS -59.0);
  clock skew -4.128 ns (cay clock phai vong qua 4 hang macro chan met1-met4). `RUN_POST_CTS_RESIZER_TIMING` dang tat.
- Magic: macro 1 KiB chua co ban `.magicsafe.gds` nen WriteLEF hong 31 lan; tao va chung minh nhu macro 2 KiB
  (`asic/evidence/MAGIC_NAMESPACE_COLLISION.md` muc 4). XOR Magic/KLayout = 0. Magic DRC tren GDS: 42,198,750 vi pham,
  mot luat duy nhat (li.3), lay mau 100 % nam trong vien macro; KLayout DRC 0; TritonRoute 0. `ERROR_ON_MAGIC_DRC`
  giu true, Magic DRC chay tren DEF (`MAGIC_DRC_USE_GDS false`), KLayout kiem toan bo GDS ke ca ben trong macro.
- Antenna 429 sau repair, 94.5 % tren cell thuong.
- EQY lan dau duoc bat (`RUN_EQY` mac dinh false): boc guard `$fatal` cua `cache_data_ram_sram4.v` trong
  `ifndef __openlane__`; script EQY rieng chuyen `read_liberty` sang phan `[gate]`. Sau do chet o `read_ids` cua EQY
  (loi may, file ids 346 MB). Chuoi EQY tiep theo: muc 9 "EQY va LEC".
- Kiem ke moi cong kiem tra: `MAX_SLEW/CAP_VIOLATION_CORNERS` la `['']` nen hai checker khong kiem goc nao trong khi co
  10,914 slew / 1,744 cap; dat `['*tt*']`. Doc 115 canh bao lint (107 UNUSEDSIGNAL, 4 PINMISSING nguon macro, ...).

### 2026-09-23 Run thu hai voi cac co che sua dang tat, va trang thai lai

- Bat `RUN_POST_CTS_RESIZER_TIMING`, `RUN_POST_GRT_DESIGN_REPAIR`, diode heuristic, `DIODE_ON_PORTS both`,
  `GRT_ANTENNA_ITERS 6`, `GRT_ANTENNA_MARGIN 15`, `GPL/DPL_CELL_PADDING 4/2` (dieu kien tien quyet ghi trong docstring cua
  HeuristicDiodeInsertion; 19 lan hong truoc khi dat).
- So do duoc: repair sau CTS dua setup TNS -32,031 -> 0, hold TNS -59 -> -0.58; repair sau GRT dua slew 3,286 -> 288,
  cap 1,578 -> 151; fanout khong doi (`repair_design` khong co tuy chon fanout, cac cell vi pham la buffer do chinh no
  chen, fanout 26-31 so voi gioi han 8).
- Diode heuristic o nguong 90 um: diode 3,673 -> 101,367, vi pham 429 -> 529 (te hon), +3.5 % dien tich, roi
  RepairAntennas hong vi GRT-0226. Da bo.
- Cau hinh sua khi flow dang chay khong duoc ap dung (OpenLane doc cau hinh mot lan luc bat dau): dung va chay lai.
- GRT-0226 that ra do trang thai lai: run 2 duoc tiep tuc tren database da qua detailed routing cua run 1 (state chain:
  CTS <- ... <- DetailedRouting), nen global routing chi dinh tuyen 1,320 net moi. Ba gia thuyet truoc do (diode, num
  antenna, padding) deu sai; ban va `GRT_FORCE_FULL_ROUTE` da go. Cac so "cai thien" cua run 2 khong dung duoc cho
  sign-off. Chay lai tu trang thai sach `105-openroad-detailedplacement`; xoa 697 thu muc step that bai (31 GB).

### 2026-09-24 Hai latch that trong netlist trong khi Verilator bao 0

- `check_setup` cua OpenSTA bao 2 chan latch khong co clock: `dlxtn_1` cho `baud_rx_en` va `write_fifo` cua
  `rx_block.sv` (nhanh `default` chi gan `rx_done`). Trang thai 2'b11 khong the dat toi nen khong sai chuc nang; ban sua
  ap dung trong dot sua RTL cung ngay (gan du ba dau ra trong `default`).
- Verilator `--Werror-LATCH` bao 0 latch vi khoi la `always @(*)`. Bang chung "khong co latch" la dem cell
  `dlxtn` / `dlxtp` trong netlist cong va doc `check_setup`, khong phai `design__inferred_latch__count`.

### 2026-09-24 Loi SDC create_clock va chay lai full flow tu buoc 1

- `soc.sdc` viet `set clocks [create_clock ...]`; `create_clock` cua OpenSTA khong tra ve gi nen clock uncertainty, clock
  transition va moi I/O delay khong duoc ap dung (chi tiet va so do lai: muc 9 "SDC create_clock"). Sua thanh
  `create_clock ...; set clocks [get_clocks ...]`; endpoint khong rang buoc 161 -> 86 (con lai la chan macro SRAM).
- SDC cua ban 1 KiB cong bo cung loi, nhung ban cong bo chi doc: file giu nguyen, so do lai luu o
  `asic/evidence/sdc_recheck_1kb_published/` va `sdc_recheck_1kb_research/`.
- Ap dung tu day: thay doi anh huong tu tong hop tro di (SDC, cau hinh) phai chay full flow tu buoc 1, khong noi tiep tu
  giua; khong sua bai bao.
- `ERROR_ON_LINTER_WARNINGS` ha ve false: 115 canh bao, 87 trong cac wrapper ASIC, 28 trong `hdl/`; loi lint va latch
  van chan flow. Cac wrapper ASIC duoc lam sach trong dot sua RTL 2026-09-24.

## 3. 2026-09-24 .. 2026-09-26: dot sua RTL, view ASIC, ban 8 KiB-RAM

### 2026-09-24 Dot sua RTL va view ASIC

- PD dung trong luc sua. Quy tac cua dot (sau nay thanh quy tac chung, `QUY_TRINH.md` muc C): RTL truoc PD; moi thay
  doi RTL keo ca chuoi; moi phep do chay hai lan; khi RTL da dong bang thi PD khong sua RTL. Snapshot truoc khi sua:
  `hdl_pre_rtlfix_20260924T093817Z.tar.gz` (nay trong `results/pd_run_archive/asic_experiments_20261007.tar.gz`).
- Cac muc da lam:
  - Quet latch bang Yosys (`scripts/latch_sweep.sh`, moi to hop CACHE_CONFIG x LINE_COUNT): 2 latch cua `rx_block`
    (moi to hop) -> nhanh `default` gan du ba dau ra -> 0 latch.
  - Read-enable cho `cache_dse_data_bank.v` (bank cua DSE core doc moi chu ky): bo doc o chu ky ranh va chu ky L0 hit,
    nhung giu doc trong IDLE khi request sap vao LOOKUP vi store hit cua D-cache ghep byte tu ket qua doc phat ra trong
    IDLE. Chu ky khong doi.
  - Loi ghi AXI posted (`m_axi_bresp` bi bo qua): ghi nhan loi kieu khong chinh xac. Co sticky `wr_err` va dia chi loi
    dau tien o sysmon `0xAC` / `0xB0`, ghi 1 vao bit 0 cua `0xAC` de xoa; ident `0x53380001` -> `0x53380002`. Test T19
    cu co the PASS ma khong tiem loi (tat loi truoc khi lenh ghi toi RAM); da viet lai.
  - UART: `STATUS` bit 5 `tx_fifo_full`, bit 6 `rx_fifo_empty`. Test moi `tb_uart_apb` (truoc do khong testbench nao
    cham `uart_apb` o muc thanh ghi) bat loi `RXDATA` khong bao gio tra byte vua nhan (chot luc `rx_done`, truoc khi FIFO
    duoc doc). Nay `RXDATA` la byte cu nhat chua doc, tu nap truoc tu FIFO. Firmware khong nhan UART nen so lieu cu
    khong doi.
  - Chan nguon macro trong wrapper: khong lam; `PDN_MACRO_CONNECTIONS` noi chung va LVS dat.
  - Mot SoC top duy nhat cho ASIC: ban sao `soc_top_asic.v` da lech 66 dong (thieu 3 tham so, con 8 day probe da xoa
    khoi `hdl/soc_top.v`). Wrapper RAM ASIC doi ten module thanh `axi_ram_32` (thay the theo ten module, nhu
    `cache_data_ram_sram4.v`), `soc_asic_top` instance thang `hdl/soc_top.v` voi tham so ghi ro.
    `scripts/lint_asic.sh` doc `VERILOG_FILES` tu `config.json` va coi MODDUP la loi (glob cu co 3 MODDUP ma van PASS).
  - Script EQY tro vao netlist cua run cu: `yosys.py` cua openlane-local thay `@NETLIST@` / `@PDK_FORMAL@` bang netlist
    va model cua chinh run.
- View ASIC (lan dau bo nho ASIC duoc mo phong): `tb/compile_asic_view.do` thay RAM FPGA bang wrapper SRAM va model
  OpenRAM, nap chuong trinh qua backdoor, `run_ablation.py --asic-view`. Lan dau 1/12 kernel PASS (chi crc32, khong co
  store). Ba loi RTL that trong bo nho ASIC:
  1. `axi_ram_32_asic_macro.v` dung bien truoc khai bao: Questa khong bien dich, file chua tung qua Questa.
  2. Dia chi ghi khong bypass khi AW va W den cung chu ky, nen lenh ghi vao dia chi cua lenh ghi truoc (91/115 lenh ghi
     sai dia chi). Netlist ASIC da qua PD truoc do khong chay duoc chuong trinh nao co store.
  3. `cache_data_ram_sram4.v` khong giu gia tri doc: model OpenRAM tra X sau chu ky khong doc, trong khi controller dung
     `data_rd_line` sau chu ky do. Moi bank chot gia tri da doc (264 FF, khong them chu ky).
  Sau sua: 12/12 PASS; moi truong kien truc va moi bo dem cache trung view FPGA, chi `mcycle` khac (muc 9 "View ASIC va
  view FPGA"). Ket qua PD cua run `ch4kb_full` (netlist tu RTL con loi 2 va 3) bi bo. Probe chan doan giu o `tb/diag/`.
- Dong bang 170 file (manifest mo rong them UVM, firmware va Verilog ASIC), tong `aa8e32f9`; regression 128 PASS x2.

### 2026-09-25 Chi con 4 KiB; do du thong so; loi APB pstrb

- Dung moi cong viec 1 KiB (ket qua 1 KiB da co giu nguyen lam tham chieu).
- Do thieu thong so, da sua: `run_fpga_points.py` tu 6 so len 116 cot (tai nguyen chi tiet, timing 3 goc, cong suat theo
  khoi / mien clock / nguon / module; thieu truong la FAIL); cong suat chay sau moi fit (truoc chi chay mot lan, tren seed
  chay cuoi); report luu rieng tung seed; parser snapshot doc moi cap key=value (38 truong + 8 bat bien); harness in du 37
  thanh ghi sysmon. `scripts/fpga_seed_summary.py`: bang 4 seed (min/max/mean/do trai), thieu seed hay truong la FAIL.
  Report Quartus dung CRLF lam regex khong khop; cong "thieu truong" bat duoc truoc khi chay that.
- Dung sweep bang co huy hop tac `results/.abort_fpga_sweep` (TaskStop de lai vong lap, lenh kill bi tu choi).
- Lint OpenLane voi `ERROR_ON_LINTER_WARNINGS` true: 112 canh bao, phan loai tung cai. Hai loi that: `uart_apb.v` bo qua
  `pstrb` (vi pham APB4: ghi mot byte vao CFG de ca 3 byte con lai; sua va them test), `axi_ram_32_asic_macro.v` co thanh
  ghi chet `rd_addr_q` (xoa). 111 canh bao con lai deu co ly do thiet ke: `asic/soc_dm_4kb/lint_baseline.tsv` +
  `scripts/lint_baseline_check.py` (fail neu co canh bao moi); `ERROR_ON_LINTER_WARNINGS` false.
- Dong bang `b82c2717` roi `c235dfb7` (chi them truong in cua harness). Chuoi day du xanh: 128 PASS x2, Embench va CoreMark
  trung tham chieu, random diff 50/50, view ASIC = view FPGA tren 33 truong.
- Quartus 4 KiB (4 seed x 2 luot, trung tung truong): DM va DM_DSE dat ca 4 seed; SA2 truot 2/4 seed, DM_VC4 1/4 seed o
  Slow 85C / 50 MHz.

### 2026-09-25 PD tren RTL dong bang dau tien (run rtlfix_c235)

- 84 endpoint khong rang buoc deu do hang so dieu khien (cong 2 SRAM khong dung, `wmask0` / `web0` co dinh, chan LCD co
  dinh, `trap_mcause`): khong co duong timing nao bi bo sot.
- Bay metric cong don: `STAMidPNR` chi phan tich nom_tt nhung `state_out.json` mang so ss/ff cu tu STAPrePNR;
  `scripts/pd_metrics.py` chi lay so mot goc khi buoc co thu muc report cua goc do (muc 9 "Bay trang thai run").
- ResizerTimingPostCTS chet hai lan (cung frame bang bam tag), lan ba qua. Hai ban phat lai voi ASLR tat cho cung so va
  cung netlist; mot ban lech dung mot dong DEF (huong N / FN cua mot cell). Lech cung kieu lap lai tren run sau nen xep
  "chua xac dinh nguyen nhan"; doi chieu PD dung netlist + metric + dong `final` cua resizer, khong dung hash ODB/DEF.
- Driver `ch4kb_run.sh` resume tu mot buoc bi gate tat, va OpenLane lay `state_out.json` moi nhat tim de quy, nen
  RepairAntennas chay lai tren database da sua. Thay bang `asic/pd_driver.py`: danh sach buoc theo gating cua
  `classic.py`, kiem chuoi `state_in == state_out` cua buoc truoc, cach ly thu muc step do dang, chi thu lai crash native.
- RepairAntennas qua ngay lan dau tren run sach; antenna sau detailed routing 511 net.
- STA ky ten 9 goc: nom_tt -0.272 ns (4 endpoint), max_tt -0.477; nom_ss -11.75; hold truot o cac goc ss tu cong
  `uart_rx` / `key1_n` (dan toi bo dong bo dau vao); cong suat vectorless nom_tt 154.34 mW.
- Magic DRC 4,187 loi `nwell.4` la hien vat cua view LEF (LEF cell chuan khong co hinh hoc tap N+). Thi nghiem doi chung:
  GDS that cua cell chuan, SRAM giu LEF -> 0. Tu do buoc Magic DRC cua flow chay tren GDS voi macro truu tuong
  (`drc.tcl` cua openlane-local, `MAGIC_DRC_USE_GDS true`); noi bo macro do KLayout DRC kiem.
- EQY chet sau `combine`; gia thuyet OOM bi bac bo (con 12 GB trong). Python cua EQY doc file ids 346 MB hong ca tren file
  hop le (loi may). LVS khop, KLayout DRC 0.

### 2026-09-25 Bo dong bo dau vao bat dong bo (RTL a0c425f8) va run r8_a0c4

- `uart_rx` di thang vao logic next-state cua `rx_block`; wrapper FPGA dong bo reset va `key1_n` nhung khong dong bo
  `uart_rx`; wrapper ASIC khong dong bo gi, va `set_false_path -from reset_n` lam recovery/removal khong bao gio duoc
  kiem. Them dong bo 2 flop (FPGA: `uart_rx`; ASIC: reset nha dong bo, `key1_n`, `uart_rx`); SDC false path cho
  `key1_n` / `uart_rx` chi hop le sau khi da dong bo. Test moi `tb/top_wrapper_sync_tb.sv` (hai wrapper chua tung duoc
  mo phong): RTL cu 4 va 10 FAIL, RTL moi PASS. lint_asic bat SYNCASYNCNET trong bo dong bo reset moi (mot vector vua la
  du lieu vua la reset); tach thanh `reset_meta_q` / `reset_sync_q`. Dong bang `a0c425f8`, regression 129 PASS x2.
- Quartus sau thay doi nay: moi cau hinh co it nhat mot seed truot Slow 85C (DM seed 2 -0.924 ns) du duong toi han khong
  qua bo dong bo: bien o Slow 85C chi khoang +-1 ns va doi theo placement. Slow 0C dat ca 4 seed. Log cua lan fit that bai
  nay duoc giu (`<ten>.attemptN.failed.log`).
- Run r8_a0c4: die 8.12 mm2 (cell chuan 1.46 + 12 macro 2.66 mm2), 195,518 cell; hold 0 vi pham o ca 9 goc; nom_tt
  -0.569 ns (3 endpoint), max_tt -0.827; ss -11.3 .. -13.4; Magic DRC 0, KLayout DRC 0, LVS khop; antenna 578 net;
  cong suat vectorless 102.96 mW (154.34 cua run truoc la hien vat: `reset_n` la cong vao chinh nen cay reset ~9k flop
  bi tinh nhu dao lien tuc). EQY 3/3 that bai (loi may).
- Bon thi nghiem chi doi PD de dong tt (resizer chi theo tt+ff, GRT setup margin 0.8, ca hai, them timing-driven
  placement): -0.63 .. -1.01 ns nom_tt, khong cai nao tot hon baseline. Suy giam GRT -> RCX ~0.65-0.7 ns lon hon moi
  bien resizer tao duoc. Duong toi han la duong nua chu ky tu SRAM I-cache (muc 9 "OpenRAM suon xuong").
- Thu noi clock 21.5 ns (nom_tt +0.190, max_tt -0.064) roi bo: ASIC bat buoc 50 MHz.
- Kham pha chien luoc tong hop (buoc 35, sau CTS): AREA 0 -0.788, AREA 1 -0.177, AREA 2 -0.394, AREA 3 +4.326, DELAY 0..4
  +0.13 .. +2.64 ns. AREA 3 khong route duoc (GRT-0118): script cua no co `buffer -c -N 8` viet cung, ABC dung cay buffer
  khong biet vi tri, HPWL 2.32x. AREA 3 + `DESIGN_REPAIR_REMOVE_BUFFERS` route duoc (+4.553 ns sau GRT); DELAY 1 nghen.
  Bai hoc: chon cau hinh tong hop phai co tieu chi routability (GRT), khong chi timing sau CTS.
- Mo phong muc cong (thay the chuc nang cho EQY): `asic/gls/`, netlist sau fill, model cell chuc nang, model OpenRAM;
  12/12 kernel PASS, `mcycle` trung view ASIC tung chu ky (`results/gls_r8_a0c4.csv`).
- Cong suat theo hoat dong (GLS -> SAIF -> OpenSTA): phuong phap va cac bay o muc 9 "Cong suat"; so dau tien crc32
  116.15 mW so voi vectorless 102.96 mW.

### 2026-09-25 Bo cong dich fetch, mot bo nhan 33x33, chan nguon macro (RTL 358cb660)

- Rang buoc: chi sua RTL khong doi CPI (hanh vi tung chu ky giu nguyen); khong kha thi thi quay ve `a0c425f8`.
- Duong fetch ASIC: dout SRAM (suon xuong) -> giai ma -> mux imm -> bo cong 32 bit `pc_f + imm` -> `pc_next`, trong nua
  chu ky. Viet lai: phan cao cua tong chi co the la `pc_hi`, `pc_hi+1`, `pc_hi-1` (tinh som tu `pc_f`); chi mot bo cong
  ngan phu thuoc `instr` (12 bit cho B, 12 + carry-select 8 cho J); chon bang AND-OR de Yosys `opt_share` khong gop lai.
  Chung minh SAT tren moi `pc_f` x moi `instr` (miter) + doi chung am. Sau CTS: nom_tt -0.788 -> +2.766 ns, +0.9 % dien
  tich cell.
- ALU co ba bo nhan 32x32 (ss, uu, su) trong mot chu ky EX; thay bang mot bo nhan co dau 33x33 (mo rong dau theo lenh),
  cung ket qua. Mo phong so voi ALU cu 20,025,600 phep, 0 sai khac, co doi chung am. FPGA: 24 -> 8 khoi nhan 9 bit, cong
  suat bo nhan 6.22 -> 1.53 mW, DM seed 2 -0.924 -> +1.340 ns.
- Chan nguon macro trong hai wrapper ASIC duoi `ifdef USE_POWER_PINS` (6 PINMISSING -> 0; netlist cong khong doi).
- `alu.v` bi sua 9 giay truoc khi buoc tong hop cua mot thi nghiem doc no; log cho thay no doc ban cu. Quy tac: khong sua
  `hdl/` khi con flow co the doc.
- Dong bang `358cb660`; chuoi xanh, Embench / CoreMark trung tham chieu (khong doi CPI).
- Run r7r8_358c: nom_tt +2.190 ns, max_tt +1.974 (lan dau dat tt o 50 MHz); ss -11.20 / -12.26 (nom / max); hold 0 vi pham
  o ca 9 goc; slew / cap tt 828 / 853; day 6.54 m; Magic DRC 0, KLayout DRC 0, LVS khop; antenna 469 net / 653 pin.
- EQY lan dau qua `combine`, roi xung dot ghep ten: sau khi lam phang model formal cua cell, net RTL thanh bi danh cua day
  noi bo cell. Them luat an ten (`rename -hide` cac day phia gate khong co trong RTL; `gold-nomatch` cho bi danh clk/PCLK);
  partition chay het lan dau 2026-09-26.
- Thi nghiem antenna tu state sau CTS: ITERS 10 + MARGIN 30 -> 429 net (slew te hon); diode heuristic > 250 um -> 124 net /
  135 pin (-74 %, diode 6,006 -> 29,499); ca hai. Thi nghiem goc ss: AREA 3 + go buffer nghen GRT tren RTL moi; gate
  cloning khong co loi (giu tat).
- Loi runner: dong `echo "$(date) ... rc=$?"` in rc cua `date`, nen moi lan chay deu bao rc=0; doc ket qua tu log flow.

### 2026-09-26 Sua co trong tam cho goc ss khong doi CPI (RTL ecf4fc03 -> d030ad12)

- ss tren r7r8_358c: 2,820 endpoint truot, 70 % xuat phat tu `d_req_addr`; xau nhat -12.26 ns (result_src_w -> mux ghi
  nguoc -> forwarding -> ALU -> d_req_addr). Quyet dinh: chi sua co trong tam, khong doi CPI.
- Thanh ghi hoa giai ma (`scripts/apply_r9.py`): select forwarding thanh thanh ghi; giai ma kieu load one-hot va lan byte
  o tang W; `is_upper` / `is_link` o tang M. Checker tuong duong trong RTL (chi mo phong) so moi giai ma cu moi chu ky:
  447,858,365 chu ky, 0 lech. Dong bang `ecf4fc03`. Cong lint baseline bi bo sot sau lan doi RTL truoc, chay bu va phan
  loai canh bao moi (baseline 110).
- `asic/sta_query/`: STA truy van nap dung lib / SPEF / SDC cua buoc STAPostPNR, tai lap dung -7.575 ns max_ss. Duong xau
  nhat: `pc_f` -> mux valid 256:1 cua I-cache (7 ns) -> hot_hit -> stall -> retire -> chuoi ripple 20 AND -> `csr_minstret`.
- RTL: `hot_mvalid` (8 flop) giu ban sao bit valid cua dong ma moi hot entry dang giu, nen hot hit khong con doc mux 256:1;
  `(* keep *)` tren gia tri tang cua 36 bo dem perf va `minstret` (enable tre ra khoi chuoi carry: 23 -> 3 cell). Chung
  minh: k-induction cho `hot_mvalid` (256 va 8 dong) + doi chung am; equiv cho keep (1,256/1,256 va 5,281/5,281 cell)
  + doi chung am. Checker mo phong hong o cau hinh 8 dong (lat cat [-1:0]), sua rieng checker.
- Quartus ton trong `keep` tung bit nen +17 % LE; keep chi con duoi `__openlane__` (`d030ad12`), netlist ASIC trung tung
  byte.
- Ung vien so sanh hot tag theo tung entry: ABC dung lai sau hon, khong co loi, khong ap dung. Bai hoc: o cau hinh tong
  hop nay cau truc RTL chi giu duoc qua diem cat `keep`.
- PD tren RTL moi: run r10A te hon r9_ecf4 (tt +1.721 / +2.878, max_ss -9.518 / -7.575) du logic khong sau hon: bien dong
  PD giua cac netlist khoang 1 ns o tt va vai ns o ss, mot lan chay khong du phan dinh mot thay doi RTL ~2 ns. Resizer
  thay ss sai do lon (muc 9 "Uoc luong RC"); 18,525 buffer hold do margin 0.1 ns (muc 9 "Buffer hold"); setup truoc hold
  (`PL_RESIZER_FIX_HOLD_FIRST false`) +0.25 ns tt / +0.7 ns ss; setup margin 2.0 +0.41 / +0.52; dem day dai giam slew /
  cap 31 / 58 % nhung hai timing.
- EQY trong r10A: partition xong lan dau, roi `make: command not found` (nix-shell `--pure` cua OpenLane khong co make):
  `asic/run_pd_mk.sh` them GNU make vao PATH. Pha chung minh `-j 8` bi OOM; them `memory_map`. Python cua EQY lai crash
  (loi may).
- Tra cuu nguon ngoai: OpenRAM issue #298 (max_transition 0.04 ns), dynamatic PR #42 (dout suon xuong; doc+ghi cung dia
  chi khong xac dinh; wrapper du an da chan hoac khong the xay ra), Liberty chi co TT cho macro dang dung, README
  OpenROAD (setup truoc hold), ORFS #3969 (uoc luong RC). Chi tiet o muc 9.
- Bang chung loi may moi: phep thu shlex (`asic/parse_ids_probe.py`) hong trong WSL ca tren file tong hop hop le, Windows
  64/64 sach tren moi logical CPU; WHEA ID 19 parity loi noi CPU APIC 33 (muc 9 "Loi may").

### 2026-09-26 RTL cuoi cua ban 8 KiB-RAM (e21ef330 -> 8b163675)

- Sau khi thanh ghi hoa giai ma, DM_VC4 vuot 20,000 LE (20,002 .. 20,077): chon one-hot AND-OR khong dong goi duoc vao LUT4.
  Ban FPGA dung select ma hoa (`e21ef330`, -145 LE, DM_VC4 19,834 .. 19,893), chung minh bang nhau bang k-induction.
- ABC `fraig_restore` cham benh ly (~1 gio) tren netlist ASIC cua dang ma hoa; ASIC giu dang one-hot duoi `__openlane__`,
  FPGA dung dang ma hoa. Netlist ASIC trung tung byte run r10A. Dong bang `8b163675` (RTL cua ban ky ten 8 KiB-RAM);
  chuoi xanh; Quartus 16/16 fit x 2 luot trung tung truong.
- Quy tac moi trong ngay (20,000 LE la muc tieu mem, chay lai loi may ngau nhien, don workspace bat buoc, quy uoc bao cao
  post-PD): `QUY_TRINH.md`. Don 47 run loi thoi: muc 10.

## 4. 2026-09-26 .. 2026-09-28: ky ten DM 8 KiB-RAM

### 2026-09-26 Chon cau hinh PD cho RTL 8b163675 va chay kep

- Ba mau mat do placement tren cung netlist (diode heuristic > 250 um, GRT hold margin 0.1, setup truoc hold, setup margin
  2.0): density 38 / 40 / 42. Quy tac chon ghi truoc: (1) tt WNS xau nhat qua cac goc RC (max_tt), (2) max_ss, (3) dien
  tich / cong suat. Chon 42 (`config_FINAL.json`): max_tt +1.960, max_ss -8.335. Dai bien dong do placement: tt 0.25 ns,
  max_ss 1.26 ns.
- Ba lan chay doc lap (mau 42, final_A, final_B) trung moi chi so STAPostPNR va trung hash netlist / DEF.

### 2026-09-27 Ban ky ten 8 KiB-RAM dau tien (final_A / final_B)

- Sign-off: Magic DRC 0, KLayout DRC 0, XOR 0, route DRC 0, overlap 0, LVS sach, IR drop 0.43 mV, hold 0 vi pham o 9 goc.
  Setup nom_tt +2.112 / max_tt +1.960 ns; nom_ss -7.436 / max_ss -8.335. Antenna 140 net / 159 pin. Cell chuan 1.453 mm2
  / 212,196 cell. Metric `power__total` cua flow (115.73 mW) la goc max_ff; vectorless nom_tt 102.24 mW; theo hoat dong
  111.03-116.02 mW.
- EQY: gold giu bus, netlist tach bit nen gan nhu khong ten nao khop (169); them `splitnets` -> 21,116 ten chung. EQY
  trong flow chet o `read_ids` (loi may). Ban va tokenizer (`asic/eqy-local/fast_ids.py`) khong bao gio duoc flow dung vi
  wrapper nix cua `openlane` dat `eqy` goc len dau PATH. EQY chay doc lap: 795/876 partition PASS; ba nguyen nhan do duoc,
  khong phai loi thiet ke (muc 9 "EQY va LEC").
- Chung minh rieng buoc `fsm` (4 FSM, 36,303 `$equiv`, co doi chung am). Kiem tra tuan tu bang ABC (`asic/equiv/sec/`,
  cat 12 SRAM, reset ep o chu ky 0): tuong duong co gioi han 19 chu ky, doi chung am bat duoc o frame 0 va 19; khong gioi
  han: UNDECIDED.
- LEC anh xa thanh ghi (`asic/equiv/lec/`): chuoi RTL+fsm == N1 (truoc ABC) == netlist cuoi, 19,881 output, 0 phan vi
  du. 235 flop chi co o gold duoc chung minh hang bang SAT (lay mau ngau nhien da xep nham mot flop); ban sao do
  `opt_merge` duoc trich RTL va tu kiem; bat bien one-hot cua 4 FSM duoc chung minh. 34 output cuoi (bo nhan 33x33) dong bang
  viet lai nguoc dai so tren Z/2^64 (`macc_alg.py`, 1,128 don thuc, ~2 s), noi bang `&cec` sau khi chup mang muc tu
  dung cach nhom cua synthesis (`techmap -max_iter 1`), 5 techmap cell kiem bang SAT, co doi chung am, moi buoc chay hai lan
  trung hash. Nguyen nhan SAT khong dong duoc: `maccmap` nhom tich rieng phan theo trang thai tien trinh Yosys (40 % nut ben
  trong khong co doi tac). `&acec` bao "NOT EQUIVALENT" sai hai lan: chi tin khi no bao equivalent.
- Golden snapshot v1 `E:/Projects/RISCV-research_GOLDEN_20260927` (19,373 file; hard link cho artefact bat bien).
- Bao cao ban giao: `results/FINAL_METRICS.md` (nay gop vao `RESULTS.md`).

### 2026-09-27 Antenna sau detailed routing, DRV, goc ss; ban ky ten final3

- Antenna 140 net: 100 % la PAR tren met1-met3. OpenLane 2.3.10 chi sua antenna tren global route. Thi nghiem:
  `repair_antennas` chay duoc tren routing chi tiet, `detailed_route` bo sung hoi tu ve 0 DRC; 140 -> 1 net. Them vao
  openlane-local (mac dinh tat): `DRT_ANTENNA_REPAIR_ITERS` / `DRT_ANTENNA_REPAIR_MARGIN` va vong sua trong `drt.tcl`.
- DRV: 3,276 / 3,277 vi pham fanout du lieu chi ton tai vi diode heuristic duoc tinh la tai (fanout that <= 8); slew o
  chan vao SRAM la gioi han Liberty (muc 9 "Liberty OpenRAM"); cap o 738 driver cell chuan va 106 dout SRAM.
- Uoc luong RC cua resizer thap hon RCX 1.93-2.37x (muc 9 "Uoc luong RC"); khai bao `LAYERS_RC` trong openlane-local.
  Phan ra goc ss: muc 9 "Goc ss".
- Thi nghiem tu trang thai final_A: (1) bo diode heuristic + sua antenna sau DRT: antenna 0/0, 1.400 mm2 / 192.0k cell
  (-3.6 %), timing nhu final_A, hold +0.030 ns; (2) them `LAYERS_RC` k=2: slew 757 -> 201, cap 807 -> 406, nhung tt giam
  0.2 ns, max_ss -8.615 va 1 vi pham hold; (3) them cap margin: hold +0.082, tt +1.755; (4) (2) + GRT hold 0.15: 2 vi pham
  hold. Ca hai buoc global placement timing-driven doc `set_rc.tcl`, nen `LAYERS_RC` doi placement tu buoc 23.
- Full flow co `LAYERS_RC` (final2_A): nom_ss -8.973 / max_ss -9.518 va 3 vi pham hold max_ff: loai.
- `config_FINAL3.json` = `config_FINAL` + bo diode heuristic + sua antenna sau DRT (5 vong, margin 10) + script EQY co
  `splitnets`, khong `LAYERS_RC`. Chay kep final3_A / final3_B: 302 chi so trung, netlist cuoi `326cc257`, DEF `2f31dfab`.
  Antenna 0/0, cell chuan 1.400 mm2 / 192,005 cell, nom_tt +2.086 / max_tt +1.960, nom_ss -7.413 / max_ss -8.311, hold 0
  vi pham (+0.030 max_ff). LEC buoc N1 == netlist chay tren ca hai (equivalent). GLS 12/12; cong suat theo hoat dong
  110.61-115.43 mW, vectorless 102.05 mW, EPI 2,379-3,637 pJ. final3_B can chay lai tu buoc 1 mot lan va tiep tuc hai lan
  sau crash ngau nhien (ResizerTimingPostCTS, DetailedRouting, CellFrequencyTables). Day la ban ky ten 8 KiB-RAM
  (`RESULTS.md`).
- EQY trong flow vao toi pha chung minh roi chet vi `grep: command not found` (nix `--pure`); launcher them grep.
- Sua bao cao: "view ASIC trung ca 33 truong" sai; `mcycle` / `i_wait` / `d_wait` cua view ASIC thap hon, CPI chip 1.2755.
  Cot EPI dung CPI view FPGA nen lech toi 12 %; da sua `asic/gls/power_csv.py` (muc 9 "View ASIC va view FPGA").
- Golden snapshot v2 `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928` (22,656 file, sha256 tung file, `--diff` /
  `--restore`). Ban v1 hard-link ca `transcript` va vsim da ghi de tai cho; v2 chi hard-link artefact bat bien.
- Don dep 2026-09-27 va 2026-09-28: muc 10.

## 5. 2026-09-28 .. 2026-09-30: thu nghiem sau ky ten 8 KiB-RAM

### 2026-09-28 Thu nghiem tren ban ky ten final3 (golden giu nguyen)

- Quy tac tu day: chup golden truoc moi thay doi; moi thi nghiem chay tag moi, khong resume vao run da ky ten.
- EQY goc tren netlist final3 (grep tren PATH): 10 partition chung minh, roi FAIL o `LCD_EN` (FSM ma hoa lai). Cong cu EQY
  goc khong the qua tren thiet ke nay; tuong duong van do chuoi LEC chung minh (muc 9 "EQY va LEC").
- Tu trang thai sau global placement cua final3_A: gioi han day 800 um -> slew / cap nom_tt 536 / 439 nhung 1 vi pham hold;
  `LAYERS_RC` k=2 chi trong `repair_design` (bien moi `LAYERS_RC_SCOPE`) -> 213 / 402, +4.1 % dien tich cell, timing giu.
- Dinh chinh: vi pham slew o chan SRAM khong phai "khong the sua": chi addr0 / addr1 / wmask0 co gioi han 0.04 ns, va day la
  so do 10-90 % (bang 0.030 ns theo quy uoc 20-80 % cua thu vien cell). buf_8 chi dat neu cach chan <= ~8 um; halo cat row
  10 um giu buffer >= 12 um nen con 44-70 chan vuot 0.1-5.6 ps (muc 9 "Liberty OpenRAM").
- Hai buoc moi trong openlane-local (mac dinh tat): `OpenROAD.MacroPinBuffers` (buf_8 tai chan vao macro, buf_4 tai chan ra
  dai, tuy chon buffer tang truoc) va `OpenROAD.PostRouteHoldECO` (trich RCX tren routing that, `repair_timing -hold`,
  DRT tang dan, vong antenna). Loi tat dinh da sua: thieu bien RCX; `global_route -start_incremental` segfault trong tien
  trinh moi; `detailed_placement` lat lai huong moi cell da route (giu cell cu FIRM); access point cua master cu sau khi
  doi kich thuoc (chay `pin_access` truoc GRT). Clock goc: day 2.5 mm khong buffer vi uoc luong RC thap -> 
  `CTS_CLK_MAX_WIRE_LENGTH 800`.
- Ket qua (STAPostPNR): them buffer chan macro + clock goc + hold ECO: slew nom_tt 80, hold +0.061, nhung tt giam 0.5 ns
  (cay clock doi skew co loi cua duong nua chu ky). AREA 3 + go buffer: max_ss -8.339 (khong doi), day +22 %, DRV x5,
  30 vi pham hold: AREA 3 khong phai loi giai goc ss. `repair_design` sau route tren SPEF: max_ss -12 .. -13 ns (doi kich
  thuoc hang nghin cell), giu tat. Buffer tang truoc: slew 47 (44 chan SRAM).
- Vi pham cap song sot vi `repair_design` dat repeater theo cay Steiner ngan hon route that, va diode antenna chen sau.
- Thu RTL cycle-exact tren ban sao (khong vao `hdl/`): so sanh hot tag song song, ban sao thanh ghi PC cho I-cache, bo so
  sanh nhanh dang prefix, mux forwarding rieng cho bo so sanh. PD te hon (max_ss -9.930, nom_tt +1.194): khong port. Bien
  the nhan 2 tang (+1.03 % chu ky) khong chay PD. STA what-if: dong max_ss o 50 MHz can pipeline moi (muc 9 "Goc ss").
- `asic/run_resume_retry.sh`: chi xet phan `error.log` cua lan thu hien tai (OpenLane ghi noi qua cac lan resume) va xet
  ma tra ve, vi crash "unexpected error" khong ghi gi vao `error.log`.

### 2026-09-30 Thac dien tich va bien hold

- Thac dien tich cell (DEF sau fill + liberty, tong khop metric flow): final3 1,399,590 um2, trong do buffer hold 189,693
  (19,019 cell, 13.6 %); ban 16 KiB-RAM (thi nghiem E10) 1,544,690 um2, chenh +145,100 chu yeu do buffer "wire" cua
  `repair_design` (+84,449, do `LAYERS_RC` k=2) va tap (+22,982, die lon hon 31 %).
- Histogram hold slack truoc resizer: ~17,000 endpoint duoi 0.1 ns nhung chi ~50 vi pham that; bien 0.1 ns sinh ra
  18-19k buffer hold (muc 9 "Buffer hold").
- Danh gia lai final3 voi bien hold 0.02 + hold ECO tren RCX: cell 1.3996 -> 1.2153 mm2 (-13.2 %), hold sach, nhung max_ss
  -10.930 (xau 2.6 ns): khong nang golden. Bien the thu hai (final3 + mat do 55 + bien hold 0.03 / ECO 0.02 + cum CTS 8,
  xong 2026-09-30 12:30 UTC, truoc day chua ghi o dau): nom_tt +2.442, max_tt +2.312, nom_ss -8.248, max_ss -9.023 ns,
  hold +0.021 (0 vi pham), cell 1.2835 mm2 (180,453 cell), slew / cap nom_tt 1,250 / 706, antenna 0, route DRC 0: khong
  nang golden (max_ss xau hon final3 0.71 ns).
- Quy tac moi trong ngay (DRV xep sau dien tich va setup/hold; giao thuc nang golden): `QUY_TRINH.md`.

## 6. 2026-09-29 .. 2026-10-02: RAM chinh 16 KiB, Embench goc, ky ten DM tren luoi 3665x2900

### 2026-09-29 RAM chinh 8 -> 16 KiB va bo Embench-IoT goc

- Gioi han so bai Embench chay duoc la RAM thong nhat (code + du lieu + stack 1 KiB), khong phai cache. Do 19 kernel
  Embench-IoT goc (commit 09c2ed8c): 8 KiB vua 8 bai, 16 KiB 14, 32 KiB 18, 64 KiB 19. Chon 16 KiB (ASIC 8 macro 2 KB; 32 KiB
  can 16 macro). Sau khi gan khung bao ket qua (~2 KB), 12 bai vua: aha-mont64, crc32, depthconv, edn, huffbench,
  matmult-int, md5sum, nettle-sha256, slre, statemate, tarfind, ud (nettle-aes va sglib-combined vuot 15 KiB).
- Danh sach thay doi day du (chuyen nguyen tu `RAM16K_CHANGES.md`):

  Thay doi RTL (dong bang ban dau `535ec0f9`):

  | File | Thay doi |
  |---|---|
  | `hdl/soc_top.v` | `IMEM_DEPTH`/`DMEM_DEPTH` mac dinh 1024 -> **2048** |
  | `hdl/board/de2_115_top.v` | `IMEM_DEPTH`/`DMEM_DEPTH` mac dinh 1024 -> **2048** (ban FPGA DE2-115) |
  | `hdl/axi/axi_ram_32.v` | `DEPTH_WORDS` mac dinh 2048 -> **4096** (soc_top van truyen tong IMEM+DMEM) |
  | `asic/soc_dm_4kb/soc_asic_top.v` | `.IMEM_DEPTH(2048)`, `.DMEM_DEPTH(2048)` |
  | `asic/soc_dm_4kb/axi_ram_32_asic_macro.v` | RAM ASIC: so bank = `DEPTH_WORDS/512` (**4 -> 8** macro `sky130_sram_2kbyte_1rw1r_32x512_8`); do rong chon bank/dia chi word suy ra tu tham so (`BANK_BITS`, `WORD_BITS`); kiem tra luc elaborate rang do sau la boi luy thua 2 cua 512; khoi nap chuong trinh cho mo phong ASIC view liet ke 8 bank va dung mo phong neu so bank khac 8. FSM doc/ghi giu nguyen. |

  Khong doi: cache (tag lay tu dia chi 32 bit day du), bo giai ma dia chi (cua so cacheable 64 KiB da chua
  16 KiB), pipeline, CPI.

  Thay doi phan mem va cong cu:

  | File | Thay doi |
  |---|---|
  | `sw/link.ld` | `LENGTH = 8K` -> **16K**; stack (1 KiB) doi tu 0x1C00-0x1FFF len **0x3C00-0x3FFF** |
  | `sw/platform.h` | `RAM_SIZE_BYTES` 8192 -> **16384** |
  | `sw/fix_hex.py` | `--ram-bytes` mac dinh 8192 -> 16384 |
  | `sw/Makefile` | bien `RAM_BYTES ?= 16384` / `RAM_WORDS`, thay cho hang 8192 / 2048 o `rv32hex` va `install_hex` |
  | `scripts/fpga/hex_to_mif.py` | `--depth` mac dinh 2048 -> 4096 |
  | `hdl/riscv_full.hex`, `hdl/riscv_full_byte{0..3}.mif` | sinh lai (cachesweep) voi do sau 4096 |
  | `scripts/rtl_manifest.py` | manifest nay phu ca `sw/` (truoc do chi quet `sw_baremetal/`, ten cu, nen nguon firmware khong nam trong manifest); bo qua san pham build `benchmark*.hex` |
  | `scripts/run_ablation.py` | them `--fw-dir` (mac dinh `fw`) |
  | `sw/main_ramsweep.c`, `sw/embench_ramsweep.{c,h}` | **test moi** `ramsweep`: ghi/doc lai moi word trong cua RAM (word, byte, halfword) de phu ca 8 bank cua RAM ASIC; khong phai benchmark |

  Thay doi kiem thu:

  | File | Thay doi |
  |---|---|
  | `tb/benchmark_snapshot_tb.sv` | `IMEM_DEPTH`/`DMEM_DEPTH` mac dinh 2048 |
  | `verification/uvm/tb/tb_soc_top.sv` | `.IMEM_DEPTH(2048)`, `.DMEM_DEPTH(2048)` |
  | `verification/uvm/env/core_cfg.sv`, `native_mem_model.sv`, `test/core_smoke_test.sv`, `test/core_random_test.sv` | kich thuoc RAM cua SoC 8192 -> 16384 byte |

  Giu nguyen co chu y: cac test muc AXI (`axi_common.sv`, `axi_smoke_test.sv`) dung mo hinh slave rieng
  cua UVM, khong phai RAM cua SoC; cac testbench don vi tu chon do sau rieng (`mmio_bypass_tb`,
  `predictor_axi_tb`, `soc_integration_tb`, `directed_isa_tb`).

  Giu nguyen co chu y: cac test muc AXI cua UVM (mo hinh slave rieng) va cac testbench don vi tu chon do sau RAM.
- Bo Embench goc trong `sw/embench_upstream/` (`make MODE=upstream BENCH=<bai> SCALE=<n>`, `fw/up_<bai>.hex`). Thay doi
  duy nhat trong nguon goc: hook `LOCAL_SCALE_FACTOR_OVERRIDE`. Khung bao ket qua do du an viet, khong chep `support/`
  (GPL-3.0) cua Embench; 9/12 bai GPL-3.0 nen chi o cay nghien cuu. SCALE moi bai cho ~130k-350k chu ky mot lan do, sau mot
  vong lam nong; khong phai diem Embench chinh thuc.
- Test moi `ramsweep` (ghi / doc lai moi word trong cua RAM bang word / byte / halfword, phu ca 8 bank cua RAM ASIC).
- Xac minh `scripts/run_fullchain_r14.sh`, luot 3 tren dong bang cuoi `3ea52396`: 0 loi; Embench va CoreMark trung tung byte
  thiet ke 8 KiB (RTL moi + firmware cu: 48/48; firmware build lai chi khac `auipc sp,0x2` -> `0x4`); view ASIC 8 bank trung
  view ASIC 4 bank ke ca chu ky. Hai loi checker bat duoc trong luc xac minh: chi so word so voi `addr[12:2]` co dinh (sai
  moi lan ghi tren 0x2000; doi chung am: bo bit bank cao nhat thi checker bat ngay) va khoi nap ASIC view liet ke 8 bank theo
  ten (khong elaborate voi RAM 4 bank).
- Sao luu truoc thay doi: `backups/pre_ram16k_20260929/` (manifest SHA-256).

### 2026-09-29 PD DM 16 KiB-RAM tren luoi 3665 x 2900

- Floorplan: 12 macro cu giu vi tri, 4 bank RAM moi thanh cot thu 4; die 2800 x 2900 -> 3665 x 2900 um (+31 %).
- Lan dau (cau hinh thi nghiem E6): max_tt -0.162 ns. Duong tt: dout RAM (suon xuong) -> mux chon bank -> mux nap lai D-cache
  -> din D-cache, ~5 mm trong nua chu ky, 43 buf_6 lap day (~4.5 ns). Resizer bi goc ss chiem het cong suc.
- Quet knob tu trang thai sau global placement (STAPostPNR, mot lan moi bien the):

  | knob | max_tt / nom_tt | max_ss | cell chuan mm2 | ghi chu |
  |---|---|---|---:|---|
  | resizer chi tt + ff | -0.486 / -0.268 | -12.92 | 1.578 | loai |
  | cap margin 20 / 10 | +1.145 / +1.275 | -9.474 | 1.519 | |
  | + GRT cap margin 50 | +1.197 / +1.322 | -8.284 | 1.545 | slew / cap 110 / 310 |
  | + day toi da 1000 um | +1.510 / +1.654 | -8.804 | 1.545 | loai |
  | + cum CTS 8 | +1.699 / +1.800 | -8.357 | 1.541 | fanout 2,366 -> 1,379 |
  | + bien hold 0.03 / ECO 0.02 | +1.197 / +1.342 | -8.397 | 1.372 | buffer hold 18,259 -> 1,032 |
  | + mat do 55 % | +1.766 / +1.910 | -8.117 | 1.514 | tot nhat tt, ss, cong suat, day |

  Cau hinh ky ten (`config_R14_FINAL.json`) = mat do 55 + bien hold 0.03 / ECO 0.02 + cum CTS 8 tren nen GRT cap margin 50.
- Chay kep dm_grid3665x2900_r1 / _r2 (run r14F_A / r14F_B): 319 metric trung, netlist cuoi trung tung byte (`7ae150fe`).
  Sign-off sach: Magic DRC 0, KLayout DRC 0, route DRC 0, LVS 0, XOR 0, overlap 0, antenna 0, hold 0 vi pham. Setup nom_tt
  +1.894 / max_tt +1.708 ns; nom_ss -6.897 / max_ss -7.365 ns; hold xau nhat +0.021 ns. Die 10.63 mm2, cell chuan 1.3696
  mm2 / 197,878 cell, 16 macro 3.80 mm2. Cong suat vectorless nom_tt 109.15 mW; theo hoat dong 114.8-123.0 mW (TB 119.5),
  EPI 2,612-6,547 pJ; GLS 12/12. Khong nang golden so voi final3 vi la diem thiet ke khac (RAM gap doi): bao cao rieng
  (`RESULTS.md`, `results/asic_compare_dm_r14.md`).
- Phien lam viec ket thuc hai lan (2026-09-30 ~04:50 va ~23:38) va giet moi job nen (muc 9 "Job nen va ket thuc phien");
  r14F_A / r14F_B duoc resume 2026-10-02 bang `run_resume_retry.sh`.

### 2026-09-30 Bo 12 kernel tu viet; giai thich retire va minstret

- Xoa 52 file kernel do du an tu viet (git giu lich su); bo do chuan con lai = 12 kernel Embench-IoT goc + CoreMark. Anh so
  vong lap goc cho board: `fw_board/upfull_*.hex`. RTL khong doi (dau van tay `hdl/` + RTL ASIC truoc va sau trung).
- Retire vs minstret: `minstret - retire_cycles` = so chu ky co lenh retire nhung duoc tinh vao lop uu tien cao hon
  (CONTROL hoac LOAD_USE); chung minh tren 24/24 kernel (`results/a4_overlap/`).

### 2026-10-02 ACT4 va do tre ngat / chuyen ngu canh

- ACT4 (riscv-arch-test 2e655961, mo hinh tham chieu Spike): 43/43 PASS x2 (39 RV32I + 4 Zmmul), signature trung 43/43; log
  tung test trong `verification/results/act4/`. Lan truoc khong chay duoc vi file cau hinh CRLF va `$HOME` khong duoc mo rong;
  chay tu ban sao LF, file trong repo khong doi.
- Do tre ngat (FPGA view, 4 KiB, x2): vao handler 5 chu ky; ngat toi thieu tron goi 39; chuyen ngu canh day du 270 (DM) /
  292 (cac cau hinh DSE: +19 chu ky la ST_LOOKUP them cho 62 load/store). Bang hop nhat: `results/unified_metrics.md`.

## 7. 2026-09-30 .. 2026-10-06: core N-way, FAST_HIT, quet M1/M2

### 2026-09-30 Core N-way (SA4) cho phan bien M2

- `hdl/cache/{d,i}cache_nway_core.v` (WAYS 2 | 4, pseudo-LRU dang cay); CACHE_CONFIG 4 = SA4, 5 = SA2 tren core N-way (chi
  de kiem: phai trung SA2 tung truong). Nhanh cu khong doi, cau hinh 0-3 trung RTL truoc tung truong.
- Chuoi day du (lan 3, dong bang `d409b09d`): 0 FAIL; mo hinh cache doc lap EXACT 48/48 + 24/24. Quartus seed 2 x2: SA4 4 KiB
  21,821 LE (vuot 20k, +2,347 so voi SA2 4 KiB); cac diem 8 KiB tru DM va DM_DSE cung vuot 20k.
- Netlist ASIC khac tung byte (Yosys / ABC nhay voi thu tu doc); chung minh RTL truoc == RTL N-way cho chip DM (35,067
  `$equiv`, 0 chua chung minh), nen PD DM 16 KiB-RAM dai dien dung cho RTL nay. Lan kiem dau phai vuot loi lint chi so
  valid (Verilator WIDTHEXPAND).

### 2026-10-03 FAST_HIT: tra loi hit mang chinh trong ST_LOOKUP (phan bien M1)

- Tham so `CACHE_FAST_HIT` (mac dinh 0 = RTL truoc): core DSE va N-way tra loi hit mang chinh ngay trong ST_LOOKUP, bo mot
  chu ky so voi controller DM. Ap bang script (`scripts/r16_fasthit/apply_r16.py`, 34 sua, moi neo dung mot lan); chay thu
  tren ban sao: FAST_HIT=0 trung RTL truoc tung truong, FAST_HIT=1 trung moi bo dem khong phai timing.
- Chung minh: muc module 24/24 (16 tuong duong + 8 doi chung am phat hien khac biet); muc SoC cho ca ba chip (DM 35,067 /
  SA2 36,741 / DM_VC4 37,441 `$equiv`, 0 chua chung minh) sau khi doi ten `genblk1.g_dse` -> `g_dse` phia gate (lan kiem dau
  khong ghep duoc thanh ghi cache nao, bao 209 o sai va Yosys len 16 GB; da dung, log giu). Doi chung am muc SoC (SA2,
  FAST_HIT 1): 1,824 / 36,741 o chua chung minh. PD tren snapshot RTL 16 KiB-RAM dai dien dung cho RTL FAST_HIT 0.
- Test moi: do tre hit mang chinh SA2 (1 chu ky / 0 chu ky); SA2 / DM_VC4 FAST phai retire y het DM; checker moi chu ky co
  doi chung dot bien (ep `r16_word = 32'hdeadbeef` thi ca 4 checker dung mo phong). Regression them 16 run FAST (161 x2);
  latch sweep / lint them truc FAST (33 to hop). Chuoi day du 45 OK / 0 FAIL (`results/fullchain_r16.log`).
- FPGA: FAST_HIT ton +115 .. +881 LE (SA2 +456), Fmax giam toi 3.8 %; moi diem van dat 50 MHz.

### 2026-10-06 Quet thiet ke M1/M2

- Quet dung luong 256 B .. 8 KiB, line 8 / 16 / 32 B, so way 1 / 2 / 4, do sau victim 2 / 4 / 8, ca hai che do FAST_HIT, 12
  kernel Embench goc + CoreMark, moi diem chay hai lan (R15 637 dong, FAST 559 dong, p1 = p2).
- Ket qua (GM chu ky): rieng controller ton +4.33 % (256 B) .. +10.83 % (8 KiB); khi cung controller (FAST), SA2 nhanh hon
  DM_DSE o moi dung luong (-7.43 % .. -0.18 %), SA4 tuong tu, DM_VC4 cham hon (+5.99 % .. -0.01 %) vi ban sao eviction noi
  tiep voi refill. Phan du DM_DSE_fast so voi DM: +1.09 % o 256 B, 0 o 8 KiB (L0 cua D-cache va xu ly store miss). Hieu ung
  theo kernel lon ca hai chieu (o 4 KiB: nettle-sha256 +16.15 % voi SA2, statemate -8.86 %).
- Ket luan "DM thang set-associative" la ket qua cua controller. Bao cao: `results/m2/M1_M2_REPORT.md`, tra loi phan bien:
  `REVIEW_RESPONSE.md`.

## 8. 2026-09-30 .. 2026-10-07: SA2 va DM_VC4 tren ASIC, floorplan hanh lang

### 2026-09-30 Wrapper SRAM cho core DSE va SAT trong tong hop

- `asic/dse_sram/cache_dse_data_bank_sram.v` thay bank cua core DSE theo ten module, dung macro
  `sky130_sram_1kbyte_1rw1r_32x256_8`. DM_VC4 (256 set, way 0): 1 lane / macro (cong 1 doc, cong 0 ghi), 4 macro / cache. SA2
  (128 set moi way): 2 lane / macro (lane 2j hang 0-127 doc tren cong 1; lane 2j+1 hang 128-255 doc tren cong 0 khi khong
  ghi), 4 macro / cache nhu DM. Doc trong khi ghi cung chi so: chan doc lane do va giu lan doc truoc. Shadow chi mo phong so
  `rd_line` voi mo hinh bank thanh ghi moi chu ky ($fatal khi lech).
- View ASIC: 12 kernel x cfg 1, 2 x 2 luot = view FPGA tren 33 truong, shadow 0 lech; directed ISA chay tren ban sao
  testbench (ban goc tham chieu tin hieu chi co o DM).
- Tong hop: DM_VC4 giu 4 macro chet cua way 1 D-cache (Yosys khong chung minh duoc flop `refill_way` la hang; Quartus thi bo).
  openlane-local them `SYNTH_OPT_DFF_SAT` (mac dinh tat): mot luot `opt` voi SAT sau `share`; VC4 con 8 macro, DM va SA2
  gan nhu khong doi (+0.08 %, +0.22 %). Dien tich tong hop: DM 977,837 / SA2 1,051,715 (+7.6 %) / VC4 1,077,811 um2 (+10.2 %).

### 2026-10-02 SA2 va DM_VC4 tren luoi DM khong route duoc

- Knob DM (mat do 55) va mat do 42: ca hai GRT-0118. SA2: overflow 67,971, nhu cau gap doi DM, HPWL +32 %. Ban do RUDY cung
  hinh thai o ca ba thiet ke (don vao kenh giua cac hang / cot macro), cuong do p99 DM 8.8 / SA2 11.5 / VC4 11.1: diem nghen
  la suc chua kenh, khong phai mat do.
- Luoi rong (x1.15, 4211 x 3331 = 14.03 mm2): SA2 route duoc nhung nom_tt -17.573 ns o STAMidPNR-3 (than clock dai -> skew
  lon -> 5,884 cell tre hold tren duong du lieu, `GRT_RESIZER_ALLOW_SETUP_VIOS` cho phep pha setup); DM_VC4 overflow 34,086.
- Chan doan DM_VC4: macro OpenRAM chan met1-met4 (chi met5 ngang di qua), moi tuyen doc giua cac hang macro phai qua khe;
  hai cum flop tag (5,120 flop moi cum) nam o nga ba kenh. Day dai ben trong cum tag: DM 231 mm, SA2 1,142 mm, VC4 1,516 mm.
  Nguyen nhan cau truc (RTL, PD khong sua): core DSE doc valid / tag o hai chi so (`live_index` va `request_index`), tag RAM
  cua DM chi co mot cong doc. Chan macro: `dout1` canh tren; `din0` / `dout0` / `wmask0` / `addr0` canh duoi.

### 2026-10-03 Floorplan vong, tang va hanh lang

- Vong (16 macro o bien, 3200 x 3190 = 10.21 mm2): ca ba route duoc khi sang loc, nhung DM_VC4 nom_tt -1.093 ns sau sua CTS.
  Duong nua chu ky refill: core DSE ghi tung beat AXI tu dout cua RAM thang vao din cua macro lane trong cung nua chu ky
  (55 repeater, 8.02 ns tren cot 1.9 mm); DM gom refill vao thanh ghi truoc. Mau thuan: RAM va macro lane phai gan nhau,
  macro cache phai gan CPU, cum tag can vung thoang.
- Tang (RAM A / kenh 220 / RAM B / D$ / I$ / dai logic 1008 um, 3260 x 3400): DM_VC4 nom_tt +1.809 (tot nhat) nhung GRT
  overflow 233,074 (hai hang cache thanh buc tuong).
- Ho hanh lang (U2): hai hang RAM duoi cung, 4 lane moi cache thanh cum 2 x 2 ngay tren RAM B (I$ trai, D$ phai), hanh lang
  trung tam ~1 mm. DM_VC4 3400 x 3400: nom_tt +1.724, overflow 1,560 (15 vong). Xoay macro 90 do: luoi nguon hong (chan nguon
  met4 nam ngang). Hanh lang < ~1,057 um that bai (957 um: 51,831 o 50 vong).
- Sang loc voi GRT 15 vong xep hang sai (pha "Extra Run for hard benchmark" hon loan gan nguong); tu ngay 2026-10-06 sang
  loc dung 50 vong nhu flow that (`fp_tools/screen_floorplan.sh`, `fp_tools/screen_grt.sh`).
- May ao WSL tat 2026-10-03 08:22 (nhieu kha nang qua tai bo nho: DRT + resizer + 2 sang loc + 2 kiem hinh thuc muc SoC song
  song). Tu do kiem hinh thuc muc SoC chay mot minh.
- Yeu cau sign-off sach 100 % (0 DRC, 0 LVS, 0 antenna, setup / hold duong) va khong chay mu: flow co cong va dung som
  (`asic/run_gated_pd.sh`, `asic/drt_watch.sh`, `asic/fp_tools/gate_check.py`; nguong o `QUY_TRINH.md` muc D).

### 2026-10-06 Sang loc hop nhat va hai phuong an floorplan

- SA2 nghen o khe giua hai hang macro D$: SA2 dung ca cong 1 (dout1 canh tren) va bus cong 0 (canh duoi). Lat hang tren
  (FS) dua bus cong 0 cua hang tren len dai logic: 3,588 -> 1,530; them khe 220 um giua hai hang: 0 (3400 x 3400, 3250, 3100).
- DM_VC4 voi hang tren lat: 3400 -> 0, 3250 -> 4,872, 3175 -> 24,603, 3100 -> 10,347; huong N o 11.05 mm2 dao dong khong don
  dieu theo khe (120 / 170 / 220 um: 0 / 2,427 / 1,303), tuc kich thuoc nay nam o bien.
- Hai ung vien (GRT 50 vong, setup nom_tt o STAMidPNR-2): corr3400x3325_f220 (11.305 mm2) SA2 0 / DM_VC4 43 / DM 0, +1.348 /
  +1.420 / +1.803 ns; corr3400x3400_f220 (11.56 mm2) 0 / 0 / 0, +1.735 / +1.372 / +1.793 ns; hold ~+0.18 ns. Bang day du:
  `asic/fp_explore/fp_summary_20261006.md`; proxy dinh tuyen: `asic/fp_explore/route_proxy.txt`.
- O 11.305 mm2: core 11.137 mm2, macro 3.802 mm2 (34 %), cell chuan 1.32 / 1.44 / 1.47 mm2, tuc ~20 % phan core ngoai macro:
  thiet ke bi gioi han boi dinh tuyen qua hanh lang (macro chan met1-met4), khong boi cho dat cell. Nho hon nua thi phai doi
  hinh hoc macro / vi tri chan hoac cau truc truy cap tag cua core DSE (RTL), ngoai pham vi PD.
- Quyet dinh: chay ca hai phuong an cho ca ba thiet ke (6 flow, toi da 3 dong thoi). Pham vi timing: setup >= 0 o tt va ff,
  ss chi bao cao; hold >= 0 o moi goc; DRC / LVS / antenna = 0. Ban DM 10.63 mm2 da ky ten giu lam tham chieu lich su.

### 2026-10-06 .. 2026-10-07 Lo 6 flow hop nhat

- Cong grt_overflow / cts_tt_slack (sau GRT, STAMidPNR-2): DM_VC4 A 43 / +1.420 va B 0 / +1.372; SA2 A 0 / +1.348 va B 0 /
  +1.735; DM A 0 / +2.063 va B 0 / +2.150. Tat ca dat.
- Cong grt_repair_overflow / grt_tt_slack (STAMidPNR-3): SA2 B +0.764, DM A +1.508, DM B +1.573 dat. SA2 A +0.234, duoi bien
  du phong +0.3 ma setup van duong: cho chay tiep co dieu kien, cong sign-off giu nguyen.
- drt_convergence: gioi han dau tien (lay tu mot run DM) dung SA2 B o vong 6 trong khi no hoi tu deu (150,872 -> 86,950 ->
  81,050 -> 26,446 -> 13,449 -> 9,414 -> 6,906, ti le 0.70-0.73 / vong). Hieu chinh lai khi khong co DRT nao chay (QUY_TRINH
  muc D); gioi han moi van dung run SA2 luoi rong that bai (48,353 o vong 5).
- Cong grt_repair_overflow doc nham lan route lai tang dan cua RepairDesignPostGRT; nay doc lan route lai tu dau ben trong
  RepairAntennas (gia tri cuoi cua moi bao cao sau GRT, `post_grt_overflows()` trong `gate_check.py`).
- DM_VC4: lan route lai tu dau trong RepairAntennas cho overflow 19,114 (A) / 11,485 (B), so voi 0 cua DM va SA2 va gioi han
  2,000; sua DRV sau GRT chen +4,643 buffer (SA2 +4,349 / +4,416, DM +2,194). DM_VC4 nam o bien dinh tuyen tren ca hai
  floorplan: chua co ban DM_VC4 sach. Ca hai run dang o RepairAntennas khi phien ket thuc, khong chay lai; phuong an (die
  rieng cho DM_VC4, sua DRV sau GRT nhe hon, mat do thap hon) can chu du an quyet.
- DM A (dm_corr3400x3325_f220_r1): sign-off sach toi Checker.LVS (DRC / LVS / XOR / overlap / antenna 0, setup >= 0 o tt va ff,
  hold >= 0 o moi goc; ss: max -8.754, nom -8.292, min -7.871 ns). EQY bi OOM killer giet (13 GB, canh hai DRT), chua chay lai.
- 2026-10-07 01:17 phien ket thuc (het usage), moi tien trinh cua batch bi dung (SIGTERM). 08:44 tiep tuc: SA2 A va SA2 B
  detailed routing, DM B tu STAPostPNR (`asic/run_gated_resume.sh`; phan sign-off dung o Checker.LVS, EQY chay rieng sau).
- 09:35: phan Magic cua DM B chay canh hai DRT cua SA2, swap 7.6 / 8 GB. Lenh dung phan sign-off cua DM B (de bao ve hai DRT)
  bi chinh sach quyen cua cong cu tu choi; cho chu du an quyet. Bai hoc: phan sign-off (Magic / Netgen den ~8 GB) cung phai
  cho bo nho, khong chi detailed routing.
- DM B (dm_corr3400x3400_f220_r1): sign-off sach 04:23 (ss: max -10.043, nom -9.517, min -9.007 ns). drt_convergence dung
  SA2 B o vong 23 (106 vi pham, luat dung tre) va SA2 A o vong 30 (173 > 150).

### 2026-10-07 SA2 hoi tu sau 54 vong; DM_VC4 tren die rong hon van that bai; so sanh PPA tach rieng

- Quyet dinh cua chu du an (sang 2026-10-07): SA2 B chay lai detailed routing du 64 vong, bao cao DRC moi 5 vong
  (`config_u2fg_drcdiag.json`; bien moi `DRT_DRC_REPORT_ITER_STEP` trong openlane-local), khong co watchdog; DM_VC4 sang loc
  die rieng rong hon.
- SA2 B (vong: vi pham): 5: 9,414; 10: 1,424; 20: 115; 30: 72; 40: 70 (dung yen tu 28 den 44); 45: 54; 50: 39; 52: 27;
  53: 5; 54: 0. Detailed routing chinh xong sau 5 gio 43 phut. Tu vong 25 moi vi pham nam trong mot vung ~640 x 310 um cua
  hanh lang (x 1390-2028, y 1847-2156), o vong 45 thu lai con 22 x 66 um (x 1991-2013, y 1924-1990): short / spacing met1
  va met2 quanh mot cay buffer fanout (59 buffer `fanout` trong 207 cell truoc buoc sua DRV sau GRT), buffer lon (buf_12,
  nor2_8) va flop `replace_way` cua D$; buoc sua DRV sau GRT them 15 cell vao o nay. Sau do sua antenna sau detailed
  routing: 833 net / 997 chan -> chen 1,576 diode, route lai bat dau tu 48,176 vi pham.
- Nguong drt_convergence cu se dung run nay o vong 23; hieu chinh lai (QUY_TRINH muc D): 30 > 400, 40 > 200, 50 > 100, luat
  dung tre chi khi con > 300 vi pham.
- DM_VC4 tren die rong hon (corr3600x3400_f220 12.24 mm2, hanh lang 1,257 um; corr3800x3400_f220 12.92 mm2, 1,457 um):
  qua grt_overflow (0 / 0, setup nom_tt +1.168 / +1.703 ns). Overflow sau GRT: route lai cua RepairDesignPostGRT 2,375 /
  4,251; route lai tu dau trong RepairAntennas 2,295 -> 5,774 / 4,224 -> 10,627; ResizerTimingPostGRT 5,818 (gioi han
  2,000). Die rong hon khong giup, 3800 con te hon 3600.
- Nguyen nhan (ban do nhu cau tu `after_grt.guide` bang `asic/fp_tools/guide_demand.py`, tong track x gcell theo lop; cell
  va net bang `region_cells.py` / `net_probe.py`; tren corr3600x3400_f220 truoc va sau sua DRV sau GRT):
  - buoc sua DRV sau GRT chay voi `LAYERS_RC` (tu dien day ~2 lan gia tri LEF, pham vi repair_design) va
    `GRT_DESIGN_REPAIR_MAX_CAP_PCT` 50 (mac dinh cua OpenLane la 10): 1,270 vi pham slew va 11,363 vi pham cap, chen 4,671
    buffer (`wire` +2,808, `max_cap` +1,863); SA2 +4,416, DM +2,213;
  - cac buffer roi vao hai cum tag giua hanh lang (x ~1450-2300, y ~1550-2000), noi nhu cau met1-met4 da ~82 % so track danh
    dinh (chua tru dieu chinh GRT 20 % va luoi nguon) truoc khi sua; vung 850 x 450 um nay co 17,992 cell (3,757 flop, 3,809
    mux2, 5,747 buffer do resizer chen);
  - GRT phai di vong: nhu cau met1 +31 %, met2 +25 %, met3 +19 %; 6,163 net moi dai 528,975 track x gcell; vd. mot net chon
    mux co moi chan trong x 1732-1762 um bi dan toi x 3554 um;
  - truoc khi sua, DM_VC4 da can nhieu day hon SA2 tren cung die (corr3400x3400_f220): met1 +24 %, met2 +22 %, met3 +68 %,
    met4 +20 %; diem nong moi ngay tren hang macro D$ phia tren (x 2208-2539, y 2374-2539: SA2 ~6, DM_VC4 ~175);
  - 14,503 buffer `fanout` (18 % so cell logic) den tu `MAX_FANOUT_CONSTRAINT` 8 o buoc sua DRV dau tien (2,520 net vi pham).
- Quyet dinh cua chu du an (toi 2026-10-07): DM khoa o dm_grid3665x2900_r1 / _r2 (10.63 mm2, cap margin 50); SA2 va DM_VC4
  toi uu rieng theo PPA (die nho nhat con route duoc, it buffer / day nhat); gioi han cung va bang so lieu cuoi o QUY_TRINH
  muc A. DM tren hai floorplan hanh lang chi con la du lieu doi chung cung die.
- Sang loc moi (tach run bang `asic/branch_run.sh`; chi pha P2 bang `run_gated_resume.sh ... p2`, P1 con lai + P2 bang
  `asic/run_gated_branch.sh`; giu run sau cong p2):
  - cap margin 50 -> 20 (tach sau GRT): vc4_corr3400x3400_f220_capm20_r1, sa2_corr3400x3400_f220_capm20_r1
    (vc4_corr3600x3400_f220_capm20_r1 bo truoc khi chay: huong die rong da dong, nguyen tac PPA can die nho nhat);
  - them max fanout 8 -> 16 (tach truoc buoc sua DRV dau tien; `MAX_FANOUT_CONSTRAINT` chi tac dong tu RepairDesignPostGPL,
    cac buoc truoc chi dung no de bao cao STA): vc4_corr3400x3400_f220_capm20_fo16_r1, sa2_corr3400x3400_f220_capm20_fo16_r1.
- SA2 max fanout 16 + cap margin 20 (sa2_corr3400x3400_f220_capm20_fo16_r1) qua p1: so voi sa2_corr3400x3400_f220_r1, buoc
  sua DRV dau tien chen 13,508 buffer thay vi 19,987 (fanout 14,268 -> 5,613, wire 4,814 -> 5,778, max_cap 880 -> 2,083; tong
  buffer do resizer chen sau GRT 24,304 -> 17,791, -27 %), dien tich cell chuan 1,443,000 -> 1,427,050 um2 (-1.1 %), GRT
  22.28 -> 21.28 % (overflow 0), setup nom_tt +1.735 -> +1.754 ns, hold +0.182. Hai run fanout 8 + cap 20 dang cho
  (vc4_corr3400x3400_f220_capm20_r1, sa2_corr3400x3400_f220_capm20_r1) bi bo truoc khi chay vi bi bien the fanout 16 ap dao.
- SA2 cap 20 + fanout 16 qua p2: buoc sua DRV sau GRT chi con 4,208 vi pham cap (11,274 voi cap 50) va chen 477 buffer
  (4,416); moi lan GRT sau do overflow 0, 21.25 -> 21.55 % (cap 50 + fanout 8: 22.23 -> 22.95 %); cell chuan o STAMidPNR-3
  1,473,170 um2 / 213,514 cell (cap 50 + fanout 8: 1,524,290 / 223,278, -3.4 %); setup nom_tt +0.671 (+0.764), hold +0.159.
  Detailed routing chay rieng, giu run sau do (`run_gated_branch.sh ... drt`); phan sign-off chi chay khi run duoc chon.
- SA2 10.54 mm2 (sa2_corr3400x3100_f220_capm20_fo16_r1): p1 dat (overflow 0, setup nom_tt +1.521, GRT 25.83 % so voi
  21.28 % o 11.56 mm2) nhung TRUOT p2: overflow 17, setup nom_tt -1.287 ns (26 vi pham), hold -0.192 ns (74 vi pham).
  Nguyen nhan: GRT phai di vong o die chat hon. Skew clock xau nhat (setup, nom_tt) tang 0.737 -> 2.088 ns tu STAMidPNR-2
  (ky sinh uoc luong tu placement) sang STAMidPNR-3 (ky sinh tu GRT); o 11.56 mm2 chi 0.903 -> 1.225. Vd. net clock cap 1
  `clknet_1_0_1_clk`: cac chan nam trong ~385 x 324 um nhung guide dai ~4.9 mm (met1 869, met2 1,180, met3 1,780, met4 414,
  met5 642 um), tai 0.57 pF, slew 0.93 ns; o 11.56 mm2 cung net dai ~0.75 mm, chu yeu met3. Duong xau nhat (ca hai die):
  doc nua chu ky tu `dout1` cua macro I$ way1 bank 1 (suon xuong) toi flop o suon len, qua net 0.58 pF slew 1.1 ns.
  Setup mat 2.8 ns giua hai uoc luong (11.56 mm2: 1.1 ns): 10.54 mm2 qua nho cho cau hinh nay.
- SA2 11.05 mm2 (sa2_corr3400x3250_f220_capm20_fo16_r1): p1 dat (overflow 0, setup +1.529); p2: overflow 0 o moi lan GRT
  sau buoc sua, setup nom_tt +0.220 (duoi bien du phong +0.30 nhung duong), hold +0.146. Cho chay tiep detailed routing nhu
  sa2_corr3400x3325_f220_r1 (+0.234, 2026-10-06); cong sign-off giu nguyen. Detailed routing cua run nay duoc uu tien hon
  run 11.56 mm2 cung knob (chi mot detailed routing co SA2, ~11.7 GB, vua bo nho; run 11.56 giu sau P2 lam du phong).
  Thu tu die SA2 voi cap 20 + fanout 16 (setup nom_tt STAMidPNR-2 -> STAMidPNR-3): 11.56 +1.754 -> +0.671; 11.05 +1.529
  -> +0.220; 10.54 +1.521 -> -1.287.
- DM_VC4 max fanout 16 + cap 20 (vc4_corr3400x3400_f220_capm20_fo16_r1) TRUOT p1: overflow GRT 1,272 (gioi han 500;
  fanout 8 cung die: 0), setup nom_tt +1.352. Buffer buoc sua DRV dau tien 20,213 -> 13,297, cell chuan -1.2 %, nhung nhu cau
  GRT 29.09 -> 29.90 %: met1 +7.4 %, met2 +5.3 %, met3 -5.5 %, met4 -5.8 % (`guide_demand.py`), tang quanh cum I$ va doc mep
  trai die. Cay fanout it buffer hon nhung moi nhanh dai hon va nam o met1 / met2, dung cho cum tag cua DM_VC4 da day hon SA2
  (29 % so voi 22 %). Ket luan: DM_VC4 giu max fanout 8; run fanout 8 + cap 20 bi bo luc 16:10 (suy tu SA2, chua co so lieu
  DM_VC4) duoc chay lai.
- DM_VC4 cap 20 + fanout 8 (vc4_corr3400x3400_f220_capm20_r1) TRUOT p2: buoc sua DRV sau GRT chi chen 357 buffer (4,662 voi
  cap 50), route lai 6 -> 42; nhung buoc sua antenna o GRT chen 17,135 diode (4,632 net o vong dau, `GRT_ANTENNA_MARGIN` 30)
  va lan route lai sau do 79 -> 3,934 (ResizerTimingPostGRT 3,762 / 3,962); setup nom_tt -5.329 ns, hold -0.294, skew
  2.012 ns (STAMidPNR-2: +1.372 / +0.184 / 0.863). Duong xau nhat qua mot net 1.82 pF slew 11.6 ns (route vong cuc dai).
  So diode o buoc nay: DM 5,920 (route lai 0 -> 0), SA2 10,557-12,684 (0 -> 0, 10.54 mm2: 1 -> 21), DM_VC4 3600 13,695
  (2,295 -> 5,774). Thu tiep: `GRT_ANTENNA_MARGIN` 30 -> 10 (bang bien sua antenna sau detailed routing),
  vc4_corr3400x3400_f220_capm20_antm10_r1.
- Sang loc kich thuoc die cho SA2 (cap 20 + fanout 16, P1 + P2, giu sau p2): corr3400x3100_f220 (10.54 mm2),
  corr3400x3250_f220 (11.05 mm2), floorplan sinh bang `fp_tools/make_u2_fp.py ... 100 220 150 220 F`. `run_gated_pd.sh` dung
  chung khoa khoi dong voi `run_gated_resume.sh p2` va `run_gated_branch.sh`.
- Chu du an cho phep dung run da that bai khi da biet nguyen nhan (QUY_TRINH muc B). Hai run die rong (3600 / 3800) dung luc
  22:42 o ResizerTimingPostGRT (SIGTERM dung tien trinh OpenLane va openroad cua tung run, ly do ghi vao `gated_pd.log`).
- Sua antenna sau detailed routing cua SA2 B cham hon DM nhieu: DM (dm_corr3400x3400_f220_r1) 368 net -> 854 diode -> route
  lai tu 9,938 vi pham, 0 sau 10 vong, ca buoc 28 phut; SA2 B 833 net -> 1,576 diode -> route lai tu 48,176 vi pham
  (7,416 o vong 7).

### 2026-10-08 Doi cach toi uu: full flow sau moi thay doi, dung som khi co dau hieu that bai

- Kiem tra treo / crash luc 06:30: khong co (WSL chay lien tuc 14 gio, dmesg sach, probe 8 / 8 OK, 0 su kien WHEA tu chieu
  2026-10-07). Rieng SA2 B o lan route lai sau sua antenna dung o 136 vi pham tu vong 38 toi 46, mot luong (moi vong 7-63
  phut, vong 44 mat 63 phut), giu 12.4 GB.
- Chu du an: hon 100 loi o vong 50 van co the het loi o vong 64 (SA2 B tu 70 o vong 44 ve 0 o vong 54), nen bo gioi han sau
  vong 40 cua drt_convergence; mot run duoc dung theo GIA TRI cua no. SA2 B (cap 50 + fanout 8) bi cau hinh cap 20 + fanout
  16 ap dao nen dung luc 07:06 voi su dong y cua chu du an; thu muc run giu lam bang chung.
- Tu danh gia: trong ~10 gio da chay 8 run sang loc (5 truot cong), 3 run bo truoc khi chay (1 bo sai roi chay lai); cach thu
  - sai bang knob toan cuc chi doi loi sang cho khac. Cac so SA2 / DM_VC4 bao cao den nay la so sang loc, chua toi uu.
- Quy tac moi cua chu du an (QUY_TRINH muc D): moi lan dieu chinh chay full flow toi sign-off, chan doan tung pha, dung ngay
  khi co dau hieu that bai. Cong p2 trong full flow: setup >= 0. Bao cao DRC moi 5 vong cho moi lan goi detailed_route,
  giu rieng theo lan goi (`drc_iter_main/`, `drc_iter_ant<i>/`, openlane-local `drt.tcl`).
- Thi nghiem tiep theo (full flow), nham dung nguyen nhan da do: SA2 10.54 mm2 + padding 1 site moi ben (`GPL_CELL_PADDING` /
  `DPL_CELL_PADDING` = 2, vi script chia doi bang phep chia nguyen, 1 la khong padding) + dat cell theo timing
  (`PL_TIME_DRIVEN`) + clock tren met3-met5 (`RT_CLOCK_MIN_LAYER` met3): sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1.
  Run 11.05 mm2 (sa2_corr3400x3250_f220_capm20_fo16_r1) chay tiep detailed routing va sign-off; DM_VC4 bien antenna 10 %
  chay tiep sau p2 neu dat.
- Du bao diem nong truoc detailed routing (`asic/fp_tools/pin_hotspots.py`, DEF dau vao detailed routing + LEF cell chuan,
  o 20 um): o co mat do chan cao nhat cua sa2_corr3400x3400_f220_r1, (2020, 1940), trung dung o ma detailed routing ket 54
  vong. Mat do chan max / 100 um2 (util p99): DM corr3400x3400_f220 29.0 (0.76), hoi tu o vong 17; SA2 cap 50 + fanout 8
  11.56 mm2 32.2 (0.90), 54 vong; 11.305 mm2 32.0 (0.91), dung 173 o vong 30; SA2 cap 20 + fanout 16: 11.56 mm2 29.2
  (0.88), 11.05 mm2 34.8 (0.89) o (1260, 1940), 10.54 mm2 33.2 (0.90).

### 2026-10-08 Bang LE theo module (A1), golden cu, RAM cua CoreMark

- A1: `scripts/le_breakdown.py` doc bang "Fitter Resource Utilization by Entity" cua cac report fit da luu
  (`results/fpga_points/r16_p{1,2}/<diem>/s2/`), khong chay lai Quartus; luot 1 = luot 2 tung dong; bang
  `results/a1_le_breakdown_r16.md`. DM 15,440 LE: core 6,451 (register file 1,386 va BHT 962 nam trong flop), I$ 2,439,
  D$ 1,896, observability 2,356. Controller DSE +1,453 LE; moi victim buffer cua DM_VC4 ~+1,275 LE / +795 flop (moi cache
  mot bo).
- Golden: `E:\Projects\RISCV-research_GOLDEN_20260927` (snapshot 27/09, RTL 8b163675, final_A / final_B: antenna 140 net,
  chua LEC) bi FINAL3 thay the; so manifest: noi dung chi co o ban cu la scratch EQY that bai cua final_B va file trung
  gian SEC da lam lai bang LEC. Xoa ngay 2026-10-08 theo yeu cau chu du an (giai phong ~12 GB; ~20 GB la hard link dung
  chung voi FINAL3). Con mot golden: `RISCV-research_GOLDEN_FINAL3_20260928`. Moc DM 16 KiB-RAM dang khoa (r14F_A / B)
  khong nam trong golden nao, chi co trong workspace.
- CoreMark chay voi RAM 32 KiB, khong phai 16 KiB: ban build -O2 rv32i_zmmul can .text 13,952 + .rodata 2,445 + .data
  24 + .bss 2,020 byte + stack 1 KiB (~19.4 KiB); `sw/coremark/coremark_link.ld` (LENGTH = 32K, stack o dinh 32 KiB, khong
  doi tu truoc R14); `run_coremark.py` va `run_m2_sweep.py` dat IMEM_DEPTH = DMEM_DEPTH = 4096. `M1_M2_REPORT.md` ghi nham
  "RAM 16 KiB" cho ca CoreMark: da sua, them ghi chu o `RESULTS.md` va `REVIEW_RESPONSE.md` (A6). Cache va moi tham so
  khac nhu SoC 16 KiB, do tre RAM khong phu thuoc do sau, nen so sanh giua cac cau hinh khong bi anh huong; CoreMark khong
  chay duoc tren chip 16 KiB.
  Quyet dinh cua chu du an (2026-10-08): giu CoreMark voi RAM 32 KiB nhu hien tai (khong build lai cho vua 16 KiB); moi
  so CoreMark ghi ro la mo phong voi RAM 32 KiB.

### 2026-10-08 07:57 Tat may (chu du an di chuyen): trang thai va cach chay tiep

Moi tien trinh PD bi dung khi may tat. Ba run dang chay, buoc dang do (khong co `state_out.json`) se chay lai tu dau buoc
do; khong xoa thu muc buoc dang do (OpenLane lay `state_out.json` moi nhat, bo qua buoc khong co state).

| run | trang thai luc tat | chay tiep |
|---|---|---|
| sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1 (SA2 10.54 mm2, padding 1 site / ben, PL_TIME_DRIVEN, clock met3-5) | p1 dat (overflow 0, setup +1.516, hold +0.182, skew 1.006); 41 xong (499 buffer, overflow 0, 27.19 %); 42 xong; dang 43 RepairAntennas | (1) |
| vc4_corr3400x3400_f220_capm20_antm10_r1 (DM_VC4 11.56 mm2, cap 20, bien antenna GRT 10 %) | 40-42 xong; dang 43 RepairAntennas | (2) |
| sa2_corr3400x3250_f220_capm20_fo16_r1 (SA2 11.05 mm2, cap 20 + fanout 16) | p2: overflow 0, setup +0.220; detailed routing dang vong 14 (483 vi pham), diem nong du bao dung o x 1200-1400, y 1800-2100 | (3) |

Lenh (WSL, trong `asic/`, moi lan mot run, uu tien (1)):
1. `RESUME=1 CONFIG=config_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3.json bash run_pd_mk.sh soc_sa2_4kb sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1 --from OpenROAD.RepairAntennas --to OpenROAD.STAMidPNR-3`,
   roi `P2_MIN_SETUP=0 python3 fp_tools/gate_check.py soc_sa2_4kb/runs/<tag> p2`; neu PASS: `bash run_gated_resume.sh
   soc_sa2_4kb <tag> <config> "<ly do>" drt` (detailed routing + sign-off). Truoc detailed routing chay
   `pin_hotspots.py` tren DEF cua ResizerTimingPostGRT.
2. Nhu (1) cho DM_VC4 (`soc_vc4_4kb`, config `config_corr3400x3400_f220_capm20_antm10.json`, tu RepairAntennas).
3. Chi chay tiep neu (1) that bai: neu (1) dat p2 thi run 11.05 mm2 bi ap dao (die lon hon, diem nong 34.8 chan / 100 um2),
   hoi chu du an truoc khi bo. Chay tiep: `bash run_gated_resume.sh soc_sa2_4kb sa2_corr3400x3250_f220_capm20_fo16_r1
   config_corr3400x3250_f220_capm20_fo16.json "<ly do>" drt`.
Khong dung `run_gated_resume.sh ... p2` cho (1) / (2): che do do chay lai tu CheckAntennas tren state da sua DRV.

### 2026-10-08 16:00 May loi sau khi di chuyen: chua chay tiep PD

- Sau khi may duoc mo lai (LastBootUpTime van la 2026-10-03, tuc may ngu / ngu dong, khong khoi dong lai), probe suc khoe
  truot: WSL 0 / 8 hai lan (`AttributeError ... 'debug'`, `<invalid frame>`, du lieu lat bit `obj25769` -> `ooj25769`),
  Windows 1 / 8 roi 0 / 8 (`SystemError: unknown opcode`, `TypeError` vo ly, process chet giua chung). Sang cung ngay WSL
  8 / 8. Khong co su kien WHEA tu 2026-10-03.
- Khoanh vung tren Windows (affinity): ghim tung CPU logic 32 / 32 OK; mot nhan vat ly (CPU 0-1) 6 / 6 OK; nhom 16 nhan P
  0 / 8; nhom 16 nhan E 1 / 8; ca 32 nhan 4 / 8. Loi xay ra khi process duoc di chuyen giua cac nhan vat ly, khong do mot
  nhan cu the.
- May: ASUS ROG Strix G614JV, i9-13980HX (Raptor Lake), BIOS 334 (2026-02-11), microcode 0x12F, dang cam sac, che do nguon
  "Turbo". Khong chay tiep PD khi probe chua dat 8 / 8 ca Windows va WSL; ba run van dung o buoc ghi luc 07:57.
- Sau khi khoi dong lai that su (16:18): probe khong ghim Windows 2 / 8, WSL 0 / 8. Kiem tra them: loi o vi tri khac nhau moi
  lan va van loi khi bien dich lai `shlex` tu nguon (khong phai file .pyc hong); certutil SHA-256 file 311 MB 8 / 8 trung;
  hai phep tinh Python tat dinh (so hoc, chuoi + sha256) 6 / 6 trung; test chinh thuc cua Python tren Windows 6 / 6 (tren WSL
  khong co bo test, ket qua do khong dung duoc); voi PYTHONHASHSEED=0 xen ke: ghim 8 / 8, khong ghim 7 / 8.
- Ket luan can bang: loi cua probe la that va khong do logic script (cung dau vao cho ket qua khac nhau, ghim mot nhan luon
  dung), nhung cac phep thu khac on dinh va ti le loi thay doi theo thoi gian. Chu du an cho rang da do loi cho may qua
  muc; quyet dinh: chay lai tu dau, khong chan cong viec vi probe; chay hai lan va so khop la phep thu quyet dinh do tin cay.
- Xoa ba run bi ngat (khong con gi rieng; so P1 / P2 da ghi o tren): sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1,
  vc4_corr3400x3400_f220_capm20_antm10_r1, sa2_corr3400x3250_f220_capm20_fo16_r1. Chay lai full flow tu buoc 1 (16:26):
  hai run dau (cung ten tag), p2 voi setup >= 0; run 11.05 mm2 chi chay neu run 10.54 mm2 that bai.

### 2026-10-08 21:15 SA2 10.54 mm2: detailed routing xong, ECO hold sau route dung o DPL-0033

- sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1 (chay lai tu dau 17:00): P1 PASS (setup nom_tt +1.516), P2 PASS
  (overflow 0 o moi global route sau sua, setup nom_tt +0.280, hold +0.025), detailed routing 11:48 -> 14:11 UTC.
- Buoc 47 `OpenROAD.PostRouteHoldECO` dung: `check_placement` bao 1,204 "overlap", deu la diode antenna do vong sua antenna
  sau DRT (drt.tcl) dat sat cell. Nguyen nhan: script ECO nap lai `dpl_cell_pad.tcl`, tuc padding 2 (1 site moi ben) cua
  cong thuc nay, sau khi da route; padding la nut mat do cua GPL / DPL, khong phai luat hop le. Sua
  `post_route_hold_eco.tcl`: hop phap hoa voi padding 0 (DM va DM_VC4 da dung padding 0, khong doi gi voi chung).
- Gate final bao `setup nom_ff -100.78`, `hold nom_ff -0.021`, "only 3 corners": so cu cua STA mid-PnR vi chua co STA sau
  route, khong phai ket qua. Chay tiep tu buoc ECO (`run_gated_resume.sh ... hold`, 14:17 UTC).
- ECO hold: truoc ECO hold -0.187 (94 endpoint), chen 78 buffer, sau ECO +0.020; route lai 151 net ve 0 vi pham; sua antenna
  sau ECO 6 -> 2 -> 0 net trong 3 vong.
- STA sau route (59-openroad-stapostpnr, RC trich xuat): hold >= 0 o ca 9 goc (thap nhat min_ff +0.016); setup nom_tt +0.122,
  min_tt +0.618, ff +2.49 .. +3.68, NHUNG **max_tt -0.571 ns o 21 endpoint** (TNS -6.07); ss -7.07 .. -8.99 (khong gate).
  Duong gang: doc nua chu ky tu SRAM du lieu way 1 cua I$ (dout ra o canh xuong), qua cac net dai slew 1.0-1.3 ns (tre day
  0.53 + 0.67 + 0.47 ns) va chuoi mux chon way / word. Vi pham gioi han cung (setup >= 0 o moi goc tt) nen run nay khong ky
  ten duoc; dung phan sign-off bang tay luc 15:56 UTC (Magic DRC dang chay; DRC / LVS khong doi duoc ket luan).
- Huong sua (it dien tich nhat): them vao openlane-local tuy chon ECO setup sau route (`POST_ROUTE_ECO_SETUP`,
  `POST_ROUTE_ECO_SETUP_MARGIN`, `POST_ROUTE_ECO_SETUP_MAX_BUFFER_PCT`, `POST_ROUTE_ECO_CORNERS`; mac dinh tat, DM / DM_VC4
  khong doi): `repair_timing -setup` tren ky sinh trich xuat max_* voi chi goc tt va ff (khong duoi theo ss), truoc sua
  hold, roi hop phap hoa va route lai nhu ECO hold. Config `config_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_seco.json`;
  run moi `sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_seco_r1` re nhanh tu run cu sau detailed routing (buoc 1..46,
  `branch_run.sh`) va chay tu ECO toi LVS.
- Ket qua seco_r1 (dung bang tay 16:17 UTC, run chan doan): STA sign-off max_tt -0.573 (duong gang khong doi) va hold ff
  -0.186 (56 endpoint). Nguyen nhan: trong phien ECO, `estimate_parasitics -placement` chay TRUOC `read_spef` lam STA cua
  phien o lai tren uoc luong placement (phien thay tt +1.425 ns, hold +0.015 ns), nen khong sua gi. Bang chung: dien dung
  cua cac net tren duong gang trong SPEF cua ECO va SPEF sign-off trung tung so (0.481957 / 0.477321 / 0.519161 pF), ECO cua
  r1 (chi SPEF) khop STA sign-off o ss (-8.987 / -8.985). Them mot bay: macro SRAM chi co MOT .lib TT cho moi goc, OpenSTA
  giu no cho goc doc dau tien (STA-1140 "already exists" o cac goc sau), nen trong mot phien nhieu goc, duong tu SRAM chi
  duoc tinh o goc dau.
- Sua: ECO setup chi dung SPEF (khong uoc luong truoc); them `POST_ROUTE_ECO_HOLD` (mac dinh true). Hai luot tren run moi
  `..._secott_r1` (re nhanh tu r1 sau buoc 46): luot 1 chay rieng buoc ECO voi
  `config_..._seco_setup.json` (setup, chi goc tt, margin 0.3 ns, khong sua hold); luot 2 tu buoc ECO toi LVS voi
  `config_..._seco_hold.json` (sua hold moi goc nhu r1), roi cong final.

### 2026-10-08 23:25 DM_VC4 3400 bien antenna 10 truot p2; thu tat sua antenna o GRT

- vc4_corr3400x3400_f220_capm20_antm10_r1: P1 PASS (setup nom_tt +1.372); P2: sua antenna o GRT (bien 10) chen khoang 11,087
  diode qua 10 vong (8,400 + 1,967 + 482 + ...; bien 30 hom 07/10: 17,135), overflow sau route lai 1,707, sau
  ResizerTimingPostGRT 1,946 (gioi han 2,000); STAMidPNR-3 setup nom_tt -2.099, hold -0.568: TRUOT p2 (16:22 UTC). Buoc sua
  antenna mat 2.5 gio, ResizerTimingPostGRT gan 3 gio (vong lap repair_timing duoi theo goc ss: WNS -10.49 -> -9.17 sau
  1,400 vong, 7,609 endpoint).
- Gia thuyet: chinh cac diode cua buoc sua antenna o GRT lam tac cum tag (cung co che hai lan, bien 30 va 10). Thu: tat buoc
  do (`RUN_ANTENNA_REPAIR` false, `config_corr3400x3400_f220_capm20_antoff.json`), sua antenna chi tren route chi tiet
  (`DRT_ANTENNA_REPAIR_ITERS` 5, bien 10) nhu DM final3. Run vc4_corr3400x3400_f220_capm20_antoff_r1 re nhanh tu run tren sau
  GRT (buoc 1..39), chay P2 roi detailed routing va sign-off neu qua cong.

### 2026-10-09 03:10 Resizer duoi theo goc ss; chay lai SA2 va DM_VC4 voi resizer chi o tt va ff

- vc4_corr3400x3400_f220_capm20_antoff_r1 (tat sua antenna o GRT): TRUOT p2 (18:45 UTC): overflow cac lan GRT sau sua
  6 / 42 / 66 / 1,185, setup nom_tt -2.673, hold -0.125. Khong co diode nao ma overflow van vot o ResizerTimingPostGRT
  (66 -> 1,185): chinh buoc sua timing sau GRT gay tac, khong phai diode antenna.
- sa2_..._secott_r1 luot 1 (ECO setup o tt): sua 21 cell, nhan ban 5 cong; route lai bat dau tu 2,496 vi pham va TREO o vong
  toi uu thu 3 (40 %, 869 -> 699) tu 16:21 UTC, log im 2 gio 25 phut. Dung bang tay 20:06 UTC (co abort dat truoc nen luot 2
  khong chay).
- Chan doan chung: moi buoc resizer chay o ba goc (tt, ss, ff) voi bien setup 2.0 ns; goc ss khong cau hinh nao dong o
  20 ns (WNS -9 .. -10 ns, khoang 7,600 endpoint), nen resizer chen buffer / phong to cell hang gio vao cum tag (DM_VC4
  ResizerTimingPostGRT gan 3 gio, 1,400 vong), lam tac va ton dien tich, cong suat, ma khong giup goc bi gate (tt / ff).
- Thu (mot thay doi so voi run cuoi cua moi cau hinh): `RSZ_CORNERS` = nom_tt, nom_ff (moi buoc resizer, ke ca ECO sau
  route). ss van bao cao o STA sign-off. Full flow tu buoc 1: sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1,
  vc4_corr3400x3400_f220_capm20_antoff_rsztf_r1 (20:08 UTC).
- Cung luc: Quartus x2 cho RTL 6c4ccffd (`TAG=rfbht scripts/run_le_rtlfix.sh 1` roi `2`) va LEC buoc A cho chip DM
  16 KiB (`asic/equiv/lec/run_lec_r14.ps1 -Step A`), trong luc PD con o P1 / P2 (Windows con 16.9 GB trong, WSL 2.2 GB).

### 2026-10-09 03:55 LEC chip DM 16 KiB buoc A da chung minh; SA2 tt/ff qua p2 nhung duong I$ van thieu, chuyen sang 11.56 mm2

- LEC buoc A (RTL rtl_r14 + fsm == N1 cua tong hop r14F, replay trung tung byte buoc 06): 19,458 / 19,090 bit flop, 20,124
  output; per-output SAT 20,090 chung minh, 0 phan vi du; 235 flop hang chung minh hinh thuc (diem bat dong sau 2 vong, 2 bi
  ha bac), 28 ban sao (19 trich RTL trong `spec_manual.py`), 4 FSM one-hot nhu final3. 34 output con lai (32 bit d_req_addr
  + 2 kiem tra ban sao mem_byte_offset_m) = non bo nhan: replay t1 cua r14F_A (`synth_replay_r14/dm_r14F_t1`), `macc_alg.py`
  PROVED product == signed33(A) * signed33(B) mod 2^64 o CA HAI phia, doi chung am (spec unsigned, tich rieng phan sai) FAIL
  dung; bo nhan thuan cua cap LEC == mang cua snapshot (`&cec`); thay bo nhan da chung minh roi `&cec` 34 output: Networks
  are equivalent (0.20 s). `asic/equiv/lec/run_lec_r14.ps1`, `run_lec_r14_mul.ps1` (chay bang pwsh 7: PowerShell 5.1 lam hong
  chuoi lenh bash truyen cho wsl.exe, lan dau build_pair do do loi).
- LEC buoc B (N1 == netlist cuoi da ky ten): r14F_A (55-openroad-fillinsertion) va r14F_B (56-...): 19,090 / 19,087 bit
  flop (3 flop chi o N1 = ban sao da biet), 20,096 output, 0 phan vi du; per-output SAT 20,064, 32 bit d_req_addr dong bang
  `&cec` (Networks are equivalent, 0.54 s) -> CA HAI netlist ky ten 16 KiB-RAM tuong duong RTL (macro SRAM la hop den hai
  phia, GLS phu phan do). Luot 2 (moi dau vao sinh lai, so hash moi doi tuong chung minh) va doi chung am buoc B (mot
  and2_1 cua netlist r14F_A doi thanh or2_1 phai co phan vi du) dang chay (`run_lec_r14_pass2.ps1`).
- Luot 2 (06:20): moi dau vao sinh lai (replay N1 va t1 trung tung byte buoc 06 / luot 1, n1_flat / gold_flat, cap, spec,
  moi AIG cua cap LEC, bo nhan thuan, AIG sau thay the, danh sach output mo: trung sha256 luot 1). Thong ke SAT trung tung so
  (so loi goi Unsat / Sat / Undef, xung dot trung binh); chi 3 file mieu ta du (`msat*_b.aig` cua ABC) khac byte, phan quyet
  khong doi. Doi chung am buoc B: and2_1 dau tien cua netlist r14F_A doi thanh or2_1 -> 184 phan vi du (Sat calls), LEC bat
  duoc. LEC cua chip DM 16 KiB-RAM: XONG (r14F_A va r14F_B, RTL rtl_r14 == netlist ky ten; macro SRAM hop den hai phia).
- SA2 10.54 mm2 resizer tt / ff (..._rsztf_r1): P1 22 phut (truoc 43), setup +1.607, it hon ~1,100 cell; P2 24 phut (truoc
  76), overflow 0 o moi lan GRT, setup nom_tt +0.153, hold +0.170. Duong xau nhat van la doc nua chu ky tu SRAM way 1 bank 1
  cua I$ (+0.280 o run truoc, run do mat 0.85 ns tu P2 toi max_tt sign-off: -0.573), nen max_tt du bao ~ -0.7 ns: dung
  detailed routing (quy tac chu du an: co dau hieu that bai ro thi dung, khong cho). Chay cung bo knob tren die 11.56 mm2
  (sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1, chi doi die).
- Quartus luot 1, dm_4kb 4 seed: LE 12,810 / 12,815 / 12,823 / 12,842, Fmax s85 52.27 .. 55.52 MHz.

### 2026-10-09 04:40 SA2 11.56 mm2 va DM_VC4 voi resizer tt / ff

- DM_VC4 (vc4_corr3400x3400_f220_capm20_antoff_rsztf_r1): P1 PASS 28 phut, overflow 0, setup nom_tt +2.061 (run bien
  antenna 10: +1.372), hold +0.183. Dang P2.
- SA2 11.56 mm2 (sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1, chi doi die so voi 10.54): P1 PASS 21 phut
  (overflow 0, +1.571); P2 24 phut: overflow 0 o moi lan GRT, setup nom_tt +1.057 (10.54 mm2: +0.153; duong I$ way 1 nay du
  bien), nhung hold nom_tt -0.206 (19 endpoint flop -> flop, ky sinh uoc luong tu GRT; buoc ResizerTimingPostGRT tu bao
  +0.032 sau 38 buffer hold), nom_ff -0.021. Cong p2 truot vi hold. Cho chay tiep detailed routing va sign-off: muc hold
  nay la viec cua ECO hold sau route tren ky sinh trich xuat (run 10.54 mm2: -0.187 -> +0.020 voi 78 buffer); cong
  sign-off (hold >= 0 o moi goc) giu nguyen.

### 2026-10-09 06:50 SA2 11.56 mm2 gan sach (chi hold ff); DM_VC4: skew clock no sau GRT

- SA2 sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1: detailed routing 38 phut (10.54 mm2: hon 2 gio); STA
  sign-off: setup max_tt +0.838, nom_tt +1.118, min_tt +1.331, ff >= +3.803 (ss -6.72 .. -7.92, khong gate); hold tt / ss
  >= 0, max_ff +0.020 nhung nom_ff -0.023, min_ff -0.027 (4 endpoint). Route DRC 0, antenna 0 / 0, XOR 0, Magic DRC 0,
  KLayout DRC 0, chan ngat critical 0; LVS dang chay. Nguyen nhan hold: ECO hold sau route gan MOT trich xuat (mac dinh
  max_*) cho moi goc resizer, nen goc ff mang RC max, truong hop de nhat cho hold; xau nhat that la ff voi RC min. Sua: re
  nhanh sau buoc 46, chay lai ECO voi `POST_ROUTE_HOLD_ECO_RCX_CORNER` min_* (..._rsztf_ecomin_r1).
- DM_VC4 tat sua timing sau GRT (vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_r1): route khoe (overflow 22) nhung
  setup nom_tt -0.896, hold -3.902 tai p2. Skew clock tu ky sinh placement sang ky sinh GRT: setup 0.870 -> 4.177 ns, hold
  -1.545 -> -5.460 ns: net clock di vong qua met1 / met2 dang nghen (cung hien tuong SA2 10.54 mm2 truoc khi dua clock len
  met3). Cac lan truoc, buoc sua timing sau GRT "sua" cac vi pham gia do skew nay (hold -7.8 ns, 2,746 buffer) va lam no
  overflow. Thu: full flow voi `RT_CLOCK_MIN_LAYER` met3 (vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_r1).
- Quartus luot 1 xong (4 diem x 4 seed): DM 12,810-12,842 LE, SA2 16,675-16,739, DM_VC4 17,130-17,139, DM_DSE
  14,308-14,364 (R16: 15,440-15,546 / 19,360-19,474 / 19,810-19,875 / 16,989-17,063); Fmax 51.96-55.52 MHz.

### 2026-10-09 08:35 SA2: ECO hold cho ca hai dau RC; DM_VC4: cum victim buffer tren hang D$ gay detour clock

- SA2 ..._rsztf_r1: sign-off xong 00:03 UTC (LVS sach); cong final chi truot hold nom_ff -0.023 / min_ff -0.027. ECO tren
  trich xuat min_* thay cho max_* (..._rsztf_ecomin_r1, re nhanh sau buoc 46): max_ff -0.116, nom_ff -0.044, xau hon. ECO
  gan MOT trich xuat cho moi goc, nen moi luot chi sua duoc mot dau RC. Dang chay: ECO thu hai tren min_* chong len ECO
  max_* cua r1 (..._rsztf_ecomaxmin_r1, re nhanh sau buoc 47): 9 endpoint, 11 buffer hold, -0.027 -> +0.020 trong goc nhin
  ECO; route ECO va sign-off dang chay. Buoc 52 `Odb.ReportDisconnectedPins` crash trong CPython (`AttributeError: 'cell'
  object has no attribute 'name'` o `self.name` cua `Module.__init__`: doi tuong Python bi hong; cung code da qua o r1 va
  ecomin): doi ten thu muc thanh `crashed-52-...`, chay lai tu buoc do bang che do moi `step:<StepID>` cua
  `run_gated_resume.sh` (quy tac thu lai crash ngau nhien). STA sign-off sau hai luot ECO: hold >= 0 o ca 9 goc (xau nhat
  +0.020 min_ff / max_ff, nom_ff +0.021), setup max_tt +0.838, nom_tt +1.118, min_tt +1.331, ff >= +3.803; ss -6.72 ..
  -7.92 (khong gate). Lan chay thu hai cua cong thuc nay (`..._rsztf_r2`, full flow tu buoc 1, 01:37 UTC; sau do re nhanh
  `_ecomaxmin_r2` sau buoc 47 nhu r1).
- **SA2 KY TEN SACH** (03:04 UTC, `..._rsztf_ecomaxmin_r1`): route / Magic / KLayout DRC 0, LVS 0, XOR 0, overlap 0, antenna
  0, hold >= 0 o 9 goc, setup tt / ff >= 0. Die 11.56 mm2, cell chuan 1.4711 mm2 (215,979 cell), 16 macro 3.802 mm2, day
  9.274 m; buffer sua timing 15,240 (DM r14F_A: 24,448), clock buffer 4,519, inverter clock 824; `power__total` (max_ff, uoc
  luong cua flow) 137.0 mW. DRV con lai (goc xau nhat): slew 7,885, cap 1,827, fanout 383. r2: P1, P2 va ECO max_* trung r1
  (112 endpoint, 139 buffer hold, -0.3812 -> +0.0202). GLS + SAIF cua netlist r1 dang chay (Questa, 2 job).
- DM_VC4 clock tren met3 (..._nogrtt_clkm3_r1): TRUOT p2 (overflow 7, setup nom_tt -1.076, hold -3.192). Skew hold -1.545
  -> -4.768 ns, setup 0.870 -> 4.562 ns. Clock dich cua hold xau nhat (`min.rpt` buoc 43): `clknet_2_1_1_clk` (2 tai, HPWL
  ~670 um) co guide ~7.7 mm sau GRT (bbox x 1822-3346, y 1290-2491 um), tre day 0.86 ns, slew 1.85 ns; `clknet_4_7_0_clk`
  1.4 -> 7.1 mm sau sua DRV sau GRT; tre clock dich 7.82 ns so voi nguon 3.49 ns. Dua clock len met3 khong giup vi day la
  detour cua router, khong phai chuyen lop.
- Nguyen nhan goc: MOI run DM_VC4 tren die 11.56 mm2 (ke ca vc4uA / vc4uB) phai chay "Extra Run for hard benchmark" cua
  FastRoute o GRT dau tien; KHONG run SA2 / DM nao phai chay, die DM_VC4 3600 / 3800 cung khong. Diem nong
  (`fp_tools/guide_demand.py`, DM_VC4 tru SA2 cung die): cua so x 2208-2600, y 2374-2600 um ngay tren hang macro D$ phia
  tren, tai ~175 / 256 track danh dinh (SA2 ~5). `region_cells.py`: 3,891 cell trong o 392 x 226 um (831 mux2, 518 flop,
  637 buffer fanout, 326 clock buffer), SA2 349 cell: day la victim buffer cua D$.
- Thu (mot thay doi so voi clkm3): padding cell 1 site moi ben (cong thuc SA2),
  `config_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1.json`, run
  vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_r1, full flow tu buoc 1 (01:28 UTC). Tieu chi: GRT dau
  khong con hard benchmark, skew sau GRT gan muc P1, qua p2.
- Ket qua padding (02:39 UTC): o nong sau GPL 3,035 -> 2,516 cell; GRT dau VAN chay hard benchmark (overflow cuoi 11, day
  +2.6 %); net clock tang 2 `clknet_2_1_0_clk` (HPWL 462 um) guide ~5.5 mm; TRUOT p2: overflow sau sua DRV 60, setup nom_tt
  -0.190, hold -1.157 (clkm3: -1.076 / -3.192), skew hold -4.77 -> -2.69 ns, setup 4.56 -> 2.24 ns. Cua so nong nhat luc nay:
  x 1932-2208, y 1822-1987 um (cum tag D$ o mep hanh lang, 2,277 cell, trong do 806 buffer fanout / max_cap). Padding giup
  nhung chua du o 11.56 mm2.
- Tiep (mot thay doi so voi run padding): die 3500 x 3400 (11.90 mm2, hanh lang 1,157 um), cung knob
  (`config_corr3500x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1.json`, `macro_placement_corr3500x3400_f220.cfg`).
  Die 3600 x 3400 chua bao gio can hard benchmark; 3500 la buoc nho hon ke tiep, can thu truoc de chung minh die nho nhat.
- Co che (log GRT): SA2 va DM cung chay vong them cua FastRoute (GRT-0101 "Running extra iterations to remove overflow")
  nhung tu ve 0 trong do; chi DM_VC4 roi vao GRT-0103 "Extra Run for hard benchmark" (route lai cac net con overflow voi
  khung rong: detour dai). Sang loc chi GRT (`..._pad1_grtit150_grtscr_r1`, tu trang thai STAMidPNR-2 cua run padding,
  `GRT_OVERFLOW_ITERS` 150 thay 50): VAN co GRT-0103; overflow cuoi 11 -> 0, day 14.36 -> 14.27 m, `clknet_2_1_0_clk`
  5.5 -> 3.6 mm. So vong khong go duoc nguyen nhan; khong dua vao full flow.
- Die 3500 (03:12 UTC, P1 PASS, setup nom_tt +2.011): GRT dau VAN co GRT-0103 nhung overflow cuoi 0, day 13.47 m; detour clock
  nho hon (`clknet_6_29_0_clk` 336 um HPWL -> 4.05 mm, `clknet_2_1_0_clk` 3.09 mm). TRUOT p2 (03:36): overflow 0, setup
  nom_tt +0.548, hold -1.926 (1,675 endpoint, TNS -1,176 ns), skew hold -3.37 ns: nhanh clock 2_1_0 -> 3_3_0 -> 6_29_0 tai
  0.37-0.81 pF, slew 1.2-1.5 ns, cham them ~2.5 ns.
- Ma nguon OpenROAD edf00dff (GlobalRouter.cpp, FastRoute.cpp): clock va tin hieu route chung mot luot; net clock khong phai
  la (isNonLeafClock) nhan dai lop rieng va FastRoute chi cong capacity cac lop trong dai do; GRT-0103 bat o vong congestion
  thu 20 khi overflow con > 200 (vi vay tang so vong khong co tac dung). Do skew ngay sau GRT dau (`fp_tools/grt_skew_screen.sh`:
  buoc STAMidPNR cua OpenLane tren trang thai buoc 39; hold skew / hold nom_tt / so endpoint): SA2 ky ten -1.92 / -0.126;
  DM_VC4 3600 cu (khong padding, resizer goc mac dinh, clock met1) -2.00 / -0.364 / 162; 3800 cu -3.77 / -2.209; 3500
  padding -2.66 / -1.250; 3400 padding + clock met4-met5 (sang loc `..._clkm4_pad1_grtscr_r1`) -3.79 / -2.133, overflow 16,
  `clknet_2_1_0_clk` 6.26 mm (clock van con 22 mm tren met3: dai lop khong giu chat khi thieu cho). Skew khong giam deu theo
  die; nguyen nhan la vai net than cay clock bi detour quanh cua khe giua hai hang macro D$ o mep hanh lang.
- Tiep (04:04 UTC): die 3600 voi phan truoc GRT GIONG HET vc4_corr3600x3400_f220_r1 (flow tat dinh: GRT dau tai lap skew
  -2.00) va knob sau GRT da do: cap 20, tat sua antenna o GRT, tat sua timing sau GRT
  (`config_corr3600x3400_f220_capm20_antoff_nogrtt.json`, run vc4_corr3600x3400_f220_capm20_antoff_nogrtt_r1). Hold 162
  endpoint -0.364 nam trong tam ECO hai luot (SA2: 112 endpoint -0.38 sau DRT, 139 buffer).
- Ket qua (05:11 UTC): GRT dau TRUNG run cu tung byte (sha256 guide va DEF; day 11.94 m, khong GRT-0103, P1 setup +1.168).
  Nhung p2 TRUOT: skew hold -3.41 ns, hold nom_tt -2.030 (1,863 endpoint), setup -0.535. Nguyen nhan: buoc
  `OpenROAD.RepairDesignPostGRT` (`repair_design_postgrt.tcl`) chen 368 buffer vao 2,289 net, hop phap hoa roi chay LAI
  TOAN BO global route; 744 net clock bi route lai, `clknet_2_2_0_clk` 1.1 -> 4.6 mm. Moi lan GRT toan bo la mot lan "boc
  tham" cho than cay clock o DM_VC4.
- Tiep (05:14 UTC): bo buoc sua DRV sau GRT (`RUN_POST_GRT_DESIGN_REPAIR` false; `DiodesOnPorts` khong lam gi vi
  `DIODE_ON_PORTS` none), GRT dau tot di thang vao DRT; DRV con lai bao cao theo loai (quy tac H). Full flow tu buoc 1:
  vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1 (`P2_MIN_SETUP=0` theo quy tac full flow). Rui ro: setup nom_tt
  sau GRT chi +0.046 (duong nua chu ky RAM bank[4] dout0 -> I$ bank[2] din0, slew 0.87 ns, qua nhieu buffer resize duoc).
- LEC SA2 (chuan bi): replay tong hop cua `sa2_..._rsztf_r1` voi 4 hook chup trang thai KHAC buoc 06 (77,157 so voi
  77,562 cell); voi 1 hook (`synthesize_n1only.py`, 06:35 UTC) TRUNG TUNG BYTE: `synth_replay_r14/sa2_rsztf_r1_n1only/
  n1_pre_abc_fast.il` la trang thai N1 dung cua OpenLane cho LEC SA2 (chua chay LEC; chu du an quyet dinh).
- Ban giao (06:40 UTC): `HANDOVER_CODEX.md` (tieng Anh) ghi trang thai, cac job dang chay va cach khoi phuc, danh sach
  viec theo thu tu (DM_VC4 ky ten va chay kep, cong suat SAIF, chung minh die nho nhat cho SA2 / DM_VC4, bang PPA cuoi,
  chay board voi RTL 6c4ccffd, LEC SA2 / DM_VC4, sua cong p2, don dep, git). Cong cu chi co trong phien truoc duoc chep vao
  repo: `asic/fp_tools/clock_detour.py`, `clock_layers.py`, `asic/gls/gls_power_csv_rebuild.sh`; nguon trang bao cao
  `results/report_page/bao_cao_soc_v5.html`; danh sach dung luong run `results/cleanup_candidates_20261009_sizes.txt`.
- **SA2 CHAY KEP XONG** (05:14 UTC): `..._rsztf_ecomaxmin_r2` (r2 full flow tu buoc 1, re nhanh sau buoc 47, ECO min_*) KY
  TEN SACH; so voi `_ecomaxmin_r1`: netlist cuoi va DEF trung tung byte (sha256 08901143 / 07a82698), SPEF trung tru dong
  `*DATE`, 319 / 319 metric trung. Ban ky ten cua r2 tung buoc cung trung r1 (P1, P2, ECO max_*, sign-off co so).

### 2026-10-09 14:23 FPGA: 10 seed chung, board seed 2; kiem tra tiep nhan

- Manifest 6c4ccffd khop 227 file; Quartus rfbht p1 / p2 khop 16 / 16 dong. Health check 300,000 dong: Windows 8 / 8,
  WSL 8 / 8 OK (`results/health_board_20261009/`). Replay N1-only SA2 khop SHA-256 netlist buoc 06: 46e3066895914f1a.
- Phuong an chon seed PPA rieng cho tung cau hinh bi thay the TRUOC khi refit hoac build SOF nao duoc khoi dong.
  Phuong phap moi: cung bo seed 1..10 cho bon cau hinh, so sanh ghep cap theo seed, hai luot doc lap; khong dung best seed
  rieng. Board chot seed 2 chung cho ca bon, chuan bi truoc va hen phien vat ly sau. Quy tac cap nhat o QUY_TRINH muc E.
- J1 VC4 3600 con chay buoc 43 DetailedRouting; log vong 6 con 14,060 vi pham. Chua co sign-off. J2 SA2 GLS: 10 / 12
  kernel PASS, tarfind va ud dang chay. Khong khoi dong lai cac job nay.
- drt_watch.sh dang chay con ap nguong sau vong 40, khac quy tac muc D (khong gioi han sau 40); chua sua script dang chay.

### 2026-10-09 14:36 VC4 dung o cong DRT; SA2 GLS xong; khoi dong ma tran seed chung

- Watchdog dung VC4 3600 luc 14:28: vong 10 con 5,689 > 5,000 (gated driver ghi STOP 14:29). Day la loi hoi tu,
  khong phai crash ngau nhien. Chua resume hay khoi dong run PD knob moi.
- Doc bao cao drc-10: 5,689 marker khop log, 4,512 short; 4,089 marker o x 1500..1600, y 1800..2000 um.
  Cum do co 1,392 cell (397 fanout, 105 max_cap buffer; 410 buf, 146 clkbuf); pin_hotspots max 34.5 pin / 100 um2.
  Day la chan doan cua MOT run that bai, khong phai ket qua PPA da chay kep. Bang chung:
  `results/vc4_corr3600x3400_drt_diagnosis_20261009.json`, `results/vc4_corr3600x3400_drt_region_20261009.log`.
- SA2 GLS 12 / 12 PASS, MCYCLE = RTL view ASIC = cua so SAIF. Bat dau power_cfg.ps1 Pass 1 (nom_tt, SPEF RCX);
  con Pass 2 va so tung truong. Khong cong bo so cong suat mot luot.
- Ma tran FPGA paired10_6c4ccffd_20261009 bat dau 14:33: bon cau hinh, seed chung 1..10, hai luot.
  Giu nguon goc cac phep do 1..4 da chay kep; them 5..10 va refit seed 2 cuoi moi luot (56 fit moi), tat ca tuan tu.
  Khong chon best seed rieng; board seed 2 chung. Bo kiem tra phuong phap 5 / 5 dat, co doi chung thieu seed / field /
  trung dong (`results/board_seed_method_validation_20261009.json`). Ma tran 10 seed chua du va chua la ket qua.

### 2026-10-09 15:14 Cong suat SA2 da chay kep; chuan bi board seed 2 chung

- T3 phan SA2 xong: 12 kernel GLS PASS, hai phien OpenSTA doc lap khop moi nhom power va thong ke nguon hoat dong;
  hai phien vectorless khop du sau nhom cua flow nom_tt. So da kiem chung cap nhat RESULTS muc 4.2 va REVIEW_RESPONSE A9;
  bang chung `_power_p1.csv`, `_power_p2.csv`, `_power_verification.json` theo tag SA2 ky ten.
- `verify_activity_power.py` so truoc khi lam tron CSV; doi chung thay doi nguon hoat dong va thieu nhom power deu bi bat.
  Day la hai lan OpenSTA tu cung dau vao SAIF, khong phai doc lai mot report; GLS chi capture mot bo SAIF nhu quy trinh T3.
- Ma tran 10 seed chung con dang chay; seed 5 luot 1 da du bon cau hinh, dang seed 6. Chua cong bo so moi mot luot.
- Tham chieu board dang sinh lai tren 6c4ccffd (`prepare_board_reference.py`, thu vien rieng moi config / pass, hai lane):
  100 truong hop x2, toan bo frame counter phai khop R14; khong build FAST_UART.
- Builder moi `build_board_matrix.py` chi nhan fit receipt seed 2 CHUNG va tham chieu da chay kep; chua build SOF nao.
  MIF chuan duoc backup / khoi phuc, reassemble bon diem va kiem manifest; ket qua vat ly o template ghi NOT_RUN.

### 2026-10-09 15:50 Tiep tuc ma tran seed chung va tham chieu board sau ngat phien

- Hai job Windows khong con PID / session luc kiem tra; log dung khoang 15:33, khong co ket luan FAIL cua cong cu.
  Khong quy loi cho phan cung. Hash dau vao giu nguyen; 8 fit va 38 case tham chieu da hoan tat / doi chieu van hop le.
- Archive 18 file, ca log fit seed 7 do dang va mo phong md5sum do dang, cung source driver truoc khi them resume:
  results/board_preparation_interrupted_20261009_1541/EVIDENCE.json. Khong xoa run folder / ket qua nao.
- Go lock fit mo coi sau khi xac nhan PID 41988 da chet va lock trung ban archive; khoi dong lai dung dau vao.
  Fit chua xong chay lai tu map; case mo phong chua xong compile thu vien rieng va chay tu dau. Giu 38 CSV khop R14;
  log tiep tuc co ten moi, khong ghi de dau vet ngat. Quy trinh resume ghi o QUY_TRINH muc E.
- Bo tiep tuc foreground complete_board_preparation.py dang cho hai cong VERIFIED; sau do tu build / audit 100 SOF
  seed 2 CHUNG. PID / log / trang thai o results/board_preparation_6c4ccffd_seed2_20261009.json; chua program board.
- Builder 11 / 11 doi chung dat; audit SOF / counter / template 5 / 5 dat bang fixture nho, khong phai phep do FPGA.
  MIF chuan va manifest 6c4ccffd khong doi. Khong sua driver dang chay, RTL, SDC, paper hoac repo cong bo.

### 2026-10-09 16:44 T9: bo doc p2 cho config tat sua design sau GRT

- Khong co flow PD dang chay khi sua gate_check.py. Bien P2_INITIAL_GRT_FALLBACK=1 mac dinh tat; chi doc route
  cuoi khi resolved.json ghi ro RUN_POST_GRT_DESIGN_REPAIR=false. GlobalRouting phai hoan tat truoc STAMidPNR-3.
- 34 doi chung dat: hanh vi mac dinh cua run DM / SA2 / VC4 giu nguyen; setup / hold / overflow am va thieu du lieu
  deu khong qua cong. Block final sign-off giu nguyen; khong sua nguong, RTL, SDC hoac clock.
- Bang chung: results/gate_p2_no_repair_20261009/verification.json va source truoc sua. QUY_TRINH D ghi bien moi;
  HANDOVER T9 hoan tat. VC4 cu van FAIL p2 tren hold am; khong tu dong CONTINUE.

### 2026-10-09 16:44 T4: chuan bi hai dien tich SA2 voi cong thuc da ky ten

- prepare_sa2_minimality.py sinh cap config max-first / min-second ECO cho 3400x3250 va 3400x3325.
  Chi doi DIE_AREA, CORE_AREA, MACRO_PLACEMENT_CFG; EXPERIMENT metadata ghi ro chua chay.
- Kiem 16 macro theo LEF: trong core, khong overlap. Hash va diff o results/sa2_minimality_preparation_20261009.json.
- Chua khoi dong flow: terminal WSL chua mo; ma tran fit / tham chieu board dang chay. Thu 3250 truoc, chi thu
  3325 neu 3250 that bai; ket qua ky ten phai full flow tu buoc 1, cung quy trinh hai luot ECO va chay kep.

### 2026-10-09 16:44 Watchdog: ap dung ban va quy tac sau vong 40 da duoc duyet

- Phe duyet ap dung proposed.patch trong results/drt_watch_rule_alignment_20261009/ da co; khong co flow PD dang
  chay luc sua drt_watch.sh. G5_UNLIMITED_LATE_PHASE=1 (mac dinh tat) bo nguong convergence / stall sau vong 40
  dung QUY_TRINH D; nguong den vong 40 va gate sign-off cuoi giu nguyen.
- 12 doi chung dat, bash -n dat, source da ap dung khop noi dung da duyet. Loi VC4 vong 10 (5689 > 5000) van dung;
  ban va nay khong phai sua nguyen nhan DRC cua VC4 va khong cho phep resume nguyen trang.
- Bang chung va hash source truoc / sau: results/drt_watch_rule_alignment_20261009/verification.json.
  Chua chay PD moi: can terminal WSL mo va tai nguyen phu hop; khong dung meo giu VM nen.

### 2026-10-09 17:03 DM_VC4: chuan bi gia thuyet gian cell tren die 12.24 mm2

- prepare_vc4_padding.py sinh hai config (max-first va min-second ECO), chi doi GPL_CELL_PADDING / DPL_CELL_PADDING
  tu 0 thanh 2, tuc 1 site moi ben theo Tcl hien tai. Die, macro, resizer corners mac dinh, clock layers, RTL va SDC giu nguyen.
- Gia thuyet dua tren diem nong short / spacing cua run dung o vong 10; khong doi watchdog de cho qua loi nay.
  Bang chung / lenh / tieu chi: results/vc4_padding_hypothesis_20261009.md; hash / diff: results/vc4_padding_preparation_20261009/inputs.json.
- Chua chay PD; can terminal WSL va tai nguyen. Full flow tu buoc 1, giu sau p2 de chan doan skew / nghen truoc DRT.
  Khong tao nhieu thi nghiem knob song song.

### 2026-10-09 17:03 DM: thieu bang chung STA cong suat lan hai

- Chi tim thay 12 report power va vectorless luot dau trong results/gls_power_r14F_A/, khong co .power.p2.rpt
  hay receipt chay kep. Khong ket luan chua tung chay lan hai; bang chung hien tai chua du de cong bo ket qua chay kep.
- Hash 12 pin-SAIF, report dau, netlist, SPEF va dau vao; chuan bi Pass 2 va lenh verify trong
  results/dm_activity_power_second_pass_preparation_20261009.json. STAPostPNR DM la buoc 58, buoc 57 la RCX.
- RESULTS / REVIEW_RESPONSE danh dau cong suat va EPI DM chua du bang chung; CSV / report cu giu nguyen.
  Run PD DM van khoa va ky ten sach; chua chay STA moi hoac PD lai.

### 2026-10-09 17:07 T6: bang PPA phan da du bang chung cho DM va SA2

- asic_ppa_audit.py doi chieu day du key set / 319 metric, gate final hai run, netlist / DEF tung byte va 3 SPEF
  chi bo dong DATE. Du 9 goc timing, buffer theo flow / moi ECO / cell master cuoi, SA2 SAIF power raw hai luot.
- 17 doi chung chan bang chung thieu / sai dat. So thu tu thu muc ECO DM khac nhau (47 va 48) la provenance;
  cung StepID va 39 buffer chen, khong phai khac phep do. Nguong ky ten khong doi; VC4 that bai khong duoc nhan.
- Bang / receipt: results/asic_ppa_verified_subset_20261009.md va .json. Chi la phan da kiem chung, khong phai
  T6 cuoi: DM STA lan hai, SA2 minimality va VC4 sign-off con thieu. CPI / hit dung hai CSV rfbht hien tai.
- RESULTS sua goc hold xau nhat DM thanh max_ff (-40 C, 1.95 V), theo so khop r1 / r2; log lich su giu nguyen.
  README sua lenh chuoi hien tai sang run_fullchain_rfbht.sh. Khong khoi dong lai chuoi da dat.

### 2026-10-09 17:57 T6: cap nhat bang hop nhat tu nguon rfbht da chay kep

- unified_table.py dung cap Embench / CoreMark rfbht hien tai, full-iteration R14 da chay kep, va seed 2 CHUNG
  cua fit rfbht. Bo so LE / Fmax cua RTL cu; chi bo cot seconds khi so hai pass FPGA, khong bo truong hardware.
- SA2 GLS / cong suat doc dung tag ky ten; raw STA hai luot va CSV phai khop. DM power giu pending thieu STA lan hai;
  board ghi NOT_RUN. CoreMark ghi ro mo phong RAM 32 KiB. Nguon / phuong phap / corner ghi trong bang.
- Da sinh lai results/unified_metrics.md va .csv; CPI / hit khop bang T6 tu cap CSV rfbht hien tai.
  Khong dung so ma tran 10 seed chua qua cong chay kep, khong chay lai phep do nao.

### 2026-10-09 17:57 T10: archive bang chung va chuan bi de xuat 19 run, chua xoa

- Danh sach sizes cu la inventory 40 run, gom ca run phai giu. prepare_cleanup_proposal.py tach 19 PROPOSE_ONLY,
  10 KEEP, 11 DEFER; tong sizes goc cua 19 run la 89,857 MB theo inventory, khong phai dung luong reclaim do moi.
- Archive 19 run du resolved.json / metric gop / step list / log / timing report, so hash source va ban sao.
  Text evidence giu khoang 7,923 MiB; khong xoa source. De xuat: results/cleanup_proposal_20261009.md va .json.
- Lan archive dau dung o nhanh SA2 thieu resolved.json; giu archive da xong / ban sao do dang. Kiem toan thay
  hai nhanh SA2 / VC4 thieu resolved.json; dua ca hai vao DEFER, khong gia lap config hay cho qua dieu kien archive.
- Resume chi kiem lai archive hop le va luu run con lai; synthesis provenance va VC4 control cho T5 cung DEFER.
  Da trinh duyet 19 run; chua co phe duyet xoa. cleanup_deleted.txt va bang muc 10 chua ghi viec xoa nao.

### 2026-10-09 17:59 T7: 100 cap tham chieu board hien tai da mo phong kep

- prepare_board_reference.py hoan tat 17:56:04: 200 case = 25 firmware x 4 config x 2 pass, thu vien compile rieng.
  Hai CSV 100 dong khop moi truong, khong bo cot; toan bo frame counter khop R14, RTL 6c4ccffd.
- Da so lai 34 hash dau vao / firmware / CSV aggregate voi metadata VERIFIED_100_PAIRED_ROWS_EQUAL_R14.
  Bang chung: results/board_reference_6c4ccffd_20261009_p1.csv / _p2.csv va _inputs.json; log tiep tuc giu nguyen.
- Day la tham chieu mo phong de lap INDEX, khong phai do tren board. Ma tran fit 10 seed chung van dang luot hai;
  coordinator chi build 100 SOF sau khi fit receipt VERIFIED. Board seed 2 chung; phien vat ly van NOT_RUN.

### 2026-10-09 18:33 Board: buoc tiep tuc dung, giu bang chung

- Ly do: fits job stopped: Only 5384 MB free; owner scheduling decision required; no retry
- Khong restart job, khong xoa output, khong program board; chi kiem tra read-only truoc khi xu ly tiep.
- Trang thai: results/board_preparation_6c4ccffd_seed2_20261009.json.

### 2026-10-09 18:40 Kiem toan workspace va don 17 run, 22 thu vien mo phong

- Kiem ke 73,861 file, 11,891 thu muc, 254.6 GiB logic; doc text nguon / config va doi chieu raw RTL, formal,
  UVM, Embench, ACT4, board reference, PD. Ban do chuc nang va pham vi: WORKSPACE_MAP.md;
  chi muc tung path / file nguon: results/workspace_audit/. File nhi phan va ma ben thu ba chi kiem ke.
- 19 archive duoc so lai SHA source / ban sao, metric gop va step list. Quet dependency toan workspace tim them
  final_B (LEC / replay) va VC4 clkm3_pad1_r1 (3 nhanh GRT). Giu hai nguon nay; 17 run khong con dependency da xoa,
  82,819,435,929 byte logic; receipt cleanup_execution.json va cleanup_deleted.txt. Khong sua run ky ten / RTL.
- Xoa 22 thu vien Questa idle, tai tao duoc (2,605,315,241 byte); giu 16 compile artefact board va moi raw log / CSV /
  signature / SAIF / SPEF. Receipt cache_cleanup.json. Tong 79.558 GiB logic, khong dong nhat voi disk reclaim NTFS.
- 21 file nguon / coverage cu luu ZIP, kiem SHA; xoa 20 ban goc va doi ten golden helper bi tool review tu choi
  (blocked by policy), chua thay doi ban goc. Xoa 4 VCD va 2 log root cung bi tu choi. Khong doi cong cu de lach chan.
- Sau khi coordinator da thoat, doi HANDOVER_CODEX.md thanh PROJECT_STATE.md; luu ban goc va coordinator goc,
  cap nhat hai tham chieu trong coordinator, khong doi logic. Bo persona khoi tai lieu trang thai hien hanh.
- Sua mo ta R16 hien hanh, so FSM I/D, nguon ket qua, lien ket diag va cac gioi han kiem chung. Them bai hoc moi
  vao muc 9; khong sua nguon firmware / testbench / manifest. Hash input ASIC ngoai manifest luu rieng.

### 2026-10-09 20:36 Chot kiem toan va kiem tra bang chung sau don

- SOURCE_CATALOG.md co 1,985 entry text / config / Markdown, path inventory hien tai 61,666 file;
  inventory truoc don giu rieng. WORKSPACE_MAP.md phan biet current source, result, historical proof, vendor va build.
- verify_workspace_audit.py PASS: manifest 227 file unchanged; header va moi field cua 7 cap CSV khop;
  hash 25 firmware / 7 reference input / 16 compile / 200 case / 2 output board khop, 32 fit input khong doi.
  Archive va deletion receipts khop; 42 input moi ASIC design khong doi. Day la kiem tra evidence, khong la lan do moi.
- Cao nhat receipt fit la 51/56, khong phai 50 luc job cuoi dang chay: con p2 DM_DSE seed10 va bon p2 seed2.
  Fit / coordinator da thoat; RAM hien ~4.0 GiB, chua du guard 6,000 MB. Khong restart / relax guard / dong chuong trinh khac.
- Generator va bang unified / M2 ghi ro CoreMark full-program / RAM32KiB / CRC gate pending; khong doi counter.
  Tai lieu trang thai va bang alias khop sau doi ten. Source / doc / coverage originals bi tool review chan van con nguyen;
  hai raw root log da copy-only vao source_archive, khong retry xoa. RTL / firmware / TB va repo cong bo khong sua.

## 8a. 2026-10-08: register file va BHT vao M9K tren FPGA (A1, phuong an b); conflict probe mo rong

### 2026-10-08 Thiet ke, chung minh, testbench

- Muc tieu (A1): core DM 6,451 LE trong do register file 1,386 va BHT 962 LE nam o flip-flop. Chuyen ca hai vao M9K, chi
  tren FPGA (`ifndef __openlane__`), giu dung tung chu ky. Ap bang `scripts/apply_rf_bht_m9k.py` (tu ban R16, chay thu tren
  ban sao truoc).
- regfile: hai ban M9K (moi cong doc mot ban), dia chi doc dang ky tai canh la truong rs ma `instr_d` nhan tai canh do (dau
  vao D cua `instr_d`, day `instr_d_next` trong datapath); RAM tra du lieu cu (truoc lan ghi cua canh do), lan ghi do duoc
  bypass tu ban sao dang ky we / rd / wd; write-through cua chu ky hien tai giu nguyen; x0 = 0.
- bht_2bit: bo dem trong hai ban M9K (doc fetch, doc update) dia chi theo dau vao D cua `pc_f` / `pc_e`; bit valid moi entry
  (flip-flop, reset bat dong bo) giu nghia "reset dua moi entry ve 01"; lan update cua canh truoc duoc bypass cho ca hai
  cong doc.
- Checker chi mo phong (translate_off) dat mang cu canh mang moi, `$fatal` o chu ky dau tien khac nhau; liveness: ep `q1` /
  `qf` sai tren up_crc32 thi ca hai checker dung mo phong (`scripts/rf_bht_m9k/checker_mutation.sh`).
- Chung minh k-induction (`asic/equiv/rf_bht_m9k/`, gen.py + run.sh, Yosys `sat -tempinduct`): (1) regfile moi == cu khi dia
  chi doc tuan giao thuc read-ahead, bat bien noi dung hai ban M9K == mang cu; (2) BHT moi == cu, bat bien theo entry (valid
  thi hai ban == mang cu, khong valid thi mang cu = 01); (3) giao thuc trong datapath: `instr_d`, `pc_f`, `pc_e` bang dung
  `*_next` cua canh truoc. That 3/3 PROVEN; doi chung am 3/3 FAIL co phan vi du (bo bypass cua regfile, bo kiem valid cua
  BHT, bo flush trong `instr_d_next`). Mot dot bien bi loai vi tuong duong: bo `stall_pipe` khoi `pc_f_next` van chung minh
  duoc, vi `stall_f` da giu `pc_f` moi khi `stall_pipe` bat.
- Testbench: 74 truy cap truc tiep `regfile.regs[...]` / `u_bht.bht_mem[...]` trong 7 TB + UVM chuyen sang macro
  `tb/rf_bht_backdoor.svh` (ghi backdoor tac dong nhu ghi mang cu: moi ban, mang tham chieu cua checker, thanh ghi doc /
  bypass dang giu entry) bang `scripts/apply_rf_bht_m9k_tb.py`. `tb/bht_tb.sv` viet lai theo giao thuc read-ahead, them
  BHT-7..10 (doc qua RAM khong bypass, update lien tiep hai entry, fetch dung entry dang update, reset giua chung).
  `tb/regfile_tb.sv` moi: 20,073 chu ky so voi mang bat dong bo, phan loai tung lan doc (RAM / lan ghi canh truoc /
  write-through) va doi ca ba duong. Ca hai bench dung tren view ASIC (mang cu) lan view FPGA.

### 2026-10-08 Dong bang, chuoi day du, Quartus sang loc

- Dong bang lan dau dcbf3495. Chuoi day du (`scripts/run_fullchain_rfbht.sh`, cac lane song song moi lane mot thu vien
  Questa: ~55 phut thay vi ~5 gio) 46 OK, 1 FAIL: lint_asic `SYNCASYNCNET`, checker BHT kiem muc `reset_n` trong khoi
  `@(negedge clk)` (lint_asic khong bo qua translate_off). Sua: so sanh o canh len trong chinh cau truc reset bat dong bo cua
  mang tham chieu (doi `apply_rf_bht_m9k.py`, ap lai tu ban R16). Dong bang lai **6c4ccffd** (chi khac bht_2bit.v, phan
  translate_off). Chuoi cua dcbf3495 (luu `results/fullchain_rfbht_dcbf3495/`): Embench 72 + 72, FAST_HIT 60 + 60, CoreMark,
  random diff 50 seed (ca hash), view ASIC, ramsweep deu TRUNG R16 tung truong; ACT4 43/43 x2, chu ky trung lan truoc.
- Quartus sang loc (dcbf3495; tong hop giong 6c4ccffd vi chi khac code translate_off), dm_4kb seed 2: LE 15,440 -> 12,815
  (-2,625, -17.0 %), thanh ghi 8,430 -> 7,198, M9K 26 -> 30 (+2 regfile, +2 BHT), setup s85 0.778 -> 0.870 ns, Fmax s85
  52.02 -> 52.27 MHz. Quartus x2 day du chay sau chuoi cua 6c4ccffd.
- Chuoi day du tren **6c4ccffd** (21:17-21:56, 39 phut): **0 loi**. Static (latch, lint_rtl, lint_asic) sach; regression x2
  178 / 178 PASS (R16: 161, them tb_regfile va BHT-7..10); UVM 5/5 x2, AXI 3 kich thuoc line x2; Embench 72 + 72 va
  FAST_HIT 60 + 60, CoreMark (6 + 5), random diff 50 seed (ca hash), view ASIC 12 kernel, ramsweep: pass 1 = pass 2 va TRUNG
  R16 tung truong; directed ISA va bo dong bo view ASIC PASS; checker liveness 2/2; ACT4 43/43 x2, chu ky trung lan truoc;
  khong co thong bao checker M9K trong log nao. Chung minh k-induction chay lai tren cay that: 3/3 PROVEN, 3/3 doi chung am
  co phan vi du. Fit Quartus dau tien cua 6c4ccffd (dm_4kb seed 2) trung tung truong fit sang loc.
- Tai nguyen: chay song song chuoi 9 lane + Quartus + 2 flow PD lam RAM trong cua Windows xuong 1.6 GB, CPU 100 % (21:30).
  Dung Quartus bang co abort sau fit dang chay; chay lai Quartus x2 sau chuoi. Quy tac: khi 2 flow PD chay, khong chay
  Quartus cung luc voi chuoi nhieu lane.
- ASIC: moi config PD doc snapshot RTL (`asic/snapshots/rtl_r14` cho SA2 / DM_VC4, `rtl_r16` cho tong hop R16), khong doc
  hdl/. Vi vay buoc "tong hop SA2 / DM_VC4 so netlist voi run PD" cua `run_rf_bht_m9k_asic_checks.sh` ban dau la vo nghia
  (ca hai doc cung snapshot) va da bo. Bang chung dung: dong nhat token cua view ASIC (3/3 file, co doi chung am la view
  FPGA phai khac) va tong hop DM tu snapshot moi `rtl_rfbht` (config_rfbht_synth.json) so voi `dm_synth_r16_r1`.
  Ket qua (14:25 UTC): netlist `dm_synth_rfbht_r1` == `dm_synth_r16_r1` tung byte (sha256 da06d38f); cong lint baseline
  OpenLane 0 canh bao moi (1 muc baseline khong con, giong R16). Chip DM da khoa (r14F, PD input == R16 da chung minh trong
  `asic/equiv/r16_eq`) va hai run SA2 / DM_VC4 (snapshot rtl_r14) van dung cho RTL nay.

### 2026-10-08 Conflict probe mo rong (sw_metrics/conflict)

- Probe cu (`sw/embench_cachesweep.c`) chi doc N dong cua MOT set theo vong; o diem thiet ke 4 KiB stride 1024 cua no khong
  con dung do nhau. Probe moi (ngoai sw/, khong vao manifest): dong (s, k) o 0x0C00 + k * SPAN + s * 16 (cung set o moi to
  chuc voi cung s), vung 0x0C00-0x3DFF de trong (link_probe.ld: image < 0x0C00, stack 512 B), 35 thi nghiem: tuan hoan 1 set
  N = 1..8, nhieu set N = 2 / 3 / 4, thu tu ngau nhien (xorshift32), doc-sua-ghi, doc dong 0 ghi dong khac, chi ghi. Moi
  cua so do do chinh ham la mo / dong (khong co truy cap stack ben trong); firmware tu kiem so truy cap == P x S x N.
  `tb_conflict_probe.sv` in mot dong moi snapshot; `model_windows.py` chay lai trace D$ qua mo hinh cache doc lap
  (`scripts/cache_model.py`) tung cua so.
- 4 KiB (SPAN 4096, 6 cau hinh): 180 / 180 cua so TRUNG mo hinh. SA2 giu 2 dong / set o moi set (toi 32 set); DM_VC4 giu 2
  dong / set chi toi 4 set (victim buffer 4 entry dung chung) roi con 50 %, N = 3 chi toi 2 set; thu tu ngau nhien giam dan
  (90 / 84 / 76 / 65 % voi 5 / 6 / 8 / 16 set) thay vi sap; DM giu duoc N = 2 trong MOT set nho L0 2 entry; victim hit ton
  ~19-22 chu ky / truy cap so voi ~10-14 khi hit mang chinh.
- Loi gap khi chay: (1) ban SPAN 1024 bi GCC shrink-wrap luu s0 SAU khi mo cua so (1 doc + 1 ghi stack), firmware bat duoc
  va bao FAIL; sua bang `-fno-shrink-wrap`. (2) bang UART in sau moi cua so ton ~19M chu ky (115200 baud), ban 1 KiB (35
  dong) vuot gioi han 20M cua TB; nang len 40M. Khi sua (2) toi da sua `run_conflict_probe.sh` luc no dang chay (vi pham quy
  tac "khong sua script dang chay"); `sed -i` thay file moi nen ban dang chay doc ban cu; luot do bi bo, chay lai toan bo.
- Ket qua cuoi (23:46): 24 run x 2 luot, 390 cua so, MOI cua so TRUNG mo hinh, luot 1 = luot 2 (`results/conflict_probe.csv`).
  1 KiB (hinh hoc bang 6 cua bai): DM_VC4 mot set vong N <= 5 -> 100 %, N = 6 -> 66.7 %, N = 7 / 8 -> 0 %, nhung NGAU NHIEN
  N = 8 -> 59.0 % (sap la do thay the vong tron gap truy cap tuan hoan, khong phai do dung luong); SA4 N <= 4 -> 100 %, N = 5
  -> 0.3 % (PLRU vong), ngau nhien N = 8 -> 49 %; DM giu N = 2 (98.4 %) nho L0 hai entry, DM_DSE (khong L0) 0 %: diem gay cua
  DM tren RTL hien tai la N = 3, khong phai 2 nhu probe cu. Nhieu set: DM_VC4 giu N = 2 toi 4 set, 5 set tro di 50 % (victim
  buffer 4 entry dung chung); SA2 / SA4 giu o moi set.

### 2026-10-09 21:10 UVM bon cau hinh, AXI stress va UART RX da chay kep

- Runner bo sung `scripts/verification/run_uvm_matrix.py`: 48 ca moi luot; 4 cau hinh cache x directed/periph/RX
  x seed 1/2/3, AXI stress 4 line size x 3 seed. Hai lan bien dich va mo phong doc lap; so moi truong scoreboard khop.
- UART truyen 0xa5 va 0x3c qua chan rx, CPU doc qua APB va tu kiem; doi chung truyen sai 0xa4 bi bat ca hai luot.
  Adapter chi chon CACHE_CONFIG va noi assertion tag-allocation dung nhanh DM/DSE; khong tat assertion.
- Nguon frozen 227 file khong doi; adapter, hex, log, status va UCDB luu rieng. Receipt:
  `results/uvm_cache_uart_20261009/verification.json`. Coverage la functional, khong phai code coverage.

### 2026-10-09 21:10 Adapter architecture 1 MiB da kiem tra ca nua tren

- `scripts/verification/run_architecture_window.py` generate ban sao TB voi 6 index [18:2] -> [19:2]; khong sua
  nguon frozen. 43 ACT4 x2 co signature tung byte, cycles va retirements trung ket qua truoc.
- Test moi doc/ghi 0x1000 va 0x81000 doc lap, thuc thi lenh o 0x90000; signature nua tren dung o hai luot.
  Ban adapter cu chay cung chuong trinh bi timeout dung do alias, doi chung duoc bat.
- Receipt `results/architecture_window_20261009/verification.json`; pham vi I/Zmmul unprivileged giu nguyen.

### 2026-10-09 21:17 Cong CSV va random fail-closed, random 50 seed da chay kep lai

- `verify_double.py` kiem day du schema, field count, key duy nhat va metric khong rong; khong so chi cot giao nhau.
  `run_random_diff.sh` gate rc Questa, PASS/termination, loi Fatal/Error, trace day du va tung byte; raw rieng moi pass.
- 43 controls bat ca truong hop mat cot / hai metric cung rong / hai trace cung bi cat. Fullchain caller truyen pass
  va luu PIPESTATUS ngay sau pipeline, gate process rc truoc chap nhan CSV; bash -n va false-pipeline control dung.
- Hai lan compile moi va 50 seed doc lap moi lan: 100/100 case VERIFIED, 50 paired rows va full trace SHA/bytes
  trung RF/BHT cu. 500 raw files khop 100 case receipts. `results/random_diff_checked_20261009/verification.json`.
- Generator Windows ghi CRLF nhung manifest hex hash duoc tinh LF truoc khi ghi; checker kiem dung hash text LF,
  receipt luu them SHA256 byte file thuc. Khong sua generator hay RTL, khong mo rong thanh oracle ISA doc lap.

### 2026-10-09 21:32 CoreMark CRC nguon va counter hien tai da chay kep

- Quan sat thu dong byte APB UART TX trong mo phong, khong sua firmware/TB/RTL frozen. Sau preflight dau
  bi dung vi regex compile library bat nham `vlog -work`, guard da doi sang parse target Tcl thuc te.
  Lan preflight bi dung duoc giu rieng; dot checked moi chay 11 diem x2, CRC seed/list/matrix/state/final
  khop reference trong core_main.c, ca 40 counter bang baseline. RAM32KiB, window full coremark_main,
  thoi gian ngan nen khong official score. Scope nay khong thay cho CRC toan bo sweep capacity cu.
- Runner canonical run_coremark.py da them observer va gate CRC truoc CSV/PASS, giu CLI va 43 cot.
  DM256 compile moi hai lan, moi cot bang baseline; 15 controls bat CRC sai/thieu du counter hop le.
  Bang chung o results/coremark_crc_checked_20261009 va coremark_canonical_checked_20261009.

### 2026-10-09 21:38 Tach dependency LEC khoi run PD cu final_B

- Sau archive 6 input va doi chieu 562 evidence files, 14 reader Yosys/PowerShell/Bash chi doi literal path.
  Formal model byte-identical, frozen RTL 42 file con du, target DM r1/r2/negative control giu nguyen.
  --verify-staged va --verify-applied dat; syntax va substitution control dat. Khong chay lai proof.
- Lenh native PowerShell xoa final_B bi automatic tool review tu choi `blocked by policy`; khong co ly do
  chi tiet. Folder con nguyen, khong doi cong cu de thu lai. Run khoa DM va cac flow hien tai khong doi.
  Bang chung migration va proposed.patch o results/final_b_dependency_migration_20261009.

### 2026-10-09 23:28 FPGA muoi seed chung va SOF seed2 da hoan tat

- Continuation foreground Windows doi dung >=6,000 MB, khong dong chuong trinh khac. Khi bo nho du, nam
  fit con lai chay tuan tu; 56/56 additional fits du, bang40 cap seeds1..10 khop115 hardware fields.
  Seed2 dung chung cho DM/SA2/DM_VC4/DM_DSE, khong chon seed rieng theo PPA. Runtime khong la hardware metric.
- Builder chi update_mif/asm tu fitseed2 da kiem, khong fit lai:100 SOF, INDEX expectedMCYCLE/MINSTRET/hash,
  template200 dong NOT_RUN. Canonical MIF/assembly da khoi phuc. Board vat ly hen sau, khong co so board.
  Bang chung continuation plan/progress/PPA/board_audit va output_files_board_matrix_6c4ccffd_seed2/.

### 2026-10-10 02:00 Do STA cong suat DM luot hai tu SAIF da luu

- Kiem33 input frozen khop SHA va chua co output luot2. Chay foreground power_cfg.ps1 -Pass2 voi
  lockedDM r14F_A, fill55 va STAPostPNR58, goc nom_tt_025C_1v80, RCX SPEF cua run. Khong chay lai PD,
  khong sua layout. Moi report luot2 la mot phienOpenSTA moi; GLS/SAIF luot truoc giu de tai lap power.
- Log results/dm_activity_power_20261010_p2.log. Tat ca6 power groups x4 fields va activity-origin fields
  phai khop truoc khi publish power/EPI. Quan sat memorySTA tang sau startup; khong chay PD/formal song song.
- Ket thuc va verify:13 phienSTA moi deu rc0 (12 kernel +vectorless); moi group/origin khop luot1 va vectorless
  khop flow. Input33SHA giu nguyen; receipt dm_activity_power_second_pass_20261010.json va paired powerCSV.

### 2026-10-10 02:16 Bang FPGA, ASIC va unified da kiem toan lai theo evidence moi

- Kiem doc lap40 cap FPGA115 cot,100 SOF va200 dong NOT_RUN, firmware/counter/source/seed2/hashes va MIF restoration.
  Cac controls du lieu sai bi bat; receipt fpga_common_seeds_completion_audit_20261010. Khong do lai board.
- ASIC subset du319 metric moi cap DM/SA2, signoff/artifact/timing du9goc va12 raw activitySTA da kiem lai;
  bang datedOct10 giu banOct9 lich su. Unified gateFPGA40 cap, CRC11 cap; chi2 o DM power/EPI thay doi,
  98 o metric con lai giu nguyen. Nguon/report/corner/method ro trong bang; VC4/minimality/finalLEC con pending.

### 2026-10-10 02:23 Kiem moi truong va hang cho foreground VC4 padding

- Host probe300k dong:8Windows va8WSL deuOK, logs giu rieng. Day la check tokenisation, khong exhaustive hardware test.
  External tool probe dau doan sai source-tree devshell-dir; actualpaths lay tu launcher nix-shell deu co.
  Actualtools9 va external927 file duoc SHAcheck, khongPD/synthesis trong preflight.
- Wrapper optional moi, controls38ca, plan219inputs gom42RTL/8macro/SDC20ns va writtenhypothesis.
  Hang cho Windows doi >=10,000MB, moi30s; childWSL foregroundgiuhetP1/P2, STOP_AFTER=p2 de inspect.
  Coqueueabortchi nganlaunch; khongkillchild. NguongWSL/gate/signoff khong doi. Ghi cu ownerterminal da doi
  theoQUYB: terminal rieng can cho job phai song qua controlling-session exit; flow foreground phai giu client.
  Queue receipt/log o results/vc4_padding_queue_20261010; chuaPD khi Windowschi2,260MB free.

### 2026-10-10 07:47 VC4 padding bat dau full flow tu step1

- Sau khi Windows free dat15,149MB va WSL available23,171MB, queue launch candidate
  vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1. Kiem219 input SHA va manifest227file
  IDENTICAL truoc launch; chi GPL/DPL padding0->2 theo hypothesis da luu, die12.24mm2 va clock20ns giu nguyen.
- WSL client foreground giu suot child; flow hold sauP1/P2 de xem gate/clock/congestion. Day la luot1 dang chay,
  khong signoff hay double-result. Khong dong ownerapps; gate/signoff khong doi. Receipt/log trong
  results/vc4_padding_queue_20261010/, gated_pd.log va candidate run. Khong sua active flow scripts.

### 2026-10-10 07:50 Dong reset-base va clock subproof, gioi han lai DM LEC

- Rasoat SA2 thay legacy const_check/inv_check chi sample reset; mapped cut khong kiem clock/polarity.
  Khong suy zeroSATcounterexamples thanh full sequential proof. Legacy SAT/CEC/algebra/negative artifacts giu nguyen.
- Hai invocation cofactor moi tren preserved raw gold AIG, moi PI khac symbolic:235constant,28duplicate va4FSM
  reset-base duoc prove, reset synchronizer D tu externalreset duoc prove truoc khi tieQ. Hai report byte-identical;
  2positive va24negative controls duoc bat, gom exactwitness rare24input. Raw19,458Q khong tieconstant/onehot.
- Hai invocation streaming clock tren4 preserved flatIL deu positiveedge/scalar topclk, moi semanticfield khop;
  3positive+21negative controls PASS, peak19.66MiB. Day chi clock prerequisite, khong fullLEC/hardwaremeasurement.
- N1/final paired reset relation (11,560 goldpairedD van symbolic), bridge exactinput invariant/FSM va
  setundef-undriven-zero/source-model abstraction con mo. Currentdocs khong con claim fullDMLEC vo dieu kien;
  khong ket luan RTL sai, khong doi PD/GLS/power. SA2 chi77inputs+24preparedartifacts verified, chua proof.
- Bang chung: lec_proof_scope_20261010.md/json, dm_reset_base_structural_20261010_p1/p2.json,
  execution.log, lec_reset_base_controls_20261010.json, dm_lec_clock_audit_20261010/receipt.json.

### 2026-10-10 07:51 Goi tai lieu viet bao da dong va kiem ZIP

- results/colleague_materials_20261010.zip gom121file,114sourcecopy,3,265,539byte compressed.
  28cap CSV/2,124pairedrows, ACT4 JSON44cap, model/conflict/IRQ va hashmembership/ZIPCRC/roundtrip deuPASS;
  portable verifier khop120payloadfiles. Khong chay them measurement trong packaging.
- Giu originalmanuscript1KiB va5imageco san dung byte;5PDF references thieu o published va research workspace,
  ghi ASSET_STATUS/MISSING_ASSETS. Manuscipt chua sua. Goi co currentPPA/verification/LECproofscope,
  10commonseeds va boardINDEX/templateNOT_RUN; khongnhung100SOF/database/loglon vao ZIP.
- Provenance/SHA o SOURCE_ORIGINS.csv, SHA256SUMS.txt va package_receipt.json; README ghi boundary,
  FPGApowerestimate, ASICnom_ttSAIF, CoreMarkRAM32KiB/fullprogram, boardpending va fullsequentialLECopen.

### 2026-10-10 08:06 Bo sung CRC cho toan bo CoreMark sweep

- Runner moi scripts/verification/run_coremark_sweep_crc.py bat dau 92point x2 tu private compilation rieng,
  mot simulator moi luc. 49base va43FAST point dung dung grid da luu; SA4_256B_L16 van excluded do4sets
  khong du3bit index cho L0. Kiem actual elaborated I/D lines, linewords, victimdepth, FAST, RAM, L0 va predictor.
- Source-known numeric CRC va40counter phai khop ca2luot va historical sweep, moi processRC/log/UART duoc luu.
  36negative/positive metadata/profile controls PASS truoc launch; khong sua RTL/TB/firmware hay sweep cu.
- Windows free11,443MB, WSL available21,227MB, swap0 truoc launch; mot PD tai postCTS repair va mot RTLsim,
  khong Quartus/GLS/verification multilane. Singlelane guard3,000MB theo measured~0.3GB private process.
- Evidence dang IN_PROGRESS o results/coremark_sweep_crc_20261010; chua nang claim M2/RESULTS.
  RAM32KiB/fullprogram/ITERATIONS1 van khong la officialscore. ZIP dongnghiep da dong duoc giu nguyen.

### 2026-10-10 08:10 VC4 postCTS native crash va retry chan doan khong doi recipe

- Luot fullflow padding dung08:07 tai37-openroad-resizertimingpostcts, Signal11 o sta::PathVisitor::visitEdge
  trong RepairSetup sau iteration330. Khong state_out/runtime; P1=MISSING, chuaGRT/P2. DriverchildRC0 khongPASS.
- Kiem219pinnedinputs khop, synthesisNL khopbaseline; toolpeakRSS1GiB/thread2, WSLavailable23,159MB/swap0.
  Kernelghi nativeSignal11; khongOOM trong80dong cuoi, queryWHEA45phut khongevent. Chua xac dinh nguyen nhan,
  khongganloimay. Failure receipt va SHA o results/vc4_postcts_crash_20261010.json.
- Giu37 thanh crashed-37-openroad-resizertimingpostcts, khongxoa. Mot diagnosticretry khongdoi config/RTL/corners
  batdau08:10 tu completed36 qua gatedresume step:OpenROAD.ResizerTimingPostCTS, chi toiGlobalRouting.
  P1 phai check that sau khi ketthuc; finalgate cua partialdriver khongla signoff. Neu signaturelaplai thi dung,
  dieutra deterministictoolfailure; khongthu knobmoi. Logdecision da ghi gated_pd.log truocrename/retry.

### 2026-10-10 08:25 Bao cao de doc ket qua va clarification model LEC

- Bao cao ASCII moi results/bao_cao_trang_thai_20261010.md dan38link toi RTL/alias, inventory, verifieddata,
  boundary proof/benchmark/board va cleanupoutcome. Day la snapshot, khongclaim jobdangchay dafinished.
- Maintaineddocs sua4seedthanh10commonseed theoQUYE, "published4KiB" thanh research4KiB,
  corridorDMpower thanh archiveGLS/SAIFchua pairedSTA, va M1CoreMarkngoai11diem CRCverified vanprovisional.
  ZIPwriting da dong giu nguyen; thaydoi moi se kem supplement.
- Audit modelinitialization doc40inputSHA, phanloai11,560unresetstates theo tag/RF/SRAMread, khongtiezero.
  LocalBooleanPDKmux coverage vaN1PClow-X enablemask duoc check, nhung chuafullundefinedcone/globalLEC.
  FSM structuralscreen ghi assumptions/resetdeassert vaUNKNOWN conlai, khongsuyUNKNOWNthanhPASS.
  Report: results/lec_model_initialization_audit_20261010.md/json. KhongRTL/tool/gatechange.
- IndependentCRC92verifier36sourceprofilecontrols cua runner va26raw-evidencecorruptioncontrols daPASS;
  fixtureNOT_A_MEASUREMENT vaIN_PROGRESSreject duocghi. Chi auditraw khi184simulations that complete,
  khongco freshmeasurement trongverifier. CRC/PDjobs van tieptuc, clientforegroundduocgiu.

### 2026-10-10 08:39 Xuat figure research tu cac bang hai luot da verified

Hai figure common-seed FPGA PPA va Embench controller/organisation duoc xuat PDF/SVG/PNG
kem source, paired inputs, plot CSV va portable verifier. 40 cap FPGA x115 truong,
72 cap Embench x43 truong va condition cua80 power report duoc kiem tra; 9 doi chung am,
2 doi chung duong dat. Power ghi Typical1.20V, ambient25C, auto junction26.6..26.8C,
Quartus vectorless defaulttoggle12.5%, khong do board. Hai anh render tu PDF duoc kiem
bo cuc; ZIP24file/911092byte co membership/CRC/SHA/roundtrip PASS, root kiem doc-lai
SHA moi member PASS. Dependency plotting pin trong .tools/paper_plotting/; khong sua
Python global, khong fit/sim/do moi, khong sua manuscript/ZIP dong nghiep cu. Research
figure khong thay cac PDF thieu cua bai goc1KiB. Receipt: results/paper_figures_20261010_package_receipt.json.

### 2026-10-10 08:46 VC4 retry qua P1 va screen firstGRT truoc P2

Retry postCTS khong doi input hoan tat step37/38/39; p1 PASS: overflow0,
STAMidPNR-2 nom_tt_025C_1v80 setup+1.51761ns/hold+0.181665ns. FirstGRT STA
screen moi co runtime/state/skew/report day du: nom_tt setup+0.491013ns,
hold-0.202347ns tai9endpoint, hold skew-1.719956ns. 219inputSHA giu nguyen;
crash goc van cause-undetermined, khong quy loi may. Log retry toiGRT da copy
truoc khi driver p4 co the overwrite. P2 resume theo gateddriver batdau sau
CONTINUE co ly do trong gated_pd.log; P2_INITIAL_GRT_FALLBACK=1/P2_MIN_SETUP=0
theo frozenplan. Kiem P2 truocDRT, finalsignoffgate giu nguyen. Driver partial
resume in finalFAIL vi chua co signoff va non-tt stale; actualp1PASS duoc kiem
rieng. Day la mot execution bi ngat, chua ket quaPPA. Receipt:
results/vc4_padding_initialgrt_20261010/receipt.json.

### 2026-10-10 08:49 VC4 tiep DRT va dong them sau cofactor AXI

P2 VC4 padding giu overflow0, nom_tt_025C_1v80 setup+0.491013ns/hold-0.202347ns
tai9endpoint; gatep2FAILduocgiu, CONTINUEcochan doan cho postrouteECO. Worstpath
old_main_block[7] -> motmux2_1 -> vc_block[1][7]; NOTE sua annotation2muxes trong
log, khongdoi so/gate/quyetdinh. DRT batdau08:48+07 voi Windowsfree13761MB,
WSLavail23155MB, foregroundclientvaapprovedwatchdog. Chua signoff/PPA.

Sau transitioncofactor AXI cua goldrawmodel duocBDDprove2CLI va vetcan doclap
2CLI,36864assignment/pass, forbiddenzero/multihot0. lec_q_g00088vaotherQgiu
free. BDD25fixturecontrols va actualrawcone rare24mutationcontrol2passdat;
evaluatorvetcan5focusedcontrolsdat, peak59.68MiBduoi256MiB. 14ALUUNKNOWNvi
911supportvuot128bound; proofALUbangCNFchuanbithaydoihypothesisduynhat,
khongdoan state/resetpremises. FullsequentialLEC/sourceundefinedgapconOPEN.
Receipt: results/dm_onehot_boolean_20261010_verification.json va
results/dm_axi_exhaustive_audit_20261010_receipt.json. Khong suaRTL/toolflowdangchay.

### 2026-10-10 09:01 Dong ALU onehot subproof va phan loai DRV signoff DM/SA2

14ALUcase cua goldrawmodel co hai exactCNFCLI doclap, ca14PROVED/0UNKNOWN,
reportbyte-identical. Moi case4958vars/12142clauses; emptyclausechungchi
resolution duocluu. Independentparser/cofactor/Tseitin/resolve replay28ALUproof
va2rawmodelnegativebaseline,73296steps;2659smallCNForacle/144truth-table va
corrupt/malformed/resourcecontrols dat,peak134.72MiBduoi256MiB. Noextrastate
premises; fullsequential/sourceundefinedgap vanOPEN. Joint235const/28dup/fourFSM
induction la subtasktieptheo, khongfullSoCtoolcungPD. Receipt:
results/lec_onehot_cnf_independent_review_20261010.json.

DM/SA2 finalSTAPostPNR DRV trichxuatkhongdoSTA/PDmoi: ca27constraint-corner
group/designkhopidentity/limit/actual/slack/net/master/diodeload/category x2;
footer==metrics,45inputSHAgiunguyen,17controlsdat,peak44.12MiB. SRAM-first/
diodenet/stdcategoriesdisjoint; blankfanoutslackgiuUNKNOWN_REPORTED_BLANK,
khongdienactual-minus-limit. Countsla violatingpinrows,netcounts tachrieng,
khongdungstale midPNR. Numbers/fullcorner/units oRESULTS va
results/asic_drv_categories_20261010/paired_final_reports/receipt.json. DRV
khonghardgate; T6chua finalviVC4/minimality/fullLECconthieu.

### 2026-10-10 09:16 Bat bien dong thoi va dau vao minimality

Hai CLI doc lap tren raw GOLD chung minh286 nghia vu:235hang,28quan he trung va23ma hop le cua4nhom one-hot;
ket qua giong tung byte. Review doc lap tai tao266structural+40CNF cap, replay74.938buoc resolution;
kiem reset-base rieng khong dung premise bat bien hay gan RAM/registre chua reset=0. Chi dong reset-base
va buoc induction khi hai reset synchronizer da tha; bridge cac pha reset, pairedGOLD/N1/final initial-state
va sourceundefined van OPEN. Bang chung: results/lec_joint_invariant_independent_review_20261010.json
va results/lec_joint_reset_base_independent_review_20261010.json. Khong sua RTL/PD input.

Preflight6config minimality SA2/VC4:241existingSHA,219frozenqueue inputs va227manifest files giu nguyen;
16macro+halo10um fit,17negativecontrols va36commandsyntax checks PASS. Tao moi VC43500pad1 base/ecomin
va macroplacement chi doi3geometryfields tu3600pad1. Recipe3500cu doi4knob khac nen khong dung lam chung
minh minimality. ChuachayPD; capmoi chi hop le sauT1/T2 chap nhan recipe nguon. Chi tiet
results/pd_minimality_preflight_20261010.json. Cong viec tiep tuc hoan tat project, khong tao them goi gui ngoai.

### 2026-10-10 13:55 CoreMark92 diem sweep da chay kep va audit doc lap

Bo92diem hop le(49base+43FAST) hoan tat184simulation thuc,2privatecompilation rieng. Moi CRC nguon va40counter
khop hai luot va ca2reference cu; profiler xac nhan tham so cache/RAM/L0/predictor thuc. Raw verifier doc lap
doc184logs/UART,241sourceinputs,379artifacts va92pairedCSVrows, PASS;26verifiercontrols da qua. Receipts
results/coremark_sweep_crc_20261010/verification.json va
results/coremark_sweep_crc_independent_audit_20261010/receipt.json. ScopeRAM32KiB/windowfullprogram/iteration1
giu nguyen, khongofficialscore/khongchaychip16KiB. SA4_256B_L16 voi4sets<L0=8 bi loai, khong bao cao thanh phep do.
RTL/firmware frozen khong doi; noikhacCRC capacity-sweep trongRESULTS/REVIEW_RESPONSE da dong theo scope nay.

### 2026-10-10 14:22 Reset phase, BHT, cua so cong suat va SA2 die nho

Reset phase theo buoc clock da dong 1716 nghia vu moi luot, chay hai lan byte-identical: 1696 structural va
20 CNF. Review doc lap dung lai sau pha va replay 40 certificate, 74938 resolution steps. Lan review dau
gap TypeError chua xac dinh nguyen nhan; kiem tra source/module/code hash va retry lenh y het da PASS.
Trace va execution receipt giu nguyen; khong quy loi hardware. BHT update va read cung chay hai lan,
dong cuc bo 257/358 dong X/Z connect; con 101 dong, khong dong full LEC hay nguon four-state.
Chi tiet: results/dm_reset_phase_20261010_verification.json,
results/lec_reset_phase_independent_review_20261010.json,
results/bht_read_default_definedness_20261010_verification.json.

Audit Embench xac nhan 200 raw board-reference simulation, firmware goc, 40 counter va 10 private libraries.
24 SAIF DM/SA2 deu dai (mcycle+1)*20ns, trong khi TB cycle count bang MCYCLE; cot win_t*_ns thuc te la ps.
Hai phep STA van tai lap dung voi dau vao cu, nhung cong suat dung cua so can capture moi va STA hai luot.
Khong sua SAIF/TC/report cu; observer moi dang chuan bi, khong sua frozen TB/RTL/firmware.
Receipt: results/embench_gls_evidence_audit_20261010/receipt.json.

SA2 T4 bat dau full flow die 3400x3250 (11.05mm2) luc 14:07 +07, chi doi ba truong hinh hoc tu recipe da ky.
241 preflight inputs va 227 manifest files giu nguyen; Windows free 10056MB, WSL available 13109MB.
Foreground driver dung sau P2 de doc timing; VC4 antenna van chay. Mot luot dang chay chua la minimality.
Tag: sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1; decision va gate ghi asic/gated_pd.log.

### 2026-10-10 14:23 Firmware build dung khi compiler loi

scripts/metrics/build_upfull_fw.sh truoc day tiep tuc khi make loi va co the exit0 voi hex cu con tren disk.
Mock negative control tai lap false success exit0; ban sua tra exit1. Ap dung dung hai dong da kiem:
set -euo pipefail va exit1 thay continue. Source ngoai manifest va frozen PD inputs, khong instance dang chay.
bash -n PASS, manifest227 files IDENTICAL. Khong build lai firmware hay sua hex/MIF/RTL.
Bang chung mock va patch cu giu nguyen tai results/embench_gls_evidence_audit_20261010/.

### 2026-10-10 14:29 Review BHT doc lap da dong

Parser RTLIL rieng theo module va interpreter bit-vector LSB-first xac nhan 256 read addresses,
1024 update selector cases va 2048 state/taken data cases, ke ca thu tu B/S concat va reduced output.
Khong import parser/evaluator tu hai BHT checkers. 18 finite controls PASS; hard limit256MiB, peak57MiB.
Loi namespace cua parser moi o preflight da sua khi idle, traceback giu nguyen; frozen proof/IR khong doi.
Receipt: results/bht_definedness_independent_review_20261010.json. Con101 classified X/Z lines,
full source abstraction va full sequential LEC van OPEN.

### 2026-10-10 14:29 Counter boundary control chay hai luot

Hai private compilation moi va N=1/2/17 moi luot, 8 native CLI exit0, 6 actual simulation controls.
Nguyen source perf_counters/apb_performance_monitor khop byte PD snapshot. Observer freeze_q cu cho countN
nhung wall time(N+1)*20ns; observer counter_freeze thuc va independent closing interval+1 cho countN,
wall timeN*20ns. Hai luot raw fields khop; peak observed process family RSS234.93MiB, khong sua timestamp.
Receipt: results/embench_gls_evidence_audit_20261010/counter_boundary_controls/receipt.json.
Day chi la source boundary control, chua la mapped GLS/benchmark/power hay proof mapped freeze alias.

### 2026-10-10 14:29 SA2 die11.05 P1 PASS

Full flow sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 qua P1 luc07:27:56UTC.
GRT overflow0; STAMidPNR-2 nom_tt_025C_1v80 setup+1.581ns, hold+0.182ns. P2 dang chay,
chua extracted-RC sign-off va chua paired result. Gate co tham quyen o asic/gated_pd.log.

### 2026-10-10 14:40 UART baud default va so lieu unified

UART baud PMUX dang16bit chon du bon cfg_reg[1:0] codes: 20832/10416/5207/433. Hai CLI thuc byte/all-field
identical; separate parser MSB-first review PASS, khong import checker hay BHT parser. Raw selector fault
code3 lam default0/65535 hien ra; dao16bit B slice cho433 thanh36224, controls6malformed guards PASS.
Tong BHT/UART258 classified X/Z connect lines dong cuc bo, con100; full sequential LEC/four-state vanOPEN.
Receipts: results/uart_baud_default_definedness_20261010_verification.json va
results/uart_baud_definedness_independent_review_20261010.json. Frozen source khong doi.

Generator unified_table them caveat mot chu ky20ns thua trong24 SAIF cu va chay lai nativeexit0; FPGA40cap,
CoreMark11cap canonical, power receipt/raw reports da duoc recheck. Khong doi phep do cu; README/WORKSPACE_MAP
va cac state docs dong bo scope exact-window power pending. Khong tao them goi gui dong nghiep.

### 2026-10-10 19:35 SA2 die11.05 dung tai setup P2

Full-step1 sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 dung dung gate15:01:55+07.
Nom_tt_025C_1v80 setup-0.331932ns/10endpoints, hold-0.0579186ns/4endpoints, overflow16. Setup path thuc
Icache way1/bank1 SRAM dout1[25] -> if_req_addr[31], arrival23.654978ns > required23.323046ns.
Hold path Dcache way0/bank0 hold_a_q[9] -> hot_line1[9]. Chi nom_tt moi duoc chay o buoc nay;
cac corner khac ke thua la stale. Khong CONTINUE setup am, khong DRT hay ky ten, khong quy loi may.
Audit: results/sa2_minimality_screen_20261010/first_execution_audit.json. Can full-step1_r2 cung3250
recipe de kiem reproducibility truoc thu3325; mot lan that bai chua la minimum-area result.

### 2026-10-10 19:35 Icache hot-array default review doc lap

Ba PMUX hot-array Icache co unused A-default da qua hai CLI doc lap, byte/all-field identical;
review rawIR bang parser rieng PASS. Moi luot24free3bit index cases,1224data bits symbolic;
6faults selector/data thuc da duoc replay, khong reset/init/legal-state premises. Tong261/358
classified GOLD X/Z connect lines dong cuc bo,97con mo; don vi la connect line, khong phai bit/bug.
Selected B-data va whole-Y definedness vanOPEN; khong nang thanh full sequential LEC.
Receipts: results/icache_hot_default_definedness_20261010_verification.json va
results/icache_hot_definedness_independent_review_20261010.json. Frozen RTL/IR khong doi.

### 2026-10-10 19:37 Mapped MCYCLE freeze da review va GLS screen bat dau

DM/SA2 moi design65nghia vu qua hai CLI doc lap, byte/all-field identical. Full-freeze alias,
32increment functions va32actual D consumers clear/hold/increment duoc rang vao netlist ky ten.
Review bang raw-netlist/PDK parser/interpreter rieng replay252paired CNF certificates/340338resolution
steps,8structural roots va12actual wrong-observer witnesses; nativeexit0, peakworking145.8MB trong cap256MiB.
Receipts: results/mapped_counter_freeze_checked_20261010/{verification.json,independent_review.json}.
Scope Boolean observer cuc bo, khong full LEC/initialization/other counters/asynchronous-delay proof.

Fresh DM up_ud screening bat dau19:36+07: results/gls_exact_dm_ud_screen_20261010/receipt.json;
private compile nativeexit0/Error0 luc19:37:10, firmware va frozenTB/RTL khong doi. Windowsfree9580MiB,
WSLavailable13102MiB va mot VC4 antenna job; khong chay them SA2flow khi GLSdangdungRAM.
Can completed GLS/LEDHEX + independent count + elapsedMCYCLE*20ns + raw/pin SAIFspan truoc full12x2.
Khong sua DURATION de ep gate, khong doi capturescu, chua cong suat moi. Lich SA2_r2 sau screen/GLS an toan RAM.

### 2026-10-10 19:41 SA2 die11.05 full-step1 luot thu hai

Sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r2 bat dau tu step1, cungconfigSHA9b0b9588
va recipe3250, STOP_AFTER=p2/P2_MIN_SETUP=0. Kiem lai241preflightinput va227manifestfiles khop;
tagmoi, globalabortflag khongco. Windowsfree12494MiB/WSLavailable13099MiB/swap0; currentGLS~0.13GiB
va VC4postDRTantenna serial10.3GiB, duRAM cho hai cong viec da co co so, khong spraying knobs.
Gia thuyet duy nhat: lap lai nominaltt setup failure cua die11.05 cung recipe. Foregroundclient31576
giu WSL, khongdetachment; serialized heavy signoff/ECO neu can. Decision da ghi gated_pd.log.
Chua paired timing/minimum/signoff result; can reportsP1/P2 moi va path comparison voi_r1.

### 2026-10-10 19:53 VC4 silent phase co CPU sample FastRoute

Mot read-only perf_event_open CPU-clock probe ordinary WSL UID, exactTID669/exec/run/starttime, user-only20Hz,
khongptrace/attach/pause/signal/install/permissionchange. Nativewall4.968s gomstartup/disable/exit,98samples,
lost0; pinned .symtab SIZE-range resolve moiPC vao grt::FastRouteCore::mazeRouteMSMD. Khong lap probe.
Results/vc4_cpu_sampling_20261010/receipt.json giu rawIPs/maps/sources/bin/compiler/control/commandSHA.
Sourcecomparison: results/vc4_postdrt_antenna_comparison_20261010.json; signedSA2 steps46 duration36m45.497s
va34m32.522s, currentVC4 sau mainDRT da hon10h khongmarkerreturn. Inference firstsilentantenna-check truoc
do khong duoc stack/PC ung ho; phase chinhxac/callchain va net vanchua biet. Khong suy machinefault/hang,
khongkillrun, khongdoi knobs hay runningflow inputs. PROJECT_STATE sua gioihan inference.

### 2026-10-10 20:00 Main RAM bank default da chay kep va review doc lap

Dung49mainRAM PMUX A-defaults dong cuc bo:392free3bit-bank cases va98actualrawselector/datafaults moi pass,
398original B-data atoms symbolic,32actualselectorcone cells. Hai CLI doclap native0/0, byte/all-field identical;
module/MSB-first parserreviewrieng native0, source/macro/bank parameters va data-order khop; cap256MiB, peaks<59MB.
Reviewer preflight lan1 dung deterministic do instr_d unrelated wire offset7; error/sourceSHA duoc giu,
newreviewer chi record metadata ngoai49cones va failclosed neu targetdung offset/upto chua support. Khongdoiloimay.
Receipts: results/ram_bank_default_definedness_20261010_verification.json,
results/ram_bank_definedness_independent_review_20261010.json va ram_bank_definedness_execution_20261010.json.
Tong310/358classified GOLD X/Z connectlines dong unusedA;48conmo=14PMUX(AXI3/TX8/RX3)+7mux+27moduleconnect.
Bang97dong truocproofduocgiu: results/lec_source_x_remaining_20261010/. SelectedB/wholeY/RAMinit/sourceX/fullLEC
vanOPEN; khongdoi RTL/IR/frozenproofs hay kytenPD. Sharedstate chi capnhat scope, lichsu giu tai mucnay.

### 2026-10-11 00:34 GLS du12 kernel kep va doi chieu SA2 die11.05

DM ud screening native compile/sim/Windowsconversion0, LEDRa5, MCYCLE=win_cycles144388,
elapsed2887760000ps, du99471rawSAIFspan khop; chi SINGLE_SCREEN_NOT_RESULT.
Hai private compile moi cho du12kernel da batdau00:29 va00:30+07 tai
results/gls_exact_dm_full_p1_20261011/ va gls_exact_dm_full_p2_20261011/; chua co pairedcapture/power moi.
Memory-wait patch da apdung20:04 ngay10-10 khi khonginstance: opt-in macdinhOFF, nguong6000MiB giunguyen,
foreground30s/inputSHAguard, abortchi ngan tooltieptheo; QUY_TRINH F da capnhat exactwindow/rawpreservation.
P2 SA2 die11.05 hai fullstep1 r1/r2 cungFAIL:568metricfields/config/N1/GRTnetlistDEFguide khop,
nom_tt_025C_1v80 setup-0.331932ns/10endpoints, hold-0.0579186ns/4endpoints, overflow16.
Receipt results/sa2_minimality_screen_20261011_pair.json; khongco signoff/minimumdieclaim.
Gia thuyet tiep theo chi tang dieheight3250->3325 voi cungrecipe, fullstep1 STOP_AFTER=p2/P2_MIN_SETUP=0;
queue results/sa2_minimality_queue_20261011.json cho Windowsfree>=10000MiB roi WSLgate.241inputs va227manifest
giu nguyen. VC4 native669 conchayFastRoute; khongkill healthyflow, khongthem speculativeknobs.
Lan goiGLSpass2 preflight dau sai tenlib1p80V thayvi1v80: failclosed truoc taooutput/tool;
sua dungpath va khoichaytu inputs dung, khongtinh lafaultmay hay measurement.

### 2026-10-11 00:38 Hang doi tu dong paired GLS sang activity power DM

Foreground queue results/exact_power_queue_20261011.json doi du12kernel hai pass, strictpaircheck,
roi cho Windowsfree>=7000MiB truoc26STA moi tai results/activity_power_exact_dm_20261011/.
Capture/pairFAIL dung queue, khongstartpower; nativeSTA van6000MiBWindows/5000MiBWSLguard.
Khongdetach/nohup, khongedithelper dangchay, chua co resultpower moi.

### 2026-10-11 01:16 Random50seed da khop Spike hai luot

100native Spikeprocess0, 50seedx2, khop200traceRTL da chay doclap va giu tu09-10;7105retirements/pass.
So PC/instruction/GPRwrite/storeaddress/enabledbytes/strobes;300wrongtracecontrols bi bat.
Receipt results/spike_random_reference_20261011/receipt.json; input227manifest va frozenRTLtrace khongdoi.
SpikeCLI nativeFAIL do debugdevice0..0x1000 trung RAMprogram0; directprocessor_t adapter chi gan memory/
PC0/zeroGPRdata theoTB, khongvietISAsemantics. Dunginstalledlibriscv.so/SHAvaRV32I_Zmmul.
Preflight lan1 sai tenkeyreceipt firmware, lan2 CLIcollision, lan3 mergedstdoutstderrWSL mat daucommit:
giu errors/executedrunner trong cacfolder stopped; runner cuoi tach rawstdout/stderr va kiemHALT/native0.
Khongloimay, khongdoiRTL/gate/clock. Scope generatedcoresubset, chua MMIO/IRQ/cache/timing/fullprivilegedISA.

### 2026-10-11 01:32 CoreMark port timer va firmware cho phep do du10giay

- Port cu chi bat timer, trong khi apb_timer.v mac dinh CMP=40 va dung tang COUNT khi cham CMP; khong the dung
  nguyen port do de do10giay. Port tach rieng coremark_standard_apb_port.c dat CMP=0xffffffff truoc interval,
  khong bat IRQ, giu nguyen thuat toan CoreMark, RTL, manifest, firmware cu va RAM mo phong32KiB.
- Hai build doc lap -Os/HAS_FLOAT=0/ITERATIONS=0 da khop ELF/HEX cho ca performance va validation. Footprint
  tinh gom1KiB stack la15.056byte; linker van dat stack32KiB, chua phai bang chung thuc thi tren RAM16KiB.
  Receipt results/coremark_standard_apb_build_pair_20261011.json. Phat bieu firmware -O2 cu khong vua16KiB
  duoc gioi han lai cho dung firmware do, khong ket luan moi port CoreMark deu khong vua.
- Screening CSR DM ket thuc tu nhien nativeexit0, CRC dat, interval1100iterations/700.135.504ticks; chi la
  screening mot luot. Source datapath co nhanh ghi CSR khi doc mcycle, nen khong dung screening CSR de chot
  diem. Screening APB dang chay; observer thuc te doi chieu tung read duoc chap nhan voi canh clock va20ns.
- Ma tran tiep theo co4cau hinh,2profile,2luot doc lap; chi nhan diem khi CRC, interval>=500.000.000tick,
  timer delta=clock delta=time delta va moi truong hai luot khop. Diem mo phong khong thay the board hay
  dang ky/chung nhan EEMBC. Log/receipt cua cac port thu va loi harness duoc giu de debug.

### 2026-10-11 02:09 CoreMark du10giay da khop hai luot cho4cau hinh

- Ma tran APB hoan tat tu nhien nativeexit0:4cau hinh x performance/validation x2luot=16/16PASS. Tam cap
  khop tat ca108scalarfield/cap, gom40counter, CRC va APB read/clock/time;864so sanh. Tieu chi timer va
  firmware xem su kien01:32; so lieu chot o RESULTS.md1.1 va CSV trong coremark_standard_apb_matrix_20261011.
- Moi luot co model RTL bien dich rieng; DMperformance screening du dieu kien lam luot1 va luot2 thuc thi
  doc lap. Hai firmware build doc lap khop byte;8model private (1screen+7matrix) va16native sim thuc su.
  Cac compile chi co TIMESCALEMOD/WIDTHEXPAND da duyet, assert bat; khong doi RTL/SDC/clock/manifest.
- Receipt VERIFIED_TWO_INDEPENDENT_STANDARD_COREMARK_SIMULATIONS_RAM32K_50MHZ;365inputhash giu nguyen,
  manifest227file IDENTICAL. Xuat cases.csv16dong va performance_paired.csv4dong, giu exactdecimal strings.
  Tat ca22nativecommand cua matrix va3command cua screen tra0; healthyjob ket thuc tu nhien.
- Pham vi diem: mo phong RAM32KiB/50MHz, GCC14.2 -Os,2000B/singlecontext,1100iterations, iterate_only.
  Khong tron voi bang -O2/full_program cu; chua co diem board hay dang ky/chung nhan EEMBC.

### 2026-10-11 03:02 Chuan bi phienboard12thang10 va dungUART Hercules

- Chotngay2026-10-12; chua chotgio/COM/boardidentity. Audit read-only100SOF/25firmware, RTLmanifest227file,
  seed2chung4config, pairedreference100cap/200rawlog/40counter deu khop. Ket luan o
  results/board_20261012/readiness.json; observation200NOT_RUN, physicalUARTNOT_TESTED.
- Doi chieu fitpinreport va manualTerasic phat hien checklistcu ghiRS-232 nhungSOF dafit dungJP5GPIO3.3V
  TTL/CP2102 (AB22TX/AC15RX). Sua checklist va mucEQUY_TRINH cho dungfitteddesign, khong doiRTL/QSF/SOF.
  Manualduocgiulai kemhash; JP5orientation/GND/JP6voltagesource ro trong sessionREADME. Firmwarebootngay,
  KEY1khongstart; Hercules/logmo truocprogramming,2pass deu programSOFtuoi.
- Tao sessionREADME/runlist200dong/results200NOT_RUN/sessionmetadata va folderuart/photos/programming.
  Programmerhelpermacdinhplan-only, checksource/SOF/FW/seed, chi -Programvao ngayphienmoiJTAG. Dryrun case1p1
  va case100p2dat, khongprogram. LoiPSparserbien $Pass: duocsua bang ${Pass}: truocdryrun; loitatdinhharness,
  khongphai maycrash. UARTchecker so28field voi2reference,6syntheticcontroldat; controls khongla ketquaboard.
- UARTdividerhientai448clock/bit (~111607baud/50MHz); smoke ramsweep/Herculesnominal1152008N1OFF truocmatrix.
  Giu failedcapturesvaCRC/countermismatch, khongsuaRTLdecheloi. upfull_* va up_* coBENCHlabelchungnen gan
  capturesvoi hostkernel/config/pass/SOFhash. CoreMarkRAM32KiB chua thuocboSOF RAM16KiBnay.
- Khi kiemtralancuoi, VC4DRT dangchay, DMGLSx2 dang up_huffbench sau4/12case/pass; SA2minimality da
  qua hangchoRAM va chayP1, activitypowerdoihaiGLS. Chua dungjob hay yeucaushutdown; tatmayse ngatstepchua xong.

### 2026-10-11 03:03 SA2screen3325 batdau tuhangdoiRAM

- Driverforeground batdau02:56+07, WSLavailable13.017MB saucongWindowsfree10.000MiB; config/241input
  giunguyen. Gia thuyetgeometry3325 duathu vao3250r1/r2thatbaigi nhau, khongdoi knobkhac/RTL/clock/gate.
  Runtag sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1, fullstep1, STOP_AFTER=p2/P2_MIN_SETUP=0.
  KhikiemtraP1 dang customIOplacement; chua coP2/gatetiming/signoff hay ketquaminimality. DongNOTE/start
  da duocdriverghivao asic/gated_pd.log. VC4DRT vaWindowsGLSx2 tieptuc, chua themfit/chuoisimlanemoi.

### 2026-10-11 03:43 SA2 die11.305 qua P2 va giu truoc DRT

- Full-step1 sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 qua P1/P2;
  P2 hoan tat03:42:58+07, HOLD dung theo STOP_AFTER=p2, driver exit0. Goc tuoi nom_tt_025C_1v80:
  setup+0.7621281599ns, hold+0.0454112316ns, setup/hold endpoint0, post-GRT overflow0,
  hold skew-1.8713537916ns. Audit: results/sa2_minimality_screen_20261011_3325/first_execution_audit.json.
- Mot execution tu step1, chua DRT/DRC/LVS/sign-off/chaykep; chua chung minh minimum area.
  Khong dung so ff/ss ke thua pre-PnR lam timingtuoi. RTLmanifest227file khop khi kiemtralai;
  chua sua RTL, recipe, gate hay chay flow moi trong buoc kiemtra.

### 2026-10-11 04:37 Kiem tra trang thai va chan doan VC4 post-DRT

- VC4 padding run dung03:19:20+07; doc lognative da xac dinh GRT-0232 trong vong sua antenna sauDRT,
  khong dung textgeneric abort/crash de quyloi watchdog/may. Audit co hash/logline:
  results/vc4_postdrt_antenna_failure_20261011.json; co che va baydoclog ghi muc9 Antenna.
  Step43 va cac failedartifact duoc giunguyen, chua retry/thayknob/RTL/gate.
- SA2 die11.305 giu dung tai P2 PASS; xem su kien03:43 va audit tuongung. HaiDMGLS van chay,
  luc kiemtralancuoi6/12kernel/pass; activitypower dang doi capcapture. Khongco PD/Quartus dang chay.
  RTLmanifest227file IDENTICAL; receiptSpike/CoreMark kep va boardreadiness van giu trangthai da xacnhan.
  Chua tat/dung jobhealthy. Physicalboard/UART van NOT_RUN/NOT_TESTED.

### 2026-10-11 14:42 Khoi phuc GLS DM luot hai va gan monitor hien tai

- P1 exact GLS hoan tat12/12 luc06:48+07. P2 cu dung04:59+07 sau6case: up_md5sum sim PASS,
  Windows saif_to_pins.py exit1 voi TypeError contextmanager tai read_netlist `i += 1`.
  P2 rawmd5sum khop P1 ngoai DATE, dung span123904x20000ps; khong phai GLSfunctional failure.
- Diagnostic chay lai nguyen converter vao artifact moi:314input khop hash, exit0, pinSAIF khop byte voi P1.
  results/gls_pin_conversion_retry_20261011/receipt.json; chua ket luan nguyen nhan hardware.
  Receipt/log loi cu khong doi. Fullpass2 moi/privatecompile bat dau14:36:40+07, dang up_aha-mont64,
  results/gls_exact_dm_full_p2_retry_20261011/receipt.json. Strict25command verifier giu nguyen,
  khong ghep partialPASS; queue moi chi tinh26STA sau pairedcapturePASS va congRAM7.000MiB.
- scripts/watchdog.sh van tro run synth4kb cu va tat verificationwatch, khong bao phu cac job hien tai.
  Hostmonitor moi scripts/maintenance/monitor_jobs.py dat3syntheticcontrols va livecheck;
  foreground --watch bat14:41:57+07, poll600giay, results/job_monitor_status.json.
  CPU ca cay/processset/RSS/output dung de nghi treo; queryloiUNKNOWN, P2HOLDHELD, khongkill/retry/gatechange.
  Snapshot dau: VC4FAILED, SA2HELD, DMp1DONE12/12, p2cuFAILED6/12, retry/pipelineRUNNING0/12.
  Monitor ghiJSON/stdout, khong co chuc nang gui tin nhan hoi thoai. Chua co exactpower moi hay boardphysical.

### 2026-10-11 17:28 GLS da5kernel va SA2 bat dau detailed routing

- GLS DM retry hoan tat up_aha-mont64/crc32/depthconv/edn/huffbench:5/12, dang up_matmult-int.
  Kiem tra caytientrinh truoc khi doi kernel: vsim.exe launcher khong tangCPU, nhung vsimk.exe tang3.5s
  va log tang10.570byte trong3.45s; khong ket luan treo tu CPU launcher. Monitorvan poll600giay.
- SA2 die11.305 P2audit6hash/RTLmanifest227file khop, setup/holdtuoi nom_tt_025C_1v80 duong;
  Windowsfree13.359MiB, WSLavailable23.172MiB/swap0, khongco PD/Quartus khac.
  GatedDRT resume17:27:25+07, step46/OpenROADPID673, foregroundWSL giu suot pha.
  G5_UNLIMITED_LATE_PHASE=1 nhu quytrinh; recipe/RTL/clock/gate khong doi, van la executionthu1.
- Them4dong HOLD_AFTER_DRT=1 macdinhtat vao resumehelper khi chua coflow chay, dekiem RAMtruocP4
  (Magic co thecan14GiB, khong tudonglaunchvoi13.3GiBWindowsfree). bash-n/3mockcontrols deuPASS,
  defaultbyteexactngoai4dongthem: results/gated_resume_phase_hold_20261011.json; da ghiQUY_TRINH mucD.
  Chua DRTfinal/signoff/chaykep; chua retryVC4fatal. Gatedlog coCONTINUE/RESUME/detailedroutingstart.

### 2026-10-12 18:04 GLS tiep tuc tu nativeprefix va SA2 doi RAM sign-off

- SA2 step46 da hoan tat18:37+07 ngay11/10: routeDRC0, antenna0net/0pin, placement0,
  runtime01:08:19.415, motexecution/chuaLVS/timingsignoff. Antenna count459 trongstate la soGRTke thua;
  audit results/sa2_minimality_screen_20261011_3325/detailed_routing_audit_20261012.json ghi so tuoi0/0.
- DMGLS retry dung sau7case va simthu8PASS vi doc TTlib quaUNC loiErrno22;16nativecommands deu exit0.
  Prepare314input/hash/log/raw/pin va originalprivatecompile truocresume; luu failedreceipt/queue nguyenbyte
  trong results/gls_exact_dm_p2_continuation_20261012/. Helpermoi macdinhprepare-only,3controlPASS;
  --run noi tiep9lenhconthieu, khongchaylaicase da xong, giu strict25command verifier. Da8/12PASS, dang up_slre.
- Hang doi P4_RESOURCE_WAIT=1 foreground bat17:58+07; doi Windows/WSLfree15000MiB, Windowsluccheck12656MiB.
  Wrappermoi macdinhtat, bash-n/2mockguardsPASS, drivercu khongdoi; khongdungownerprogram. Da ghiQUY mucD.
  Chua firstECO/signoff/chaykep. ControllerGLS -Resume se pairverify roi moi tinh26STA; congRAMSTA7000MiB.
- Khoi dong lai monitor600giay cho jobs hien tai. Chi diagnosticloop duoc dung de sua parser WAIT/RESUME/
  finalFAIL roi batlai; producerGLS vaPDqueue khongbi ngat. Monitorghi SA2WAITING, GLS/pipelineRUNNING;
  moi kieusosuspectedstall van dung CPUcacay/RSS/output, khongtudongkill/retry. RAW failed evidence giunguyen.

### 2026-10-13 05:20 Tiep nhan lai: SA2 11.305 crash o ECO, cong suat DM cho RAM, gia thuyet antenna DM_VC4

- Trang thai luc tiep nhan: khong co PD, GLS hay Quartus nao chay; WSL dung. Windows con ~5 GB trong vi mot ung dung
  cua chu du an dung ~15 GB; khong dung ung dung do.
- SA2 die 11.305 (`sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1`): P4 bat dau 2026-10-12 11:27 UTC; ECO
  hold sau route sua 326 endpoint (197 buffer, -0.4224 -> +0.0202 ns), detailed route tang dan sau ECO: 2442 / 821 /
  698 / 335 / 236 / 188 / 176 / 167 / 124 / 123 / 123 / 106 / 80 roi 24 tu vong 13 den 18, sau do OpenROAD SIGSEGV
  (Signal 11, `drt::FlexGCWorker::Impl::checkMetalSpacing_short_skipFixed`) o vong 19. Die 11.56 cung buoc nay: 794 ->
  0 sau 4 vong. Lan dau xay ra: thu muc chuyen thanh `crashed-47-openroad-postrouteholdeco`, dong NOTE trong
  gated_pd.log; MOT lan chay lai nguyen trang phan sign-off qua cong tai nguyen P4 se phan dinh ngau nhien / tat dinh.
  Neu lai dung tren 0 hoac crash: ghi 11.305 truot o route sau ECO.
- Cong suat cua so chinh xac DM: cap capture hai luot da VERIFIED (`gls_exact_dm_full_pair_retry_20261011.json`);
  driver STA dung o cong bo nho cua chinh no (Windows free 5,323 MiB < 6,000) sau STA vectorless; thu muc cu giu
  nguyen, lan chay moi ghi vao `results/activity_power_exact_dm_20261013`.
- Hang doi foreground `scripts/maintenance/queue_dm_power_sa2_eco_retry.sh` (log
  `results/queue_dm_power_sa2_eco_retry_20261013.log`): (1) cong suat DM khi Windows free >= 7,000 MiB; (2) chay lai
  sign-off SA2 11.305 qua `P4_RESOURCE_WAIT=1` (>= 15,000 MiB ca hai phia). Dang cho bo nho.
- DM_VC4: run padding 3600 dat main route DRC 0 o vong 45 (18.5 gio), roi check_antennas 2,243 net / 3,211 pin (DM
  r14F_A 481 net, SA2 653), repair_antennas chen 5,978 diode va GRT tang dan noi diode dung o GRT-0232. Ma nguon
  OpenROAD edf00dff: GRT-0232 chi bao trong `updateDirtyRoutes` khi khong cho nghen. Gia thuyet mot thay doi: cho nghen
  rieng trong vong sua antenna (`DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`, them vao openlane-local, mac dinh tat, cu phap
  Tcl / Python da kiem) va giu main route (`DRT_SAVE_MAIN_ROUTE`). Config da chuan bi, CHUA chay:
  `config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong.json` (chi khac hai bien do). Full flow khoang
  20-24 gio, can chu du an dong y va du RAM.

### 2026-10-13 05:45 May loi tinh toan: dung moi job nang; phan tich PPA SA2

- Khi bo nho du (05:29), driver cong suat DM crash hai lan cung cho (Windows access violation trong
  `verify_gls_exact_pair.py:130 compare_saif`), du ham nay voi cung input da PASS ngay 2026-10-12 13:35 UTC.
  Kiem tra suc khoe `asic/parse_ids_probe.py --synth 300000`: Windows 2/8 OK (segfault, `'shlex' object has no
  attribute '_pushback_chars'`, `'bool' object does not support the context manager protocol`), WSL 0/8 OK (segfault va
  CORRUPT token sai, vd. 'obj208511w=7:0'); ngay 2026-10-09 ca hai 8/8 OK. Khong co su kien WHEA trong 5 ngay. Laptop
  i9-13980HX (ASUS G614JV, BIOS G614JV.334), RAM 2 x 16 GB DDR5-4800 (khong ep xung), uptime 11.7 gio, vua chay game.
  Log `results/health_20261013/`. Da dat `asic/.abort_gated_pd`: lan chay lai SA2 11.305 chua bat dau (dong STOP).
  Khong chay PD / GLS / Quartus cho toi khi probe lai 8/8 o ca hai phia; ket qua tinh tren may loi khong duoc dung.
- PPA SA2 (doc du lieu da luu, moi phep tinh chay hai lan va trung): cong suat theo hoat dong nom_tt SA2 129.64 mW vs DM
  119.45 mW; chenh lech chu yeu o clock 43.10 vs 33.02 mW (+10.1) va tuan tu 41.50 vs 38.71; macro 37.87 nhu nhau. Kiem
  dem cell tu DEF cuoi (khong tinh fill / decap / tap): SA2 1.3423 mm2 / 113,040 cell, DM corridor dmuB 1.2472 mm2;
  SA2 co 14,184 diode antenna (DM r14F_A 7,360), trong do 12,619 do buoc sua antenna o GRT (`RUN_ANTENNA_REPAIR` true,
  margin 30), sau DRT chi chen them ~1,550. CTS ca DM va SA2: `CTS_SINK_CLUSTERING_SIZE` 8 (mac dinh OpenLane 25),
  `CTS_CLK_MAX_WIRE_LENGTH` 800, ke thua tu config DM cu, chua tung toi uu; SA2 co 3,391 clkbuf + 1,939 clkload.
  OpenROAD edf00dff co `clock_tree_synthesis -dont_use_dummy_load` (cts.tcl chua noi). Huong thu (moi lan mot thay doi,
  full flow + nhanh ECO hai luot): tat sua antenna o GRT; clustering 8 -> 16 / 25; bo dummy load; bo padding o 11.56;
  max fanout 16 -> 24.

### 2026-10-13 14:40 Ra soat chuan bi board; may van loi sau khoi dong lai

- Chu du an (2026-10-13): lam TUAN TU, phan quan trong de viet bai: (1) kiem lai chuan bi board so voi thiet ke hien tai,
  chay board; (2) PD SA2 / DM_VC4 toi uu rieng, KHONG chep thong so / ket qua cua DM (config DM ky ten chi tam chap nhan);
  (3) LEC cho SA2 / DM_VC4; (4) bao cao cac muc danh_gia.txt da giai quyet; (5) liet ke day du phan mo rong so voi ban
  cache 1 KiB.
- Suc khoe may sau khi khoi dong lai 13:05: probe Windows 6/8 OK, WSL 1/8 OK (Python WSL 3.14.4); ghim nhan: P-core
  (luong 0-15) 0/6 OK, E-core (16-31) 4/6 OK; tat turbo (max processor state 99 %) 1/8 OK, da tra lai 100 %. Log
  `results/health_20261013_after_reboot/`, `_affinity/`, `_turbo_off/`. Khong chay PD / LEC / GLS nang cho toi khi probe
  lai 8/8 o ca hai phia.
- Board (moi kiem tra chay hai lan va trung): manifest `6c4ccffd` IDENTICAL (227 file); bon project point chi khac
  `CACHE_CONFIG` 0/1/2/3, tham so trung top PD (`soc_asic_top.v` cua DM / SA2 / DM_VC4: 256 dong x 16 B, victim 4, L0 8,
  BHT 256, BP va perf counter bat, IMEM / DMEM 2048 tu, miss penalty 2, FAST_HIT 0); bao cao map cua fit seed 2
  (2026-10-09) xac nhan cac tham so do. 100 SOF (25 firmware x 4 cau hinh), RTL `6c4ccffd`, seed 2: sha256 SOF va
  firmware trung INDEX.csv; mcycle / minstret ky vong trung tham chieu RTL hien tai p1 = p2 (100 / 100 moi truong) va
  bang R14 (100 / 100). 81 vi tri chan trung thiet ke board da cong bo (UART JP5: TX AB22, RX AC15, 3.3-V LVTTL, CP2102).
  Baud UART that: 433 >> 4 = 27 -> 28 x 16 = 448 clock / bit = 111,607 baud (-3.1 % so voi 115,200; dac tinh RTL tu ban
  cong bo). `program_board_case.ps1 -Case 1 -Pass 1` (khong JTAG): ramsweep DM, HEX 0003D520, LEDR A5, hash khop.
- Board do view FPGA: minstret trung view ASIC 36 / 36, mcycle view ASIC thap hon -4.18 % (DM), -3.67 % (SA2), -3.23 %
  (DM_VC4) vi wrapper RAM ASIC khong co hook do tre RAM FPGA (muc 9 "View ASIC va view FPGA"); so board voi INDEX (view
  FPGA), khong so voi GLS.

### 2026-10-13 14:55 Kiem tra lai may: loi hep, khong phai "may hong toan bo"; ghim nhan la cach lach

- Chu du an khang dinh may khong loi va yeu cau kiem tra lai that ky (quy tac P: khong do loi may qua tay). Ket qua
  (log `results/health_20261013_percore/`):
  - Moi truong Python chuan: Windows 3.11.0 chinh thuc, WSL Ubuntu 26.04 Python 3.14.4 he thong; khong co bien PYTHON*,
    khong co module che thu vien chuan canh probe.
  - Cong cu native: `sha256sum` file 130 MB 8 / 8 trung, `gzip | sha256sum` 8 / 8 trung (WSL).
  - Python thuan tu kiem KHONG dung shlex (`pure_python_selfcheck.py`: split / join, dict, so hoc, checksum dong):
    Windows 8 / 8 OK, WSL 8 / 8 OK, checksum trung.
  - Probe shlex ghim MOT logical CPU ngay khi tao tien trinh (`cmd start /affinity`, 32 CPU x 2): 63 / 64 OK (mot lan
    dung o 240000 tren CPU 10). Cung probe khong ghim: Windows 6 / 8; ghim nhom 16 CPU P-core (dat affinity sau khi
    chay): 0 / 6.
  - Event log thang 10: khong WHEA, khong Kernel-Power 41, khong bugcheck (WHEA / KP41 cuoi cung la 18-30/09).
- Ket luan: hien tuong co that nhung HEP (mot dang tai Python dac thu khi luong chuyen giua cac nhan), khong lam sai cac
  tai thong thuong; ket qua san xuat van tai lap hai lan (vd. SA2 r1 = r2 tren 319 metric). Viec dung toan bo luc 05:45 la
  qua tay: da go `.abort_gated_pd`. Cach lam tiep: cong cu Python phia Windows chay ghim mot CPU (`cmd /c start /wait /b
  /affinity <mask>`); crash ngau nhien duoc chay lai; chay kep van la la chan ket qua.
- Driver cong suat cua so chinh xac DM chay ghim CPU 2: qua buoc kiem cap capture (truoc do crash hai lan khong ghim) va
  dang chay STA.

### 2026-10-13 15:09 Chuan bi board tung case va Hercules bi chan

- USB-Blaster USB-0 va CP210x COM3 duoc nhan; jtagconfig doc chipID020F70DD. Luc dau cablelist rong,
  luc kiem lai da nhan; khong ket luan loi may/driver. SOF/fw ramsweepDM va manifest227file khop,
  pairedreferenceMCYCLE0003D520/MINSTRET00028073. Chua nap hay do board.
- Tao results/board_20261013/ voi index/runlist200case/results200NOT_RUN va sessionmetadata.
  Moi workload/config phai dung cho xacnhan truoc case tiep/reset/rerun. Khong ghi expected thanh observed.
- Cau hinh Hercules chua hoan tat: automatictoolpolicy tu choi download+launch, ke ca sau xacnhan cho phep;
  chi thong bao blocked by policy, khong co ly do cu the. Khong doi tool hay wrapper de lach lenh bi chan.
  Setupstatus giu rawUART/observedLED/HEX null, programmingfalse. ReceiverUART Windows da chuan bi/syntaxcheck,
  chua moCOM va chua duoc chon thayHercules. Can ungdungHercules duoc mo truoc khi nap case1.

### 2026-10-13 15:20 Kiem tra sau ve may: loai tru nguyen nhan phia du an; loi tinh toan am tham van con

- Muc tieu (quy tac P): tim nguyen nhan phia minh (script, cau hinh, phan mem moi cai, tai may) truoc khi quy cho phan cung.
  Nguon: Event log Windows, `powercfg`, `results/health_*`. Bo doi chung moi: `results/health_20261013_recheck/`
  (`run_recheck.ps1`, `run_silent_plan_ab.ps1`, `summary*.txt`).
- Dong thoi gian:
  - Probe 8 / 8 + 8 / 8: 2026-10-09 14:18 (che do ASUS Turbo) va 2026-10-10 02:14 (Performance).
  - 2026-10-10 13:36 cai Riot Vanguard (driver nhan `vgk`, start = system). Lan khoi dong dau sau do: 2026-10-12 17:49;
    loi dau tien: SA2 buoc 47 SIGSEGV 18:27-18:40 cung ngay, probe 05:33 ngay 13. Vanguard da go luc 2026-10-13 05:36
    (khoa dich vu `vgk` / `vgc` khong con), khoi dong lai 13:05, probe van loi 14:13-15:18: KHONG phai nguyen nhan hien tai.
  - Che do nguon: moi dot loi deu o Turbo, nhung plan Turbo va Performance co cai dat bo xu ly Windows giong het (min state
    100 %, EPP 0, boost mode 2) va 2026-10-09 14:18 Turbo van 16 / 16. Thu A/B plan Silent (min 5 %, EPP 45, boost policy
    60) 15:17: khong tot hon (Windows 2 / 8, WSL 0 / 8); da tra lai Turbo.
  - Luc do may ranh (CPU 2 %, RAM trong 18.9 GB); khong WHEA / Kernel-Power 41 / bugcheck trong thang 10; driver nhan ben
    thu ba dang nap (ASUS, Intel, NVIDIA, VMware, MiniTool) deu co tu truoc cac dot 8 / 8; khong driver anti-cheat nao
    (ACE, NEP, vgk) dang nap. `.wslconfig` (2026-09-26) binh thuong.
- Bo doi chung 15:06-15:18 (Turbo tru dong Silent):

  | phep thu | Windows 3.11.0 | WSL 3.14.4 |
  |---|---|---|
  | probe shlex khong ghim | 6 / 8 (Turbo), 2 / 8 (Silent) | 0 / 8, 0 / 8 |
  | probe shlex ghim mot CPU (0, 4, ..., 28) | 8 / 8 (ngay 13 tong 71 / 72) | khong ghim duoc nhan vat ly |
  | Python thuan khong shlex | 8 / 8 | 7 / 8 + 8 / 8 |
  | SHA-256 native file 380 MB | 4 / 4 trung | 4 / 4 trung (cung gia tri) |

  Loi am tham (khong crash) ghi duoc: WSL Python thuan tinh lai cung mot checksum ra 253721207 thay vi 270688859; Windows
  probe mat mot token o dong 263728; WSL `SystemError: unknown opcode 124` (bytecode doc sai). Mot chuong trinh 20 dong chi
  dung so hoc / chuoi khong the cho hai ket qua khac nhau tren CPU va bo nho dung, du phan mem nao chay.
- Ket luan: khong tim thay nguyen nhan phia du an (script, Python, plan nguon, driver game, tai may). Loi nam duoi tang
  phan mem cua du an (CPU / nen tang), xuat hien khi tien trinh chuyen giua cac nhan vat ly (WSL nang nhat vi vCPU troi
  giua cac nhan). Loi khong rong: native sach, Python ghim sach, cac ket qua chay kep van trung. Khong dung cong viec vi
  probe; Python phia Windows chay ghim; chay kep la cong quyet dinh. Ban danh gia thuc te: may khong "hong" voi tai
  thuong, nhung khong the noi "khong co loi"; chan doan phan cung chinh thuc (vd. Intel Processor Diagnostic Tool) do chu
  du an quyet dinh.
- Sua nhan dinh muc 14:55: "Python thuan 8 / 8 ca hai phia" chi dung cho lan do do; lan nay WSL co mot lan tinh sai, nen
  loi khong chi o shlex (shlex chi nhay hon). Tieu de muc do da sua gio (ghi nham 15:40, gio thuc 14:55).
- SA2 buoc 47 (SIGSEGV trong `drt::FlexGCWorker::Impl::checkMetalSpacing_short_skipFixed`, DRT tang dan sau ECO hold cua
  minh, dung o 24 vi pham tu vong 13) KHONG quy cho may: co the la bay tat dinh cua flow (nhu `global_route
  -start_incremental` SIGSEGV tat dinh). Lan chay lai khong doi se phan dinh; neu lap lai thi sua ky thuat.
- Cong suat DM cua so chinh xac XONG (chay ghim CPU 2): hai GLS moi + hai STA, p1 = p2 tung truong; tong 114.81-122.99 mW
  (TB 119.45), dong TB 119.02, ro 0.437 mW, EPI GM 3,608 pJ; lech so voi SAIF cu toi da 0.005 mW
  (`results/activity_power_exact_dm_20261013/receipt.json`). SA2 cua so chinh xac van cho.

### 2026-10-13 15:35 Board ramsweep DM: hien thi khop, UART chua nhan

- Sao chep Hercules3.2.8 tu tools cua ban cong bo sang tools/hercules trong research; hash khop, nguon khong doi.
  Mo COM3/115200/8N1/handshakeOFF. Nap SOF ramsweep/DM/seed2 mot lan, Quartus nativeexit0 luc15:22:35.
- Doc truc tiep LEDR[7:0]=10100101 (A5), HEX=0003D520, khop pairedreference. Chi mot luot hien thi; chua co
  MINSTRET thuc do/anh/UARTframe. Ghi observationJSON va dong pass1/ramsweep/DM, 199dong khac van NOT_RUN.
  UARTlog0byte, khong chot PASS day du, khong dua vao RESULTS. Khong reset/rerun/chuyen case khi chua xacnhan.
- Read-only fit/source: TXAB22=JP5pin1, RXAC15=JP5pin2, GNDJP5pin12; firmware in boot va fullreport truoc LEDRA5,
  sau do loop, khong tu phat lai. Can kiem tra wiring va capture truoc khi duyet rerun. Menu Hercules doi vi tri
  khi tat NVT; checkbox phai doc theo commandID/label. Giulai diagnosticcu, khong suy ra HideReceived tu index.
  Evidence: results/board_20261013/{hercules_launch.json,hercules_menu_by_command.json,p1_ramsweep_DM.observation.json}.

### 2026-10-13 15:41 Board ramsweep DM: UART khop 28 truong sau reset thu cong

- Xac nhan wiring CP2102RXD->JP5pin1/GND->JP5pin12 va co reset thu cong. Hercules receivepane co hai fullframe;
  xuat nguyen van GUI va tach frame de kiem tra: ca hai deu khop28truong voi pairedreference. Khong tinh hai
  frame thanh pass2, vi chi mot programmingreceipt. Khong reset/nap them bang script.
- Bat native logging vao p1_ramsweep_DM.additional_uart.log; snapshot712byte mot fullframe, checkerPASS28truong,
  MCYCLE0003D520/MINSTRET00028073. Giu log0byte ban dau va GUIexport; CSV ghi observedMINSTRET tu UART thuc.
  Mot case singlepass khop LED/HEX/UART, thieu anh va pass2; 199case con NOT_RUN. RESULTS khong doi.
- MenuLog nam trong submenu; HideReceived thuc te bat khi kiem tra readiness, da tat bang command38. Doc state
  theo ID trong dung submenu, khong suy doan tu index. LoggingON/NVTOFF/HideReceivedOFF duoc kiem lai.
  Cho xacnhan truoc ramsweep/SA2/pass1. Evidence: results/board_20261013/session.json, observationJSON,
  uart/p1_ramsweep_DM.native_capture_after_manual_reset.uart.log.validation.json, hercules_logging_ready.json.

### 2026-10-13 15:45 Board ramsweep SA2: UART singlepass khop28truong

- Chuyen Hercules sang native log rieng sau khi luu receivecu; loggingON/NVTOFF/HideReceivedOFF truoc nap.
  Quartus nap ramsweepSA2 seed2 nativeexit0 luc15:43:23; khong fit/reset/rerun.
- Native UART712byte mot PASS/DONE frame, MCYCLE0003D521/MINSTRET00028073; checker khop28truong voi paired
  reference va hashSOF/FW. Luu receipt, rawlog, GUIexport, validationJSON va CSV. Cho doc LED/HEX, chua ghi
  observedLEDR/anh/pass2. 198dong khac NOT_RUN, RESULTS khong doi. Dung cho xacnhan truoc case3.
- Evidence: results/board_20261013/p1_ramsweep_SA2.observation.json va uart/p1_ramsweep_SA2.uart_validation.json.

### 2026-10-13 15:50 Board ramsweep DM_VC4: UART singlepass khop28truong

- Xac nhan hien thi SA2 LEDRA5/HEX0003D521, ghi observed va cho phep case3. Chuyen Hercules sang native log
  rieng sau khi luu receivecu; Quartus nap ramsweepDM_VC4 seed2 nativeexit0 luc15:49:35, khong fit/reset/rerun.
- Native log712byte mot PASS/DONE frame, MCYCLE00041769/MINSTRET00028073; checker khop28truong voi paired
  reference va hashSOF/FW. Luu rawlog, GUIexport, validationJSON, receipt, observationJSON va CSV.
  Cho doc LED/HEX; chua ghi observedLEDR/anh/pass2. 197dong khac NOT_RUN, RESULTS khong doi.
  Dung cho xacnhan truoc ramsweep/DM_DSE. Evidence: results/board_20261013/p1_ramsweep_DM_VC4.observation.json.

### 2026-10-13 15:55 Board ramsweep DM_DSE: UART singlepass khop28truong

- Xac nhan DM_VC4 LEDRA5/HEX00041769 va cho phep case4. Nap ramsweepDM_DSE seed2 mot lan,
  Quartus nativeexit0 luc15:54:21; khong fit/reset/rerun. Hercules log rieng bat truoc nap, flush sau DONE.
- Mot fullUARTframe khop28truong voi pairedreference, MCYCLE0003D521/MINSTRET00028073. Luu programmingreceipt,
  rawlog, validationJSON, observationJSON va observedCSV. Cho doc LED/HEX; thieu anh va pass2; 196dong NOT_RUN.
  RESULTS khong doi. Dung cho xacnhan truoc up_aha-mont64/DM/pass1.
- Them helper hercules_case_ui.py chuyen/flush log va record_board_case.py ghi mot case offline de giam thao tac
  lap lai. Da doc source, AST/help recordhelperPASS, va chay thuc te confirmcase3/logcase4/recordcase4PASS.
  Helper khong nap/reset/mocase tiep, luu receivecu truoc clear, khong sua cac dong CSV khac.
  Evidence: results/board_20261013/p1_ramsweep_DM_DSE.observation.json va uart/p1_ramsweep_DM_DSE.uart_validation.json.

### 2026-10-13 15:59 Board aha-mont64 DM ban ngan: UART singlepass khop28truong

- Xac nhan DM_DSE LEDRA5/HEX0003D521 va cho phep case5. Nap up_aha-mont64/DM seed2 mot lan,
  Quartus nativeexit0 luc15:58:23; khong fit/reset/rerun. Hercules native log rieng mo truoc nap, flush sau DONE.
- Checker khop28truong voi pairedreference: MCYCLE00023DE3/MINSTRET00021C81. Giu rawlog, validationJSON,
  programmingreceipt, observationJSON va CSV. Ban ngan, khong gan nhan officialiterations; cho doc LED/HEX.
  Thieu anh va pass2, 195dong NOT_RUN, RESULTS khong doi. Dung cho xacnhan truoc up_aha-mont64/SA2/pass1.
- Evidence: results/board_20261013/p1_up_aha-mont64_DM.observation.json va uart/p1_up_aha-mont64_DM.uart_validation.json.

### 2026-10-13 16:04 Board aha-mont64 SA2 ban ngan: UART singlepass khop28truong

- Xac nhan DM LEDRA5/HEX00023DE3 va cho phep case6. Nap up_aha-mont64/SA2 seed2 mot lan,
  Quartus nativeexit0 luc16:02:22; khong fit/reset/rerun. Hercules native log rieng mo truoc nap, flush sau DONE.
- Checker khop28truong voi pairedreference: MCYCLE00024837/MINSTRET00021C81. Giu rawlog, validationJSON,
  programmingreceipt, observationJSON va CSV. Ban ngan; cho doc LED/HEX. Thieu anh va pass2, 194dong NOT_RUN,
  RESULTS khong doi. Dung cho xacnhan truoc up_aha-mont64/DM_VC4/pass1.
- Evidence: results/board_20261013/p1_up_aha-mont64_SA2.observation.json va uart/p1_up_aha-mont64_SA2.uart_validation.json.


### 2026-10-13 16:07 Board UART up_aha-mont64 DM_VC4

- board 20261013 case 7 pass 1: native UART khop 28 truong; MCYCLE=0x00024837, MINSTRET=0x00021C81.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:06:40.0040419+07:00; evidence: results/board_20261013/programming/p1_up_aha-mont64_DM_VC4.20261013_160632_757.log.json, uart/p1_up_aha-mont64_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 16:10 Board: thu hep phien vat ly con mot luot

- Pham vi duoc chot: chi pass1 cho100workload/config, van dung sau tungcase de kiem tra/xacnhan.
  Pass2 khong duoc len lich; giu100dong pass2 trong CSV voi NOT_SCHEDULED_SINGLE_PASS_SCOPE,
  khong xoa bangchung. Runlist chi con100casepass1. Day la ngoai le pham vi phien board;
  quy tac lap lai cho verification/FPGAfit/PD/power khong doi. So board ghi singleexecution,
  khong gan nhan doubleexecuted hay capdo doclap.


### 2026-10-13 16:11 Board UART up_aha-mont64 DM_DSE

- board 20261013 case 8 pass 1: native UART khop 28 truong; MCYCLE=0x00024837, MINSTRET=0x00021C81.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:11:00.8044712+07:00; evidence: results/board_20261013/programming/p1_up_aha-mont64_DM_DSE.20261013_161053_312.log.json, uart/p1_up_aha-mont64_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 16:14 Khoa helper board theo pham vi pass1

- program_board_case.ps1 va record_board_case.py tu choi pass ngoai scheduled_passes truoc ghi/nap;
  mac dinh legacy van[1,2]. Sau case100 trong phien[1], next_case/next_pass=None, khong len lich pass2.
- Python AST/help va PowerShell parserPASS. Hai lenh pass2 offline deu exit1 "is not scheduled";
  programhelper kiem bang PLAN ONLY, khong -Program. Hash session/CSV/NHAT_KY truoc/sau giunguyen.
  Khong thao tac board/UI/serial; day la kiem tra guard, khong la phep do vat ly.


### 2026-10-13 16:15 Board UART up_crc32 DM

- board 20261013 case 9 pass 1: native UART khop 28 truong; MCYCLE=0x00026CC2, MINSTRET=0x0001CC5E.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:15:28.4610376+07:00; evidence: results/board_20261013/programming/p1_up_crc32_DM.20261013_161521_073.log.json, uart/p1_up_crc32_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:17 Board UART up_crc32 SA2

- board 20261013 case 10 pass 1: native UART khop 28 truong; MCYCLE=0x0002E4DE, MINSTRET=0x0001CC5E.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:17:30.7282131+07:00; evidence: results/board_20261013/programming/p1_up_crc32_SA2.20261013_161723_401.log.json, uart/p1_up_crc32_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:23 Board UART up_crc32 DM_VC4

- board 20261013 case 11 pass 1: native UART khop 28 truong; MCYCLE=0x0002E4DE, MINSTRET=0x0001CC5E.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:23:06.4647432+07:00; evidence: results/board_20261013/programming/p1_up_crc32_DM_VC4.20261013_162259_199.log.json, uart/p1_up_crc32_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:28 Board UART up_crc32 DM_DSE

- board 20261013 case 12 pass 1: native UART khop 28 truong; MCYCLE=0x0002E4DE, MINSTRET=0x0001CC5E.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:28:34.0761356+07:00; evidence: results/board_20261013/programming/p1_up_crc32_DM_DSE.20261013_162826_802.log.json, uart/p1_up_crc32_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 16:30 Xac nhan day du matrix board ke ca cac bai lau

- Matrix giu du100ca:4ramsweep +48Embenchbanngan +48Embenchfulliterations, pass1duynhat.
  Khong bo case theo thoi gian chay; van cho xacnhan tung workload/config truoc ca tiep.
  Session ghi include_full_iteration_cases=true/skip_long_cases=false, runlist du100ca.
- Phai cho UART DONE day du truoc flush/logcheck. Het mot khoang cho chi tiep tuc kiem tra ca dang chay,
  khong cat firmware/khoi dong lai hay tu gan FAIL. Ban ngan va full dung cac reference tuong ung.


### 2026-10-13 16:34 Board UART up_depthconv DM

- board 20261013 case 13 pass 1: native UART khop 28 truong; MCYCLE=0x00023400, MINSTRET=0x0001AC47.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:34:42.9900360+07:00; evidence: results/board_20261013/programming/p1_up_depthconv_DM.20261013_163435_516.log.json, uart/p1_up_depthconv_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 16:34 Bo sung cho UART DONE cho bai board lau

- hercules_case_ui.py co --wait-done chi doc WM_GETTEXT tu dungPID/control, poll0.25s, default30s/range1..55.
  Dung truoc flush logging; timeout/multipleDONE/loi doc khong doi logging, khong reset hay nap lai board.
- AST/helpPASS, GUIfunctionalcheckthuc te DONEcount1 exit0 khong thao tacUI/hardware;
  receipt results/board_20261013/uart_wait_helper_check.json. Root doc source, ca13 cung qua waitDONE/recordUART.
  Khong tinh kiem tra helper thanh phep do board hay pass2.


### 2026-10-13 16:38 Board UART up_depthconv SA2

- board 20261013 case 14 pass 1: native UART khop 28 truong; MCYCLE=0x0002AB11, MINSTRET=0x0001AC47.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:38:44.3605768+07:00; evidence: results/board_20261013/programming/p1_up_depthconv_SA2.20261013_163837_137.log.json, uart/p1_up_depthconv_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:41 Board UART up_depthconv DM_VC4

- board 20261013 case 15 pass 1: native UART khop 28 truong; MCYCLE=0x0002AB11, MINSTRET=0x0001AC47.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:40:58.7122949+07:00; evidence: results/board_20261013/programming/p1_up_depthconv_DM_VC4.20261013_164051_344.log.json, uart/p1_up_depthconv_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:42 Board UART up_depthconv DM_DSE

- board 20261013 case 16 pass 1: native UART khop 28 truong; MCYCLE=0x0002AB11, MINSTRET=0x0001AC47.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:42:32.2511164+07:00; evidence: results/board_20261013/programming/p1_up_depthconv_DM_DSE.20261013_164224_883.log.json, uart/p1_up_depthconv_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:47 Board UART up_edn DM

- board 20261013 case 17 pass 1: native UART khop 28 truong; MCYCLE=0x00022301, MINSTRET=0x0001D78B.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:47:47.4579606+07:00; evidence: results/board_20261013/programming/p1_up_edn_DM.20261013_164740_085.log.json, uart/p1_up_edn_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 16:48 Giai thich depthconv DM_VC4 va DM_DSE trung counter

- Native UART hai config trong up_depthconv trung tat ca parsedcounter: victimhitI/D=0/0, Imiss3/Dmiss837,
  Iwait24419/Dwait37260, MCYCLE174865/MINSTRET109639. Hai config dung chungDSEctl, victimprobe tohop trong
  ST_LOOKUP; zero victimhit khong tu chung minh khongcoeviction. Khong suy doan khongmiss hay cache luonfit.
- Boardramsweep phanbiet ro: DM_VC4 Dvictimhit16/MCYCLE268137, DM_DSE Dvictimhit0/MCYCLE251169.
  Khong ket luan victimluonnhanh hon; SoF va controllerconfig duocgan qua receipt/hash da kiem.
  Chi singleexecution vatly, khongthemtest/trace hay doiRTL. Evidence: results/board_20261013/cache_comparison_depthconv.json.


### 2026-10-13 16:54 Board UART up_edn SA2

- board 20261013 case 18 pass 1: native UART khop 28 truong; MCYCLE=0x000236C1, MINSTRET=0x0001D78B.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:54:17.7026800+07:00; evidence: results/board_20261013/programming/p1_up_edn_SA2.20261013_165410_222.log.json, uart/p1_up_edn_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:55 Board UART up_edn DM_VC4

- board 20261013 case 19 pass 1: native UART khop 28 truong; MCYCLE=0x00023ECB, MINSTRET=0x0001D78B.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:54:59.2366383+07:00; evidence: results/board_20261013/programming/p1_up_edn_DM_VC4.20261013_165451_881.log.json, uart/p1_up_edn_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:55 Board UART up_edn DM_DSE

- board 20261013 case 20 pass 1: native UART khop 28 truong; MCYCLE=0x00023EDB, MINSTRET=0x0001D78B.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:55:52.0108909+07:00; evidence: results/board_20261013/programming/p1_up_edn_DM_DSE.20261013_165544_537.log.json, uart/p1_up_edn_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:57 Board UART up_huffbench DM

- board 20261013 case 21 pass 1: native UART khop 28 truong; MCYCLE=0x000540B8, MINSTRET=0x0003A5EB.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:57:05.5415717+07:00; evidence: results/board_20261013/programming/p1_up_huffbench_DM.20261013_165658_148.log.json, uart/p1_up_huffbench_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 16:58 Board UART up_huffbench SA2

- board 20261013 case 22 pass 1: native UART khop 28 truong; MCYCLE=0x000594EB, MINSTRET=0x0003A5EB.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T16:58:08.6044547+07:00; evidence: results/board_20261013/programming/p1_up_huffbench_SA2.20261013_165801_122.log.json, uart/p1_up_huffbench_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:00 Board UART up_huffbench DM_VC4

- board 20261013 case 23 pass 1: native UART khop 28 truong; MCYCLE=0x00059A98, MINSTRET=0x0003A5EB.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:00:04.8284411+07:00; evidence: results/board_20261013/programming/p1_up_huffbench_DM_VC4.20261013_165957_298.log.json, uart/p1_up_huffbench_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:01 Board UART up_huffbench DM_DSE

- board 20261013 case 24 pass 1: native UART khop 28 truong; MCYCLE=0x0005975B, MINSTRET=0x0003A5EB.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:01:15.1625948+07:00; evidence: results/board_20261013/programming/p1_up_huffbench_DM_DSE.20261013_170107_903.log.json, uart/p1_up_huffbench_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:02 Board UART up_matmult-int DM

- board 20261013 case 25 pass 1: native UART khop 28 truong; MCYCLE=0x000223B2, MINSTRET=0x00014467.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:02:18.3393101+07:00; evidence: results/board_20261013/programming/p1_up_matmult-int_DM.20261013_170210_911.log.json, uart/p1_up_matmult-int_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:04 Board UART up_matmult-int SA2

- board 20261013 case 26 pass 1: native UART khop 28 truong; MCYCLE=0x0002332E, MINSTRET=0x00014467.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:04:20.3645850+07:00; evidence: results/board_20261013/programming/p1_up_matmult-int_SA2.20261013_170412_973.log.json, uart/p1_up_matmult-int_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:06 Board UART up_matmult-int DM_VC4

- board 20261013 case 27 pass 1: native UART khop 28 truong; MCYCLE=0x0002468C, MINSTRET=0x00014467.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:06:32.9399815+07:00; evidence: results/board_20261013/programming/p1_up_matmult-int_DM_VC4.20261013_170625_630.log.json, uart/p1_up_matmult-int_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:07 Board UART up_matmult-int DM_DSE

- board 20261013 case 28 pass 1: native UART khop 28 truong; MCYCLE=0x00024B30, MINSTRET=0x00014467.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:07:48.2129173+07:00; evidence: results/board_20261013/programming/p1_up_matmult-int_DM_DSE.20261013_170740_889.log.json, uart/p1_up_matmult-int_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:09 Board UART up_md5sum DM

- board 20261013 case 29 pass 1: native UART khop 28 truong; MCYCLE=0x0001F857, MINSTRET=0x000171BC.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:09:15.4565880+07:00; evidence: results/board_20261013/programming/p1_up_md5sum_DM.20261013_170908_117.log.json, uart/p1_up_md5sum_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:10 Board UART up_md5sum SA2

- board 20261013 case 30 pass 1: native UART khop 28 truong; MCYCLE=0x00022D91, MINSTRET=0x000171BC.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:10:27.9915610+07:00; evidence: results/board_20261013/programming/p1_up_md5sum_SA2.20261013_171020_518.log.json, uart/p1_up_md5sum_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:12 Board UART up_md5sum DM_VC4

- board 20261013 case 31 pass 1: native UART khop 28 truong; MCYCLE=0x00022FA5, MINSTRET=0x000171BC.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:12:10.4399505+07:00; evidence: results/board_20261013/programming/p1_up_md5sum_DM_VC4.20261013_171202_983.log.json, uart/p1_up_md5sum_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:13 Board UART up_md5sum DM_DSE

- board 20261013 case 32 pass 1: native UART khop 28 truong; MCYCLE=0x00022CF1, MINSTRET=0x000171BC.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:13:40.2166949+07:00; evidence: results/board_20261013/programming/p1_up_md5sum_DM_DSE.20261013_171332_884.log.json, uart/p1_up_md5sum_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:14 Board UART up_nettle-sha256 DM

- board 20261013 case 33 pass 1: native UART khop 28 truong; MCYCLE=0x000231AE, MINSTRET=0x0000F24D.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:14:32.4684500+07:00; evidence: results/board_20261013/programming/p1_up_nettle-sha256_DM.20261013_171425_032.log.json, uart/p1_up_nettle-sha256_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:15 Board UART up_nettle-sha256 SA2

- board 20261013 case 34 pass 1: native UART khop 28 truong; MCYCLE=0x0002B143, MINSTRET=0x0000F24D.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:15:33.0381682+07:00; evidence: results/board_20261013/programming/p1_up_nettle-sha256_SA2.20261013_171525_576.log.json, uart/p1_up_nettle-sha256_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:16 Board UART up_nettle-sha256 DM_VC4

- board 20261013 case 35 pass 1: native UART khop 28 truong; MCYCLE=0x0002C072, MINSTRET=0x0000F24D.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:16:25.4264747+07:00; evidence: results/board_20261013/programming/p1_up_nettle-sha256_DM_VC4.20261013_171618_035.log.json, uart/p1_up_nettle-sha256_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:17 Board UART up_nettle-sha256 DM_DSE

- board 20261013 case 36 pass 1: native UART khop 28 truong; MCYCLE=0x00025BCE, MINSTRET=0x0000F24D.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:17:18.5878200+07:00; evidence: results/board_20261013/programming/p1_up_nettle-sha256_DM_DSE.20261013_171711_219.log.json, uart/p1_up_nettle-sha256_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:18 Board UART up_slre DM

- board 20261013 case 37 pass 1: native UART khop 28 truong; MCYCLE=0x00027DA6, MINSTRET=0x00015A66.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:18:09.8044303+07:00; evidence: results/board_20261013/programming/p1_up_slre_DM.20261013_171802_111.log.json, uart/p1_up_slre_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:19 Board UART up_slre SA2

- board 20261013 case 38 pass 1: native UART khop 28 truong; MCYCLE=0x0002F1AB, MINSTRET=0x00015A66.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:19:04.3257557+07:00; evidence: results/board_20261013/programming/p1_up_slre_SA2.20261013_171856_907.log.json, uart/p1_up_slre_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:21 Board UART up_slre DM_VC4

- board 20261013 case 39 pass 1: native UART khop 28 truong; MCYCLE=0x0002F17B, MINSTRET=0x00015A66.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:21:00.5810018+07:00; evidence: results/board_20261013/programming/p1_up_slre_DM_VC4.20261013_172053_264.log.json, uart/p1_up_slre_DM_VC4.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:21 Board UART up_slre DM_DSE

- board 20261013 case 40 pass 1: native UART khop 28 truong; MCYCLE=0x0002F18B, MINSTRET=0x00015A66.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:21:43.7991138+07:00; evidence: results/board_20261013/programming/p1_up_slre_DM_DSE.20261013_172136_412.log.json, uart/p1_up_slre_DM_DSE.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:23 Board UART up_statemate DM

- board 20261013 case 41 pass 1: native UART khop 28 truong; MCYCLE=0x00021B5F, MINSTRET=0x0000A7EF.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:23:21.3532732+07:00; evidence: results/board_20261013/programming/p1_up_statemate_DM.20261013_172314_038.log.json, uart/p1_up_statemate_DM.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.


### 2026-10-13 17:24 Board UART up_statemate SA2

- board 20261013 case 42 pass 1: native UART khop 28 truong; MCYCLE=0x00020925, MINSTRET=0x0000A7EF.
- Nap SOF seed2 nativeexit0, ket thuc 2026-10-13T17:24:34.1034231+07:00; evidence: results/board_20261013/programming/p1_up_statemate_SA2.20261013_172426_748.log.json, uart/p1_up_statemate_SA2.uart.log.
- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.

### 2026-10-13 19:20 IPDT PASS; khong chay tiep tu buoc fail; ECO hai luot trong mot buoc; khoi chay SA2 E1 va DM_VC4

- Intel Processor Diagnostic Tool 4.5 (goi offline tu downloadmirror.intel.com/919695, SHA-256 trung trang Intel, chu ky
  Intel hop le; chu du an duyet UAC cai va chay): ket qua PASS toan bo (Genuine Intel, brand, cache, MMX/SSE, IMC, so
  nguyen to, dau phay dong, Math FMA3, GPU stress, DGEMM AVX2 182 s). Ban luu `results/health_20261013_recheck/ipdt_4.5/`.
  IPDT la bai thu chuc nang / stress ngan; no khong phu dang tai Python chuyen nhan ma probe bat loi, nen hai ket qua
  khong mau thuan: theo tieu chi cua Intel CPU dat, va thuc hanh ghim nhan + chay kep giu nguyen.
- Quy tac chu du an nhac lai: khong chay tiep tu buoc fail (QUY_TRINH muc B, D). Hau qua:
  - sa2_corr3400x3325_..._rsztf_r1 (11.305 mm2) DONG o trang thai FAIL, huy lan chay lai tu PostRouteHoldECO. Chan doan:
    DRT tang dan sau ECO (197 buffer hold, dich toi da 28.1 um) dung o 24 short / spacing met1-met2 tu vong 13 toi 18 roi
    SIGSEGV trong boost::polygon cua `checkMetalSpacing_short_skipFixed`: loi hinh hoc cua die 11.305, khong quy cho may.
    11.305 chua chung minh route duoc; muon chung minh phai full flow moi tu buoc 1.
  - Quy trinh ECO hai luot cua SA2 (tach run sau buoc 47, config `_ecomin`) va CONTINUE sau cong p2 hold FAIL deu la noi
    tiep sau FAIL nen thay bang: (1) `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` (openlane-local, mac dinh tat) chay luot min_* trong
    cung buoc; kiem chung doc lap: luot 1 trung tung byte buoc 47 cua sa2_..._rsztf_r1, luot 2 trung tung byte buoc 48 cua
    ecomaxmin_r1 (netlist 9b7d9f43 / d6abb882, DEF 6a751591 / ddd22342; `asic/soc_sa2_4kb/eco2pass_check_20261013/`);
    (2) `P2_MIN_HOLD` cua gate_check.py (mac dinh 0) khai bao luc khoi dong; doi chung x2 tren hai run cu dung ky vong.
- Kiem tra doc lap so do board cua phien 2026-10-13 (`results/board_20261013_independent_check/`): 42 / 42 case co log UART
  du (boot..DONE, RESULT=PASS), 25 bo dem + D_ACCESS trung CA HAI luot tham chieu RTL, VERIFY_CODE trung giua 4 cau hinh
  cua tung kernel, HEX trung MCYCLE o moi case co doc hien thi. VERIFY_CODE la gia tri tra ve cua kernel, khong phai ma
  loi (lan doc dau cua checker hieu nham, da sua). Pham vi board chot: chi pass 1, 100 case; con 58 (10 ban ngan:
  statemate DM_VC4 / DM_DSE, tarfind x4, ud x4; 48 ban full iterations).
- Khoi chay (chu du an "chay tiep"), full flow tu buoc 1, env `G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5
  P2_INITIAL_GRT_FALLBACK=1`, log `asic/gated_queue_20261013_sa2cts25_vc4antcong.log`:
  - sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r1: thi nghiem SA2 tu toi uu E1, chi doi
    `CTS_SINK_CLUSTERING_SIZE` 8 -> 25 (mac dinh OpenLane; 8 ke thua tu DM). Ly do do: cay clock SA2 3,391 clkbuf + 1,939
    dummy load (0.0703 mm2) so voi DM 2,819 + 1,088 (0.0517 mm2) cho nhieu hon 7 % flop; cong suat clock 43.10 vs 33.02 mW.
  - vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong_r1: gia thuyet antenna-nghen da chuan bi
    (`DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`, `DRT_SAVE_MAIN_ROUTE`) + ECO hai luot trong buoc; ~20-24 h.

### 2026-10-13 20:25 SA2 E1 r1 crash ngau nhien, chay lai r2; LEC SA2 luot 1 buoc A dong; audit reset bat dong bo va clock

- sa2_..._rsztf_cts25_r1: P1 PASS (GRT overflow 0, STAMidPNR-2 nom_tt setup +1.627 / hold +0.181; ban ky ten +1.571),
  roi buoc 41 RepairDesignPostGRT SIGSEGV trong `pdr::primDijkstra` (Steiner tree cua global route). Dong FAIL, khong chay
  tiep. Chay lai doc lap rieng buoc 41 tu config / state_in cua chinh no (`asic/soc_sa2_4kb/diag_cts25_step41_20261013/`):
  xong khong crash, nen crash la ngau nhien. Theo quy tac: run MOI tu buoc 1 `_cts25_r2` (P1 PASS, so trung r1). DM_VC4
  antcong_r1 bat dau 12:52 UTC.
- LEC SA2 (`asic/equiv/lec/run_lec_sa2.ps1`, thu muc `results/lec_sa2_20261013/p1`, front end chuan bi tu
  `prepare_sa2_lec.py`): replay N1 trung tung byte buoc 06; chung minh `fsm` ma hoa lai 4 FSM: equiv_induct PROVEN.
  Buoc A (RTL + fsm == N1): 20,803 / 20,465 bit flop, 20,465 cap, 338 chi o gold; 231 flop hang chung minh hinh thuc (diem
  bat dong sau 2 vong, 2 bi ha bac), 18 ban sao, 4 nhom one-hot; 21,489 output: SAT 0 phan vi du, 34 output mo (32 bit
  d_req_addr + 2 kiem tra ban sao mem_byte_offset_m) = non bo nhan, dong bang: replay t1 (`synthesize_n1only_t1.py`),
  `macc_alg.py` PROVED product == signed33(A)*signed33(B) mod 2^64 o CA HAI phia, doi chung am (spec unsigned, tich rieng
  phan sai) NOT PROVED dung; `&cec` mang snapshot == bo nhan cua cap LEC (ca hai phia); thay bo nhan da chung minh roi
  `&cec` 34 output: Networks are equivalent. Bat bien one-hot 4 FSM: Q one-hot => D one-hot (4 UNSAT), ma reset one-hot.
- Audit cau truc reset bat dong bo (`asic/equiv/lec/arst_audit.py`, `run_arst_audit.ps1`, `results/lec_arst_audit_20261013/`;
  mo hinh truoc async2sync): moi bit flop ghep theo ten giua RTL va netlist cuoi phai cung co / khong co reset bat dong bo,
  cung nguon reset (qua alias / buf / not), cung muc tich cuc, cung gia tri reset. SA2 r1 va r2: 20,462 / 20,462 bit ghep,
  8,074 co reset (`reset_sync_q` muc 0) + 12,388 khong, 0 sai khac; DM r14F_A va r14F_B: 19,087 / 19,087, 7,519 + 11,568, 0
  sai khac; moi audit chay hai lan JSON trung tung byte; hai doi chung am (lat mot bit ARST_VALUE, doi nguon ARST sang
  reset_n) deu FAIL dung 1 sai khac. Dong muc "reset bat dong bo giua hai canh clock" cua LEC cho DM va SA2 o muc cau truc.
- Audit clock (`scripts/verification/lec_clock_audit_files.py` goi nguyen `lec_clock_audit.py`): 4 mo hinh phang SA2
  (gold, N1, final r1, r2) moi flop clock = input `clk`, canh len; hai lan, facts hash trung
  (`results/lec_clock_audit_sa2_20261013/`).
- Bat bien one-hot DM chung minh lai tren dung nguon hien tai (`results/lec_dm_inv_20261013/`: gold_flat_r14 trung hash
  luot 1, spec tao lai tu specAR14_c2 trung AR14_spec.json): 4 UNSAT, ma reset one-hot. Dong muc "cau noi bat bien" cu.
- Con chay: buoc B SA2 (N1 == netlist cuoi r1, r2), doi chung am FSM va buoc B; luot 2 doc lap cua toan bo LEC SA2.

### 2026-10-14 00:35 LEC SA2 luot 1 xong, X khong anh huong (DM + SA2); SA2 E1 r2 het RAM; DM_VC4 antcong dung o vong sua antenna

- LEC SA2 luot 1: buoc B1 / B2 (N1 == netlist cuoi r1 / r2): 21,471 output, SAT 0 phan vi du, 32 bit d_req_addr dong bang
  `&cec` (Networks are equivalent), ket qua hai netlist giong het. Doi chung am FSM (ma en_phase 10 / 01 doi cho): 10 $equiv
  khong chung minh, rc 1 dung. Doi chung am buoc B (netlist and2 -> or2) HOAN vi RAM (`DEFER_HEAVY`), chay sau.
- Gia tri khong xac dinh (`asic/equiv/lec/run_xsens.ps1`): moi bit x va net khong noi cua mo hinh gold LEC thanh input tu do,
  miter voi ban dat 0. SA2: 1,552 nguon, 21,489 / 21,489 output UNSAT; DM: 1,401 nguon, 20,124 / 20,124 UNSAT; moi ben chay hai
  lan giong nhau; doi chung am (`lec_d_p00001` = 1'x) cho dung 1 output SAT o ca DM va SA2. Nghia la khong output va trang
  thai ke tiep nao phu thuoc gia tri khong xac dinh o bat ky trang thai nao: dong toan bo muc "358 dong X" (48 dong con mo cua
  DM) va tuong tu cho SA2, khong can chung minh tung dong.
- sa2_..._cts25_r2: P1 PASS (+1.627 / +0.181), P2 PASS (STAMidPNR-3 nom_tt setup +0.959, hold +0.182; cong thuc ky ten +1.057 /
  -0.206), detailed routing xong 46 phut; buoc 51 Odb.ReportDisconnectedPins chet MemoryError (Python) luc 14:30 UTC khi
  detailed routing cua DM_VC4 (dinh 12.4 GB) chay cung VM WSL 24 GB: het tai nguyen, khong phai loi thiet ke. Dong FAIL;
  chay lai `_cts25_r3` tu buoc 1, mot minh tren may (bai hoc: P4 cua mot run va DRT cua run khac khong vua 24 GB).
- vc4_..._antcong_r1: main detailed route XONG 0 vi pham (main_route.odb luu); vong sua antenna 1: 2,270 net / 3,234 chan,
  global route cho nghen KHONG con GRT-0232 (gia thuyet dung o buoc GRT), chen 5,920 diode, nhung detailed route tang dan bat
  dau 59,810 vi pham, vong 13 con 8,323 > 5,000: drt_watch dung (cung nguong cho moi lan goi detailed_route). Dong FAIL.
  Phan tich: o buoc GRT co 2,916 net vi pham antenna (DM sau route 481, SA2 653), ty le toi 21.5x, tap trung o net dai toi
  chan SRAM (din0 / csb0) va mux du lieu victim. OpenROAD edf00dff chi co diode (khong jumper). Gia thuyet tiep: chuyen phan
  lon sua antenna ra TRUOC detailed routing (RUN_ANTENNA_REPAIR true, bien 10) tren die 3600 co padding va khong sua timing
  sau GRT; sang loc rieng buoc RepairAntennas tren trang thai sau GRT cua run nay (`asic/soc_vc4_4kb/screen_antgrt10_20261014/`,
  chi sang loc) de dem diode va overflow truoc khi ton full flow.
- Dang chay: sa2_..._cts25_r3 (mot minh), LEC SA2 luot 2 doc lap (`results/lec_sa2_20261013/run_pass2.sh`), sang loc antenna VC4.

### 2026-10-14 01:00 Sang loc antenna VC4 dat; SA2 E1 r3 crash ngau nhien lan ba; DM_VC4 V2 bat dau; LEC luot 2 chay lai

- Sang loc (khong phai ket qua) RepairAntennas o GRT, bien 10, 10 vong, tren trang thai sau GRT cua vc4_..._antcong_r1:
  vi pham 3,428 -> 1,015 -> 227 -> 54 -> 13 -> 7 -> 6 -> 4, 9,225 diode, overflow global route 0 (su dung 23.3 %), day 12.27 ->
  12.45 m. Khac die 11.56 mm2 ngay 2026-10-08 (cung buoc lam nghen cum tag). Gia thuyet V2:
  `config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json` (chi RUN_ANTENNA_REPAIR true, bien GRT 10).
  vc4_..._antgrt10_nogrtt_nogrtd_antcong_r1 bat dau 17:41 UTC (hang doi cho SA2 r3 ket thuc).
- sa2_..._cts25_r3: P1 trung r1 / r2; trong buoc 43 RepairAntennas, buoc con 2-openroad-checkantennas SIGSEGV trong
  boost::polygon (ant::wiresToPolygonSetMap), da chay 1 thread. Chay lai doc lap buoc con do: xong, 419 net vi pham (binh
  thuong giua chung), khong crash: ngau nhien. Ba lan that bai cua cong thuc nay deu khong do thiet ke (r1 SIGSEGV GRT, r2
  MemoryError, r3 SIGSEGV antenna) va moi buoc loi chay lai deu qua. Theo quy tac: r4 tu buoc 1, xep sau V2
  (`asic/queue_sa2_e1_r4_after_vc4_v2_20261014.sh`).
- LEC SA2 luot 2: front end lan dau (`p2/`) chet SIGSEGV Python WSL trong `evert.py pair`; khong noi tiep, chay lai tu dau o
  `p2b/` voi `asic/equiv/lec/run_frontends_mixed.ps1` (Yosys o WSL, moi buoc Python o Windows ghim mot CPU): replay trung
  tung byte buoc 06, fsm PROVEN, cap ghep trung luot 1 (gold-N1 20,465 cap / 338 chi gold; N1-final 20,462 / 3).
- Ban nhap cho chu du an: `results/review_status_20261014.md` (20 diem danh_gia: 10 da giai quyet, 4 mot phan, 6 chi con
  viec viet bai), `results/extensions_vs_published_1kib_20261014.md` (38 muc mo rong so voi ban 1 KiB).

### 2026-10-14 01:50 Do cong suat exact-window SA2 bat dau; kiem toan quy tac Q cua DM / SA2 da ky; chuan bi LEC DM_VC4

- Hai loi cua minh trong cach ghim CPU, sua ngay:
  - `start /affinity` nhan mat na HEX. `run_xsens.ps1` ghi `32` (= 0x32 = CPU 1, 4, 5, hai loi vat ly) thay vi mot CPU;
    sua thanh `20` (CPU 5). Ket qua cu van dung: hai luot DM chi khac 3 byte la dau thoi gian ABC ghi vao chu thich AIGER.
  - `cmd /c "start /wait ..."` tra 0 du chuong trinh con thoat 3 (thu truc tiep). Lay ma thoat dung bang
    `cmd /v:on /c "start /wait ... & exit !ERRORLEVEL!"` (thu 3 / 0 / 1 deu dung). Script LEC SA2 khong dung ma thoat (doc
    log); script moi tu nay dung cach tren va dung ngay khi ma thoat khac 0.
- Cong suat exact-window SA2 (tren netlist SA2 da ky, ecomaxmin): `scripts/maintenance/run_sa2_capture_20261014.ps1`,
  hai luot GLS doc lap (`results/gls_exact_sa2_full_p{1,2}_20261014`, chung minh freeze da co tu 2026-10-10), roi kiem
  cap; pha STA (WSL) chay rieng khi khong co detailed route. Ghim CPU 8 (qua probe ghim 2026-10-13). Bat dau 18:08 UTC,
  khoang 6 gio moi luot.
- Kiem toan quy tac Q (quy tac co tu 2026-10-13, sau hai lan ky):
  - DM r14F_A / r14F_B: ket thuc phien 2026-09-30 ~23:38 UTC giet ca hai, resume 2026-10-02 bang `run_resume_retry.sh`.
    r14F_A bi giet o Magic streamout (layout, netlist, RCX, STA xong); r14F_B bi giet trong detailed routing (buoc 46),
    route lai tu buoc 47. Netlist cuoi trung tung byte. Khong tuan thu quy tac Q khi thuc hien; chay lai kep tu buoc 1 la
    quyet dinh cua chu du an (DM dang khoa).
  - SA2 ecomaxmin: hai run nguon `_rsztf_r1/_r2` vuot cong p2 FAIL bang dong CONTINUE roi FAIL cong cuoi (hold ff
    -0.023 / -0.027); `_ecomaxmin` la nhanh cua hai run do sau buoc 47; `_ecomaxmin_r1` con resume buoc 52 sau crash
    CPython. `_ecomaxmin_r2` khong crash, netlist trung. SA2 tuan thu se la E1 (neu thang PPA) hoac E0 = cung cong thuc
    chay mot flow (`_rsztf.json` + CORNER_2 + P2_MIN_HOLD). Ghi trong PROJECT_STATE muc ASIC.
- LEC DM_VC4, phan chi phu thuoc tong hop: moi run DM_VC4 (12 run) co netlist buoc 06 trung tung byte (`c0448aa2`), 4 FSM
  ma hoa lai giong SA2. `scripts/verification/prepare_vc4_lec.py` (script .ys sinh lai cho SA2 trung 11/11 voi ban da dung,
  chi khac CRLF), `asic/equiv/lec/run_frontends_vc4.ps1`, `run_lec_vc4.ps1` (sinh tu `run_lec_sa2.ps1`, cung phuong phap,
  them kiem ma thoat), chuoi `results/lec_vc4_20261014/run_gold_n1_passes.sh` (p1, p2: front end, A, Mul, Inv, NegFSM,
  xsens) tu chay sau khi LEC SA2 luot 2 xong. Buoc B / NegB cho hai netlist DM_VC4 da ky.

### 2026-10-14 02:00 LEC SA2 xong hai luot giong het; DM_VC4 V2 vao detailed routing

- LEC SA2 luot 2 (`results/lec_sa2_20261013/p2b`): A, Mul, Inv, B1, B2, xsens deu trung luot 1; so tung doi tuong
  (`compare_lec_passes.py`): 39 doi tuong trung tung byte, moi dong ket luan trung: PASS1_EQUALS_PASS2, 0 khac biet.
  So lieu: fsm 38,300 cell proven / 0 unproven; gold 20,803 bit flop, 20,465 cap voi N1, 338 chi gold = 231 hang (diem
  bat dong lon nhat) + 18 ban sao + 89 tu do; 21,489 output, 34 con lai sau SAT tung output (32 bit d_req_addr + 2 kiem
  ban sao, deu sau bo nhan) dong bang chung minh nhan dai so (doi chung am unsigned / dot bien tich rieng phan deu FAIL)
  va `&cec`; one-hot 4 / 4 UNSAT; N1 == netlist cuoi r1 / r2: 20,462 cap, 21,471 output, 0 SAT, 32 dong bang `&cec`;
  X: 1,552 nguon, 21,489 / 21,489 UNSAT. Con mo: doi chung am NegB (and2 -> or2), hoan vi RAM. Ghi RESULTS 4.2.
- vc4_..._antgrt10_..._antcong_r1 (V2): P1 PASS trung hai run VC4 truoc (+1.518 / +0.182); P2 PASS: sua antenna o GRT hoi
  tu con 4 vi pham GRT (bo kiem tren uoc luong GRT bao 742 net), setup nom_tt +0.528, hold -0.235 (nguong khai bao -0.5);
  detailed routing bat dau 18:31 UTC (WSL con 23.2 GB).
- GLS exact-window SA2 luot 1: kernel dau (aha-mont64) dat: mcycle 149,553 = tham chieu, cua so dung 149,553 x 20 ns,
  97,945 muc SAIF; khoang 22 phut moi kernel.
- Sua RESULTS / PROJECT_STATE: board 42/100 (cau cu "chua do board"), ket qua 11.305 mm2 (cau cu "chua chay"), ghi chu
  quy tac Q cho DM / SA2 da ky.

### 2026-10-14 08:40 DM_VC4 V2 FAIL o vong sua antenna; SA2 E1 r4 crash Tcl; LEC DM_VC4 lan a dung (SRAM way 1), sua va chay lai

- vc4_..._antgrt10_..._antcong_r1 (V2) FAIL: detailed route chinh 0 vi pham o vong 31 (42 phut, nhanh hon nhieu so voi
  18.5 gio cua run 3600 dem truoc); kiem antenna sau route: 1,031 net / 1,453 chan (antcong_r1: 2,270); vong sua 1 chen
  2,295 diode, route lai 78,513 -> 1,389 (vong 16) -> 2,063 (vong 17), drt_watch dung luc 20:37 UTC (luat dinh tre: 2,063 so
  voi 2,219 bon vong truoc). Doi chieu: DM 481 net -> 1,051 diode -> route lai tu 21k, hoi tu; SA2 653 -> 1,453 -> 33k, hoi
  tu; VC4 1,031 -> 2,295 -> 78k, dinh tre. Muc tieu cho VC4: <= ~650 net sau route.
- Sang loc (khong phai ket qua): bien antenna o GRT 10 / 20 / 30 % -> 9,225 / 11,611 / 15,107 diode nhung con 742 / 753 /
  641 net vi pham sau sua GRT (GRT tu bao 4 / 6 / 8; sau do vong "extra iterations to remove overflow" route lai va sinh vi
  pham moi): bien KHONG phai don bay. Phan tich `main_route.odb` cua V2
  (`asic/soc_vc4_4kb/screen_ant_postdrt_v2_20261014/`): moi vi pham la PAR side-area (met3 885, met2 307, met1 194, met4 93),
  cong mux2 521 / a221o 238 / a22o 230, 837 / 1,031 net do resizer tao, dai trung vi 731 um (p90 1,138), 1,020 / 1,453 chan
  nam trong vung logic giua cot macro I$ va D$ (x 1200-2400, y 1200-2100). Nguyen nhan: chan dout1 (doc, met4, canh tren) cua
  ca 4 macro moi cache deu quay vao kenh 220 um giua hai hang macro (hang duoi N, hang tren FS), 128 bit doc moi cache cung
  bo dem victim (mux a22o / a221o) do ve vung giua.
- Sang loc tiep: chay lai rieng buoc DetailedRouting cua V2 (`screen_drt_replay_v2_20261014`: cung input / config, chi 1
  vong antenna, KHONG watchdog) de xem vong route lai co hoi tu khi du 64 vong khong; dong thoi kiem tinh tat dinh cua route
  chinh. Neu hoi tu: V3 = V2 voi luat watchdog cho vong antenna khai bao truoc; neu khong: doi cau truc (huong macro de dout1
  quay vao vung giua, chieu dai day toi da, diode heuristic).
- sa2_..._cts25_r4 FAIL: buoc 34 DetailedPlacement Tcl panic "TclParseNumber: bad acceptState 10 parsing '2720'" sau 6.5 s
  (trang thai khong the co tren mot so hop le: ngau nhien). Lan that bai ngau nhien thu tu cua cong thuc E1. r5 tu buoc 1
  (01:36 UTC) voi STOP_AFTER=p2 (dung co ke hoach sau P2) de DRT khong chay canh ban chay lai VC4; DRT se chay bang
  `run_gated_resume.sh ... drt` sau khi sang loc VC4 xong.
- LEC DM_VC4 lan a (`results/lec_vc4_20261014`) DUNG o buoc A p1: giao dien gold / N1 khac (input 22,609 / 22,353, output
  22,573 / 22,117) vi RTL tao ca way 1 cua hai cache DSE (8 macro SRAM) ma DM_VC4 khong doc va tong hop da xoa; runner moi
  bat duoc ngay (aig_syms exit 1). Sua: `asic/equiv/lec/sram_align.py` (dout cua macro chi co o gold la input tu do o ca hai
  ben; chan vao cua chung thanh day noi bo o gold vi macro khong ton tai trong chip), buoc A / Mul so ban can chinh, buoc B
  van so N1 goc voi netlist cuoi (cung 16 macro); doi chung am moi `NegAlign` (mot output so sanh lay bit dout way 1: phai
  SAT). Lan b (`results/lec_vc4_20261014b`) chay tu dau, hai luot.
- Lan b cung DUNG o buoc A p1 (09:38): so cong da khop (22,609 / 22,117 moi ben) nhung THU TU input lech 771 vi tri. Yosys
  `write_aiger` xep input / output AIGER theo thu tu KHAI BAO day (khong theo so hieu cong), ABC ghep hai ben theo vi tri; cong
  gia cua N1 bi khai bao o dau module. Loi cua minh: lan thu truoc chi kiem tap ten cong, khong kiem thu tu. Sua:
  `sram_align.py` khai bao cong gia ngay sau cong chung dung truoc no trong thu tu cua gold va tu kiem thu tu khai bao hai
  ben (khac thi exit 1); kiem tron chuoi can chinh -> evert cut -> AIG -> aig_syms tren front end that cua lan b: 0 vi tri
  lech. Lan c (`results/lec_vc4_20261014c`) chay tu dau 01:44 UTC.

### 2026-10-14 09:50 Chu du an sua quy tac Q; ban chay lai DRT cua V2 trung tung vong; watchdog rieng cho vong antenna

- Quy tac Q sua (chu du an, 2026-10-14): khi phat trien duoc sua va chay tiep tu buoc loi; khi moi thu da qua thi BAT BUOC
  mot lan chay tron tu buoc 1 (tag moi, khong resume / tach nhanh / CONTINUE, nguong khai bao luc khoi chay); chi lan chay
  tron do la ket qua. Ghi trong QUY_TRINH muc B, D va PROJECT_STATE muc 1. He qua: DM r14F_A/B va SA2 ecomaxmin can moi
  thiet ke mot lan chay tron.
- Ban chay lai buoc DetailedRouting cua V2 (sang loc, khong watchdog): route chinh trung V2 tung vong (0: 141,013, 1: 72,401,
  ..., 17: 283, ..., 31: 0), kiem antenna 1,031 net, chen 2,295 diode, route lai 0: 78,513, 1: 30,580 ...: flow tat dinh.
- `asic/drt_watch.sh`: them luat rieng cho cac lan goi detailed_route thu hai tro di (vong sua antenna), TAT mac dinh, bat bang
  `G5_ANT_ROUND_RULES=1` khai bao luc khoi chay (nguong tam: vong 20 > 3000, 30 > 600, 40 > 200, luat dinh tre tu vong 20);
  `DRT_WATCH_ROOT` / `DRT_WATCH_LOG` de thu. Thu (`scratchpad drtw_test.sh`, log that cua V2 + log gia): mac dinh tai hien
  dung lan dung o vong 17; bat luat antenna: khong dung; doi chung dinh tre tu vong 12: dung; 3,500 o vong 20: dung. Nguong
  that se chon theo quy dao cua ban chay lai. Bay khi thu: pgrep cua watchdog khop ca dong lenh `bash -c` co chua duong dan
  run, nen phep thu phai chay tu file script.
- LEC DM_VC4 lan c: buoc A qua (735 bit flop chi gold = 364 hang + 18 ban sao + 353 tu do; 22,117 output, 0 SAT, 34 mo = nhom
  bo nhan nhu SA2); doi chung am NegAlign: lec_d_p00001 noi vao bit doc way 1 -> 1 SAT, phat hien dung. Buoc Mul DUNG o mot
  phep kiem sai cua minh: doi netlist cuoi cua replay t1 trung tung byte buoc 06 (khong trung, voi SA2 cung vay; replay t1
  chi de chup mang maccmap, moc chung minh la `&cec` cua bo nhan thuan). Sua `run_lec_vc4.ps1`: ghi chu tham khao thay vi
  dung; buoc Mul dung khi ket luan that sai (dai so PROVED, hai doi chung NOT PROVED, hai moc `&cec` va `&cec` sau thay the
  equivalent; thu tren dau ra that cua SA2). Theo quy tac moi: chay tiep p1 tu Mul de phat trien: Mul qua (dai so PROVED ca
  hai phia, doi chung NOT PROVED, moc t1 / rtl equivalent, 34 output equivalent), Inv 4 / 4 UNSAT, NegFSM 10 cell khong chung
  minh rc 1, xsens 1,796 nguon -> 22,117 / 22,117 UNSAT. Bang chung cuoi: lan d (`results/lec_vc4_20261014d`) hai luot tron
  tu dau, chay tu 03:02 UTC.
- Cong suat exact-window SA2 XONG: hai luot GLS doc lap VERIFIED (12/12 moi luot, cap kiem 03:25 UTC), pha STA 26 lan
  OpenSTA (12 phut, chay canh ban chay lai DRT, WSL du bo nho): p1 = p2 moi truong. Tong 127.45-131.75 mW (TB 129.64),
  dong 127.02-131.31, ro 0.437, EPI 2,848-7,354 pJ (GM 4,317), unknown 4.42 %; moi kernel lech <= 0.005 mW so voi so SAIF
  cu. `results/activity_power_exact_sa2_20261014/receipt.json`. DM so voi SA2 (exact): 119.45 / 129.64 mW, EPI GM 3,608 /
  4,317 pJ. Ghi RESULTS 4.2, PROJECT_STATE, ban nhap danh_gia (A9 con DM_VC4) va danh sach mo rong.

### 2026-10-14 12:15 LEC DM_VC4 phan tong hop xong hai luot; ban chay lai V2 cham; DM_VC4 V4 (die 3800) bat dau

- LEC DM_VC4 lan d (`results/lec_vc4_20261014d`), hai luot tron tu dau: PASS1_EQUALS_PASS2, 0 khac biet (30 doi tuong trung tung
  byte + 9 nhom ket luan). fsm 39,000 cell proven; gold 21,828 / N1 21,093 bit flop, 735 chi gold = 364 hang + 18 ban sao +
  353 tu do; 22,117 output, 0 SAT, 34 nhom bo nhan dong bang dai so + `&cec`; one-hot 4 / 4; X 1,796 nguon, 22,117 / 22,117
  UNSAT. Doi chung: NegAlign phat hien (1 SAT), NegFSM 10 cell khong chung minh rc 1, xsens 1'x: NOT_PROVED 1. Con lai sau
  khi ky: B (N1 == netlist cuoi), NegB, audit reset bat dong bo va clock. Ghi RESULTS muc 6, PROJECT_STATE.
- Ban chay lai DRT cua V2 (sang loc) qua cho V2 bi dung: route lai 2,063 (vong 17) -> 1,019 -> 745 -> 703 -> 685 (vong 21),
  vong 22 nam o 20 % hon 45 phut (CPU 420 %, 12 GB): giam cham dan, cay o vung kho. Ket luan tam: duong "V2 + noi watchdog"
  qua cham va khong chac.
- DM_VC4 V4 (`config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json`): cong thuc V2 tren floorplan 3800 x
  3400 (12.92 mm2, vung giua rong 1,457 thay 1,257 um); chi DIE_AREA / CORE_AREA / MACRO_PLACEMENT_CFG khac V2. Bat dau 05:11 UTC,
  giu sau P2 (STOP_AFTER=p2) vi ban chay lai con giu ~12 GB; DRT chay voi `G5_ANT_ROUND_RULES=1` (khai bao luc khoi chay).
- SA2 E1 r5 van giu sau P2 (DRT cua SA2 can ~10.4-10.8 GB, WSL chi con ~5-10 GB khi ban chay lai chay).
- V4 (3800): P1 PASS (setup +1.263, hold +0.182), P2 PASS (setup +0.476), giu sau P2. Chi bao som AM: kiem antenna sau sua
  o GRT con 821 net / 1,137 chan (V2 tren 3600: 742 / 1,005; 8,869 diode): be rong die KHONG phai don bay; chua cho chay DRT.
- Phan tich them V2: 538 / 1,027 net vi pham co 5-8 chan (la cua cay buffer fanout, MAX_FANOUT 8), dai trung vi 731 um. Gioi
  han chieu dai day (hien 0 = resizer tu cho 4,393 um) tinh tren do dai sau route cua V2: 500 um cat ~6,000 net (~7,500
  repeater, ~0.05 mm2) phu 754 / 1,027 net vi pham; 600 um: 4,800 / 660; 800 um: 2,700 / 430.
- V5 = V2 + `DESIGN_REPAIR_MAX_WIRE_LENGTH` 500 (mot bien; `config_..._antcong_mwl500.json`), chay phat trien giu sau P2,
  chi bao som la so vi pham o buoc kiem antenna sau sua GRT.
- V5 FAIL p2: resizer chen 23,680 buffer vao 7,038 net; STAMidPNR-3 setup nom_tt -1.068, hold -1.882; kiem antenna sau sua GRT
  van 873 net / 1,061 chan (V2 742): chieu dai day cung KHONG phai don bay (nhieu net vi pham dai 200-500 um; gioi han ngan
  hon se chen qua nhieu buffer). Ket luan: bien antenna, be rong die, chieu dai day deu khong giam duoc vi pham; duong dung la
  diode sau route, va ban chay lai cho thay vong route lai sau sua antenna HOI TU CHAM: 2,063 (17) -> 703 (20) -> 633 / 555 /
  510 -> 353 (30) -> 293 (34).
- V3 = cong thuc V2 khong doi, chay tron tu buoc 1 khong giu (`vc4_..._antcong_r2`), chi khac thiet lap luc khoi chay: luat
  watchdog cho lan goi antenna hieu chinh theo quy dao that cua ban chay lai (`G5_ANT_ROUND_RULES=1`, vong 20 > 3000, 30 > 600,
  40 > 400, khong gioi han sau 40). Flow tat dinh nen V3 vua la thu vua la nghiem thu; DRT tu cho slot bo nho khi ban chay lai
  con chay. Neu ban chay lai cho thay khong hoi tu: dung V3 bang co hop tac.
- V3: P1 PASS (+1.518 / +0.182, trung V2), P2 PASS (+0.528), cho slot DRT. Ban chay lai: 35: 283, 36: 282, 37: 281, 38: 277,
  39: 236 (vong 22 va 35 moi vong chay ~1 gio). Khong dung duoc ban chay lai de nhuong bo nho cho V3 (quy tac M: dung job PD
  dang chay de giai phong bo nho da bi tu choi, khong thu lai); bao chu du an neu muon tu dung.
- LEC SA2 doi chung am NegB (and2_1 dau tien cua netlist cuoi r1 -> or2_1): 60 output SAT (phan vi du tren if_req_addr va
  predict_taken_d) o buoc N1 == netlist cuoi: phat hien dung. LEC SA2 day du moi doi chung. Ghi RESULTS 4.2 va muc 6.
- Chuan bi lan chay tron bat buoc cua DM (quy tac Q sua): `asic/queue_dm_clean_run_20261014.sh` (config_R14_FINAL.json, snapshot
  rtl_r14, cong mac dinh: r14F_A qua p1 / p2 / final voi chung), tag `dm_grid3665x2900_r3`, chay khi khong co pha nang nao khac.
  Dinh chinh: ma netlist cuoi DM dung hien nay la sha256 `83f38f7e...` (ca r14F_A buoc 55 va r14F_B buoc 56, cung la ma cua cac
  bien nhan cong suat); ma `7ae150fe` o muc 2026-09-29 khong khop file nao con lai.
- Ban chay lai V2: 40: 235, 41: 235, 42: 231, 43: 225 (giam 1-3 % / vong, du kien ~150 o vong 64): vong route lai sau sua
  antenna cua cong thuc V2 KHONG hoi tu trong 64 vong. V3 (tai hien tat dinh cung quy dao) se that bai: dung hop tac bang
  `.abort_gated_pd` truoc DRT (08:31 UTC, "STOP ... after P2 (abort flag)"); co doi ten thanh `.abort_gated_pd.used_20261014_v3`.
  Loi cua minh: bo cho doi ten co dung `pgrep -f run_gated_pd.sh` trong `bash -c` nen tu khop chinh no va khong thoat; doi ten
  tay va TaskStop bo cho.
- Hang doi pha nang (`asic/sequence_heavy_20261014.sh`, mot pha nang mot luc, dua tren dong ket thuc trong gated_pd.log): cho ban
  chay lai xong -> SA2 E1 r5 DRT + sign-off -> V4 (3800) DRT + sign-off (moi truong da khai bao luc khoi chay) -> lan chay tron DM.
  Dung hop tac giua cac buoc: `asic/.abort_sequence_20261014`.
- Chu du an: uu tien viec ngan truoc. Doi thu tu: dung hang doi cu (co hop tac, 09:09 UTC), chay ngay lan chay tron DM
  `dm_grid3665x2900_r3` (P1 / P2 nhe; DRT tu cho slot bo nho), hang doi moi `asic/sequence_heavy_20261014b.sh`: cho ban chay lai
  va DM xong -> SA2 E1 r5 (DRT + sign-off, ~2.5 gio) -> V4 3800 (dai nhat, cuoi).
- 09:23 UTC ban chay lai DRT cua V2 ket thuc (chu du an dung OpenROAD cua no theo huong dan; dung o vong 44, 225 vi pham):
  WSL trong ~21 GB. Doi tiep thu tu cho "ngan truoc": dung hang doi b (co hop tac), hang doi c
  (`asic/sequence_heavy_20261014c.sh`): SA2 E1 r5 DRT + sign-off NGAY (09:34 UTC) trong luc DM r3 con o pha nhe P1 / P2; sau khi
  SA2 bat dau DRT, hang doi giu khoa slot DRT (`asic/.gated_drt_gate.lock`) de DM r3 (lan chay nghiem thu) khong vao DRT khi SA2
  dang route / ky ten (P4 khong co cong bo nho); nha khoa khi SA2 xong -> DM DRT + sign-off -> V4.
- Lan goi agent cloud dau tien (cap nhat trang ban giao) loi khi tao worktree (chu o dia e: / E:) va de lai worktree + nhanh
  `worktree-agent-ae25d606b11a3137d` + thu muc `.claude/` trong repo da cong bo (chi doc); lenh go cua minh bi bo loc an toan
  tu choi, khong thu lai; da dua lenh go cho chu du an. Lan goi thu hai chay duoc.
- GLS exact-window SA2: luot 1 VERIFIED 12/12 (xong 22:43 UTC), luot 2 dang chay (7/12 luc 01:15 UTC).

## 9. Van de da biet

Moi van de ghi mot lan o day, kem so lieu co tham quyen; cac muc ngay o tren chi tham chieu.

### Loi may

- Tu it nhat 2026-09-18, may tram (i9-13980HX; hai module DDR5-4800 khac ma, HMCG78AEBSA095N + HMCG78MEBSA092N) crash ngau
  nhien va doi khi tra ket qua SAI ma khong crash. Bang chung: probe Python thuan tu kiem 2026-09-18 chi sach 0/8, 1/8, 1/8
  (WSL: Python cua OpenROAD, Python he thong) va 5/8 (Windows); 9 su kien Kernel-Power 41 va 6 bugcheck (0x1E, 0x50) trong 45
  ngay; WHEA-Logger ID 19 (corrected parity error, APIC 33 = P-core 4) ngay 18-19/09; GCC internal compiler error doi file /
  pass moi lan build lai; Yosys cho 26 log khac nhau tu cung dau vao. Tu 2026-09-26: phep thu shlex hong 0/16 trong WSL ca tren
  file tong hop hop le, Windows 64/64 sach tren moi logical CPU.
- Health check hien hanh: `python3 asic/parse_ids_probe.py --synth 300000` (tu kiem so token tung dong; chay 8 lan, ky vong
  8 lan "OK"). Probe cu `probe_pure_python.py` khong con bat duoc loi (da luu tru).
- Trang thai 2026-10-13 (muc ngay 15:20): sau khi go Vanguard va khoi dong lai, may ranh, van loi: probe khong ghim Windows
  2-6 / 8, WSL 0 / 8; ghim mot CPU Windows 71 / 72; Python thuan WSL co lan tinh sai checksum; native sach. Da loai tru:
  script du an, Python, plan nguon (Turbo / Performance / Silent), driver game, tai may. Khong co WHEA / KP41 trong thang 10.
  Thuc hanh: Python phia Windows chay ghim (`cmd /c start /wait /b /affinity`), crash ngau nhien chay lai mot lan, chay kep
  quyet dinh, khong dung toan bo cong viec chi vi probe (quy tac P).
- Lech huong N / FN cua mot cell trong DEF giua hai lan chay (2026-09-25, lap lai tren run khac): chua xac dinh nguyen nhan.
- Quy tac: moi phep do chay hai lan va so tung truong; crash native doi vi tri giua cac lan thu duoc chay lai khong doi gi;
  loi tat dinh cua cong cu / thiet ke phai sua that. Buoc nang ve Python (EQY `read_ids`, report odbpy) bi anh huong nhieu
  nhat. Sua phan cung (tat XMP, thu tung DIMM, MemTest86) chua lam.

### OpenRAM suon xuong

- Macro OpenRAM sky130 dua `dout` ra o suon xuong (Liberty `timing_type falling_edge`; model `always @(negedge clk)`), nen moi
  duong tu dout SRAM toi flop suon len chi co nua chu ky (10 ns o 50 MHz).
- DM 8 KiB-RAM: vong fetch (dout I-cache -> giai ma -> bo cong dich -> PC fetch) truot -0.569 ns nom_tt / -0.827 ns max_tt;
  bon thi nghiem PD ket thuc -0.63 .. -1.01 ns; sua RTL cycle-exact ngay 2026-09-25 (bo cong dich tach phan cao / thap, chung
  minh SAT) cho +2.190 ns.
- SA2 / DM_VC4: core DSE ghi moi beat refill tu dout cua RAM chinh thang vao macro lane trong cung nua chu ky, nen khoang
  cach RAM -> macro lane quyet dinh timing (floorplan vong: 55 repeater = 8.02 ns, nom_tt -1.093 ns). Floorplan phai giu
  hang RAM sat cac macro lane.

### Uoc luong RC

- Ky sinh day ma resizer dung lay tu dien dung don vi trong tech LEF, khong co thanh phan ghep: tren 2,072 net mau, uoc luong
  theo placement thap hon RCX 2.37x (trung vi 2.13x), theo global route 1.93x (net dai 2.1-2.2x).
- He qua: vi pham slew / cap song sot qua flow (ban ky ten 8 KiB-RAM nom_tt: slew 757, cap 807) va uoc luong ss sau CTS /
  sau GRT lac quan khoang 4 ns.
- `LAYERS_RC` k = 2.0 (C = 2 x dien tich / canh trong LEF, R = RPERSQ / w_min, bang ORFS sky130hd) giam sai so con 1.19x /
  0.96x; OpenLane 2.3.10 doc `LAYERS_RC` trong `set_rc.tcl` nhung khong khai bao bien (khai bao trong openlane-local). Trong
  full flow no doi ca hai lan global placement timing-driven tu buoc 23: max_ss -8.311 -> -9.518 ns va 3 vi pham hold max_ff,
  nen khong dung cho sign-off. Chi trong `repair_design` (`LAYERS_RC_SCOPE`): slew / cap nom_tt 213 / 402 voi +4.1 % dien
  tich cell; o ban 16 KiB-RAM no sinh ~84,000 um2 buffer "wire".

### Buffer hold

- Bien hold slack 0.1 ns o PL / GRT (dat de che sai so uoc luong truoc khi co hold ECO sau route) lam resizer chen 18-19k
  `dlygate4sd3_1` trong khi chi ~50 endpoint vi pham that truoc sua: ban 8 KiB-RAM 19,019 buffer = 189,693 um2 = 13.6 %
  dien tich cell; ban 16 KiB-RAM (thi nghiem) 18,259 = 182,523 um2.
- Bien 0.03 ns + hold ECO tren RCX 0.02 ns: con 1,032 buffer (-172,000 um2), hold van sach; nam trong cau hinh ky ten 16
  KiB-RAM (cell 1.3696 mm2). Tren ban 8 KiB-RAM (bien 0.02): -13.2 % dien tich nhung max_ss xau 2.6 ns, khong nang golden.

### Job nen va ket thuc phien

- Job dai khoi tu mot phien terminal la con cua phien: khi phien ket thuc, WSL2 tat may ao khi khong con client `wsl.exe` va
  moi job nen chet (`setsid` / `nohup` trong WSL khong giup). Tach job qua WMI hay Task Scheduler bi chinh sach quyen cua
  cong cu tu choi: khong thu lai.
- Mat mat: 2026-09-26 (Quartus luot 1 dung o dse_4kb), 2026-09-30 04:50-09:59 (Quartus luot 2, hai run knob 16 KiB-RAM),
  2026-09-30 23:38 (hai run ky ten 16 KiB-RAM, chuoi N-way, hang doi SA2 / DM_VC4), 2026-10-07 01:17 (het usage: toan bo batch
  hop nhat). Khoang 2026-10-03 .. 10-06 khong mat gi vi moi job da xong.
- Phuc hoi: resume tung run tu buoc cuoi da xong (`asic/run_resume_retry.sh`, `asic/run_gated_resume.sh`). Job phai song qua
  luc phien ket thuc thi chu du an tu chay tu terminal WSL cua minh.

### Yosys nhay voi ten

- Ket qua Yosys / ABC phu thuoc ten va thu tu doc: doi ten mot port (`branch` -> `branch_en`) lam netlist 1 KiB +2,728 cell
  (+2.8 %) ma logic khong doi. Chenh lech dien tich / so cell ASIC duoi khoang 3 % khong quy duoc cho thay doi thiet ke.
- Netlist cua RTL N-way va FAST_HIT khac tung byte netlist 16 KiB-RAM vi ly do nay; tuong duong duoc chung minh thay vi so
  byte (35,067 / 36,741 / 37,441 `$equiv` cho DM / SA2 / DM_VC4).
- Nhanh generate `g_nway` doi ten core DSE thanh `genblk1.g_dse`; kiem muc SoC phai doi ten phia gate (`rename_genblk.py`, chi
  ten) truoc `equiv_make`, va co doi chung am muc SoC. Kiem muc SoC chay mot minh.
- ABC `fraig_restore` co the cham benh ly (~1 gio) tren mot dang ma hoa (2026-09-26); netlist phu thuoc trang thai tien
  trinh Yosys (cach nhom cua `maccmap`, thu tu dau vao ABC), nen ban replay voi hook co the khac tung byte du cung logic.

### Confound controller

- DM dung controller 5 trang thai; SA2 / DM_VC4 / DM_DSE dung core DSE 10 trang thai, hit mang chinh ton them mot chu ky
  (ST_IDLE -> ST_LOOKUP -> ST_HIT_RESP / ST_CPU_RESP).
- Tren 12 kernel Embench goc (line 16 B): rieng controller ton +4.33 % (256 B) .. +10.83 % (8 KiB) GM chu ky, +9.83 % o 4 KiB;
  to chuc cache tren cung controller chi doi SA2 -0.26 %, SA4 -0.07 %, DM_VC4 +1.03 % o 4 KiB. "DM thang SA2" la ket qua cua
  controller.
- Voi FAST_HIT = 1: phan du DM_DSE so voi DM +0.01 % o 4 KiB (+1.09 % o 256 B, do L0 D-cache / chinh sach store miss); set
  associative nhanh hon DM o moi dung luong (4 KiB: SA2 -0.28 %, SA4 -0.09 %; -3 .. -10 % duoi 2 KiB); DM_VC4 van cham hon
  (+1.07 % o 4 KiB) vi ban sao eviction noi tiep voi refill. Hieu ung theo kernel lon ca hai chieu nen ket luan phai theo
  workload.
- FPGA: controller sau hon ton +444 LE (+3.0 %, 1 KiB, 4 seed) va khong cham hon; FAST_HIT ton +115 .. +881 LE, Fmax giam
  toi 3.8 %. Nhan dinh 2026-09-18 rang tag dong bo "xoa confound" la sai.

### SDC create_clock

- `soc.sdc` viet `set clocks [create_clock ...]`; `create_clock` cua OpenSTA khong tra ve gi nen `set_clock_uncertainty 0.25`,
  `set_clock_transition 0.15` va moi `set_input_delay` / `set_output_delay` bi bo im lang (72 / 78 cong ra khong duoc kiem).
  Sua ngay 2026-09-24 (`create_clock`, roi `set clocks [get_clocks ...]` nhu `base.sdc` cua OpenLane). Moi timing ASIC
  truoc ngay do lac quan dung bang uncertainty.
- Do lai cac netlist 1 KiB da luu bang cong cu that (SDC cu tai lap metric da cong bo den 4 chu so):
  - ban 1 KiB nghien cuu: setup tt +3.412 -> +3.162 ns; hold tt +0.202 -> -0.048, ss +0.483 -> -0.123, ff +0.104 -> -0.146;
  - ban 1 KiB cong bo: setup tt +2.944 -> +2.694, ss -10.933 -> -11.183; hold tt +0.302 -> +0.052, ss +0.657 -> -0.231, ff
    +0.186 -> -0.064;
  - endpoint khong rang buoc 121 -> 46. Ban 4 KiB: 161 -> 86 -> 84 (ca 84 do hang so dieu khien).
- File SDC cua ban 1 KiB cong bo giu nguyen (chi doc). Bang chung: `asic/evidence/sdc_recheck_1kb_{research,published}/`.

### Magic namespace collision

- Hai loi doc lap cua cac buoc Magic voi macro OpenRAM va hai ban sua (`read.tcl` cua openlane-local; `.magicsafe.gds`),
  chung minh tung hinh: `asic/evidence/MAGIC_NAMESPACE_COLLISION.md`. `MAGIC_CAPTURE_ERRORS` luon true.

### EQY va LEC

- Current audit2026-10-10: legacy mapped SAT/CEC/algebra closure la bang chung to hop co premises,
  khong tu dong la full sequential proof. Sampling reset chi tim candidate, khong prove base;
  D-function equality khong tu chung minh clock/edge, initialization hay reachability. Subproof moi da dong
  gold reset235constant/28duplicate/4FSM va clock tren4 functional flatmodel x2. Raw N1/final paired reset,
  exactinput invariant/FSM bridge va setundef-undriven-zero/source-model abstraction van mo; xem
  lec_proof_scope_20261010 va dm_lec_clock_audit_20261010. Giu legacy verdict/log, current claim co gioi han.
- Buoc `Yosys.EQY` goc khong bao gio xong tren thiet ke nay: thieu cong cu trong shell nix `--pure` cua OpenLane (make, grep;
  `run_pd_mk.sh` them vao PATH), crash trong `read_ids` Python (loi may), va gioi han that: tong hop ma hoa lai 4 FSM sang
  one-hot, EQY ghep theo ten va cat tai net to hop (input tu do voi gia tri khong the dat), mot partition (`d_req_write`,
  ~16,700 flop) can hon 23 GB. Tot nhat: 795/876 partition (chay doc lap); voi grep tren PATH: 10 partition roi FAIL o
  `LCD_EN` (ma hoa FSM).
- Tuong duong cua netlist ky ten 8 KiB-RAM duoc chung minh bang chuoi LEC anh xa thanh ghi RTL == RTL+fsm == N1 (truoc ABC)
  == netlist da route (`asic/equiv/lec/`): 19,881 output, 0 phan vi du, 235 flop chi co o RTL chung minh la hang, 4 bat bien
  one-hot chung minh, 34 output cuoi (bo nhan 33x33) dong bang viet lai nguoc dai so (`macc_alg.py`, 1,128 don thuc, ~2 s)
  noi bang `&cec`; moi buoc chay hai lan trung hash, co doi chung am. Macro SRAM la hop den (GLS phu phan nay).
- Ban DM 16 KiB-RAM: LEC RTL - netlist ky ten da xong hai luot, co doi chung am va closure bo nhan (muc 8 ngay 2026-10-09).
  SA2 chi co replay N1 byte-exact, chua co LEC netlist cuoi; DM_VC4 chua ky ten. Khong dong nhat RTL - RTL voi LEC cuoi.
  final_B tung cap formal_pdk / config / extra / NL / Liberty cho 14 reader. Ngay 2026-10-09 da archive 6 input
  dung byte va doi reader sang archive / root formal_pdk.v byte-identical. Path-only va target binding da kiem;
  khong chay lai proof. Lenh xoa run bi tool review chan nen folder con giu; khong thu lai bang tool khac.

### View ASIC va view FPGA

- View ASIC (RTL voi model OpenRAM thay RAM FPGA) retire dung cung dong lenh, moi bo dem kien truc va cache trung (40/43
  truong; chuoi so 33), nhung `mcycle`, I-wait, D-wait thap hon vi wrapper RAM chinh ASIC khong mo phong hook do tre cua RAM
  FPGA (`ICACHE_MISS_PENALTY=2`).
- RAM 8 KiB, kernel cu: 1,436,264 / 1,449,098 chu ky (-0.89 %), CPI 1.2755 / 1.2869, theo kernel -0.2 .. -10.6 %. RAM 16 KiB,
  kernel Embench goc: DM -4.18 %, SA2 -3.67 %, DM_VC4 -3.23 %. GLS cua moi netlist ky ten tai lap `mcycle` view ASIC tung chu ky
  (12/12).
- CPI chip va nang luong moi lenh phai dung chu ky view ASIC (mot cot EPI cu tron hai view: sai toi 12 %); so view FPGA dung
  cho so sanh to chuc cache.

### Liberty OpenRAM

- `sky130_sram_1kbyte_1rw1r_32x256_8` va `sky130_sram_2kbyte_1rw1r_32x512_8` chi co Liberty TT, nen STA ss / ff dung timing TT
  cho macro va lac quan tren duong qua SRAM (macro OpenRAM cu cham hon ~10 % o SS 1.8 V).
- Chi `addr0` / `addr1` / `wmask0` co `max_transition 0.04` ns (din / csb / web 0.5 ns), do 10-90 % trong khi thu vien cell
  do 20-80 %; OpenSTA quy doi o bien thu vien nen gioi han la 0.030 ns theo quy uoc cell. buf_8 rieng chi dat khi cach chan
  ~8 um; halo cat row 10 um giu buffer >= 12 um, con 44-70 chan vuot 0.1-5.6 ps. `dout` max_capacitance 0.0276 pF.
- Theo quy tac 2026-09-30, cac vi pham nay bao cao theo loai (chan SRAM / net nhieu diode / cell chuan), khong sua bang dien
  tich lon. Cau "khong the dat voi day that" trong bao cao cu da duoc thay bang phan tich nay.

### Cong suat

- Metric `power__total` cua OpenLane la goc STA cuoi (max_ff_n40C_1v95), khong phai tt (ban 8 KiB-RAM: 115.5 mW).
- Cong suat vectorless cho logic to hop ~0 mW va phu thuoc hoat dong gia dinh cua dau vao (`reset_n` la cong vao chua dong
  bo lam switching tang ~37 mW: 154.34 -> 102.96 mW).
- Bao cao cong suat theo hoat dong: GLS -> SAIF -> OpenSTA o nom_tt voi SPEF RCX (`asic/gls/`), ghi ro ty le "unknown". Bay da
  biet: OpenSTA 2.6 `read_saif` bo qua net phang (phai gan vao chan lai, `saif_to_pins.py`), chan trong vong phan hoi khong
  duoc lan truyen, Questa giu DURATION tong khi `power reset`.
- So lich su: ban 8 KiB-RAM 110.61-115.43 mW (vectorless 102.05), EPI 2,379-3,637 pJ; ban DM 16 KiB-RAM 114.8-123.0 mW (TB 119.5,
  vectorless 109.15), "unknown" 5.38 % chan ra (dout SRAM va buffer sau no). DM chi con raw STA luot mot, thieu bang chung
  STA luot hai: khong dung activity power / EPI DM lam ket qua da chay kep. Cong suat macro SRAM lay tu Liberty TT, khong phu
  thuoc hoat dong.

### Antenna

- VC4 padding die12.24 (2026-10-11): mainDRT co DRC0 nhung post-DRT antenna round1 con2243net/3211pin;
  repair tim2604violation, chen5978diode roi fatal GRT-0232 Routing congestion too high. Tongstep18:29:33,
  khongco runtime/state_out; GATEdriver in abort/crash la thongdiepchung, khongphai nguyen nhan.
  Khongco G5ABORT/SIGSEGV/OOM evidence cho runnay, chua taihienkep. Tag ant off khong co nghia
  post-DRT repairtat: resolved.json dat5vong/margin10. DRC0truocsua khongla finalsignoff;
  khongretryunchanged, khongvohieu antenna gate. Evidence: results/vc4_postdrt_antenna_failure_20261011.json.
- LEF macro OpenRAM khong co du lieu antenna lam CheckAntennas segfault; them `ANTENNAGATEAREA 0.126` /
  `ANTENNADIFFAREA 0.4455` um2 tu thu vien cell (59 chan vao). `set_thread_count 1` sua race OpenMP trong `repair_antennas`.
- Diode heuristic o 90 um lam te hon (101,367 diode, 429 -> 529 vi pham); o 250 um giam ~74 % nhung them ~20k diode duoc
  tinh la tai, gay 3,276 / 3,277 vi pham fanout du lieu cua ban ky ten dau (con 140 net / 159 pin sau route).
- OpenLane 2.3.10 chi sua antenna tren global route; vong sua sau detailed route them trong openlane-local
  (`DRT_ANTENNA_REPAIR_ITERS 5`, margin 10; mac dinh tat) dat 0 / 0 (420 -> 22 -> 2 -> 0) khong can diode heuristic; dung
  trong moi ban ky ten tu 2026-09-28 (cell 1.453 -> 1.400 mm2, -20,191 cell).

### Bay trang thai run

1. Khong xoa thu muc step da xong cua run con co the resume: `state_in.json` cua cac buoc sau tro toi file cua buoc truoc bang
   duong dan tuyet doi (2026-09-19 lam hong resume cua hai run). Thu muc khong co `state_out.json` thi xoa duoc.
2. Khi resume, OpenLane lay `state_out.json` moi nhat tim de quy, khong phai cua buoc truoc `--from`: resume qua mot buoc bi
   gate tat lam antenna repair chay lai tren database da sua (2026-09-25); mot run noi tiep tren database da detailed route
   hong ~300 lan voi GRT-0226 (2026-09-24). `asic/pd_driver.py` kiem chuoi state.
3. Cau hinh chi duoc doc luc flow bat dau: sua xong phai chay lai.
4. `state_out.json` cua STAMidPNR mang metric ss / ff cu tu STAPrePNR; so cua mot goc chi lay tu report rieng cua goc do.
5. Thu muc step ton tai truoc khi step chay, va flow bi cat ngan cung ghi `final/`: thanh cong la `state_out.json` hoac metric.
6. Run co buoc cuoi (EQY goc) hong thi khong co `final/`: artefact ky ten nam trong thu muc step.

### Khong sua script dang chay

- Bash doc script theo offset nen sua script dang chay doi luon cai no chay tiep (2026-09-18 mot sweep chet giua chung;
  2026-10-03 mot replay ket thuc bang loi cu phap vo hai); file nguon sua trong luc flow doc cung bi doc nua chung (`alu.v`
  2026-09-25). Viet file moi; dung vong lap bang co huy hop tac (`asic/.abort_*`, `results/.abort_*`) vi lenh kill tu phien
  bi tu choi.
- Runner phai bao ma tra ve cua chinh cong cu (`rc=$?` dat sau `$(date)` tung bao rc=0 cho run loi).

### Goc ss

- Quy tac: CPI khong doi, nen ss duoc bao cao chu khong sua. Ban 8 KiB-RAM: nom_ss -7.413 / max_ss -8.311 ns (2,511 endpoint,
  ~35 MHz); ban DM 16 KiB-RAM: nom_ss -6.897 / max_ss -7.365 ns (TNS -11,439); ban DM hanh lang 11.305 mm2: nom_ss -8.292 /
  max_ss -8.754.
- Phan ra (2,557 endpoint, max_ss): trung binh 15.8 ns logic trong 22.6 cell + 7.8 ns trong 16 repeater + 0.5 ns day; 1,504
  endpoint la PC -> hit I-cache -> stall -> enable regfile / BHT. STA what-if: moi vong bi cat lai lo vong ke o -4 .. -8 ns; dong
  ss can pipeline moi (fetch 2 tang voi du doan o decode, execute 2 tang, stall dang ky, cay reset co pipeline). Cac thay doi
  cycle-exact va AREA 3 khong doi max_ss; so ss tren duong SRAM lac quan (Liberty chi TT).

### Verilator va latch

- Verilator `--Werror-LATCH` bao 0 latch voi khoi `always @(*)` (chi bat `always_comb`); `design__inferred_latch__count` cua
  OpenLane khong phai bang chung. Dung `scripts/latch_sweep.sh` (Yosys, moi to hop cau hinh) va dem cell `dlxtn` / `dlxtp`
  trong netlist cong.

### Pham vi kiem chung va provenance

- UVM frozen la subset DM, seed1; bo sung `scripts/verification/run_uvm_matrix.py` phu 4 cache cfg, seed1/2/3,
  AXI stress va UART RX. Chua phu SA4/FAST_HIT1; UCDB la functional coverage, khong phai code coverage.
  Aggregate coverage va axi_stress_test o out/ ngay 2026-09-18 la lich su, khong phai coverage RF/BHT hien tai.
- Random runner truoc 2026-10-09 chi gate hash va ghi de raw: trace co header co the PASS khi bi cat. Da sua
  gate rc/PASS/Fatal/completion va giu raw theo pass. Day la BP OFF/ON cung core, khong phai Spike doc lap.
- CSV comparator cu chi so cot giao nhau. Ban hien tai fail khi schema/field/key/metric bi mat, kem doi chung
  mat cot va hai metric rong. Du lieu Embench/board cu da duoc so full header/field, chua thay ket qua sai.
- CoreMark: sw/main_coremark.c dat PASS chi tu counter invariant, khong truyen CRC validity cua coremark_main;
  core_main.c in CRC loi qua UART nhung tra MAIN_RETURN_VAL hang. Snapshot bao quanh ca initialize / CRC / UART,
  khong chi iterate. Runner hien tai da gate CRC tu passive APB TX observer; 11 diem current x2 khop numeric
  reference. Firmware / TB khong doi; counter van full-program va khong official score. Sweep cu can CRC rieng.
- ACT4: tb/architecture_signature_tb.sv cap 1 MiB nhung index [18:2] alias moi 512 KiB. 43 ELF hien tai co non-tohost
  ALLOC <= 0x320a0, tohost 0x81ff0 duoc bat bang dia chi day du; chua thay alias anh huong cac signature hien tai.
  Suite dung payload tren 512 KiB can sua harness va kiem lai. Pham vi hien tai unprivileged I + Zmmul.
  Runner duy tri `scripts/verification/run_architecture_window.py` generate correction rieng va kiem ca nua tren;
  TB frozen cu giu de truy nguon, khong dung truc tiep cho payload vuot 512 KiB.
- Manifest chi phu ASIC top-level cua DM, khong phu top SA2 / VC4 va asic/dse_sram. Them hash provenance rieng,
  khong rewrite manifest dang khoa. Input config / SDC / .do / fw_board / sw_metrics co receipt rieng.
- R17 tung la alias cua R8 bo dong bo dau vao, khong phai successor cua R16 FAST_HIT. Ten chuc nang + ngay va
  fingerprint dung de tracuu; ten Rxx khong du de chon ket qua. Comment trong RTL frozen van co ten tai lieu cu /
  NOT YET RUN; khong sua comment roi tuyen bo manifest IDENTICAL.

## 10. Nhat ky don dep

Danh sach tung file / run da xoa: `results/cleanup_deleted.txt` (mot muc moi lan don). Bang chung cua run da xoa
(resolved.json, metric cuoi, log loi / canh bao, flow log, danh sach buoc): `results/pd_run_archive/<run>/`.

| ngay | da xoa | dung luong | ghi chu |
|---|---|---:|---|
| 2026-10-09 | final_B CHUA XOA | 0 | 6 input va 562 evidence files verified; 14 readers migrated; native deletion blocked by tool policy; cleanup_outcome.json |
| 2026-10-09 | 17 run PD da archive va 22 thu vien Questa idle | 79.558 GiB logic | SHA / metric / step list khop; giu 2 run co dependency; 20 source/coverage va 6 root file bi tool review chan, chua xoa; results/workspace_audit/ |
| 2026-09-19 | run that bai, roi step lap lai cua bao retry trong hai run con lai | 24.6 GB, roi 61 -> 13 GB | vong hai lam hong resume (muc 9 "Bay trang thai run") |
| 2026-09-24 | 697 thu muc step that bai (khong co `state_out.json`) | 31 GB | 5 log dai dien o `asic/evidence/failed_steps_20260924/` |
| 2026-09-26 | 5,074 file nhi phan tai tao duoc cua 30 run loi thoi | 157.1 GB | giu moi log / report / metric |
| 2026-09-26 | 47 run loi thoi va trung gian | ~112 GB | |
| 2026-09-27 | 159 muc: run cua netlist cu, mau mat do khong chon, scratch EQY | 68.6 GB | |
| 2026-09-27 | 177 file trung gian cua chung minh tuong duong | 7.47 GB | 2 dau vao cua chung minh dai so giu dang gzip |
| 2026-09-28 | run tham do antenna / RC, run RC hieu chinh bi loai | 43.9 GB | |
| 2026-09-30 | 15 run bi thay the | 101.3 GB | chu du an tu xoa |
| 2026-10-07 | san pham build tai tao duoc o goc (db Quartus, thu vien Questa, VCD) | ~5 GB | |
| 2026-10-07 | 77 run PD loi thoi / that bai / sang loc | 198 GB | |
| 2026-10-07 | goc `asic/`: 68 script mot lan, 178 log console, thu muc thi nghiem | ~5.7 GB | `results/pd_run_archive/asic_{console_logs,experiments}_20261007.tar.gz` |
| 2026-10-07 | tai lieu trung lap (gop vao `NHAT_KY.md`, `QUY_TRINH.md`, `RESULTS.md`, `REVIEW_RESPONSE.md`, `README.md`) | - | git giu ban goc |
| 2026-10-07 | 84 config va 45 floorplan cua cac thi nghiem da xoa run (giu 21 config, 14 floorplan dang dung); 3 thu muc thiet ke 1 KiB khong dung (`soc_dm_dse`, `soc_dse_vc1`, `soc_vc4_check`); ghi chu lac `asic/FLOW_JOURNAL.md` trong repo cong bo | 45 MB | git giu config / floorplan; file text 1 KiB trong `results/pd_run_archive/asic_1kb_designs_20261007.tar.gz` |

Luon giu: tai lieu duy tri, log (log cu duoc nen), CSV chuan da chay kep, moc 1 KiB (`asic/soc_dm_control/runs/sync_final`),
bang chung Magic (`asic/evidence/MAGIC_NAMESPACE_COLLISION.md` va cac file no liet ke), SOF board, cac run ky ten va golden
snapshot.

## 11. Bang doi ten

Ten cu van con trong log, commit, ten thu muc va comment cua script. Khong doi ten tren dia nhung gi mot run con giu
(duong dan tuyet doi trong `state_in` / `resolved.json`); ten moi dung cho tai lieu va cho run / file moi.

| ten cu | ten moi / muc trong nhat ky | loai |
|---|---|---|
| HANDOVER_CODEX.md | PROJECT_STATE.md | tai lieu trang thai, da doi sau khi coordinator thoat |
| CODEX_PROMPT.md | instructions lich su, khong la quy tac hien hanh | ban sao cu, da archive; xoa bi tool review chan |
| make_golden_snapshot2.py | golden snapshot helper, de xuat ten golden_snapshot.py | chua doi ten: tool review chan |
| dmuA / dmuB | dm_corr3400x3325_f220_r1 / dm_corr3400x3400_f220_r1 | run DM, hanh lang, lan chay 1 |
| sa2uA / sa2uB | sa2_corr3400x3325_f220_r1 / sa2_corr3400x3400_f220_r1 | run SA2 |
| vc4uA / vc4uB | vc4_corr3400x3325_f220_r1 / vc4_corr3400x3400_f220_r1 | run DM_VC4 |
| u2fg33 (`config_u2fg33.json`, `macro_placement_u2fg33.cfg`), "phuong an A" | corr3400x3325_f220 (11.305 mm2, hang cache tren lat FS, khe 220 um) | floorplan |
| u2fg (`config_u2fg.json`), "phuong an B" | corr3400x3400_f220 (11.56 mm2) | floorplan |
| U2 khac (u2a, u2s1..s5, u2f, u2fh, u2fg3/35/4, u2ng3/35, u2nm3, u2r1, u2b) | corr<W>x<H>_<n/f><khe> | floorplan sang loc (`fp_summary_20261006.md`) |
| wide, ring1, ring2, strata1, channels, column, four-corner | wide4211x3331, ring3200x3190, ring3700x3400, strata3260x3400, bands2800x2900, c1k_column1800x2900, c1k_corners1800x2900 | floorplan cu |
| r14F_A / r14F_B, `config_R14_FINAL.json`, `macro_placement_grid_r14.cfg` | dm_grid3665x2900_r1 / _r2, floorplan grid3665x2900 | DM 16 KiB-RAM da ky ten (2026-10-02) |
| final3_A / final3_B, `config_FINAL3.json` | dm_ram8k_grid2800x2900_drtant_r1 / _r2 | DM 8 KiB-RAM da ky ten (2026-09-28), golden |
| final_A / final_B / r12b_d42, `config_FINAL.json` | dm_ram8k_grid2800x2900_heurdiode_r1 / _r2 / _r3 | ban ky ten 8 KiB-RAM dau tien |
| final2_A | dm_ram8k_grid2800x2900_drtant_rc2 | bi loai (RC hieu chinh) |
| sync_final (soc_dm_control) | dm_c1k_baseline | moc 1 KiB |
| r14_A, r14_E7 .. r14_E16 | dm_grid3665x2900 + knob (bang trong "2026-09-29 PD DM 16 KiB-RAM"); E16 = cau hinh ky ten | thi nghiem knob |
| x_E1 .. x_E6, x_E3R, x_E3R2, x_E5b, x_E4_A, X1 .. X4 | thi nghiem tren final3 ("2026-09-27 Antenna sau detailed routing", "2026-09-28 Thu nghiem") | thi nghiem knob |
| f3_H1 / f3_H2 | dm_ram8k_grid2800x2900_hold002 / _dens55_hold003_cts8 ("2026-09-30 Thac dien tich") | thi nghiem |
| sa2F_A/B, vc4F_A/B, vc4R1F_A, vc4S1, <cfg>U2<fp>[G50] | sa2 / vc4 tren luoi DM, luoi rong, vong, tang; sang loc hanh lang | muc 8 |
| G1, G2, G3, G4, G5, G6 | grt_overflow, cts_tt_slack, grt_repair_overflow, grt_tt_slack, drt_convergence, signoff | cong flow |
| asic/snapshots/rtl_r14, rtl_r15, rtl_r16 | RTL 2026-09-29 "RAM 16 KiB", 2026-10-02 "core N-way", 2026-10-06 "FAST_HIT" | snapshot RTL cho PD |
| R1 .. R16 cua 2026-09-24 | cac muc trong "2026-09-24 Dot sua RTL va view ASIC" | muc cong viec RTL |
| R8 (sau goi R17), a0c425f8 | "2026-09-25 Bo dong bo dau vao bat dong bo" | ban RTL |
| R7a + R7b + R8, 358cb660 | "2026-09-25 Bo cong dich fetch, mot bo nhan 33x33, chan nguon macro" | ban RTL |
| R9 (ecf4fc03), R10 / fix 1 / fix 2 (b56fbd4e, 2bffe7cc, d030ad12), R11 | "2026-09-26 Sua co trong tam cho goc ss" | ban RTL |
| R12 (e21ef330), R12b (8b163675) | "2026-09-26 RTL cuoi cua ban 8 KiB-RAM" | ban RTL |
| R13a / R13b | thu RTL cycle-exact / nhan 2 tang ("2026-09-28 Thu nghiem") | thu nghiem RTL |
| R14 (535ec0f9, 1d584624, 3ea52396; 9b868f10 sau khi bo kernel tu viet) | "2026-09-29 RAM chinh 8 -> 16 KiB" | ban RTL |
| R15 (d409b09d) | "2026-09-30 Core N-way (SA4)" | ban RTL |
| R16 (ea3ef852, c09143ea), *_fast, r16f | "2026-10-03 FAST_HIT"; diem FAST_HIT = 1 co hau to `fast` | ban RTL |
| rtlfix / c235dfb7 (b82c2717, aa8e32f9) | "2026-09-24 Dot sua RTL" va "2026-09-25 Chi con 4 KiB" | ban RTL |
| dedup / synccache / tagfix / sanitized | trang thai RTL 2026-09-17 .. 18 (muc 1) | ten file ket qua cu |
| Entry 1 .. 33 (`CLAUDE_AUTONOMY_LOG.md`) | cac muc 2026-09-16 .. 18 (muc 1, 2) | tieu de cu |
| Entry 34 .. 35 | "2026-09-27 Ban ky ten 8 KiB-RAM dau tien" | tieu de cu |
| `PD_incident_report.md` A, B1-B4, C1-C11, D1-D5, E1-E3, F, G1-G8, Incident 33-38 | muc 2 (2026-09-18 .. 19); B3 / B4 o ghi chu bang chung Magic | tieu de cu |
| `asic/FLOW_JOURNAL.md` log 2026-09-22 .. 24, Incident 52-56 | muc 2 (2026-09-22 .. 24) | tieu de cu |
| Incident 57-61 | "2026-09-25 PD tren RTL dong bang dau tien" | tieu de cu |
| Incident 62-70 | "2026-09-25 Bo dong bo dau vao bat dong bo" | tieu de cu |
| Incident 71-75 | "2026-09-25 Bo cong dich fetch ..." | tieu de cu |
| Incident 76-81 | "2026-09-26 Sua co trong tam ..." va "2026-09-26 RTL cuoi ..." | tieu de cu |
| Incident 82 | "2026-09-26 Chon cau hinh PD cho RTL 8b163675" | tieu de cu |
| Incident 83-90 | "2026-09-27 Ban ky ten 8 KiB-RAM dau tien" | tieu de cu |
| Incident 91-92 | "2026-09-27 Antenna sau detailed routing, DRV, goc ss; ban ky ten final3" | tieu de cu |
| Incident 93 | "2026-09-28 Thu nghiem tren ban ky ten final3" | tieu de cu |
| Incident 94, 95 (ket qua r14F) | "2026-09-29 PD DM 16 KiB-RAM tren luoi 3665 x 2900", "2026-09-30 Thac dien tich va bien hold" | tieu de cu |
| Incident 96 | muc 8 | tieu de cu |
| Incident 97 | muc 9 "Job nen va ket thuc phien" | tieu de cu |
| hau to _A / _B cua run | _r1 / _r2 (lan chay kep); A / B trong "phuong an A / B" la floorplan | quy uoc |
| TAG Quartus / CSV rtlfix, c235dfb7, r7r8, r10, r10f2, r12, r12b, r14, r15, r16, r16f | giu cho file cu; do moi dung ten theo ngay (rtl_YYYYMMDD_<noi dung>) | ten file ket qua |
