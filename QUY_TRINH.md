# Quy tac va quy trinh chay

Moi quy tac dang hieu luc va cach chay tung loai cong viec, o mot cho. Quy tac moi duoc them vao muc tuong ung, ghi ngay dat.
Lich su va ly do: `NHAT_KY.md`. So lieu: `RESULTS.md`.

## A. Pham vi va muc tieu

- Lam viec trong `E:/Projects/RISCV-research`. Ban 1 KiB da cong bo (`E:/Projects/RISCV-AHB-APB-UART`) chi doc va lay du
  lieu; khong sua bai bao; khong dung vao `asic/` cua repo cong bo.
- Cache 4 KiB la cau hinh chinh (tu 2026-09-25); RAM chinh 16 KiB (tu 2026-09-29).
- CoreMark chay mo phong voi RAM 32 KiB (ban build -O2 da luu can 19.465 byte gom stack, khong vua 16 KiB); giu nguyen
  theo quyet dinh 2026-10-08. Moi so CoreMark phai ghi "mo phong, RAM 32 KiB". Han che kich thuoc nay ap dung cho
  firmware -O2 da luu; firmware moi chi duoc ghi vua16KiB sau khi kiem ca linker, stack va thuc thi voi RAM16KiB.
- ASIC bat buoc 50 MHz o goc tt, khong noi clock (2026-09-25).
- Pham vi timing ky ten (2026-10-06): setup >= 0 o moi goc tt va ff; goc ss chi bao cao (ban ky ten DM: max_ss ~ -7.4 ns);
  hold >= 0 o MOI goc; DRC / LVS / antenna = 0 tuyet doi.
- Goc ss: chi sua co trong tam, giu nguyen tung chu ky, khong doi CPI (2026-09-26).
- Toi uu PPA day du, cong suat phai do that (theo hoat dong, muc F).
- 20,000 LE la muc tieu mem tu dat (2026-09-26): van toi thieu LE va dien tich cell, moi muc tang dien tich phai can voi slack,
  CPI, cong suat do duoc.
- DRV xep sau dien tich va setup / hold (2026-09-30): khong tra dien tich lon de xoa vai gioi han slew / cap cung cua Liberty
  (nhat la chan OpenRAM); chi giam DRV khi re, bao cao phan con lai theo loai (chan SRAM / net nhieu diode / cell chuan).
- Ba to chuc cache tren ASIC dung chung mot floorplan (cung die, cung toa do macro) de so PPA cong bang (2026-10-03).
  Thay the ngay 2026-10-07 bang dong duoi.
- So sanh "chi phi vat ly doi lai loi ich kien truc" (2026-10-07): DM khoa o dm_grid3665x2900_r1 / _r2 (10.63 mm2, GRT cap
  margin 50, ky ten sach), khong chay lai. SA2 va DM_VC4 toi uu rieng (knob, floorplan) theo PPA nghiem: die nho nhat con
  route duoc (chung minh bang ung vien nho hon ke tiep that bai), it buffer va it day nhat de giu cong suat thap. Gioi han
  cung: DRC / LVS / antenna 0, setup >= 0 o tt va ff, hold >= 0 o moi goc. Bang cuoi cho ca ba: dien tich die va core, tong
  so buffer va tong chieu dai day, cong suat dong + ro (OpenSTA voi SAIF), knob ky ten tung cau hinh, CPI Embench va ti le
  hit cache.

## B. Ky luat thuc thi

- Moi phep do chay hai lan va so tung truong (may thinh thoang tinh sai am tham, nhat la tien trinh Python trong WSL,
  `NHAT_KY.md` muc 9 "Loi may"). Chay kep la cong quyet dinh ket qua co dung duoc hay khong.
- Health check may: `python3 asic/parse_ids_probe.py --synth 300000`, 8 lan (WSL va Windows). Day la bo do rat nhay; probe
  truot KHONG du de dung toan bo cong viec (quy tac P): ghi NOTE, de chay kep quyet dinh.
- Cong cu Python phia Windows (verifier, driver cong suat, script file lon) chay ghim MOT logical CPU ngay khi tao tien
  trinh: `cmd /c "start /wait /b /affinity <hexmask> "" <python.exe> <script> ..."` (khoi tu PowerShell; ghim 71 / 72 OK
  so voi 2-6 / 8 khong ghim, 2026-10-13). Trong WSL khong ghim duoc nhan vat ly: chay kep la la chan duy nhat.
  Hai bay (2026-10-14): mat na la HEX (`20` = CPU 5, `100` = CPU 8, `1000` = CPU 12; `32` la CPU 1, 4, 5); va
  `cmd /c "start /wait ..."` tra 0 bat ke ma thoat cua chuong trinh con, nen lay ma thoat bang
  `cmd /v:on /c "start /wait /b /affinity <hexmask> "" <python.exe> ... & exit !ERRORLEVEL!"` roi kiem `$LASTEXITCODE`.
- Crash ngau nhien ro rang cua may (SIGSEGV native, loi Python vo ly, WHEA, OOM ngau nhien) duoc chay lai khong doi gi; tu
  2026-10-14 duoc chay lai tu buoc loi trong luc phat trien, nhung ket qua chi duoc nhan sau MOT lan chay tron tu dau (muc D,
  quy tac "SUA VA CHAY TIEP KHI PHAT TRIEN, NGHIEM THU BANG MOT LAN CHAY TRON TU DAU"). Loi tat dinh cua cong cu / thiet ke (setup, hold, DRC, ...) phai sua bang ky
  thuat (2026-09-26). Go loi tu bang chung, khong doan.
