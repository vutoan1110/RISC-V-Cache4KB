# R14 — Tăng RAM chính từ 8 KiB lên 16 KiB, bổ sung bộ Embench-IoT gốc

Yêu cầu của người dùng ngày 2026-09-29: "có tăng RAM lên nhưng phải ghi rõ các thay đổi". File này là danh
sách đầy đủ, đọc được độc lập. Nhật ký chi tiết theo thời gian ở `NHAT_KY_RTL.md` (mục R14) và
`asic/FLOW_JOURNAL.md` (phần PD).

## 1. Vì sao là RAM chứ không phải cache, và vì sao 16 KiB

- SoC có **một RAM thống nhất** (AXI backing RAM) chứa code + dữ liệu + 1 KiB stack. Trước R14:
  `IMEM_DEPTH + DMEM_DEPTH = 1024 + 1024` word = **8 KiB**. Cache 4 KiB chỉ là bản đệm của RAM này, nên
  kích thước cache không quyết định được bài nào chạy được; RAM mới quyết định.
- Đo kích thước 19 kernel Embench-IoT gốc (commit 09c2ed8c) với cờ biên dịch của dự án
  (`scripts/embench_fit/build.sh`, kết quả `results/embench_upstream_fit-O2.tsv` / `-Os.tsv`):
  8 KiB chứa được 8 bài, 16 KiB → 14, 32 KiB → 18, 64 KiB → 19 (chưa tính khung báo kết quả của dự án).
- Chọn **16 KiB** (4096 word): phía ASIC chỉ cần 8 macro SRAM 2 KB thay vì 4 (32 KiB cần 16 macro, die
  phải lớn gần gấp rưỡi).
- Sau khi gắn khung báo kết quả của dự án (~2 KB), **12 bài gốc** vừa 16 KiB. nettle-aes và
  sglib-combined vượt ngân sách 15 KiB (16 KiB trừ 1 KiB stack) nên không đưa vào.

## 2. Thay đổi RTL (id đóng băng R14 ban đầu: `535ec0f9`)

| File | Thay đổi |
|---|---|
| `hdl/soc_top.v` | `IMEM_DEPTH`/`DMEM_DEPTH` mặc định 1024 → **2048** |
| `hdl/board/de2_115_top.v` | `IMEM_DEPTH`/`DMEM_DEPTH` mặc định 1024 → **2048** (bản FPGA DE2-115) |
| `hdl/axi/axi_ram_32.v` | `DEPTH_WORDS` mặc định 2048 → **4096** (soc_top vẫn truyền tổng IMEM+DMEM) |
| `asic/soc_dm_4kb/soc_asic_top.v` | `.IMEM_DEPTH(2048)`, `.DMEM_DEPTH(2048)` |
| `asic/soc_dm_4kb/axi_ram_32_asic_macro.v` | RAM ASIC: số bank = `DEPTH_WORDS/512` (**4 → 8** macro `sky130_sram_2kbyte_1rw1r_32x512_8`); độ rộng chọn bank/địa chỉ word suy ra từ tham số (`BANK_BITS`, `WORD_BITS`); kiểm tra lúc elaborate rằng độ sâu là bội lũy thừa 2 của 512; khối nạp chương trình cho mô phỏng ASIC view liệt kê 8 bank và dừng mô phỏng nếu số bank khác 8. FSM đọc/ghi giữ nguyên. |

Không đổi: cache (tag lấy từ địa chỉ 32 bit đầy đủ), bộ giải mã địa chỉ (cửa sổ cacheable 64 KiB đã chứa
16 KiB), pipeline, CPI.

## 3. Thay đổi phần mềm và công cụ

