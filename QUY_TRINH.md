# Quy tac va quy trinh chay

| muc | gia tri |
|---|---|
| Pham vi | moi quy tac dang hieu luc va cach chay tung loai cong viec cua ban nghien cuu `E:/Projects/RISCV-research` |
| Cap nhat lan cuoi | 2026-10-15 |
| Uu tien | khi mau thuan voi tai lieu khac, file nay thang (bao chu du an ve mau thuan) |
| Lien quan | lich su va ly do: `NHAT_KY.md`; so lieu: `RESULTS.md`; trang thai: `PROJECT_STATE.md` |

Quy tac moi duoc them vao muc tuong ung kem ngay dat; quy tac bi thay the duoc ghi ro ngay thay the.

## 0. Moc thoi gian cua quy tac

| Ngay | Quy tac (tom tat) | Muc |
|---|---|---|
| 2026-09-24 | RTL xong va dong bang truoc PD; moi thay doi RTL keo ca chuoi; PD khong sua RTL; thay doi tu tong hop tro di phai chay full flow tu buoc 1 | C, D |
| 2026-09-25 | cache 4 KiB la cau hinh chinh; ASIC bat buoc 50 MHz o goc tt, khong noi clock | A |
| 2026-09-26 | goc ss chi sua co trong tam, khong doi CPI; 20,000 LE la muc tieu mem; crash ngau nhien chay lai, loi tat dinh sua ky thuat; don dep bat buoc; bo tieu chi bao cao | A, B, J, K |
| 2026-09-29 | RAM chinh 16 KiB | A |
| 2026-09-30 | DRV xep sau dien tich va setup / hold; khong lach lenh bi tu choi; giao thuc nang golden; bang Embench hop nhat | A, B, G, K |
| 2026-10-03 | kiem hinh thuc muc SoC va EQY chay mot minh; ba to chuc chung floorplan (thay the 2026-10-07) | A, B |
| 2026-10-06 | pham vi timing ky ten: setup >= 0 o tt va ff, hold >= 0 o moi goc, ss chi bao cao | A |
| 2026-10-07 | DM khoa, SA2 / DM_VC4 toi uu rieng theo PPA nghiem; dung run da that bai khi biet nguyen nhan; phan sign-off cung cho bo nho; dat ten theo noi dung | A, B, I |
| 2026-10-08 | moi dieu chinh PD chay full flow toi sign-off, dung som khi that bai ro; CoreMark giu RAM mo phong 32 KiB; quy tac ECO sau route | A, D |
| 2026-10-09 | seed chung 1..10 cho FPGA, board seed 2 chung; `G5_UNLIMITED_LATE_PHASE`, `P2_INITIAL_GRT_FALLBACK`; tiep tuc board sau ngat phien | D, E |
| 2026-10-11 | theo doi tien do host; `HOLD_AFTER_DRT`; UART board qua JP5 GPIO 3.3 V | D, E |
| 2026-10-12 | `P4_RESOURCE_WAIT`; GLS tiep tuc tu tien to native | D, F |
| 2026-10-13 | Python phia Windows chay ghim mot CPU; `DRT_SAVE_MAIN_ROUTE`, `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`; ECO hold hai luot trong mot buoc; `P2_MIN_HOLD`; board chi mot luot vat ly; "khong chay tiep tu buoc fail" (thay the 2026-10-14) | B, D, E |
| 2026-10-14 | SUA VA CHAY TIEP KHI PHAT TRIEN, NGHIEM THU BANG MOT LAN CHAY TRON TU DAU; hai bay ghim CPU; mot RTL cho moi flow, PD doc `rtl_rfbht`; xong PD truoc khi sua trang bao cao; `G5_ANT_ROUND_RULES` | B, C, D, H |
| 2026-10-15 | mo phong chay tren RTL cu duoc chay lai x2 tren `6c4ccffd`, song song, uu tien thap tren Windows | C |
| 2026-10-15 | `NHAT_KY.md` viet lai theo chu de, chi mot phien ban; su kien moi ghi vao muc 8a roi gop vao muc chu de | H |

## A. Pham vi va muc tieu

- Lam viec trong `E:/Projects/RISCV-research`. Ban 1 KiB da cong bo (`E:/Projects/RISCV-AHB-APB-UART`) chi doc va lay du lieu; khong
  sua bai bao; khong dung vao `asic/` cua repo cong bo.
- Cache 4 KiB la cau hinh chinh (tu 2026-09-25); RAM chinh 16 KiB (tu 2026-09-29).
- CoreMark chay mo phong voi RAM 32 KiB (ban build -O2 da luu can 19,465 byte gom stack); giu nguyen theo quyet dinh 2026-10-08. Moi so
  CoreMark ghi "mo phong, RAM 32 KiB". Firmware moi chi duoc ghi vua 16 KiB sau khi kiem ca linker, stack va thuc thi voi RAM 16 KiB.
- ASIC bat buoc 50 MHz o goc tt, khong noi clock (2026-09-25).
- Pham vi timing ky ten (2026-10-06): setup >= 0 o moi goc tt va ff; goc ss chi bao cao; hold >= 0 o MOI goc; DRC / LVS / antenna = 0.
- Goc ss: chi sua co trong tam, giu nguyen tung chu ky, khong doi CPI (2026-09-26).
- Toi uu PPA day du; cong suat phai do that (theo hoat dong, muc F).
- 20,000 LE la muc tieu mem tu dat (2026-09-26): van toi thieu LE va dien tich cell; moi muc tang dien tich phai can voi slack, CPI,
  cong suat do duoc.
- DRV xep sau dien tich va setup / hold (2026-09-30): khong tra dien tich lon de xoa vai gioi han slew / cap cung cua Liberty (nhat la
  chan OpenRAM); chi giam DRV khi re, bao cao phan con lai theo loai (chan SRAM / net nhieu diode / cell chuan).