- Kiem tra job dai moi ~10 phut (treo / crash). Watchdog phai do tien trinh dang lam viec (CPU ca cay tien trinh) va dung ca hai
  tin hieu (khong ghi output va RSS khong doi) truoc khi ket luan treo.
  Dung host monitor hien tai o muc D; `scripts/watchdog.sh` chi la helper cu, dang tro `synth4kb` va tat theo doi
  verification chain, khong bao phu cac PD/GLS/queue hien tai.
- Khong sua bash script dang chay; khong sua file nguon khi con flow co the doc no. Dung vong lap bang co huy hop tac
  (`asic/.abort_*`, `results/.abort_*`).
- Khong lach mot lenh bi chinh sach quyen cua cong cu tu choi (2026-09-30): khong dung trinh thong dich, cong cu, may khac cho
  cung ket qua. Chu du an tu lam hoac them quyen.
- Run da that bai (vd. so lieu da vuot cong du chua toi buoc cham cong) duoc dung de nhuong tai nguyen (2026-10-07), voi dieu
  kien da tim ra vi sao no that bai, de run tiep theo khong lap lai loi do. Cach dung: liet ke dung tien trinh OpenLane python
  va openroad cua run do (theo `--run-tag` va duong dan run), SIGTERM, ghi ly do vao `asic/gated_pd.log`. Khong dung run con
  khoe chi de lay bo nho.
- Job dai chet khi phien terminal giu no ket thuc (WSL2 tat may ao khi khong con client `wsl.exe`); tach job qua WMI / Task
  Scheduler bi tu choi. Job can song qua luc phien ket thuc thi chu du an chay tu terminal WSL cua minh.
- Tai nguyen: WSL 24 GB + 8 GB swap, Quartus 16 luong. Quartus fit chay tuan tu. Toi da 3 flow PD song song, toi da 2 detailed
  routing (~10.5 GB moi cai) va chi bat dau khi >= 12 GB trong. Phan sign-off (Magic / Netgen den ~8 GB) cung phai cho bo nho
  (2026-10-07). EQY (~13 GB) va kiem hinh thuc muc SoC chay MOT MINH (2026-10-03).

## C. Chuoi bat buoc cho moi thay doi RTL

Thu tu: lam xong RTL, dong bang, roi moi chay PD. PD khong sua RTL. Logic moi phai co test moi; khong tat chuc nang nao de flow
qua.

1. Ap thay doi bang script, chay thu tren ban sao truoc. Dong bang bang `scripts/rtl_manifest.py` (ma tong cua manifest la danh
   tinh cua ban RTL).
2. Kiem tinh: `scripts/latch_sweep.sh` (moi to hop CACHE_CONFIG x LINE_COUNT x FAST_HIT; to hop khong elaborate duoc la FAIL),
   `scripts/lint_rtl.sh` (cung cac to hop), `scripts/lint_asic.sh`, cong lint baseline OpenLane
   (`scripts/lint_baseline_check.py`, 0 canh bao moi; `ERROR_ON_LINTER_WARNINGS` giu false).
3. Moi thay doi tai cau truc: chung minh hinh thuc (SAT / Yosys equiv / k-induction) kem doi chung am, va checker chi mo phong
   (`ifndef __openlane__` + translate_off) so tung chu ky; checker cung can doi chung dot bien.
4. Chuoi day du (`scripts/run_fullchain_*.sh`), moi hang muc x2: regression, UVM, UVM AXI o cac kich thuoc line, Embench (trung
   tham chieu truoc sua), CoreMark, random differential 50 seed (trung ca hash), view ASIC = view FPGA, directed ISA, bo dong bo,
   ramsweep.
5. Quartus x2 (muc E).
6. PD: full flow OpenLane 2 tu buoc 1 (muc D), chay kep; GLS netlist cuoi va cong suat theo hoat dong (muc F); tuong duong RTL
   - netlist (LEC, `NHAT_KY.md` muc 9 "EQY va LEC"). Neu netlist tong hop khac tung byte thi chung minh tuong duong RTL - RTL
   o muc SoC cho dung danh sach file cua PD.
7. Config PD doc RTL tu snapshot (`asic/snapshots/rtl_<ban>/`), KHONG doc hdl/. Tong hop config PD dang chay de "so voi ban
   moi" la vo nghia (ca hai doc cung snapshot; loi 2026-10-08). Thay doi chi FPGA (`ifndef __openlane__`): dong nhat token cua
   view ASIC (preprocess voi define cua OpenLane, co doi chung am: view FPGA phai khac) + tong hop tu snapshot moi so voi
   snapshot cu (`asic/run_rf_bht_m9k_asic_checks.sh`). Thay doi ca hai view: snapshot moi va PD lai.
8. Chuoi day du chay song song theo lane, moi lane mot thu vien Questa rieng (`scripts/run_fullchain_rfbht.sh`: work,
   work_asic, work_m2_1..6, work_act4; ~55 phut thay vi ~5 gio). Hai batch cung mot thu vien va cham nhau (vsim-1962); UVM
   bien dich lai `work`, nen lane `work` chay tuan tu. TB truy cap noi dung register file / BHT chi qua macro
   `tb/rf_bht_backdoor.svh` (view FPGA giu chung trong M9K).

## D. Quy trinh PD

- Launcher: `asic/run_pd_mk.sh <design dir> <tag> [--from ... --to ...]` (`CONFIG=<file>` de chon config; `RESUME=1` de chay
  tiep vao run co san). No them GNU make va grep vao PATH cho EQY (shell nix `--pure` cua OpenLane khong co).
