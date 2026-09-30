# Báo cáo: máy tính đang làm hỏng dữ liệu

*Đo ngày 2026-09-18. Viết cho người sử dụng máy và cho thợ sửa máy, nếu cần mang đi.*

---

## Kết luận ngắn

Chiếc máy này **vừa gây crash ngẫu nhiên, vừa sinh ra dữ liệu sai mà không
crash**. Nghi phạm gần như chắc chắn là RAM: hai thanh DDR5 không cùng mã đang
chạy cặp ở 4800 MT/s.

Đây không phải lỗi của OpenLane, GCC, Quartus hay VS Code. Cả bốn đã bị đổ oan
riêng lẻ trong nhiều tuần.

---

## Bằng chứng 1 — một vòng lặp 40 dòng cho ra kết quả sai

Chương trình thử chỉ tạo các bộ ba `(i, str(i), i*3)` rồi kiểm tra lại chính nó.
Không dùng thư viện gì, không đọc file, không mạng. Nó **không thể sai** trừ khi
máy tính tính sai.

Chạy 8 lần mỗi môi trường:

| Môi trường | Sạch | Ghi chú |
|---|---|---|
| Probe OpenROAD/odb (bước PD đang kẹt) | 0/8 | |
| Python **của OpenROAD**, bỏ odb ra | 1/8 | 2 lần **dữ liệu sai** |
| Python3 hệ thống trong WSL | 1/8 | 3 lần **dữ liệu sai** |
| Python 3.11 **Windows**, ngoài WSL | 5/8 | 3 lần lỗi `0xC0000005` |

Ba trình thông dịch khác nhau. Hai hệ điều hành. Một cỗ máy.

**Phần nguy hiểm nhất:** những lần ghi "dữ liệu sai" **không hề crash**. Chương
trình chạy xong bình thường và trả ra giá trị sai. Chỉ vì tôi cho nó tự kiểm tra
nên mới lộ. Một công cụ bình thường sẽ im lặng ghi kết quả sai vào file.

Cách chạy lại: `research/asic/probe_pure_python.py` — mất 2 phút, không cần cài gì.

---

## Bằng chứng 2 — Windows đã ghi nhận sẵn, 45 ngày qua

```
9 lần   tắt máy bất thường (Kernel-Power 41)   — gần nhất: 18/09 lúc 13:19
4 lần   bugcheck 0x1E KMODE_EXCEPTION_NOT_HANDLED, tham số 0xC0000005
2 lần   bugcheck 0x50 PAGE_FAULT_IN_NONPAGED_AREA
```

`0x50 PAGE_FAULT_IN_NONPAGED_AREA` là mã dừng kinh điển của RAM lỗi.
`0xC0000005` là ACCESS_VIOLATION — đúng mã mà Python trên Windows trả về ở trên.

---

## Bằng chứng 3 — trình biên dịch GCC tự sập ở chỗ khác nhau mỗi lần

Khi build thư viện `lemon-graph`, GCC báo "internal compiler error":

| Lần build | File đang dịch | Pass tối ưu đang chạy |
|---|---|---|
| 1 | `test/maps_test.cc` | `pass_copy_prop` |
| 2 | `adaptors_test`, `unionfind_test` | `pass_ccp` |

Nếu đây là lỗi của GCC thì nó phải sập **đúng một chỗ** mọi lần. Sập chỗ khác
nhau nghĩa là không phải lỗi phần mềm.

---

## Bằng chứng 4 — Quartus, đã nghi oan từ lâu

Ghi chú của dự án từ 16/09 có dòng: *"crash Access Violation ngẫu nhiên ~8%
(cả quartus_fit lẫn quartus_map), cứ thử lại là qua"*, 3/36 lần build hỏng.

Nó chưa bao giờ là đặc tính của Quartus. Và **"cứ thử lại là qua" là lời khuyên
sai lầm nguy hiểm**, vì RAM này còn cho ra kết quả sai mà không crash — thử lại
không cứu được trường hợp đó.

---

## Phần cứng

```
BANK 0   16 GB   DDR5-4800   SK Hynix   HMCG78AEBSA095N
BANK 0   16 GB   DDR5-4800   SK Hynix   HMCG78MEBSA092N
```

**Hai thanh khác mã part.** Tổng 31.6 GB. Chạy chung một cặp ở 4800 MT/s.

DDR5 rất nhạy với việc ghép thanh không cùng lô: bộ điều khiển bộ nhớ phải áp
một bộ timing chung cho hai thanh có đặc tính khác nhau. Đây là nghi phạm số một,
và cũng là thứ dễ thử nhất vì không tốn tiền.

---

## Cần làm gì, theo thứ tự

Sau **mỗi** bước, chạy `research/asic/probe_pure_python.py` 8 lần. Đạt 8/8 là xong,
không cần làm bước sau.

**1. Vào BIOS, tắt XMP / EXPO / DOCP.** Để RAM về tốc độ JEDEC mặc định
(thường 4000 hoặc 4400 thay vì 4800). Mất 5 phút, không rủi ro, và là nguyên nhân
khả dĩ nhất khi ghép hai thanh khác mã.

**2. Nếu vẫn lỗi: rút bớt còn một thanh.** Chạy probe. Rồi đổi sang thanh kia,
chạy lại. Thanh nào cho 8/8 là thanh tốt — thanh còn lại là thanh hỏng, đem bảo
hành. Nếu **cả hai** thanh đều 8/8 khi chạy riêng thì vấn đề là việc ghép cặp,
quay lại bước 1 hoặc dùng một thanh cho tới khi mua được cặp cùng lô.

**3. Xác nhận cuối bằng MemTest86** (USB boot) chạy qua đêm.

---

## Ảnh hưởng tới số liệu của dự án

Nguyên tắc: **một con số chỉ đáng tin nếu có lần chạy độc lập khác tái hiện đúng nó.**
Hỏng bộ nhớ ngẫu nhiên gần như không thể lặp lại y hệt hai lần.

| Kết quả | Tình trạng |
|---|---|
| Ma trận 48-run, config 1/2/3 trùng khớp 48/48 | tự nhất quán — **giữ** |
| 3 fit Quartus đã chạy lại và tái hiện chính xác | **giữ** |
| DM four-seed sweep | nhiều điểm — **giữ** |
| Sweep `L0_ENTRIES` (13.875 / 13.465 LE) | mỗi mức **một** fit — **phải chạy lại** |
| 4 điểm Quartus 4 KB | chưa chạy |
| Detailed routing "0 DRC violations" | một lần chạy — cần xác nhận lại |

Trong lúc chưa sửa máy, quy trình bù lại rủi ro là: **mọi số đưa vào báo cáo
phải có hai lần chạy độc lập cho ra cùng kết quả.** Chậm hơn, nhưng không phải
dừng công việc lại chờ sửa phần cứng.