- So sanh "chi phi vat ly doi lai loi ich kien truc" (2026-10-07, thay quy tac "ba to chuc chung mot floorplan" ngay 2026-10-03): DM giu
  cong thuc ky ten (grid3665x2900, 10.63 mm2, GRT cap margin 50); hai run R14 r14F_A / r14F_B la bang chung lich su bi khoa. SA2 va
  DM_VC4 toi uu rieng (knob, floorplan), khong chep thong so / ket qua cua DM (2026-10-13), theo PPA nghiem: die nho nhat con route
  duoc (chung minh bang ung vien nho hon ke tiep that bai voi cung cong thuc), it buffer va it day nhat de giu cong suat thap.
- Bang cuoi cho ca ba cau hinh: dien tich die va core, tong so buffer va tong chieu dai day, cong suat dong + ro (OpenSTA voi SAIF),
  knob ky ten tung cau hinh, CPI Embench va ti le hit cache.

## B. Ky luat thuc thi

- **Chay kep.** Moi phep do chay hai lan va so tung truong; chay kep la cong quyet dinh ket qua co dung duoc hay khong. Tren may tram
  da ghi nhan loi Python khong lap lai, nguyen nhan chua xac dinh (`NHAT_KY.md` muc 9 "Loi may").
- **Probe suc khoe.** `python3 asic/parse_ids_probe.py --synth 300000`, 8 lan (WSL va Windows). Day la bo do rat nhay; probe truot KHONG
  du de dung toan bo cong viec: ghi NOTE, de chay kep quyet dinh.
- **Ghim CPU (2026-10-13, bay 2026-10-14).** Cong cu Python phia Windows (verifier, driver cong suat, script file lon) chay ghim MOT
  logical CPU ngay khi tao tien trinh. Mat na la HEX (`20` = CPU 5, `100` = CPU 8, `1000` = CPU 12; `32` la CPU 1, 4, 5).
  `cmd /c "start /wait ..."` tra 0 bat ke ma thoat cua chuong trinh con, nen dung
  `cmd /v:on /c "start /wait /b /affinity <hexmask> "" <python.exe> ... & exit !ERRORLEVEL!"` roi kiem `$LASTEXITCODE`. Trong WSL khong
  ghim duoc nhan vat ly: chay kep la la chan duy nhat.
- **Crash va loi.** Crash ngau nhien ro rang (SIGSEGV native, loi Python vo ly, WHEA, OOM ngau nhien) duoc chay lai khong doi gi; loi tat
  dinh cua cong cu / thiet ke (setup, hold, DRC, ...) phai sua bang ky thuat (2026-09-26). Go loi tu bang chung, khong doan. Tu
  2026-10-14 duoc chay tiep tu buoc loi trong luc phat trien, nhung ket qua chi duoc nhan sau MOT lan chay tron tu dau (muc D).
- **Giam sat.** Kiem tra job dai moi ~10 phut. Watchdog phai do tien trinh dang lam viec (CPU ca cay tien trinh) va dung ca hai tin hieu
  (khong ghi output va RSS khong doi) truoc khi ket luan treo. Dung host monitor o muc D; `scripts/watchdog.sh` chi la helper cu (tro
  `synth4kb`), khong bao phu cac job hien tai.
- **Script va nguon.** Khong sua bash script dang chay; khong sua file nguon khi con flow co the doc no. Dung vong lap bang co huy hop tac
  (`asic/.abort_*`, `results/.abort_*`).
- **Lenh bi tu choi (2026-09-30).** Khong lach mot lenh bi chinh sach quyen cua cong cu tu choi (khong dung trinh thong dich, cong cu,
  may khac cho cung ket qua). Chu du an tu lam hoac them quyen.
- **Dung run da that bai (2026-10-07).** Duoc dung de nhuong tai nguyen khi da tim ra vi sao no that bai: liet ke dung tien trinh
  OpenLane python va openroad cua run do (theo `--run-tag` va duong dan run), SIGTERM, ghi ly do vao `asic/gated_pd.log`. Khong dung run
  con khoe chi de lay bo nho.
- **Ket thuc phien.** Job dai chet khi phien terminal giu no ket thuc (WSL2 tat may ao khi khong con client `wsl.exe`); tach job qua WMI /
  Task Scheduler bi tu choi. Job can song qua luc phien ket thuc thi chu du an chay tu terminal WSL cua minh.
- **Tai nguyen.** WSL 24 GB + 8 GB swap, Quartus 16 luong. Quartus fit chay tuan tu. Toi da 3 flow PD song song, toi da 2 detailed routing
  (~10.5 GB moi cai) va chi bat dau khi >= 12 GB trong. Phan sign-off (Magic / Netgen / KLayout den ~8-14 GB) cung phai cho bo nho
  (2026-10-07); P4 cua mot run canh DRT cua run khac khong vua 24 GB, nen pha nang chay tuan tu (`asic/sequence_heavy_*.sh`). EQY (~13 GB)
  va kiem hinh thuc muc SoC chay MOT MINH (2026-10-03).

## C. Chuoi bat buoc cho moi thay doi RTL

Thu tu: lam xong RTL, dong bang, roi moi chay PD. PD khong sua RTL. Logic moi phai co test moi; khong tat chuc nang nao de flow qua.

1. Ap thay doi bang script, chay thu tren ban sao truoc. Dong bang bang `scripts/rtl_manifest.py` (ma tong cua manifest la danh tinh cua
   ban RTL; `--check` chi kiem, khong co `--check` thi ghi de manifest).
2. Kiem tinh: `scripts/latch_sweep.sh` (moi to hop CACHE_CONFIG x LINE_COUNT x FAST_HIT; to hop khong elaborate duoc la FAIL),
   `scripts/lint_rtl.sh` (cung cac to hop), `scripts/lint_asic.sh`, cong lint baseline OpenLane (`scripts/lint_baseline_check.py`, 0
   canh bao moi; `ERROR_ON_LINTER_WARNINGS` giu false).
