# Quy trình và ràng buộc của dự án (bản hợp nhất)

Hợp nhất ngày 2026-09-26 theo yêu cầu "không muốn nhắc lại". Đây là nguồn duy nhất;
bản sao cho trợ lý nằm trong memory `user-rulebook.md` và phải khớp với file này.
Mọi quy tắc mới được bổ sung vào đây, ghi kèm ngày.

## A. Giao tiếp
- Trả lời bằng tiếng Việt.
- Mọi thứ đẩy lên git: tiếng Anh, chỉ ASCII, không có dòng `Co-Authored-By`, dùng danh tính git cục bộ.

## B. Phạm vi
- Làm trong `E:\Projects\RISCV-research`, chỉ cấu hình 4 KiB.
- Bản 1 KiB đã công bố: chỉ đọc và lấy dữ liệu, không chỉnh sửa. Không sửa bài báo.
- `asic/` của repo công bố: không đụng vào.

## C. Mục tiêu
- ASIC bắt buộc đạt 50 MHz ở góc tt, không nới clock.
- Góc ss: chỉ sửa có trọng tâm, giữ nguyên từng chu kỳ, **không đổi CPI**, báo cáo ss trung thực.
- Tối ưu PPA đầy đủ; công suất phải đo thật.
- 20.000 LE là mục tiêu mềm do anh tự đặt (từ 2026-09-26), không phải ngưỡng đạt/trượt.
  Vẫn phải tối thiểu LE và diện tích std-cell, và mọi mức tăng diện tích phải được cân
  với slack, CPI, công suất đo được.

## D. Chuỗi bắt buộc cho mọi thay đổi RTL

Thứ tự: làm xong RTL trước, đóng băng, rồi mới chạy PD. PD không được sửa RTL.

1. Áp thay đổi bằng script, chạy thử trên bản sao trước.
   Đóng băng bằng `scripts/rtl_manifest.py` và lấy mã aggregate.
2. Kiểm tra tĩnh:
   - latch sweep, lint_rtl (8 tổ hợp), lint_asic;
   - cổng lint baseline của OpenLane (`scripts/lint_baseline_check.py`).
   `ERROR_ON_LINTER_WARNINGS` giữ False nhưng phải qua cổng này.
3. Với mỗi thay đổi tái cấu trúc:
   - chứng minh hình thức (SAT / equiv / k-induction), **kèm đối chứng âm**;
   - checker chỉ chạy trong mô phỏng, so từng chu kỳ.
4. `scripts/run_fullchain_rtlfix.sh`, mỗi hạng mục chạy ×2:
   - regression, UVM, AXI ở các line size;
   - Embench 48 run, phải trùng tham chiếu trước sửa;
   - CoreMark;
   - random-diff 50 seed, trùng cả hash;
   - ASIC view = FPGA view, directed ISA, các bộ đồng bộ.
5. Quartus ×2 (`TAG=... scripts/run_le_rtlfix.sh 1`, rồi `2`):
   - 4 điểm × 4 seed, ghi đủ mọi trường;
   - lượt 1 phải bằng lượt 2;
   - các fit chạy tuần tự.
6. PD:
   - chạy full flow OpenLane 2 từ bước 1, gồm DRC, LVS, EQY, và chạy kép;
   - sau đó GLS netlist cuối và đo công suất theo hoạt động thật (SAIF → OpenSTA).

Logic mới phải có test mới. Không được tắt chức năng để flow pass.

## E. Kỷ luật thực thi
- Chạy kép mọi phép đo (máy có lỗi phần cứng làm hỏng dữ liệu âm thầm).
- Kiểm tra treo/crash khoảng mỗi 10 phút.
- Gỡ lỗi dựa trên bằng chứng, không đoán mò.
- Crash ngẫu nhiên rõ ràng do máy (Python SIGSEGV, WHEA, OOM ngẫu nhiên) được phép chạy lại.
  Lỗi xác định của EDA/thiết kế (setup/hold, DRC, …) phải sửa bằng kỹ thuật (từ 2026-09-26).
- Không sửa một bash script đang chạy. Lệnh kill bị chặn, nên dùng cờ dừng hợp tác.

## F. Ghi chép
- RTL: `NHAT_KY_RTL.md`.
- PD: `asic/FLOW_JOURNAL.md`, các incident được đánh số.
- Nhật ký tự chủ: `CLAUDE_AUTONOMY_LOG.md`.
- Xoá dữ liệu: ghi manifest `results/cleanup_*_deleted.txt`; bằng chứng của các run đã xoá lưu trong `results/pd_run_archive/`.
- Dọn workspace là **bắt buộc** (từ 2026-09-26):
  - Xoá: run hỏng/lỗi/bị thay thế, CSV sai, file rỗng, script tạm.
  - Giữ: báo cáo markdown, log, CSV chính tác đã chạy kép, baseline post-route 1 KiB
    (`asic/soc_dm_control/runs/sync_final`), và bằng chứng Magic namespace collision.

## G. Báo cáo

Báo cáo gồm hai mục theo thứ tự: **Achievements**, rồi **Failures & Gaps**. Có số liệu cứng, không tô hồng.

Quy chuẩn post-PD:
- ghi rõ corner cho mọi WNS/TNS/Fmax;
- tách corner ký tên timing với corner đo công suất;
- ghi rõ công suất là ước lượng của flow hay từ hoạt động chuyển mạch thật;
- DRC/LVS là cổng đạt/trượt, đặt trước bảng PPA;
- bảng theo cấu hình (DM / SA2 / DM+VC4).

Bộ tiêu chí đo (tổng hợp từ 15 bài báo anh gửi, 2026-09-26) và nguồn số liệu trong thiết kế:

| Tiêu chí | Nguồn trong dự án |
|---|---|
| CPI / IPC, số chu kỳ thực thi | Embench 12 kernel × 3 cấu hình, CoreMark (`mcycle`, `minstret`) |
| Fmax | Quartus Slow-85C / Slow-0C / Fast; ASIC STA ở tt / ss / ff |
| Tài nguyên FPGA | LE, comb, register, M9K, mult9 (Quartus, 4 seed) |
| Diện tích ASIC | Diện tích std-cell, số cell, die/core (OpenLane) |
| Công suất | FPGA: Quartus Power Analyzer. ASIC: GLS → SAIF → OpenSTA (tách dynamic/leakage) |
| Hiệu suất năng lượng | perf/W, năng lượng mỗi lệnh = P × t / minstret |
| Hit/miss I$ và D$ | perf counters: `icache_hit/miss/access`, `dcache_read_* / write_*` |
| Tỉ lệ đoán sai nhánh | `branch_prediction_count`, `branch_correct_prediction_count`, `mispredict_event_count` |
| Stall / hazard / wait-share | `load_use_cycle`, `icache_wait_cycle`, `dcache_wait_cycle`, `control_redirect_cycle`, … |
| Benchmark chuẩn | Embench-IoT, CoreMark |
