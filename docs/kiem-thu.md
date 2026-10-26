# Kết quả kiểm tra mã nguồn và bộ cài

## Bản 2.0.4 — kiểm tra khóa tệp trước khi cập nhật

[Lần dựng Windows 40293108356](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40293108356) đã thành công với mã nguồn [24ac98957eb3eac213cbe18d0556ed92856989eb](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/24ac98957eb3eac213cbe18d0556ed92856989eb). Toàn bộ **116 kiểm thử** đạt, EXE đóng gói vượt qua tự kiểm tra nghiệp vụ/GUI, ma trận **64 kiểm tra bố cục và 65 PNG**. Bộ cài đạt cài/gỡ cơ bản và kiểm tra hồi quy nâng cấp từ đúng bản 2.0.3 đã phát hành.

[Bản phát hành 2.0.4](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.4-preview.1) đã được xuất bản qua [workflow 40294506634](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40294506634), có **14 tệp** và trỏ đúng mã nguồn `24ac98957eb3eac213cbe18d0556ed92856989eb`. Bộ cài tải lại có kích thước **17.139.363 byte**, SHA256 `cf0a834749e0303bac1fbb70bd223b9dfbf0b579eeb6728ef911c0a4494b2653`; đối chiếu `SHA256SUMS.txt` đạt.

Trường hợp người dùng gặp: bộ cài 2.0.3 báo không ghi được `_internal\_sqlite3.pyd` khi cập nhật vào thư mục chương trình cũ. Tệp đang được sử dụng hoặc thư mục không cho ghi đều có thể gây lỗi này. Bản 2.0.4 bổ sung kiểm tra trước khi chép/xóa tệp bằng Windows Restart Manager và kiểm tra quyền ghi, cho phép Thử lại/Hủy mà không tự ép tắt chương trình. Chế độ im lặng phải trả mã lỗi khi chưa thể cập nhật; không coi việc bỏ qua tệp là thành công.

Các tình huống Windows đã đạt trong kiểm tra hồi quy nâng cấp:

- Cài và chạy bản 2.0.3 đã phát hành làm nền kiểm tra, rồi thử nâng cấp khi ứng dụng đó còn giữ thư viện thật.
- Khi bị khóa, bộ cài và bộ gỡ dừng trước khi thay/xóa payload, giữ bản đang cài; không tự kết thúc chương trình.
- Sau khi đóng chương trình giữ tệp, cài lại thành công; ứng dụng cài xong đạt tự kiểm tra nghiệp vụ, GUI và DPI.
- Khóa độc quyền `_sqlite3.pyd` hoặc đặt tệp này chỉ đọc đều khiến bộ cài dừng trước khi thay tệp. Cách chọn lại thư mục chương trình khi thiếu quyền ghi nằm trong hướng dẫn cài đặt.
- Công việc, ghi chú, lịch và cài đặt schema 2 của 2.0.3 tiếp tục dùng được. Không lặp nâng cấp schema khi chuyển 2.0.3 sang 2.0.4; giữ dữ liệu qua cài/gỡ.

Báo cáo [installer-upgrade-test.json](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/installer-upgrade-test.json) tải lại xác nhận `passed=true`, phiên bản 2.0.4 và nền 2.0.3. SHA256 bộ cài nền được ghim là `8f6ea8538fde80905d68083d15717dfa1fa0111ff3d982970f5faa85e1cb3fc4`. Cả **9 tình huống** đạt:

| Tình huống | Kết quả quan sát |
| --- | --- |
| Bản 2.0.3 đang chạy và đã nạp `_sqlite3.pyd` | Bộ cài trả mã 32 trong 122 ms, không dừng ứng dụng |
| Cài bị chặn | Hash toàn bộ tệp chương trình, đăng ký cài đặt và dữ liệu giữ nguyên |
| Khóa độc quyền `_sqlite3.pyd` | Mã 32 trong 108 ms |
| `_sqlite3.pyd` chỉ đọc | Mã 5 |
| Cập nhật sau khi đóng ứng dụng/thả khóa | Mã 0 |
| Ứng dụng sau nâng cấp | Tự kiểm tra nghiệp vụ/GUI đạt, giữ PerMonitorV2 |
| Gỡ khi ứng dụng đang chạy | Mã 32 trong 79 ms, chương trình và dữ liệu giữ nguyên |
| Gỡ sau khi đóng ứng dụng | Mã 0, tệp chương trình được gỡ |
| Dữ liệu đã lưu sau cài/gỡ | Hash giữ nguyên: công việc, ghi chú, lịch, kết quả buổi, cài đặt và lịch sử thông báo |

Các tình huống này chạy **chế độ im lặng** trên Windows; chúng chưa xác nhận thao tác bấm hộp thoại Thử lại/Hủy. Bộ cài có hộp thoại này theo mã nguồn, nhưng kết quả kiểm tra không suy ra việc đã bấm thử.

Báo cáo bố cục của chính EXE đóng gói xác nhận `version=2.0.4`, `frozen=true`, 64 kiểm tra và 65 PNG. Ở pha native, DPI cửa sổ là 96; tiến trình và cửa sổ đều PerMonitorV2. Các pha Tk 120/144/192 DPI chỉ mô phỏng font/bố cục, không xác nhận Scale trên màn hình vật lý ở từng mức. Khay hệ thống, thông báo Windows và tự chạy khi đăng nhập vẫn cần kiểm tra trên máy sử dụng thực tế. Bộ cài chưa ký số.

Cách xử lý khi cài lỗi và vị trí nhật ký: [cài đặt và lỗi ghi tệp](cai-dat.md).

## Lịch sử bản 2.0.3 — lịch theo deadline và ghi chú

Mã nguồn [69da6b32efd7fef51ddeb04f80fcf64da4caa66a](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/69da6b32efd7fef51ddeb04f80fcf64da4caa66a) đã được kiểm tra trên Linux/Xvfb: toàn bộ **116 kiểm thử** đạt, tự kiểm tra nghiệp vụ và GUI đều đạt. Ma trận giao diện đạt **64 kiểm tra** và tạo **65 ảnh PNG** ở hai cỡ cửa sổ logic 1120×720 / 1366×768, pha mặc định cùng các pha Tk 120/144/192 DPI. Kiểm tra bổ sung lịch tháng sáu hàng có dữ liệu đạt 24 tổ hợp bố cục. Lưới lịch tự thu gọn khoảng cách và có thể cuộn khi thiếu chiều cao, giữ vùng công việc theo ngày phía dưới; kiểm thử hồi quy xác nhận nội dung không tràn khung.

Trên Windows, [lần dựng 40289470721](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40289470721) đã thành công với cùng mã nguồn trên. Toàn bộ **116 kiểm thử** đạt; EXE đóng gói vượt qua tự kiểm tra nghiệp vụ, GUI và xác nhận PerMonitorV2 của tiến trình/cửa sổ. Chính EXE đạt **64 kiểm tra bố cục** và tạo **65 PNG**. Bộ cài đạt kiểm tra cài/gỡ tự động, tự kiểm tra nghiệp vụ/GUI và PerMonitorV2 sau cài, đồng thời giữ nguyên các tệp dữ liệu đánh dấu.

Ảnh native được chụp trên runner Windows có màn hình 1920×1080; các cửa sổ thử nghiệm lớn hơn được ghép từ vùng hiển thị thật theo điểm ảnh gốc, không co giãn ảnh. Các mức Tk 120/144/192 DPI vẫn là mô phỏng font/bố cục. [Bản phát hành 2.0.3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.3-preview.1) đã xuất bản thành công qua [workflow 40289806541](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40289806541), từ đúng artifact của mã nguồn `69da6b32efd7fef51ddeb04f80fcf64da4caa66a`. Bản phát hành có **13 tệp**. Bộ cài tải lại có kích thước **17.124.494 byte**, SHA256 `8f6ea8538fde80905d68083d15717dfa1fa0111ff3d982970f5faa85e1cb3fc4`; đối chiếu với `SHA256SUMS.txt` đạt.

