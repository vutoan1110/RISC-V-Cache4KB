# Quy tac va quy trinh chay

Moi quy tac dang hieu luc va cach chay tung loai cong viec, o mot cho. Quy tac moi duoc them vao muc tuong ung, ghi ngay dat.
Lich su va ly do: `NHAT_KY.md`. So lieu: `RESULTS.md`.

## A. Pham vi va muc tieu

- Lam viec trong `E:/Projects/RISCV-research`. Ban 1 KiB da cong bo (`E:/Projects/RISCV-AHB-APB-UART`) chi doc va lay du
  lieu; khong sua bai bao; khong dung vao `asic/` cua repo cong bo.
- Cache 4 KiB la cau hinh chinh (tu 2026-09-25); RAM chinh 16 KiB (tu 2026-09-29).
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

## B. Ky luat thuc thi

- Moi phep do chay hai lan va so tung truong (may co loi phan cung lam hong du lieu am tham, `NHAT_KY.md` muc 9 "Loi may").
- Health check may: `python3 asic/parse_ids_probe.py --synth 300000`, 8 lan, ky vong 8 lan "OK" (WSL va Windows).
- Crash ngau nhien ro rang cua may (SIGSEGV native, loi Python vo ly, WHEA, OOM ngau nhien) duoc chay lai khong doi gi; loi tat
  dinh cua cong cu / thiet ke (setup, hold, DRC, ...) phai sua bang ky thuat (2026-09-26). Go loi tu bang chung, khong doan.
- Kiem tra job dai moi ~10 phut (treo / crash). Watchdog phai do tien trinh dang lam viec (CPU ca cay tien trinh) va dung ca hai
  tin hieu (khong ghi output va RSS khong doi) truoc khi ket luan treo.
- Khong sua bash script dang chay; khong sua file nguon khi con flow co the doc no. Dung vong lap bang co huy hop tac
  (`asic/.abort_*`, `results/.abort_*`).
- Khong lach mot lenh bi chinh sach quyen cua cong cu tu choi (2026-09-30): khong dung trinh thong dich, cong cu, may khac cho
  cung ket qua. Chu du an tu lam hoac them quyen.
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
  | P3 | DetailedRouting | drt_convergence (`asic/drt_watch.sh`) | vong 5 > 20,000, 10 > 5,000, 20 > 600, 30 > 150, 40 > 30 vi pham -> dung; tu vong 12: > 100 vi pham va giam < 10 % trong 4 vong -> dung |
  | P4 | PostRouteHoldECO .. sign-off | signoff (`asic/fp_tools/gate_check.py final`) | route / Magic / KLayout DRC 0, moi so LVS 0, XOR 0, overlap 0, chan ngat critical 0, antenna net / pin 0, setup >= 0 o moi goc tt va ff, hold >= 0 o moi goc, du 9 goc; ss bao cao rieng |

  Ten cong trong log cu: G1 .. G6 theo thu tu tren. Nguong drt_convergence hieu chinh 2026-10-06 (nguong dau lay tu mot run DM
  da dung mot run SA2 dang hoi tu). Cong mid-PnR chi dung goc tt (so ss / ff o STAMidPNR la so cu, muc 9 "Bay trang thai run").
- Ket qua moi cong ghi vao `asic/gated_pd.log` va `asic/dse_pd.log` ("GATE <PASS|FAIL> <tag> <cong>: <so>"). Dung hop tac:
  `touch asic/.abort_gated_pd`. Chay tiep sau khi phien ket thuc hoac sau mot cong du phong voi slack duong:
  `asic/run_gated_resume.sh <design dir> <tag> <config> <ly do> [drt|hold|sta] [to]` (cung khoa slot DRT va cung cong
  sign-off).
- Sang loc floorplan: `asic/fp_tools/screen_floorplan.sh` (tu trang thai sau tong hop toi GlobalRouting, GRT 50 vong nhu flow
  that), `asic/fp_tools/screen_grt.sh` (chi GlobalRouting); bang: `python asic/fp_tools/fp_summary.py`. Khong dung GRT 15 vong de
  xep hang ung vien.
- Resume tay sau crash ngau nhien: `asic/run_resume_retry.sh <tag> <config> <from step> [to step]` (chi xet phan `error.log`
  cua lan thu hien tai va ma tra ve).
- Bay trang thai run (bat buoc nho): khong xoa step da xong cua run con resume; OpenLane resume tu `state_out.json` moi nhat
  tim de quy; sua config phai chay lai; so ss / ff cua STAMidPNR la so cu; thanh cong la `state_out.json` hoac metric, khong phai
  thu muc hay `final/`; thay doi anh huong tu tong hop tro di (SDC, config) phai chay full flow tu buoc 1.
- Doc so theo goc: moi WNS / TNS / Fmax ghi ro goc; `power__total` cua flow la goc max_ff, khong phai tt.

## E. Quy trinh FPGA

- `scripts/run_le_<tag>.sh 1` roi `2` (`scripts/run_fpga_points.py`): moi diem x 4 seed (hoac seed 2 khi chi do nhanh), 116 cot
  moi fit (tai nguyen, timing 3 goc, cong suat ngay sau moi fit); thieu truong la FAIL. Luot 1 phai bang luot 2
  (`scripts/verify_double.py`). Cong cho bo nho truoc moi fit (>= 6 GB trong).
- Bang 4 seed: `scripts/fpga_seed_summary.py` (min / max / mean / do trai; thieu seed hay truong la FAIL). Bao cao dai 4 seed,
  khong chi seed ghim. Dung sweep: `touch results/.abort_fpga_sweep`.
- Log cua lan fit that bai duoc giu (`<ten>.attemptN.failed.log`).

## F. Do cong suat ASIC

- GLS -> SAIF -> OpenSTA (`asic/gls/`): mo phong netlist sau fill (model cell chuc nang, model OpenRAM) cho 12 kernel; cua so do
  tu `sysmon_clear_start()` toi `sysmon_freeze_snapshot()`, lay mau o suon xuong, `win_cycles` phai bang `mcycle`; Questa
  `power report -bsaif` (viet lai DURATION, bo dong PROGRAM_VERSION); `saif_to_pins.py` gan moi net vao chan lai (OpenSTA 2.6
  bo qua net phang); `sta_power.sh` nap dung lib / SPEF RCX / SDC cua buoc STAPostPNR, goc nom_tt.
- Kiem truoc khi tin so: khong SAIF thi phai tai lap dung so vectorless cua flow; bao cao ty le chan co nguon hoat dong
  "unknown". CPI va EPI dung chu ky view ASIC (`asic/gls/power_csv.py`).

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
