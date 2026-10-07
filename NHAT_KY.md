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

- Buoc `Yosys.EQY` goc khong bao gio xong tren thiet ke nay: thieu cong cu trong shell nix `--pure` cua OpenLane (make, grep;
  `run_pd_mk.sh` them vao PATH), crash trong `read_ids` Python (loi may), va gioi han that: tong hop ma hoa lai 4 FSM sang
  one-hot, EQY ghep theo ten va cat tai net to hop (input tu do voi gia tri khong the dat), mot partition (`d_req_write`,
  ~16,700 flop) can hon 23 GB. Tot nhat: 795/876 partition (chay doc lap); voi grep tren PATH: 10 partition roi FAIL o
  `LCD_EN` (ma hoa FSM).
- Tuong duong cua netlist ky ten 8 KiB-RAM duoc chung minh bang chuoi LEC anh xa thanh ghi RTL == RTL+fsm == N1 (truoc ABC)
  == netlist da route (`asic/equiv/lec/`): 19,881 output, 0 phan vi du, 235 flop chi co o RTL chung minh la hang, 4 bat bien
  one-hot chung minh, 34 output cuoi (bo nhan 33x33) dong bang viet lai nguoc dai so (`macc_alg.py`, 1,128 don thuc, ~2 s)
  noi bang `&cec`; moi buoc chay hai lan trung hash, co doi chung am. Macro SRAM la hop den (GLS phu phan nay).
- Ban 16 KiB-RAM: moi co tuong duong RTL - RTL (Yosys equiv); LEC RTL - netlist cua ban ky ten 16 KiB-RAM da bat dau (replay
  tong hop 2026-10-03, `asic/equiv/lec/synth_replay_r14/`) va chua xong.

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
- So: ban 8 KiB-RAM 110.61-115.43 mW (vectorless 102.05), EPI 2,379-3,637 pJ; ban DM 16 KiB-RAM 114.8-123.0 mW (TB 119.5,
  vectorless 109.15), "unknown" 5.38 % chan ra (dout SRAM va buffer sau no). Cong suat macro SRAM lay tu Liberty TT, khong phu
  thuoc hoat dong.

### Antenna

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

## 10. Nhat ky don dep

Danh sach tung file / run da xoa: `results/cleanup_deleted.txt` (mot muc moi lan don). Bang chung cua run da xoa
(resolved.json, metric cuoi, log loi / canh bao, flow log, danh sach buoc): `results/pd_run_archive/<run>/`.

| ngay | da xoa | dung luong | ghi chu |
|---|---|---:|---|
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