Các tình huống được kiểm tra trong mã nguồn, tự kiểm tra EXE và ma trận giao diện:

- Số việc trong lịch khớp tập công việc có deadline đúng ngày, tính mỗi việc một lần và tách số lịch hẹn. Giữ mọi trạng thái để tra cứu.
- Bấm ngày hiển thị cùng thẻ công việc và các thao tác; đổi deadline chuyển việc sang ngày mới; chuyển trạng thái và lưu ghi chú cập nhật chính bản ghi đó.
- Ghi chú nhiều dòng có dấu lưu qua tạo/sửa, cửa sổ ghi chú, Excel và sao lưu/khôi phục; đóng khi chưa lưu giữ đúng quyết định người dùng.
- Nâng cấp cơ sở dữ liệu schema 1 đã kiểm tra lên schema 2, giữ dữ liệu và bản sao trước nâng cấp. Khôi phục sao lưu cũ qua tệp tạm, giữ nguyên tệp nguồn; cơ sở dữ liệu lạ hoặc hỏng bị từ chối.
- Kiểm tra bố cục công việc, lịch, tab lịch hẹn, biểu mẫu và cửa sổ ghi chú ở các cỡ cửa sổ/tỷ lệ font; kiểm tra EXE Windows, cài/gỡ và dữ liệu được giữ lại.

Các liên kết đã xuất bản: [bản phát hành 2.0.3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.3-preview.1), [lịch với công việc theo ngày](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/calendar-tasks-1366x768.png), [ghi chú](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/notes-dialog.png). Ảnh lịch và ghi chú được tải lại, xem trực tiếp để kiểm tra. Báo cáo bố cục xác nhận `version=2.0.3`, `frozen=true`, chương trình `NhacViecAnhHa.exe`, 64 kiểm tra và 65 ảnh; ở pha native, DPI cửa sổ là 96 và cả tiến trình/cửa sổ đều PerMonitorV2. Báo cáo GUI cũng đạt, gồm lưu ghi chú và thẻ việc theo deadline.

Lệnh kiểm tra trên Linux với màn hình ảo:

```sh
DISPLAY=:99 python -m unittest discover -s tests -v
python -m nhacviec --self-test --self-test-report /tmp/nhacviec-2.0.3-core.json
DISPLAY=:99 python -m nhacviec --gui-smoke-test --self-test-report /tmp/nhacviec-2.0.3-gui.json
DISPLAY=:104 python -m nhacviec --capture-ui /tmp/nhacviec-2.0.3-ui
```

Tự kiểm tra nghiệp vụ đã xác nhận ghi chú có dấu qua lưu trữ, Excel và sao lưu/khôi phục. Tự kiểm tra GUI đã xác nhận thẻ việc theo deadline ở cả ba chế độ lịch và sửa ghi chú từ cửa sổ thật. Các kiểm thử tích hợp còn kiểm tra luồng tạo việc từ ngày đang chọn, cập nhật deadline, thao tác trạng thái và bảo vệ ghi chú chưa lưu khi thoát.

Các pha Tk tương đương 125%/150%/200% mô phỏng font và bố cục ứng dụng; không xác nhận các mức Scale trên màn hình Windows vật lý. Khay hệ thống, thông báo Windows và tự chạy khi đăng nhập vẫn cần kiểm tra thêm trên máy sử dụng thực tế. Bộ cài chưa ký số.

## Lịch sử bản 2.0.2 — DPI và khả năng đọc

Ngày 26/10/2026: bản 2.0.2 đã đạt toàn bộ 89 kiểm thử trên Linux/Xvfb. Lệnh `python -m nhacviec --capture-ui` đạt 48 kiểm tra bố cục và tạo 48 ảnh PNG qua pha tỷ lệ mặc định cùng các pha Tk 120/144/192 DPI.