3. Moi thay doi tai cau truc: chung minh hinh thuc (SAT / Yosys equiv / k-induction) kem doi chung am, va checker chi mo phong
   (`ifndef __openlane__` + translate_off) so tung chu ky; checker cung can doi chung dot bien.
4. Chuoi day du (`scripts/run_fullchain_*.sh`, hien hanh `scripts/run_fullchain_rfbht.sh`), moi hang muc x2: regression, UVM, UVM AXI o
   cac kich thuoc line, Embench (trung tham chieu truoc sua), CoreMark, random differential 50 seed (trung ca hash), view ASIC = view
   FPGA, directed ISA, bo dong bo, ramsweep. Chuoi chay song song theo lane, moi lane mot thu vien Questa rieng (work, work_asic,
   work_m2_1..6, work_act4; ~55 phut thay vi ~5 gio); hai batch cung mot thu vien va cham nhau (vsim-1962); UVM bien dich lai `work`
   nen lane `work` chay tuan tu. TB truy cap register file / BHT chi qua macro `tb/rf_bht_backdoor.svh`.
5. Quartus x2 (muc E).
6. PD: full flow OpenLane tu buoc 1 (muc D), chay kep; GLS netlist cuoi va cong suat theo hoat dong (muc F); LEC (muc F2). Neu netlist
   tong hop khac tung byte thi chung minh tuong duong RTL - RTL o muc SoC cho dung danh sach file cua PD.
7. Config PD doc RTL tu snapshot (`asic/snapshots/rtl_<ban>/`), KHONG doc `hdl/`. Tu 2026-10-14 21:20 moi PD doc `asic/snapshots/rtl_rfbht`
   (= `6c4ccffd`, 47 file gom ca 3 wrapper SA2 / DM_VC4 nam ngoai manifest; SHA-256 trong `SNAPSHOT_ID.txt`). Tong hop config PD dang
   chay de "so voi ban moi" la vo nghia (ca hai doc cung snapshot; loi 2026-10-08). Thay doi chi FPGA (`ifndef __openlane__`): dong
   nhat token cua view ASIC (preprocess voi define cua OpenLane, doi chung am: view FPGA phai khac) + tong hop tu snapshot moi so voi
   snapshot cu (`asic/run_rf_bht_m9k_asic_checks.sh`). Thay doi ca hai view: snapshot moi va PD lai.
8. **Mot RTL cho moi flow (2026-10-14).** Moi so bao cao phai tu cung mot RTL; ket qua chay tren RTL cu la lich su cho toi khi chay lai
   (`results/rtl_consistency_audit_20261014.md`). Tu 2026-10-15 cac mo phong cu (M1/M2, A3, A4, A8, IRQ) chay lai x2 tren `6c4ccffd`,
   song song, uu tien thap tren Windows; ket qua cu giu nguyen.

## D. Quy trinh PD

**Launcher va openlane-local**
- Launcher: `asic/run_pd_mk.sh <design dir> <tag> [--from ... --to ...]` (`CONFIG=<file>` chon config; `RESUME=1` chay tiep vao run co
  san). No them GNU make va grep vao PATH (shell nix `--pure` cua OpenLane khong co).
- OpenLane: ban sao co sua `asic/openlane-local` (OpenLane 2.3.10). Cac them vao, mac dinh tat tru khi config bat: `set_thread_count 1`
  trong antenna check / repair; `LAYERS_RC` / `LAYERS_RC_SCOPE`; `DRT_ANTENNA_REPAIR_ITERS` / `_MARGIN`; `DRT_DRC_REPORT_ITER_STEP`;
  `OpenROAD.MacroPinBuffers`; `OpenROAD.PostRouteHoldECO` (+ `POST_ROUTE_HOLD_ECO_RCX_CORNER_2`, `POST_ROUTE_ECO_SETUP`,
  `POST_ROUTE_ECO_HOLD`, `POST_ROUTE_ECO_CORNERS`); `SYNTH_OPT_DFF_SAT`; `DRT_SAVE_MAIN_ROUTE`, `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`;
  `read.tcl` va `drc.tcl` cua Magic (macro truu tuong); `yosys.py` (`@NETLIST@` / `@PDK_FORMAL@` cho EQY). Danh sach co ngay:
  `NHAT_KY.md` muc 6.1. Sua flow / gate chi khi khong co flow chay, hanh vi moi sau bien moi mac dinh tat.

**Flow co cong** (`asic/run_gated_pd.sh`, `ITEMS="<design dir>:<tag>:<config> ..."`, duong dan config tuong doi voi thu muc design),
bon pha trong cung mot thu muc run:

| Pha | Cac buoc | Cong sau pha | Nguong |
|---|---|---|---|
| P1 | tong hop .. OpenROAD.GlobalRouting | grt_overflow, cts_tt_slack | overflow GRT <= 500; STAMidPNR-2 setup nom_tt >= +0.5 ns (`P1_MIN_SETUP`), hold nom_tt >= 0 |
| P2 | CheckAntennas .. STAMidPNR-3 | grt_repair_overflow, grt_tt_slack | overflow lan route lai cuoi (tu dau, trong RepairAntennas) <= 2000; STAMidPNR-3 setup nom_tt >= +0.3 ns (full flow: `P2_MIN_SETUP=0`), hold >= `P2_MIN_HOLD` (mac dinh 0) |
| P3 | DetailedRouting | drt_convergence (`asic/drt_watch.sh`) | vong 5 > 20,000, 10 > 5,000, 20 > 600, 30 > 400, 40 > 200 vi pham -> dung; tu vong 12: > 300 vi pham va giam < 10 % trong 4 vong -> dung; sau vong 40 chay toi vong 64 |
| P4 | PostRouteHoldECO .. sign-off | signoff (`asic/fp_tools/gate_check.py final`) | route / Magic / KLayout DRC 0, moi so LVS 0, XOR 0, overlap 0, chan ngat critical 0, antenna net / pin 0, setup >= 0 o moi goc tt va ff, hold >= 0 o moi goc, du 9 goc; ss bao cao rieng |