| File | Thay đổi |
|---|---|
| `sw/link.ld` | `LENGTH = 8K` → **16K**; stack (1 KiB) dời từ 0x1C00–0x1FFF lên **0x3C00–0x3FFF** |
| `sw/platform.h` | `RAM_SIZE_BYTES` 8192 → **16384** |
| `sw/fix_hex.py` | `--ram-bytes` mặc định 8192 → 16384 |
| `sw/Makefile` | biến `RAM_BYTES ?= 16384` / `RAM_WORDS`, thay cho hằng 8192 / 2048 ở `rv32hex` và `install_hex` |
| `scripts/fpga/hex_to_mif.py` | `--depth` mặc định 2048 → 4096 |
| `hdl/riscv_full.hex`, `hdl/riscv_full_byte{0..3}.mif` | sinh lại (cachesweep) với độ sâu 4096 |
| `scripts/rtl_manifest.py` | manifest nay phủ cả `sw/` (trước đó chỉ quét `sw_baremetal/`, tên cũ, nên nguồn firmware không nằm trong manifest); bỏ qua sản phẩm build `benchmark*.hex` |
| `scripts/run_ablation.py` | thêm `--fw-dir` (mặc định `fw`) |
| `sw/main_ramsweep.c`, `sw/embench_ramsweep.{c,h}` | **test mới** `ramsweep`: ghi/đọc lại mọi word trống của RAM (word, byte, halfword) để phủ cả 8 bank của RAM ASIC; không phải benchmark |

## 4. Thay đổi kiểm thử

| File | Thay đổi |
|---|---|
| `tb/benchmark_snapshot_tb.sv` | `IMEM_DEPTH`/`DMEM_DEPTH` mặc định 2048 |
| `verification/uvm/tb/tb_soc_top.sv` | `.IMEM_DEPTH(2048)`, `.DMEM_DEPTH(2048)` |
| `verification/uvm/env/core_cfg.sv`, `native_mem_model.sv`, `test/core_smoke_test.sv`, `test/core_random_test.sv` | kích thước RAM của SoC 8192 → 16384 byte |

Giữ nguyên có chủ ý: các test mức AXI (`axi_common.sv`, `axi_smoke_test.sv`) dùng mô hình slave riêng
của UVM, không phải RAM của SoC; các testbench đơn vị tự chọn độ sâu riêng (`mmio_bypass_tb`,
`predictor_axi_tb`, `soc_integration_tb`, `directed_isa_tb`).

## 5. Bộ Embench-IoT gốc (`sw/embench_upstream/`)

- **12 bài** vào bộ: aha-mont64, crc32, depthconv, edn, huffbench, matmult-int, md5sum, nettle-sha256,
  slre, statemate, tarfind, ud. Không vừa: nettle-aes, sglib-combined (vượt 15 KiB khi có khung báo kết
  quả), và nsichneu/picojpeg/qrduino/wikisort (cần 32 KiB), xgboost (64 KiB).
- Build: `make MODE=upstream BENCH=<bài> SCALE=<n>` (sw/Makefile), cài bằng `scripts/build_upstream_fw.sh`
  thành `fw/up_<bài>.hex`; chạy bằng `scripts/run_ablation.py --kernels up_<bài>,...`.
- Thay đổi duy nhất trong mã nguồn gốc: hook `LOCAL_SCALE_FACTOR_OVERRIDE` quanh `LOCAL_SCALE_FACTOR` (giá trị
  gốc vẫn là mặc định). Khung do dự án tự viết: `support.h`, `beebsc.h` (thêm `assert_beebs`),
  `libc_shim.c`, `inc/*.h`, `sw/main_upstream.c`; hàm rand/heap dùng `sw/embench_beebs.c` của dự án (cùng API).
  Không chép `support/` (GPL-3.0) của Embench. `sw/Makefile` thêm biến `LDLIBS` (rỗng mặc định; `-lgcc` ở
  MODE=upstream cho phép chia mềm, vì core là rv32i_zmmul không có DIV).
- SCALE (số vòng đếm, sau 1 vòng làm nóng): aha-mont64 13, crc32 5, depthconv 52, edn 3, huffbench 1,
  matmult-int 1, md5sum 2, nettle-sha256 7, slre 4, statemate 60, tarfind 2, ud 54 (~130k–350k chu kỳ/lần đo
  trên DM). **Không phải điểm Embench chính thức.**