- OpenLane: ban sao co sua `asic/openlane-local` (OpenLane 2.3.10). Cac them vao, mac dinh tat tru khi config bat:
  `set_thread_count 1` trong antenna check / repair; `LAYERS_RC` / `LAYERS_RC_SCOPE`; `DRT_ANTENNA_REPAIR_ITERS` /
  `_MARGIN` (sua antenna sau detailed routing); `OpenROAD.MacroPinBuffers`; `OpenROAD.PostRouteHoldECO`; `SYNTH_OPT_DFF_SAT`;
  `read.tcl` va `drc.tcl` cua Magic (macro truu tuong); `yosys.py` (`@NETLIST@` / `@PDK_FORMAL@` cho EQY).
- Flow co cong (`asic/run_gated_pd.sh`, `ITEMS="<design dir>:<tag>:<config> ..."`), bon pha trong cung mot thu muc run:

  | pha | cac buoc | cong sau pha | nguong |
  |---|---|---|---|
  | P1 | tong hop .. OpenROAD.GlobalRouting | grt_overflow, cts_tt_slack | overflow GRT <= 500; STAMidPNR-2 setup nom_tt >= +0.5 ns, hold nom_tt >= 0 |
  | P2 | CheckAntennas .. STAMidPNR-3 | grt_repair_overflow, grt_tt_slack | overflow cua lan route lai cuoi (tu dau, trong RepairAntennas) <= 2000; STAMidPNR-3 setup nom_tt >= +0.3 ns, hold >= 0 |
  | P3 | DetailedRouting | drt_convergence (`asic/drt_watch.sh`) | vong 5 > 20,000, 10 > 5,000, 20 > 600, 30 > 400, 40 > 200 vi pham -> dung; tu vong 12: > 300 vi pham va giam < 10 % trong 4 vong -> dung; sau vong 40 chay toi vong 64 |
  | P4 | PostRouteHoldECO .. sign-off | signoff (`asic/fp_tools/gate_check.py final`) | route / Magic / KLayout DRC 0, moi so LVS 0, XOR 0, overlap 0, chan ngat critical 0, antenna net / pin 0, setup >= 0 o moi goc tt va ff, hold >= 0 o moi goc, du 9 goc; ss bao cao rieng |

  Ten cong trong log cu: G1 .. G6 theo thu tu tren. Nguong drt_convergence hieu chinh 2026-10-06 (nguong dau lay tu mot run DM
  da dung mot run SA2 dang hoi tu) va 2026-10-07 (SA2 corr3400x3400_f220 chay du 64 vong: 72 o vong 30, 70 o vong 40, 0 o
  vong 54; nguong 2026-10-06 se dung no o vong 23). Cong mid-PnR chi dung goc tt (so ss / ff o STAMidPNR la so cu, muc 9 "Bay trang thai run").