- Ten cong trong log cu: G1 .. G6 theo thu tu tren. Nguong drt_convergence hieu chinh 2026-10-06 (nguong dau dung nham run SA2 dang hoi
  tu) va 2026-10-07 (SA2 corr3400x3400_f220 chay du 64 vong: 72 o vong 30, 70 o vong 40, 0 o vong 54). Cong mid-PnR chi dung goc tt (so
  ss / ff o STAMidPNR la so cu).
- Moi ket qua cong ghi vao `asic/gated_pd.log` va `asic/dse_pd.log` ("GATE <PASS|FAIL> <tag> <cong>: <so>"). Dung hop tac:
  `touch asic/.abort_gated_pd`.

**Bien opt-in cua gate scripts** (mac dinh tat, khong doi gate sign-off; khai bao luc khoi dong)

| Bien | Ngay | Tac dung | Bang chung |
|---|---|---|---|
| `G5_UNLIMITED_LATE_PHASE=1` | 2026-10-09 | khong ap nguong convergence / stall sau vong 40 (den va gom vong 40 giu nguyen); bat khi khoi dong flow moi hoac resume DRT | `results/drt_watch_rule_alignment_20261009/` |
| `P2_INITIAL_GRT_FALLBACK=1` | 2026-10-09 | chi khi `resolved.json` ghi `RUN_POST_GRT_DESIGN_REPAIR=false`: doc overflow cua GlobalRouting (hoac route lai cuoi neu co); thieu dau vao van FAIL / MISSING | `python asic/fp_tools/verify_gate_p2.py`, `results/gate_p2_no_repair_20261009/verification.json` |
| `HOLD_AFTER_DRT=1` | 2026-10-11 | voi `run_gated_resume.sh ... drt`: giu sau DetailedRouting da qua kiem convergence, de kiem tai nguyen truoc P4; HOLD khong la sign-off PASS | `results/gated_resume_phase_hold_20261011.json` |
| `P4_RESOURCE_WAIT=1` | 2026-10-12 | `asic/run_resource_gated_resume.sh ... hold` giu client WSL foreground, chi goi resume khi WSL available va Windows free deu >= 15,000 MiB (`P4_MIN_AVAILABLE_MB` / `P4_MIN_WINDOWS_FREE_MIB`); query loi = STOP / UNKNOWN; `--check-resource-only` chi doc | - |
| `P2_MIN_HOLD=-0.5` | 2026-10-13 | nguong hold p2 cho cong thuc co ECO hold sau route (SA2 / DM_VC4); cong final giu nguyen | `asic/fp_tools/check_p2_min_hold_20261013.sh` (SA2 -0.206 va VC4 -0.202: FAIL o 0, PASS o -0.5, FAIL o -0.1) |
| `G5_ANT_ROUND_RULES=1` | 2026-10-14 | luat rieng cho cac lan goi detailed_route thu hai tro di (vong sua antenna); nguong khai bao luc khoi dong (vd. vong 20 > 3000, 30 > 600, 40 > 400, dinh tre tu vong 20); `DRT_WATCH_ROOT` / `DRT_WATCH_LOG` de thu | thu tren log that cua V2 |