- Giấy phép: 9/12 bài GPL-3.0-or-later → chỉ ở cây nghiên cứu, không công bố cùng dự án (Apache-2.0).
- Kết quả (FPGA view, 4 KiB, `results/upstream_r14_4kb_p1.csv`, lượt 2 trùng khít): tổng chu kỳ DM 1,955,655;
  SA2 +9.65 %, DM_VC4 +10.86 %, DM_DSE +9.76 %. Lưu ý (memory "cache-dse-confound-st-lookup"): bộ điều khiển
  DM ít hơn một trạng thái FSM, nên chênh lệch này KHÔNG chứng minh "DM tốt hơn set-associative" (vd.
  matmult-int: SA2 ít miss hơn — 9,392 so với 10,636 — mà vẫn chậm hơn).

## 6. Sao lưu

Mọi file trước thay đổi: `backups/pre_ram16k_20260929/` (manifest SHA-256 `MANIFEST.sha256`, gồm cả `fw/`).
Tham chiếu kết quả trước thay đổi: `results/ref_pre_r14/`.

## 7. Xác minh

Chuỗi `scripts/run_fullchain_r14.sh` (mọi phép đo chạy 2 lần, so từng trường). **Lượt 3, trên cây đóng băng cuối `3ea52396`: 0 lỗi** (2026-09-29 19:15–21:16, `results/fullchain_r14.log`; lượt 1 và 2 giữ ở `results/fullchain_r14_run1_checkerbug.log`, `fullchain_r14_run2_isainit.log`):

| Giai đoạn | Kết quả |
|---|---|
| Tĩnh | latch 0 (8 tổ hợp), lint_rtl 0 cảnh báo đúng/sai (8 tổ hợp), lint_asic đạt |
| Regression có hướng | 129 PASS × 2 |
| UVM (256 dòng) / AXI (8, 32, 64 B) | 5/5 × 2 / 6/6 |
| Embench 12 bài × 4 cấu hình (FPGA view) | 48/48 × 2, **trùng khít với thiết kế 8 KiB** (`results/ref_pre_r14/`) |
| CoreMark | × 2, trùng khít với thiết kế 8 KiB |
| Random differential 50 seed | 50/50 MATCH × 2, trùng khít cả hash |
| ASIC view (8 bank SRAM) | 12/12 × 2, **trùng khít với ASIC view 4 bank cũ, kể cả chu kỳ**; = FPGA view trên 33 trường; directed ISA 6/6; bộ đồng bộ ASIC × 2 |
| ramsweep (mới) | DM/SA2/DM_VC4/DM_DSE + ASIC view đạt × 2; ASIC = FPGA |
| Embench gốc (mới) | 48/48 FPGA view + 12/12 ASIC view × 2; ASIC = FPGA |

Bằng chứng riêng phần RTL trung tính: RTL mới + ảnh firmware CŨ (layout 8 KiB) → 48/48 trùng khít
(`results/r14_oldfw_4kb.csv`). Ảnh build lại khác ảnh cũ đúng 1 word mỗi bài (`auipc sp,0x2` → `auipc sp,0x4`);
0x1C00 và 0x3C00 cùng chỉ số set ở mọi cache nên kết quả không đổi.

Lỗi gặp và sửa trong lúc xác minh (lỗi của tôi, chuỗi đã bắt được):
1. `tb/asic_view_checker.sv`, `tb/asic_view_checker_isa.sv` so chỉ số word ghi với `addr[12:2]` cố định 11 bit
   → mọi lần ghi trên 0x2000 báo sai. Sửa: `(addr >> 2) & (DEPTH_WORDS - 1)`. Đối chứng âm: wrapper cố tình bỏ bit
   bank cao nhất → bộ kiểm tra bắt ngay (`results/negctl_r14/`).
2. Khối nạp chương trình ASIC view liệt kê 8 bank theo tên → không elaborate được với testbench directed ISA
   (RAM 2048 word = 4 bank). Sửa: mỗi bank tự nạp phần của mình trong vòng generate (mọi số bank).

Đóng băng cuối: manifest `3ea52396` (`results/rtl_manifest_3ea52396.json`); snapshot PD `asic/snapshots/rtl_r14`
(42 file, trùng hash manifest). Quartus × 2 (TAG=r14) chạy trên `hdl/` không đổi từ id 1d584624 (hai lần sửa
trên chỉ chạm `tb/` và khối ASIC_VIEW_SIM của wrapper ASIC).