- Hai bien opt-in cua gate scripts (mac dinh tat, khong doi gate sign-off):
  `G5_UNLIMITED_LATE_PHASE=1` thuc thi quy tac P3 khong ap nguong convergence / stall sau vong 40; bat bien nay khi
  khoi dong flow PD moi hoac resume DRT. Den va gom vong 40, cac nguong cu giu nguyen. Khong dat bien thi hanh vi cu
  duoc giu de doi chieu. Ban va va doi chung: `results/drt_watch_rule_alignment_20261009/`.
  `P2_INITIAL_GRT_FALLBACK=1` chi cho phep doc overflow cua GlobalRouting khi resolved.json ghi ro
  `RUN_POST_GRT_DESIGN_REPAIR=false` va khong co buoc RepairDesignPostGRT. Neu co route lai sau GRT, van lay route lai
  cuoi truoc STAMidPNR-3. GlobalRouting phai hoan tat va nam truoc STAMidPNR-3; thieu dau vao van FAIL / MISSING.
  P2_MIN_SETUP / hold / overflow giu nguyen. Tu 2026-10-13 khong con CONTINUE sau cong FAIL (quy tac "KHONG CHAY TIEP TU
  BUOC FAIL" ben duoi): cong thuc nao sua hold sau route (`RUN_POST_ROUTE_HOLD_ECO`, SA2 / DM_VC4) thi khai bao bien hold p2
  NGAY KHI KHOI DONG: `P2_MIN_HOLD=-0.5` (mac dinh 0; doi chung x2 `asic/fp_tools/check_p2_min_hold_20261013.sh`: SA2 -0.206
  va VC4 -0.202 FAIL o mac dinh, PASS o -0.5, FAIL o -0.1). Cong final giu nguyen (hold >= 0 o moi goc).
  Doi chung: `python asic/fp_tools/verify_gate_p2.py`, `results/gate_p2_no_repair_20261009/verification.json`.
- Theo doi tien do host (2026-10-11): `python -B scripts/maintenance/monitor_jobs.py --output results/job_monitor_status.json`
  kiem tra mot lan; them `--watch` moi poll moi600giay trong foreground. Khong detach/persistence, khong kill/retry job,
  khong sua gate. Theo doi PD tags hien tai, GLS receipts va hang doi exact power; job HOLD theo STOP_AFTER=p2 la HELD.
  Tien trinh mat khi receipt van RUNNING la DEAD_ALERT; loi query la UNKNOWN, khong tu gan processcount0.
  SUSPECTED_STALL chi khi cung processset >=600giay, CPU ca cay khong tang, RSS khong doi va output khong thay doi;
  day la nghi van can chan doan, khong phai bang chung treo. CPU dang tang van RUNNING du log im lang.
  JSON/log la diagnostic, khong la so lieu PPA; monitor khong co chuc nang gui tin nhan hoi thoai.
- Hang cho Windows cho gia thuyet VC4 padding da chuan bi (2026-10-10), chi bat khi goi ro `--run`:
  `scripts/maintenance/queue_vc4_padding.py --prepare` dong bang plan; `--run --plan-sha256 <sha>` kiem lai
  config/RTL/macros/SDC/flow sources va doi Windows free >=10,000 MB, moi30s. Day la dieu kien bo sung;
  cong WSL >=10GB khi bat dau, >=12GB truocDRT va moi gate goc van giu nguyen. Child wsl.exe foreground
  giu hetP1/P2, khong detachment/persistence helper; STOP_AFTER=p2 de inspect clock/skew truocDRT.
  `results/.abort_vc4_padding_queue` chi ngan launch; sauSTARTED dung global PD abort protocol de ngan pha moi,
  khong kill healthy step. Process exit0 khong la gatePASS. Controls38ca va plan219input o
  results/vc4_padding_queue_controls_20261010/. ExternalNix/PDK phai check tu launcher environment thuc.
- Cach toi uu (chu du an, 2026-10-08): moi lan dieu chinh chay FULL FLOW toi sign-off (sua mot loi co the lam lo loi moi o
  pha sau), co chan doan o tung pha va dung ngay khi co dau hieu that bai ro rang, khong cho lau. Moi lan mot thi nghiem co
  gia thuyet; khong rai nhieu run song song de do. Cong p2 khi chay full flow: setup nom_tt >= 0 (`P2_MIN_SETUP=0`), bien
  +0.3 chi ghi chu. drt_convergence khong co gioi han sau vong 40 (cac vong cuoi doi chien luoc; sa2_corr3400x3400_f220_r1
  roi tu 70 xuong 0 giua vong 44 va 54). Bao cao DRC moi 5 vong (`DRT_DRC_REPORT_ITER_STEP` 5) de chan doan khi detailed
  routing dung lai; moi lan goi detailed_route giu bao cao rieng trong `drc_iter_<lan goi>/`.
- ECO sau route (`OpenROAD.PostRouteHoldECO`, 2026-10-08): hop phap hoa voi padding 0 (padding la nut cua GPL / DPL, diode
  antenna sau DRT dat sat cell); STA trong phien ECO chi dung SPEF trich xuat (goi `estimate_parasitics` truoc `read_spef`
  lam phien o lai tren uoc luong); macro SRAM chi co mot .lib TT nen trong phien nhieu goc no chi gan voi goc doc dau tien
  (STA-1140): sua setup thi chay rieng goc tt (`POST_ROUTE_ECO_SETUP`, `POST_ROUTE_ECO_CORNERS`, `POST_ROUTE_ECO_HOLD` false),
  roi chay lai buoc ECO voi sua hold moi goc. So timing chi lay tu STA sign-off (moi goc mot phien).
  ECO hold gan MOT trich xuat cho moi goc (`POST_ROUTE_HOLD_ECO_RCX_CORNER`, mac dinh max_*), nen moi luot chi sua mot dau
  RC (SA2 11.56 mm2, 2026-10-09: chi chay min_* thi max_ff -0.116; max_* roi min_* thi hold >= 0 o ca 9 goc). Tu 2026-10-13
  luot thu hai chay TRONG CUNG buoc: `POST_ROUTE_HOLD_ECO_RCX_CORNER_2` = "min_*" (mac dinh trong = mot luot nhu cu; file luot 1
  giu trong `pass1/`, log luot 2 `*_2.log`). Khong con tach run sau buoc ECO / config `_ecomin`. Kiem chung doc lap tren trang
  thai buoc 47 cua sa2_..._rsztf_r1: luot 1 trung tung byte buoc 47 cua r1, luot 2 trung tung byte buoc 48 cua ecomaxmin_r1
  (netlist va DEF; `asic/soc_sa2_4kb/eco2pass_check_20261013/`).
- Ket qua moi cong ghi vao `asic/gated_pd.log` va `asic/dse_pd.log` ("GATE <PASS|FAIL> <tag> <cong>: <so>"). Dung hop tac:
  `touch asic/.abort_gated_pd`. Chay tiep sau khi phien ket thuc hoac sau mot cong du phong voi slack duong:
  `asic/run_gated_resume.sh <design dir> <tag> <config> <ly do> [drt|hold|sta|p2] [to]` (cung khoa slot DRT va cung cong
  sign-off); dung de noi tiep mot diem dung co ke hoach (HOLD_AFTER_DRT, STOP_AFTER=p2) hoac, tu 2026-10-14, mot buoc
  da fail sau khi da sua nguyen nhan (quy tac duoi).
- SUA VA CHAY TIEP KHI PHAT TRIEN, NGHIEM THU BANG MOT LAN CHAY TRON TU DAU (chu du an, sua 2026-10-14; ban 2026-10-13
  "khong chay tiep tu buoc fail" lam qua trinh qua dai):
  - Buoc nao fail (crash, loi, watchdog dung, cong FAIL): ghi FAIL + nguyen nhan da chan doan vao `gated_pd.log` /
    NHAT_KY, giu thu muc run; sau khi sua duoc phep chay tiep tu buoc loi (`run_gated_resume.sh ... step:<StepID>` /
    `drt` / `hold`, tach nhanh) de phat trien nhanh.
  - Nghiem thu: khi moi cong da qua, chay MOT lan tron tu buoc 1 (tag moi, khong resume, khong tach nhanh, khong
    CONTINUE, moi nguong khai bao luc khoi chay). Chi lan chay tron do (va lan chay kep cua no khi can) la ket qua.
  - Khi flow tat dinh va cach sua chi la mot thiet lap luc khoi chay, duoc di thang toi lan chay tron (vua thu vua nghiem thu).
  - Cong cu khac PD cung vay: go loi bang chay tiep, bang chung cuoi tu cac lan chay tron.
  - Run da ky bang resume / tach nhanh (DM r14F_A/B, SA2 ecomaxmin) can mot lan chay tron moi run.
- Tam giu truoc sign-off (2026-10-11): `HOLD_AFTER_DRT=1` voi `run_gated_resume.sh ... drt` chi giu sau khi
  DetailedRouting hoan tat va kiem tra runtime/convergence hien hanh da qua. Mac dinh0 giu nguyen flowcu.
  Dung de kiem tra tai nguyen truoc PostRouteHoldECO/Magic; HOLD khong la DRC/LVS/timing sign-off PASS.
  Tiep tuc bang `run_gated_resume.sh ... hold` khi du RAM va clientWSLforeground. Khong doi threshold/gate/recipe.
  Doi chung bash-n va3mockcontrol: results/gated_resume_phase_hold_20261011.json. Chi sua helper luc khong co flow.
- Hang doi tai nguyen P4 (2026-10-12): `P4_RESOURCE_WAIT=1 bash asic/run_resource_gated_resume.sh ... hold`
  giu clientWSLforeground cho job sign-off dang doi; chi goi gated resume khi WSLavailable va Windowsfree deu
  >=15000MiB. Mac dinh flagtat, wrapper goi driver cu nguyenargs. Hai muc tai nguyen co the dat ro bang
  P4_MIN_AVAILABLE_MB/P4_MIN_WINDOWS_FREE_MIB; day la dieu kien RAM, khong phai gate sign-off.
  QueryWindows qua pwsh7 co timeout15s; queryloi STOP/UNKNOWN, khong gan0. Doi30s, ghiWAIT moi10phut,
  dung hop tac qua .abort_gated_pd. `--check-resource-only` chi doc mot lan, khong goi flow.
- Hai bien DRT moi (2026-10-13, mac dinh tat, `drt.tcl` + `steps/openroad.py`): `DRT_SAVE_MAIN_ROUTE` ghi
  `main_route.odb` sau main route, truoc vong sua antenna (khong doi ket qua); `DRT_ANTENNA_REPAIR_ALLOW_CONGESTION`
  goi `grt::set_allow_congestion 1` truoc moi `repair_antennas`, de GRT tang dan noi diode khong dung o GRT-0232
  (`GlobalRouter::updateDirtyRoutes` chi bao loi khi khong cho nghen); detailed route tang dan phai go overflow, DRC van
  do cong sign-off kiem. Chi dung khi da co bang chung vong sua antenna that bai vi nghen (DM_VC4 3600 padding).
- GLS bi ngat sau nativeprefix thanh cong (2026-10-12): `scripts/verification/resume_gls_exact_window.py`
  mac dinhprepare-only, --run moi tiep tuc. Chi nhan1privatecompile+canonicalsim/conversionprefix exit0;
  snapshot stoppedreceipt nguyenbyte, check314input va cac log/raw/pin da co, giu nguyen compiledlibrary.
  UNC hashdoc loi transport duoc thu doc toi da3lan/3s timeout, khong thay file/path/hash va khong retry nativejob.
  Nativecommandthatbai hoac outputstale bi tu choi; strict25command/counter/SAIF pairverifier van giu nguyen.
  Controller `run_dm_capture_power_retry.ps1 -Resume -Run` chi tiep tuc plan da kiem, luu stoppedqueue truocghi
  tien do; capGLS dat moi chay26STA. Khong bien partialcapture thanh PASS va khong chay lai cac case da xong.
- Sang loc mot knob chi tac dong sau GRT (vd. bien cap cua sua DRV sau GRT): tach run tu mot run da qua P1,
  `bash asic/branch_run.sh <design dir> <tag nguon> <tag moi> <so buoc GlobalRouting>` (chep cac buoc 1 .. N, sua duong dan
  trong file state, run nguon chi doc; file `BRANCHED_FROM` ghi nguon), roi `run_gated_resume.sh ... p2` (chi pha P2, cong p2,
  giu run sau cong); knob tac dong tu buoc sua DRV dau tien (`MAX_FANOUT_CONSTRAINT`): tach o buoc 30 va
  `asic/run_gated_branch.sh <design dir> <tag> <config> <ly do> OpenROAD.RepairDesignPostGPL` (phan con lai cua P1 + P2).
  `run_gated_branch.sh ... drt`: chi detailed routing (khoa slot, `drt_watch.sh`), giu run sau do; phan sign-off chi chay khi
  run duoc chon (`run_gated_resume.sh ... hold`). Run tach chi de sang loc; run sign-off chinh thuc van la full flow tu buoc 1.
- Sang loc floorplan: `asic/fp_tools/screen_floorplan.sh` (tu trang thai sau tong hop toi GlobalRouting, GRT 50 vong nhu flow
  that), `asic/fp_tools/screen_grt.sh` (chi GlobalRouting); bang: `python asic/fp_tools/fp_summary.py`. Khong dung GRT 15 vong de
  xep hang ung vien.
- Du bao diem nong detailed routing truoc khi chay no (chi doc, Windows): `python asic/fp_tools/pin_hotspots.py <DEF cua
  ResizerTimingPostGRT> <sky130_fd_sc_hd.lef> 20` (mat do chan / util theo o 20 um; DM hoi tu nhanh o max ~29, SA2 can 54
  vong o max 32).
- Chan doan nghen (chi doc, chay tren Windows): `asic/fp_tools/guide_demand.py <guide> [<guide 2>]` (nhu cau dinh tuyen theo
  cua so 55 um tu `after_grt.guide`, va phan tang giua hai buoc), `region_cells.py <def> x0 y0 x1 y1` (thanh phan cell trong
  mot o), `net_probe.py <def> <guide> <net> ...` (chan, vi tri cell, khung guide cua net).
- Dau hieu nghen som: dong "Extra Run for hard benchmark" trong log GRT dau (`grep -c "hard benchmark"`). FastRoute chi chay
  no khi con overflow sau cac vong thuong; detour cua no keo ca net clock (DM_VC4 11.56 mm2: net clock 2 tai ~7.7 mm, skew
  hold -1.5 -> -4.8 ns o p2). Khi thay dong nay, chan doan cum bang `guide_demand.py` / `region_cells.py` truoc khi chay tiep.
- `asic/run_resume_retry.sh` (resume tay sau crash): ngung tu 2026-10-13, lai duoc dung cho phat trien tu 2026-10-14; ket qua
  van can mot lan chay tron tu dau (quy tac "SUA VA CHAY TIEP KHI PHAT TRIEN, NGHIEM THU BANG MOT LAN CHAY TRON TU DAU").
- Bay trang thai run (bat buoc nho): khong xoa step da xong cua run con resume; OpenLane resume tu `state_out.json` moi nhat
  tim de quy; sua config phai chay lai; so ss / ff cua STAMidPNR la so cu; thanh cong la `state_out.json` hoac metric, khong phai
  thu muc hay `final/`; thay doi anh huong tu tong hop tro di (SDC, config) phai chay full flow tu buoc 1.
- Doc so theo goc: moi WNS / TNS / Fmax ghi ro goc; `power__total` cua flow la goc max_ff, khong phai tt.

## E. Quy trinh FPGA

- Pham vi rieng phien board2026-10-13: chi chay pass1 cho100workload/config theo chi dinh moi;
  khong len lich pass2. So board phai ghi singleexecution, khong gan nhan doubleexecuted.
  Van dung sau moi workload/config de kiem tra/xacnhan truoc ca tiep, reset hay rerun.
  Ngoai le nay chi ap dung cho phep do vat ly trong phien board; verification, Quartusfit,
  PD va activitypower van theo quy tac hai luot. Session/resultsCSV giu ro pham vi va bang chung.
- Tu 2026-10-09: bo seed chung 1..10 cho DM / SA2 / DM_VC4 / DM_DSE 4 KiB; so sanh cac cau hinh TRONG CUNG seed.
  Khong chon seed tot nhat rieng cho tung cau hinh. Bao cao du 10 seed, min / max / mean / do lech chuan va cac chenh lech
  ghep cap theo seed. Cac bo 4 seed da do giu nguyen lam bang chung lich su; mo rong phai cung RTL va dau vao.
  Board dung seed 2 CHUNG cho ca bon cau hinh (chot truoc khi xem ket qua mo rong); phien board hen sau khi chuan bi SOF.
- Phien board2026-10-12 dung Hercules, nominal115200/8N1/handshakeOFF. SOF dafit duaUART raJP5 GPIO3.3V LVTTL:
  TX=GPIO[0]/AB22, RX=GPIO[1]/AC15, dungUSB-TTL vaGNDchung, VCCadapter de trong; khong dungDB9 RS-232.
  Xemmanualpinorientation vaJP6short7-8=3.3V trong results/board_20261012/README.md. BauddividerRTL hien tai
  tao448clock/bit (~111607baud tai50MHz); smokeUART ramsweep truocmatrix, giuRTL. Firmwarebootngay, khongchoKEY1:
  moHercules/log truocprogramming. Moi case moi pass phai programSOFtuoi, khongthaybangresetKEY0. Loggandung
  kernel/config/pass/SOFsha; upfull_* va up_* dungchungBENCHlabel nenkhongphanbietchi bangtextBENCH.
- `scripts/run_le_<tag>.sh 1` roi `2` (`scripts/run_fpga_points.py`): driver cu do 4 seed; bo mo rong dung
  `scripts/fpga/run_paired_seed_matrix.py` (1..10, hai luot); 116 cot
  moi fit (tai nguyen, timing 3 goc, cong suat ngay sau moi fit); thieu truong la FAIL. Luot 1 phai bang luot 2
  (`scripts/verify_double.py`). Cong cho bo nho truoc moi fit (>= 6 GB trong).
- Bang seed: `scripts/fpga_seed_summary.py --seeds 1,2,3,4,5,6,7,8,9,10` (min / max / mean / do lech chuan / do trai;
  thieu seed hay truong la FAIL; mac dinh 4 seed cho du lieu cu). Dung sweep: `touch results/.abort_fpga_sweep`.
- Log cua lan fit that bai duoc giu (`<ten>.attemptN.failed.log`).
- Tiep tuc board sau ngat phien (2026-10-09): kiem tra read-only PID / log / hash dau vao; archive log do dang truoc.
  `run_paired_seed_matrix.py --run --resume` giu fit da ghi nhan, chay lai TRON fit chua xong; chi go lock khi PID cu da
  chet va lock da luu. `prepare_board_reference.py --run --resume` chi giu case co CSV day du khop moi counter voi R14
  va dau vao khong doi; case chua xong bien dich lai thu vien rieng, mo phong tu dau, dung ten log moi de giu dau vet cu.
  Moi pass van la phep do doc lap; khong dem output doc lai thanh lan do thu hai.
- Tiep tuc sau cong bo nho 2026-10-09: `scripts/fpga/continue_common_seed_preparation.py` kiem 32 input va 51 fit
  da ghi nhan, dong bang plan moi bang `--prepare`, roi `--run` chi thuc thi nam fit con thieu. Bang chung phien cu
  giu nguyen. Runner doi Windows free >=6,000 MB truoc moi fit, khong retry loi tat dinh hay dung chuong trinh khac
  de lay RAM. Sau 40 cap khop, moi xuat PPA va goi builder / audit 100 SOF seed2 chung. Co dung hop tac giua buoc.
- `scripts/fpga/complete_board_preparation.py` (mac dinh chi in plan) cho hai job VERIFIED, cong bo bang 40 cap fit va
  chi sau do build / audit 100 SOF seed 2 chung khi 100 cap tham chieu cung VERIFIED. Khong program board, khong restart
  job that bai, khong chay PD. Co `results/.abort_board_completion` chi dung buoc tiep tuc, khong dung job do con khoe.
  `--run --launch-resume` chi danh cho lan ngat da chan doan va archive ngay 2026-10-09, khong phai retry tong quat.

## F. Do cong suat ASIC

- GLS -> SAIF -> OpenSTA (`asic/gls/`): mo phong netlist sau fill (model cell chuc nang, model OpenRAM) cho 12 kernel; cua so do
  tu `sysmon_clear_start()` toi `sysmon_freeze_snapshot()`. Capture moi dung mapped freeze observer da chung minh tren
  dung netlist; `win_cycles` = `mcycle`, elapsed ps = `mcycle` * 20000 va moi SAIF T0+T1+TX phai khop cua so.
  Giu raw `power report -bsaif` nguyen byte; khong ep DURATION de che sai cua so. Questa 2024.1 da cho raw header khop
  trong screening ud. `saif_to_pins.py` chuan hoa duration tu span va gan moi net vao chan lai (OpenSTA 2.6
  bo qua net phang); `sta_power.sh` nap dung lib / SPEF RCX / SDC cua buoc STAPostPNR, goc nom_tt.
- Kiem truoc khi tin so: khong SAIF thi phai tai lap dung so vectorless cua flow; bao cao ty le chan co nguon hoat dong
  "unknown". CPI va EPI dung chu ky view ASIC (`asic/gls/power_csv.py`).
- `scripts/verification/run_gls_exact_window.py --wait-for-memory` la opt-in, mac dinh tat: cho foreground 30 giay
  truoc tool tiep theo neu Windows free RAM < 6000 MiB; khong ha nguong. Moi lan cho kiem lai input SHA256.
  File `abort_before_next_native` trong output chi ngan tool tiep theo, khong giet tool dang chay. Moi pass dung
  private compile moi; giu capture cu va so sanh du 12 kernel qua hai pass truoc khi chay OpenSTA kep.

## F2. LEC (tuong duong RTL - netlist da ky ten)

- Chuoi anh xa thanh ghi (`asic/equiv/lec/`): RTL + `fsm` == N1 (trang thai tong hop truoc `abc -fast`, replay trung tung
  byte buoc 06) == netlist cuoi (ca r1 va r2). DM: `run_lec_r14.ps1 -Step A|B`, `run_lec_r14_mul.ps1`,
  `run_lec_r14_pass2.ps1`. SA2 (va DM_VC4 sau nay): `<thu muc luot>/run_frontends.sh` (tao bang
  `scripts/verification/prepare_sa2_lec.py`) roi `pwsh -File asic/equiv/lec/run_lec_sa2.ps1 -Work <thu muc luot>
  -Step A|Mul|Inv|B|NegB|NegFSM`. Hai luot doc lap (front end va replay moi moi luot), so hash cac doi tuong chung minh;
  doi chung am: ma hoa FSM sai, spec bo nhan unsigned / tich rieng phan sai, netlist and2 -> or2.
- Cac tien de cua chuoi tren, kiem rieng (2026-10-13), moi kiem hai lan va co doi chung am:
  - Reset bat dong bo: `arst_audit.py` / `run_arst_audit.ps1` tren mo hinh TRUOC async2sync (gold_pre / gate_pre): moi bit
    flop ghep theo ten phai cung co / khong co reset bat dong bo, cung nguon (qua alias / buf / not), cung muc, cung gia tri.
  - Gia tri khong xac dinh: `run_xsens.ps1` (`x_free_aig.ys` + `aig_tie_inputs.py`): moi bit x va moi net khong noi cua
    mo hinh gold LEC thanh input moi, miter voi chinh no khi cac input do = 0; moi output UNSAT => khong output nao phu
    thuoc gia tri khong xac dinh o bat ky trang thai nao. Doi chung am: `lec_d_p00001` = 1'x phai SAT.
  - Clock: `scripts/verification/lec_clock_audit_files.py` (goi nguyen `lec_clock_audit.py`) tren 4 mo hinh phang.
  - Bat bien one-hot FSM: `-Step Inv` (`evert.py --inv` + `inv_check.py`) tren dung nguon hien tai.
- Ngoai kha nang (khong lam): tuong duong tuan tu toan phan khong anh xa thanh ghi (bai toan qua lon cho cong cu mo nguon);
  macro SRAM la hop den (GLS phu phan nay).
- Tai nguyen: front end gate (~0.57 GB IL) can vai GB trong WSL. Khi detailed routing dang chay va Windows free < 2 GB, dat
  file `DEFER_HEAVY` trong thu muc luot de hoan buoc nang (NegB), chay lai sau.

## G. Golden snapshot va giao thuc nang golden

- Chi MOT golden (hien tai `E:/Projects/RISCV-research_GOLDEN_FINAL3_20260928`, ban DM 8 KiB-RAM). Snapshot truoc moi thay doi co
  rui ro; `scripts/make_golden_snapshot2.py` (sha256 moi file, chi hard-link artefact bat bien, `--verify` / `--diff` /
  `--restore`).
- Mot run vuot golden o MOI mat (dien tich, timing, cong suat, DRV chap nhan duoc): bao cao bang so sanh va DUNG, khong khoi
  dong viec moi cho toi khi chu du an duyet; duyet xong moi nang lam golden duy nhat va xoa golden cu (2026-09-30).
- So sanh cung loai (cung RAM, cung bo macro); thi nghiem mot phan khong nang truc tiep: can full flow x2, DRC / LVS, GLS + SAIF,
  LEC truoc.

## H. Ghi chep

- Mot lich su duy nhat: `NHAT_KY.md` (tieu de `### YYYY-MM-DD <chu de>`, moi su kien mot lan; van de lap lai vao muc 9 cua no).
  Quy tac: file nay. So lieu hien hanh: `RESULTS.md`. Tra loi phan bien: `REVIEW_RESPONSE.md`.
- Log flow: `asic/dse_pd.log`, `asic/gated_pd.log`, `asic/pd_log.md` (do launcher ghi). Moi CSV ket qua co cap `_p1` / `_p2`.
- Danh tinh mot ban RTL la ma manifest (`results/rtl_manifest_<id>.json`) cong ten theo ngay va noi dung.
- Git: tieng Anh, chi ASCII, khong co dong `Co-Authored-By`, danh tinh git cuc bo. Tai lieu noi bo tieng Viet khong dau; bao cao
  cho nguoi doc ngoai (RESULTS, REVIEW_RESPONSE, README) tieng Anh.

## I. Dat ten (2026-10-07)

- Dat theo noi dung va ngay, khong theo so dem: khong R1 .. R17, E1 .. E16, X1 .. X4, Incident NN, Entry NN, final2 / final3,
  _v2, _b.
- Cau hinh cache: dm, dmdse, sa2, vc4, sa4 (hau to `fast` khi FAST_HIT = 1); RAM chinh ram8k / ram16k, chi ghi khi khac 16 KiB.
- Floorplan: ho + kich thuoc die W x H (um) + thuoc tinh khi anh em khac nhau: grid3665x2900, corr3400x3325_f220 (hang cache
  tren lat FS, khe 220 um), wide4211x3331, ring3200x3190, strata3260x3400.
- Run OpenLane: chu thuong [a-z0-9_], `<cfg>_<floorplan>[_<knob><gia tri>...]_<rN>`; r1, r2 la hai lan chay kep (khong dung
  A / B); sang loc ket thuc bang `scr15` / `scr50`, chi tong hop bang `synth`; gia tri khong co dau cham (hold003 = 0.03 ns,
  dens55 = 55 %).
- Thi nghiem dat ten theo mot thay doi so voi mot nen co ten (dm_grid3665x2900_hold003).
- Cong kiem tra dat ten theo cai no kiem (grt_overflow, cts_tt_slack, grt_repair_overflow, grt_tt_slack, drt_convergence,
  signoff). Muc phan bien giu ma cua phan bien (M1, M2, A1 .. A9).
- Khong doi ten tren dia nhung gi mot run con giu (duong dan tuyet doi trong state / resolved.json). Bang doi ten cu -> moi:
  `NHAT_KY.md` muc 11.

## J. Don dep (bat buoc, 2026-09-26)

- Xoa: run hong / that bai / bi thay the, CSV sai, file rong, script dung mot lan, san pham build tai tao duoc.
- Truoc khi xoa mot run: luu resolved.json, metric cuoi, log loi / canh bao, flow log, danh sach buoc vao
  `results/pd_run_archive/<run>/`; ghi tung muc vao `results/cleanup_deleted.txt` (them mot muc cho lan don moi).
- Giu: tai lieu duy tri, log (log cu nen lai), CSV chuan da chay kep, moc 1 KiB (`asic/soc_dm_control/runs/sync_final`), bang
  chung Magic (`asic/evidence/MAGIC_NAMESPACE_COLLISION.md` va cac file no liet ke), SOF board, run ky ten, golden snapshot.
- Xoa thu muc run can chu du an dong y; run dang chay hoac con resume khong dong vao.

## K. Bao cao

- Hai phan theo thu tu: thanh qua, roi that bai va khoang trong; so cung, khong to hong.
- Sau PD: ghi goc cho moi WNS / TNS / Fmax; tach goc ky ten timing voi goc do cong suat; ghi ro cong suat la uoc luong cua flow
  hay tu hoat dong that; DRC / LVS la cong dat / truot dat truoc bang PPA; bang theo cau hinh (DM / SA2 / DM_VC4).
- Bo tieu chi (2026-09-26): CPI / IPC va chu ky (Embench, CoreMark); Fmax (FPGA va ASIC theo goc); LE / LUT / FF / M9K va dien
  tich + so cell ASIC; cong suat dong + tinh; hieu suat nang luong (perf/W, nang luong moi lenh); hit / miss I$ / D$; ty le doan
  sai nhanh; stall / wait / hazard (bo dem phan cung).
- Bang Embench hop nhat (2026-09-30), moi kernel x cau hinh: `mcycle` khop giua RTL, view ASIC, GLS (va board khi co), CPI, hit
  I$ / D$, doan sai nhanh, cong suat GLS; them kich thuoc code (.text / .rodata / .data, rv32i_zmmul -O2), toc do / MHz kieu
  Embench va CoreMark / MHz, GM va GSD, do tre ngat va chuyen ngu canh (`scripts/metrics/unified_table.py`).