**SUA VA CHAY TIEP KHI PHAT TRIEN, NGHIEM THU BANG MOT LAN CHAY TRON TU DAU** (chu du an, sua 2026-10-14; ban 2026-10-13 "khong chay
tiep tu buoc fail" lam qua trinh qua dai va da bi thay the):
- Buoc nao fail (crash, loi, watchdog dung, cong FAIL): ghi FAIL + nguyen nhan da chan doan vao `gated_pd.log` / NHAT_KY, giu thu muc run;
  sau khi sua duoc phep chay tiep tu buoc loi (`run_gated_resume.sh ... step:<StepID>` / `drt` / `hold`, tach nhanh) de phat trien nhanh.
- Nghiem thu: khi moi cong da qua, chay MOT lan tron tu buoc 1 (tag moi, khong resume, khong tach nhanh, khong CONTINUE, moi nguong khai
  bao luc khoi chay). Chi lan chay tron do (va lan chay kep cua no khi can) la ket qua.
- Khi flow tat dinh va cach sua chi la mot thiet lap luc khoi chay, duoc di thang toi lan chay tron (vua thu vua nghiem thu).
- Cong cu khac PD cung vay: go loi bang chay tiep, bang chung cuoi tu cac lan chay tron.
- Run da ky bang resume / tach nhanh (DM r14F_A/B, SA2 ecomaxmin) can mot lan chay tron moi.
- `asic/run_resume_retry.sh` (resume tay sau crash) ngung 2026-10-13, lai duoc dung cho phat trien tu 2026-10-14.

**Cach toi uu (chu du an, 2026-10-08)**
- Moi lan dieu chinh chay FULL FLOW toi sign-off (sua mot loi co the lam lo loi moi o pha sau), chan doan o tung pha va dung ngay khi co
  dau hieu that bai ro rang. Moi lan mot thi nghiem co gia thuyet; khong rai nhieu run song song.
- Bao cao DRC moi 5 vong (`DRT_DRC_REPORT_ITER_STEP` 5); moi lan goi detailed_route giu bao cao rieng trong `drc_iter_<lan goi>/`.
- Resume va tach nhanh: `asic/run_gated_resume.sh <design dir> <tag> <config> <ly do> [drt|hold|sta|p2|step:<StepID>] [to]` (cung khoa
  slot DRT va cung cong sign-off) cho diem dung co ke hoach (`HOLD_AFTER_DRT`, `STOP_AFTER=p2`) hoac buoc fail da sua nguyen nhan.

**ECO sau route** (`OpenROAD.PostRouteHoldECO`, 2026-10-08)
- Hop phap hoa voi padding 0 (padding la nut cua GPL / DPL; diode antenna sau DRT dat sat cell).
- STA trong phien ECO chi dung SPEF trich xuat (goi `estimate_parasitics` truoc `read_spef` lam phien o lai tren uoc luong). Macro SRAM
  chi co mot .lib TT nen trong phien nhieu goc no chi gan voi goc doc dau tien (STA-1140): sua setup thi chay rieng goc tt
  (`POST_ROUTE_ECO_SETUP`, `POST_ROUTE_ECO_CORNERS`, `POST_ROUTE_ECO_HOLD` false), roi chay lai buoc ECO sua hold moi goc. So timing chi
  lay tu STA sign-off (moi goc mot phien).
- ECO hold gan MOT trich xuat cho moi goc (`POST_ROUTE_HOLD_ECO_RCX_CORNER`, mac dinh max_*), nen moi luot chi sua mot dau RC (SA2
  11.56 mm2, 2026-10-09: chi min_* thi max_ff -0.116; max_* roi min_* thi hold >= 0 o ca 9 goc). Tu 2026-10-13 luot thu hai chay TRONG
  CUNG buoc: `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` = "min_*" (mac dinh trong = mot luot; file luot 1 trong `pass1/`, log luot 2 `*_2.log`).
  Khong con tach run sau buoc ECO / config `_ecomin`. Kiem chung: luot 1 trung tung byte buoc 47 cua sa2_..._rsztf_r1, luot 2 trung tung
  byte buoc 48 cua ecomaxmin_r1 (netlist va DEF; `asic/soc_sa2_4kb/eco2pass_check_20261013/`).

**Hai bien DRT (2026-10-13, mac dinh tat, `drt.tcl` + `steps/openroad.py`)**
- `DRT_SAVE_MAIN_ROUTE`: ghi `main_route.odb` sau main route, truoc vong sua antenna (khong doi ket qua).
- `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`: goi `grt::set_allow_congestion 1` truoc moi `repair_antennas`, de GRT tang dan noi diode khong
  dung o GRT-0232 (`GlobalRouter::updateDirtyRoutes` chi bao loi khi khong cho nghen); detailed route tang dan phai go overflow, DRC van
  do cong sign-off kiem. Chi dung khi co bang chung vong sua antenna that bai vi nghen.

**Sang loc va chan doan (chi doc, khong phai ket qua)**
- Sang loc knob chi tac dong sau GRT: `bash asic/branch_run.sh <design dir> <tag nguon> <tag moi> <so buoc GlobalRouting>` (chep buoc
  1 .. N, run nguon chi doc, file `BRANCHED_FROM`), roi `run_gated_resume.sh ... p2`; knob tac dong tu buoc sua DRV dau tien
  (`MAX_FANOUT_CONSTRAINT`): tach o buoc 30 va `asic/run_gated_branch.sh <design dir> <tag> <config> <ly do>
  OpenROAD.RepairDesignPostGPL`; `run_gated_branch.sh ... drt` chi detailed routing. Run sign-off chinh thuc van la full flow tu buoc 1.
- Sang loc floorplan: `asic/fp_tools/screen_floorplan.sh` (tu sau tong hop toi GlobalRouting, GRT 50 vong nhu flow that),
  `asic/fp_tools/screen_grt.sh`; bang: `python asic/fp_tools/fp_summary.py`. Khong dung GRT 15 vong de xep hang ung vien.
- Du bao diem nong DRT: `python asic/fp_tools/pin_hotspots.py <DEF cua ResizerTimingPostGRT> <sky130_fd_sc_hd.lef> 20` (DM hoi tu nhanh
  o max ~29 chan / 100 um2, SA2 can 54 vong o max 32).
- Chan doan nghen: `asic/fp_tools/guide_demand.py <guide> [<guide 2>]`, `region_cells.py <def> x0 y0 x1 y1`, `net_probe.py <def> <guide>
  <net> ...`; clock: `clock_detour.py`, `clock_layers.py`, `grt_skew_screen.sh`.
- Dau hieu nghen som: dong "Extra Run for hard benchmark" (GRT-0103) trong log GRT dau (`grep -c "hard benchmark"`); detour cua no keo ca
  net clock (DM_VC4 11.56 mm2: net clock ~7.7 mm, skew hold -1.5 -> -4.8 ns o p2). Khi thay dong nay, chan doan truoc khi chay tiep.

**Theo doi va hang doi**
- Host monitor (2026-10-11): `python -B scripts/maintenance/monitor_jobs.py --output results/job_monitor_status.json` kiem tra mot lan;
  `--watch` poll moi 600 giay o foreground. Khong detach, khong kill / retry job, khong sua gate. Trang thai: RUNNING (CPU dang tang du
  log im lang), HELD (dung theo `STOP_AFTER=p2`), DEAD_ALERT (tien trinh mat khi receipt van RUNNING), UNKNOWN (loi query),
  SUSPECTED_STALL (cung process set >= 600 giay, CPU ca cay khong tang, RSS va output khong doi: nghi van can chan doan, khong phai bang
  chung treo).
- Hang cho Windows cho mot gia thuyet PD (vd. `scripts/maintenance/queue_vc4_padding.py`, 2026-10-10): `--prepare` dong bang plan; `--run
  --plan-sha256 <sha>` kiem lai input va doi Windows free >= 10,000 MB; child `wsl.exe` foreground; co abort `results/.abort_vc4_padding_queue` chi ngan launch. Process exit
  0 khong la gate PASS. Controls va plan: `results/vc4_padding_queue_controls_20261010/`; input Nix / PDK phai kiem tu moi truong launcher thuc.

**Bay trang thai run (bat buoc nho)**
- Khong xoa step da xong cua run con resume; OpenLane resume tu `state_out.json` moi nhat tim de quy; sua config phai chay lai; so ss / ff
  cua STAMidPNR la so cu; thanh cong la `state_out.json` hoac metric, khong phai thu muc hay `final/`; thay doi tu tong hop tro di (SDC,
  config) phai chay full flow tu buoc 1.
- Doc so theo goc: moi WNS / TNS / Fmax ghi ro goc; `power__total` cua flow la goc max_ff, khong phai tt.
- Tu R15/R16 macro cache co ten `u_soc.u_{i,d}cache.genblk1.g_dse.*`; file macro placement cua R14 khong khop.

## E. Quy trinh FPGA

- **Seed (2026-10-09).** Bo seed chung 1..10 cho DM / SA2 / DM_VC4 / DM_DSE 4 KiB; so sanh cac cau hinh TRONG CUNG seed; khong chon seed
  tot nhat rieng. Bao cao du 10 seed, min / max / mean / do lech chuan va chenh lech ghep cap. Bo 4 seed cu giu lam bang chung lich su;
  mo rong phai cung RTL va dau vao. Board dung seed 2 CHUNG cho ca bon cau hinh (chot truoc khi xem ket qua mo rong).
- **Chay fit.** `scripts/fpga/run_paired_seed_matrix.py` (seed 1..10, hai luot; driver cu `scripts/run_le_<tag>.sh 1` roi `2` /
  `scripts/run_fpga_points.py` do 4 seed). 116 cot moi fit (tai nguyen, timing 3 goc, cong suat ngay sau moi fit); thieu truong la FAIL.
  Luot 1 phai bang luot 2 (`scripts/verify_double.py`). Cong bo nho truoc moi fit (>= 6 GB trong). `quartus_sh --seed` ghi seed vao
  .qsf; xac nhan seed va RTL cua fit tu report truoc khi dung database.
- **Bang seed.** `scripts/fpga_seed_summary.py --seeds 1,2,3,4,5,6,7,8,9,10` (thieu seed hay truong la FAIL). Dung sweep:
  `touch results/.abort_fpga_sweep`. Log fit that bai duoc giu (`<ten>.attemptN.failed.log`).
- **Tiep tuc sau ngat (2026-10-09).** Kiem tra read-only PID / log / hash dau vao; archive log do dang truoc.
  `run_paired_seed_matrix.py --run --resume` giu fit da ghi nhan, chay lai TRON fit chua xong; chi go lock khi PID cu da chet va lock da
  luu. `prepare_board_reference.py --run --resume` chi giu case co CSV day du khop moi counter voi R14 va dau vao khong doi.
  `scripts/fpga/continue_common_seed_preparation.py` (`--prepare` roi `--run`) chi chay fit con thieu, doi Windows free >= 6,000 MB, khong
  retry loi tat dinh, khong dung chuong trinh khac de lay RAM. `scripts/fpga/complete_board_preparation.py` mac dinh chi in plan; co
  `results/.abort_board_completion` chi dung buoc tiep tuc, khong dung job dang khoe.
- **Board (2026-10-11 .. 13).** UART qua JP5 GPIO 3.3 V LVTTL: TX = GPIO[0]/AB22, RX = GPIO[1]/AC15, USB-TTL va GND chung, VCC adapter de
  trong; khong dung DB9 RS-232 (orientation va JP6 trong `results/board_20261012/README.md`). Divider RTL tao 448 clock/bit (~111,607 baud
  tai 50 MHz). Firmware boot ngay, khong cho KEY1: mo Hercules / log truoc khi nap. Moi case program SOF moi, khong thay bang reset KEY0.
  Log gan dung kernel / config / pass / SOF sha (`upfull_*` va `up_*` dung chung nhan BENCH). Nap bang `quartus_pgm -c USB-Blaster -m JTAG
  -o "p;<file.sof>"`.
- **Pham vi board 2026-10-13.** Chi pass 1 cho 100 workload/config; khong len lich pass 2. So board ghi "single execution", khong gan nhan
  double executed. Dung sau moi case de kiem tra / xac nhan truoc case tiep, reset hay rerun. Ngoai le nay chi cho phep do vat ly;
  verification, Quartus fit, PD va activity power van theo quy tac hai luot.

## F. Do cong suat ASIC

- GLS -> SAIF -> OpenSTA (`asic/gls/`): mo phong netlist sau fill (model cell chuc nang, model OpenRAM) cho 12 kernel; cua so tu
  `sysmon_clear_start()` toi `sysmon_freeze_snapshot()`. Capture moi dung mapped freeze observer da chung minh tren dung netlist;
  `win_cycles` = `mcycle`, elapsed ps = `mcycle` x 20000 va moi SAIF T0+T1+TX phai khop cua so. Giu raw `power report -bsaif` nguyen
  byte; khong ep DURATION de che sai cua so. `saif_to_pins.py` chuan hoa duration tu span va gan moi net vao chan (OpenSTA 2.6 bo qua net
  phang; chay Python phia Windows, ghim CPU); `sta_power.sh` nap dung lib / SPEF RCX / SDC cua buoc STAPostPNR, goc nom_tt.
- Kiem truoc khi tin so: vectorless phai tai lap dung so cua flow; bao cao ty le chan co nguon hoat dong "unknown". CPI va EPI dung chu ky
  view ASIC (`asic/gls/power_csv.py`).
- `scripts/verification/run_gls_exact_window.py --wait-for-memory` (opt-in): cho foreground 30 giay neu Windows free < 6000 MiB; moi lan
  cho kiem lai input SHA256; file `abort_before_next_native` chi ngan tool tiep theo. Moi pass dung private compile moi; so du 12 kernel
  qua hai pass truoc khi chay OpenSTA kep.
- GLS bi ngat sau tien to native thanh cong (2026-10-12): `scripts/verification/resume_gls_exact_window.py` mac dinh prepare-only, `--run`
  moi tiep tuc; chi nhan mot private compile + tien to sim / conversion exit 0; giu nguyen receipt da dung, kiem 314 input va moi log / raw
  / pin da co; doc hash qua UNC duoc thu toi da 3 lan. Controller `run_dm_capture_power_retry.ps1 -Resume -Run`. Khong bien capture do dang
  thanh PASS va khong chay lai case da xong.

## F2. LEC (tuong duong RTL - netlist da ky ten)

- **EQY goc cua OpenLane khong qua tren thiet ke nay** (gioi han cong cu: ma hoa lai FSM, ghep theo ten, partition > 23 GB). Do khong
  phai ket luan khong tuong duong; khong tron ket qua EQY voi chung minh tu viet duoi day.
- **Chuoi anh xa thanh ghi** (`asic/equiv/lec/`): RTL + `fsm` == N1 (trang thai tong hop truoc `abc -fast`, replay trung tung byte buoc 06)
  == netlist cuoi (ca r1 va r2). DM: `run_lec_r14.ps1 -Step A|B`, `run_lec_r14_mul.ps1`, `run_lec_r14_pass2.ps1`. SA2:
  `<thu muc luot>/run_frontends.sh` (tao bang `scripts/verification/prepare_sa2_lec.py`) roi `pwsh -File asic/equiv/lec/run_lec_sa2.ps1
  -Work <thu muc luot> -Step A|Mul|Inv|B|NegB|NegFSM`. DM_VC4: `scripts/verification/prepare_vc4_lec.py`, `run_frontends_vc4.ps1`,
  `run_lec_vc4.ps1` (them `sram_align.py` va doi chung `NegAlign` cho 8 macro way 1 khong doc). `6c4ccffd` (2026-10-15):
  `scripts/verification/prepare_lec_6c4c.py`, `scripts/maintenance/run_lec_6c4c_goldn1.sh`; gold tu `rtl_rfbht`.
- Hai luot doc lap (front end va replay moi moi luot), so hash cac doi tuong chung minh (`compare_lec_passes.py`); doi chung am: ma hoa
  FSM sai, spec bo nhan unsigned / tich rieng phan sai, netlist and2 -> or2. Chung minh voi gold `rtl_r14` khong phai chung minh cho layout
  `6c4ccffd`.
- Cac tien de, kiem rieng (2026-10-13/14), moi kiem hai lan va co doi chung am:
  - Reset bat dong bo: `arst_audit.py` / `run_arst_audit.ps1` tren mo hinh TRUOC async2sync: moi bit flop ghep theo ten phai cung co /
    khong co reset bat dong bo, cung nguon (qua alias / buf / not), cung muc, cung gia tri.
  - Gia tri khong xac dinh: `run_xsens.ps1` (`x_free_aig.ys` + `aig_tie_inputs.py`): moi bit x va net khong noi cua mo hinh gold thanh input
    tu do, miter voi chinh no khi cac input do = 0; moi output UNSAT. Doi chung am: `lec_d_p00001` = 1'x phai SAT.
  - Clock: `scripts/verification/lec_clock_audit_files.py` (goi `lec_clock_audit.py`) tren 4 mo hinh phang.
  - Bat bien one-hot FSM: `-Step Inv` (`evert.py --inv` + `inv_check.py`) tren dung nguon hien tai.
- Ngoai kha nang: tuong duong tuan tu toan phan khong anh xa thanh ghi; macro SRAM la hop den (GLS phu phan nay).
- Tai nguyen: front end gate (~0.57 GB IL) can vai GB trong WSL. Khi detailed routing dang chay va Windows free < 2 GB, dat file
  `DEFER_HEAVY` trong thu muc luot de hoan buoc nang (NegB). Script moi dung ma thoat dung (muc B) va dung ngay khi ma thoat khac 0.

## G. Golden snapshot va giao thuc nang golden

- Chi MOT golden (hien tai `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928`, ban DM 8 KiB-RAM). Snapshot truoc moi thay doi co rui ro;
  `scripts/make_golden_snapshot2.py` (sha256 moi file, chi hard-link artefact bat bien, `--verify` / `--diff` / `--restore`).
- Mot run vuot golden o MOI mat (dien tich, timing, cong suat, DRV chap nhan duoc): bao cao bang so sanh va DUNG, khong khoi dong viec moi
  cho toi khi chu du an duyet; duyet xong moi nang lam golden duy nhat va xoa golden cu (2026-09-30).
- So sanh cung loai (cung RAM, cung bo macro); thi nghiem mot phan khong nang truc tiep: can full flow x2, DRC / LVS, GLS + SAIF, LEC truoc.

## H. Ghi chep

- Mot lich su duy nhat: `NHAT_KY.md`, theo chu de tu 2026-10-15, MOT phien ban (ban theo gio cu chi con trong git, commit
  `35ebf92`). Su kien moi: ghi vao muc 8a dang `### YYYY-MM-DD HH:MM <chu de>` (moi su kien mot lan; script
  `scripts/fpga/record_board_case.py --sync-tracking` cung ghi vao day), roi gop vao muc chu de (1-8) o lan ra soat tai lieu ke tiep;
  van de lap lai vao muc 9, don dep muc 10, ten moi muc 11. Khong doi ten cac tieu de `## 8a.` / `## 9.` (script tim chung) va giu
  nghia so muc 8 / 9 / 10 / 11 (script, comment va tai lieu cu tham chieu). Quy tac: file nay. So lieu hien hanh: `RESULTS.md`. Tra
  loi phan bien: `REVIEW_RESPONSE.md`. Ket qua cho nguoi doc ngoai: trang bao cao (`report_page/soc_report.html`); xong PD truoc khi
  sua trang (2026-10-14).
- Log flow: `asic/dse_pd.log`, `asic/gated_pd.log`, `asic/pd_log.md` (do launcher ghi). Moi CSV ket qua co cap `_p1` / `_p2`.
- Danh tinh mot ban RTL la ma manifest (`results/rtl_manifest_<id>.json`) cong ten theo ngay va noi dung.
- Git: tieng Anh, chi ASCII, khong co dong `Co-Authored-By`, danh tinh git cuc bo. Tai lieu noi bo tieng Viet khong dau; bao cao cho nguoi
  doc ngoai (RESULTS, REVIEW_RESPONSE, README, PROJECT_STATE) tieng Anh.
- Khong ghi loi ket luan "may hong" khi chua co bang chung doc lap; ghi trung tinh (hien tuong, so lieu, bang chung).

## I. Dat ten (2026-10-07)

- Dat theo noi dung va ngay, khong theo so dem: khong R1 .. R17, E1 .. E16, X1 .. X4, Incident NN, Entry NN, final2 / final3, _v2, _b.
- Cau hinh cache: dm, dmdse, sa2, vc4, sa4 (hau to `fast` khi FAST_HIT = 1); RAM chinh ram8k / ram16k, chi ghi khi khac 16 KiB.
- Floorplan: ho + kich thuoc die W x H (um) + thuoc tinh khi anh em khac nhau: grid3665x2900, corr3400x3325_f220 (hang cache tren lat FS,
  khe 220 um), wide4211x3331, ring3200x3190, strata3260x3400.
- Run OpenLane: chu thuong [a-z0-9_], `<cfg>_<floorplan>[_<knob><gia tri>...]_<rN>`; r1, r2 la hai lan chay kep (khong dung A / B); sang
  loc ket thuc bang `scr15` / `scr50`, chi tong hop bang `synth`; gia tri khong co dau cham (hold003 = 0.03 ns, dens55 = 55 %). Run tren
  RTL moi them hau to noi dung (vd. `_rtl6c4c`).
- Thi nghiem dat ten theo mot thay doi so voi mot nen co ten (dm_grid3665x2900_hold003).
- Cong kiem tra dat ten theo cai no kiem (grt_overflow, cts_tt_slack, grt_repair_overflow, grt_tt_slack, drt_convergence, signoff). Muc
  phan bien giu ma cua phan bien (M1, M2, A1 .. A9).
- Khong doi ten tren dia nhung gi mot run con giu (duong dan tuyet doi trong state / resolved.json). Bang doi ten cu -> moi: `NHAT_KY.md`
  muc 11.

## J. Don dep (bat buoc, 2026-09-26)

- Xoa: run hong / that bai / bi thay the, CSV sai, file rong, script dung mot lan, san pham build tai tao duoc.
- Truoc khi xoa mot run: luu resolved.json, metric cuoi, log loi / canh bao, flow log, danh sach buoc vao `results/pd_run_archive/<run>/`;
  ghi tung muc vao `results/cleanup_deleted.txt`; them mot dong vao `NHAT_KY.md` muc 10.
- Giu: tai lieu duy tri, log (log cu nen lai), CSV chuan da chay kep, moc 1 KiB (`asic/soc_dm_control/runs/sync_final`), bang chung Magic
  (`asic/evidence/MAGIC_NAMESPACE_COLLISION.md` va cac file no liet ke), SOF board, run ky ten, golden snapshot.
- Xoa thu muc run can chu du an dong y; run dang chay hoac con resume khong dong vao.

## K. Bao cao

- Hai phan theo thu tu: thanh qua, roi that bai va khoang trong; so cung, khong to hong.
- Sau PD: ghi goc cho moi WNS / TNS / Fmax; tach goc ky ten timing voi goc do cong suat; ghi ro cong suat la uoc luong cua flow hay tu
  hoat dong that; DRC / LVS la cong dat / truot dat truoc bang PPA; bang theo cau hinh (DM / SA2 / DM_VC4); ghi ro so mot luot / sang loc.
- Bo tieu chi (2026-09-26): CPI / IPC va chu ky (Embench, CoreMark); Fmax (FPGA va ASIC theo goc); LE / LUT / FF / M9K va dien tich + so
  cell ASIC; cong suat dong + tinh; hieu suat nang luong (perf/W, nang luong moi lenh); hit / miss I$ / D$; ty le doan sai nhanh; stall /
  wait / hazard (bo dem phan cung).
- Bang Embench hop nhat (2026-09-30), moi kernel x cau hinh: `mcycle` khop giua RTL, view ASIC, GLS (va board khi co), CPI, hit I$ / D$,
  doan sai nhanh, cong suat GLS; them kich thuoc code (.text / .rodata / .data, rv32i_zmmul -O2), toc do / MHz kieu Embench va CoreMark /
  MHz, GM va GSD, do tre ngat va chuyen ngu canh (`scripts/metrics/unified_table.py`).

## Lich su tai lieu

| Ngay | Thay doi |
|---|---|
| 2026-10-07 | gop quy tac va quy trinh vao mot file (commit `507c3fb`) |
| 2026-10-08 .. 14 | them quy tac ECO, seed chung, cac bien gate, board, ghim CPU, quy tac phat trien / nghiem thu |
| 2026-10-15 07:46 | trang thai 2026-10-15 (commit `2d4202d`) |
| 2026-10-15 | sap xep lai: bang moc thoi gian quy tac (muc 0), bang bien opt-in co ngay, tach cac doan dai muc D thanh nhom, sua cac cho bi dinh chu, bo tham chieu toi quy tac 2026-10-13 da bi thay the, them quy tac "mot RTL cho moi flow", snapshot `rtl_rfbht`, LEC DM_VC4 / `6c4ccffd`, ghi chep trung tinh ve loi may |
| 2026-10-15 | quy tac ghi lich su cho `NHAT_KY.md` mot phien ban (muc 8a, so muc tuong thich) |