Trên Windows, [lần dựng 40255800533](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40255800533) đã thành công với mã nguồn [897adf34821c12f68951ad75dc2c1ebf9a665362](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/897adf34821c12f68951ad75dc2c1ebf9a665362). Toàn bộ 89 kiểm thử đạt; EXE đóng gói vượt qua tự kiểm tra nghiệp vụ và GUI, xác nhận cả tiến trình lẫn cửa sổ thực đang ở chế độ PerMonitorV2. Cùng EXE tạo 48 ảnh và vượt qua 48 kiểm tra bố cục ở pha DPI thực khi khởi động cùng các pha Tk 120/144/192 DPI. Báo cáo đã xuất bản xác nhận `frozen=true`, ứng dụng `NhacViecAnhHa.exe` và DPI thực của cửa sổ trên runner là 96. Kiểm tra cài/gỡ im lặng đã đạt, bao gồm tự kiểm tra nghiệp vụ, GUI và PerMonitorV2 của ứng dụng sau cài, cùng việc giữ nguyên các tệp dữ liệu đánh dấu.

Ảnh được chụp từ EXE đóng gói qua Win32 PrintWindow. Với cửa sổ thử nghiệm lớn hơn màn hình runner 1920×1080, công cụ ghép các phần hiển thị thực của cùng cửa sổ theo điểm ảnh gốc, không co giãn ảnh; trường `capture_method` trong báo cáo ghi rõ phương thức này.

Manifest trích từ chính EXE ứng dụng trong bộ cài đã phát hành xác nhận `dpiAware=true/pm`, `dpiAwareness=PerMonitorV2,PerMonitor` và `gdiScaling=false`. Đây là đối chiếu tệp nhị phân phát hành, bổ sung cho trạng thái DPI được đo khi EXE chạy.

[Bản phát hành 2.0.2](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.2-preview.1) đã được xuất bản từ artifact đã kiểm chứng qua [workflow phát hành 40256024229](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40256024229). Bản phát hành có 11 tệp, gồm bộ cài, SHA256, báo cáo nghiệp vụ/GUI/bố cục và các ảnh Windows. Bộ cài có kích thước 17.114.081 byte, SHA256 `9765523bf93c57e690d77b04d4f8d1c05f6f24cad18ca5f29f747e60071e3e99`. Ảnh gốc và ảnh mô phỏng của 2.0.2 được giữ trong Assets của bản phát hành nêu trên.

Các lệnh kiểm tra Linux: bộ kiểm thử chạy trên Xvfb `:99`; ma trận ảnh chạy trên Xvfb `:104` kích thước 3840×2160 để chứa đủ cửa sổ mô phỏng 200%:

```sh
DISPLAY=:99 python -m unittest discover -s tests -v
DISPLAY=:104 python -m nhacviec --capture-ui /tmp/nhacviec-2.0.2-ui
```

Ma trận bố cục mới tách pha DPI thực của cửa sổ khi khởi động và các pha thay đổi tỷ lệ font/bố cục Tk tương đương 125% (120 DPI), 150% (144 DPI), 200% (192 DPI). Các pha Tk mô phỏng không đổi thiết lập hiển thị Windows và không xác nhận ứng dụng đã chạy trên màn hình vật lý ở từng tỷ lệ đó. Chuyển một cửa sổ đang mở qua các màn hình có DPI khác nhau chưa được xác nhận hỗ trợ tự đổi kích thước.

Các kiểm tra GUI và chụp ảnh của EXE bắt buộc tiến trình/cửa sổ thật ở chế độ PerMonitorV2; chúng ghi DPI của cửa sổ và tỷ lệ Tk vào báo cáo. Kiểm tra mã nguồn hoặc mô phỏng API được tách riêng khỏi bằng chứng chạy EXE này. Chi tiết thay đổi và nâng cấp: [readability.md](readability.md).

## Lịch sử bản 2.0.1

Ngày 22/10/2026: bản 2.0.1 đạt 77 kiểm thử trên Linux/Xvfb, hai kiểm tra ứng dụng `--self-test` / `--gui-smoke-test`, cùng 24 kiểm tra bố cục và 24 ảnh chụp ở 1120×720, 1366×768, cỡ chữ mặc định và Tk 120 DPI. Các kiểm tra hồi quy mới xác nhận văn bản dài không bị cắt khi thay đổi kích thước và nút lưu luôn hiển thị khi cuộn biểu mẫu.

Trên Windows, [lần dựng GitHub Actions 39719044251](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719044251) đã thành công với mã nguồn [6dc1acf1db2d04e6f9972e11d0fb5801f590496b](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/6dc1acf1db2d04e6f9972e11d0fb5801f590496b), runner `windows-2022` và Python 3.13 x64. Lần dựng đã chạy đạt 77 kiểm thử, tạo EXE bằng PyInstaller và chạy thành công hai kiểm tra `--self-test` / `--gui-smoke-test` của EXE. Kiểm tra giao diện đạt 24 tình huống bố cục ở cỡ chữ mặc định và Tk 120 DPI. Bộ cài NSIS đã qua kiểm tra cài/gỡ im lặng, chạy tự kiểm tra sau khi cài và giữ nguyên các tệp dữ liệu đánh dấu.

[Bản phát hành Windows 2.0.1](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.1-preview.1) đã được xuất bản từ artifact đã kiểm chứng qua [workflow phát hành 39719246638](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719246638). Bản phát hành có tám tệp, gồm bộ cài, SHA256, báo cáo kiểm tra và ảnh giao diện Windows. Bộ cài `NhacViecAnhHa-Setup-2.0.1-x64.exe` có kích thước 17.070.511 byte, SHA256 `4590f51fd53842366c219f12613a79fd47dbf3986c52211408575cb93e3da38c`.

Các kết quả này xác nhận quá trình dựng và các kiểm tra tự động; khay hệ thống, thông báo Windows và tự chạy khi đăng nhập vẫn cần kiểm tra trên máy sử dụng thực tế. Bộ cài chưa ký số.

Ảnh giao diện Windows đã được xác minh trong [lần chụp 39720076183](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39720076183): 24 ảnh đầy đủ và 24 kiểm tra bố cục đạt, dùng màn hình runner 1920×1080 và cửa sổ 1120×720 / 1366×768, ở cỡ chữ mặc định và Tk 120 DPI. Workflow xác nhận mã ứng dụng và dependency trùng với bản dựng đã kiểm thử trước khi cập nhật ảnh và báo cáo trên Releases. Bộ cài và mã SHA256 giữ nguyên.

## Lịch sử bản 2.0.0

Ngày kiểm tra gần nhất: 22/10/2026. Trên Windows, [lần dựng GitHub Actions 39707130999](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707130999) đã thành công với mã nguồn [b0097407d3a19f8d5c3e564206af40f9e1531f26](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/b0097407d3a19f8d5c3e564206af40f9e1531f26), runner `windows-2022`, Python 3.13 x64 và dependency đã ghim trong `requirements-build.txt`.

Lịch sử Linux: Python 3.12.14, Tk 9.0.4 trên màn hình ảo Xvfb. Ngày 21/10 đã kiểm tra trong môi trường riêng với dependency ghim trong `requirements.txt`: openpyxl 3.1.5, et-xmlfile 2.0.0, Pillow 11.3.0. Lần kiểm tra lại 22/10 dùng runtime hiện có: openpyxl 3.1.5, Pillow 12.3.0.

Bộ kiểm thử dưới đây đã đạt đầy đủ trên Linux/Xvfb và trong lần dựng Windows nêu trên:

| Nhóm | Đạt | Bỏ qua | Thất bại |
| --- | ---: | ---: | ---: |
| SQLite, lịch lặp, nhắc việc, Excel | 47 | 0 | 0 |
| Giao diện lịch và chọn ngày | 10 | 0 | 0 |
| Giao diện công việc và tích hợp cửa sổ chính | 7 | 0 | 0 |
| Khóa một phiên, adapter khay và thông báo | 11 | 0 | 0 |
| Tổng | 75 | 0 | 0 |

Các kiểm tra GUI dùng widget Tkinter thật và cơ sở dữ liệu tạm. Kiểm tra adapter Windows dùng đối tượng thay thế có kiểm soát; chúng không xác nhận khay hoặc thông báo trên Windows thật.

Lệnh đã chạy trên Linux từ thư mục gốc dự án:

```sh
DISPLAY=:99 python -m unittest discover -s tests -v
python -m nhacviec --self-test --self-test-report /tmp/nhacviec-final-core.json
DISPLAY=:99 python -m nhacviec --gui-smoke-test --self-test-report /tmp/nhacviec-final-gui.json
```

`--self-test` đạt 4 nhóm kiểm tra: công việc và hai bộ lọc; lịch tháng/năm với ngày thiếu; báo cáo Excel và bảng dữ liệu; sao lưu/khôi phục. `--gui-smoke-test` đạt thêm kiểm tra cửa sổ công việc và chuyển Tuần/Tháng/Năm. Mọi phép kiểm tra dùng dữ liệu tạm, không chứa công việc cá nhân và không ghi vào dữ liệu bản 1.7.0.

Các tình huống hồi quy đã kiểm tra gồm việc tạm dừng/mở lại trong nhóm Cần làm, đổi trạng thái không đổi bộ lọc đang chọn, giữ biểu mẫu chưa lưu khi hủy yêu cầu đóng, ngày 31 không bị lệch sau tháng 2, ngày 29/2, nhắc không trùng sau khởi động lại, không gửi dồn buổi đã hết giờ, sửa lịch không tạo thêm buổi quá khứ, bật lại không tạo bù thời gian tạm dừng, sao lưu nhất quán và từ chối cơ sở dữ liệu khác schema.

Lần dựng Windows đã chạy đạt 75 kiểm thử, tạo EXE bằng PyInstaller 6.16.0, chạy thành công `--self-test` và `--gui-smoke-test` của EXE, rồi tạo bộ cài bằng NSIS 3.11. Kiểm tra cài đặt/gỡ cài đặt im lặng đã đạt; EXE sau khi cài vượt qua tự kiểm tra và các tệp dữ liệu đánh dấu trong thư mục của cả bản mới lẫn bản 1.7.0 được giữ nguyên. Hai báo cáo JSON và SHA256 được lưu cùng bộ cài trong artifact.

[Bản phát hành thử nghiệm Windows 2.0.0](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.0-preview.1) đã được xuất bản từ artifact của lần dựng này qua [workflow phát hành 39707344668](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707344668). Bản phát hành có bốn tệp: bộ cài, `SHA256SUMS.txt`, `self-test.json` và `gui-smoke-test.json`. Bộ cài có kích thước 17.048.630 byte, SHA256 `5abf9b9ab560b3a58ad1c4e9a394de3664de6fe382d27a29e6e481cb9e4c8cef`.

Chưa kiểm tra khay hệ thống, thông báo Windows và tự chạy khi đăng nhập trên máy sử dụng thực tế. Bộ cài chưa ký số. Chưa có mẫu cơ sở dữ liệu 1.7.0 để viết và kiểm thử chuyển đổi dữ liệu cũ.

Cập nhật 22/10: đóng kết nối SQLite đích trước khi đổi tên tệp sao lưu, tránh lỗi khóa tệp trên Windows. Thêm kiểm thử mô phỏng quy tắc khóa tệp của Windows; đóng tường minh các kết nối SQLite trong fixture kiểm thử. Bộ 75 kiểm thử chạy đạt đầy đủ trên Linux/Xvfb, không có ca bỏ qua. Kiểm thử ứng dụng `--self-test` cũng đạt 4 nhóm kiểm tra.
