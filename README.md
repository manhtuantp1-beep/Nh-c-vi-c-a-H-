# Nhắc việc anh Hà — 2.0.2

Ứng dụng desktop được viết mới từ hướng dẫn sử dụng bản 1.7.0 và yêu cầu bổ sung trong cuộc trao đổi. Đây là dự án mã nguồn mới, không phải mã nguồn khôi phục từ bộ cài cũ. Không kèm công việc cá nhân hoặc dữ liệu mẫu tự nạp vào cơ sở dữ liệu thật.

Ứng dụng quản lý công việc, hiển thị lịch tuần/tháng/năm, tạo lịch lặp, nhắc việc, xuất Excel và sao lưu. Giao diện dùng Python Tkinter; dữ liệu dùng SQLite trong tài khoản hiện tại.

## Giao diện và chữ hiển thị trong 2.0.2

- Khai báo nhận biết DPI trong EXE và khởi tạo trước cửa sổ Tk để tránh Windows phóng ảnh chữ từ một cửa sổ không nhận biết DPI. Cỡ chữ và bố cục lấy DPI thực của cửa sổ lúc mở ứng dụng.
- Thanh điều hướng xanh navy, vùng nội dung trắng và chữ đậm màu. Chữ nội dung 12 pt, tên công việc 13 pt đậm, thông tin phụ 11 pt; ưu tiên Segoe UI trên Windows.
- Công việc hiển thị theo từng hàng gọn: tên và nội dung bên trái, trạng thái, hạn hoàn thành và thao tác bên phải. Ba ô tổng quan cho biết việc chưa bắt đầu, đang làm và quá hạn.
- Bộ lọc và các nút biểu mẫu tự sắp xếp theo chỗ trống. **Bộ lọc +** mở thêm sắp xếp và khoảng ngày; **Dữ liệu và báo cáo** gom các thao tác Excel, sao lưu và khôi phục.
- Lịch Tuần/Tháng/Năm và biểu mẫu giữ nút lưu/đóng ở vùng riêng; nội dung có thể cuộn khi màn hình thấp.

Hướng dẫn chữ hiển thị và nâng cấp: [docs/readability.md](docs/readability.md). Thao tác giao diện: [docs/giao-dien.md](docs/giao-dien.md).

## Tải và cài trên Windows

**[Tải bộ cài Nhắc việc anh Hà 2.0.2 — Windows x64](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/NhacViecAnhHa-Setup-2.0.2-x64.exe)**

Mã nguồn hiện tại là **2.0.2**, dành cho Windows 10/11 x64. Bộ cài đã được dựng và kiểm tra thành công trong [lần dựng Windows 40255800533](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40255800533), rồi [phát hành tại đây](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.2-preview.1). Mã nguồn: [GitHub](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-).

1. Tải bộ cài ở liên kết trên và [SHA256SUMS.txt](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/SHA256SUMS.txt) trong cùng bản phát hành.
2. Đối chiếu SHA256, mở bộ cài và làm theo hướng dẫn. Dùng bộ cài không cần cài Python hoặc NSIS.
3. Mở Nhắc việc anh Hà từ menu Start hoặc trang cuối của bộ cài. Dữ liệu mới nằm riêng tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`.

Nếu đang dùng 2.0.0 hoặc 2.0.1, sao lưu rồi **Thoát hẳn** ứng dụng trước khi chạy bộ cài mới. Cài vào cùng vị trí sẽ dùng lại dữ liệu 2.0.x; không cần khôi phục hoặc nhập lại công việc.

Kích thước bộ cài: 17.114.081 byte. SHA256: `9765523bf93c57e690d77b04d4f8d1c05f6f24cad18ca5f29f747e60071e3e99`.

Bộ cài chưa ký số; Windows có thể hiển thị cảnh báo SmartScreen. Khay hệ thống, thông báo Windows và tự chạy khi đăng nhập cần được kiểm tra thêm trên máy sử dụng thực tế.

Ảnh từ EXE đóng gói trên Windows ở DPI thực của runner: [Danh sách công việc](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768.png) · [Lịch tháng](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/calendar-month-1366x768.png) · [Biểu mẫu công việc](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/task-dialog.png). Xem ảnh trong [hướng dẫn giao diện](docs/giao-dien.md).

Ảnh mô phỏng tỷ lệ font/bố cục Tk: [125%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk120dpi.png) · [150%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk144dpi.png) · [200%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk192dpi.png). Đây là mô phỏng trong ứng dụng, không phải bằng chứng thay đổi Scale của Windows sang từng mức đó.

## Chạy mã nguồn

Cài Python 3.12 trở lên, có Tkinter. Trên Windows, dùng bộ cài Python chính thức và giữ thành phần Tcl/Tk. Mở terminal tại thư mục dự án:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe NhoViec.pyw
```

Trên Linux có Tkinter và màn hình đồ họa:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m nhacviec
```

Tkinter cần phiên desktop hoặc màn hình ảo khi kiểm tra giao diện. Chạy kiểm thử nghiệp vụ không cần màn hình:

```sh
python3 -m unittest discover -s tests -v
```

## Dữ liệu được lưu riêng

Đường dẫn mặc định của bản dựng mới:

```text
%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db
```

Trên Linux, đường dẫn tương ứng là `~/NhacViecAnhHaMoi/data/tasks.db`. Cơ sở dữ liệu được tạo trống lần đầu. Bản mới không ghi vào `~/NhacViecAnhHa/data/tasks.db` của bản 1.7.0. Chức năng khôi phục chỉ nhận bản sao lưu đúng schema của bản dựng mới; chưa có mẫu cơ sở dữ liệu cũ để xác nhận chuyển đổi. Không đổi tên cơ sở dữ liệu bản 1.7.0 rồi chép đè vào bản mới.

## Hai lựa chọn công việc

- **Tất cả việc chưa hoàn thành:** nhóm Cần làm cùng Đang thực hiện, bao gồm việc quá hạn.
- **Chưa bắt đầu:** nhóm Cần làm hiện tại; việc tạm dừng hoặc mở lại cũng trở về nhóm này.
- Việc hoàn thành và hủy có danh sách riêng. Quá hạn là dấu hiệu theo deadline, không tạo thêm công việc trùng.

## Lịch tuần, tháng, năm

Các chế độ xem dùng chung dữ liệu. Lịch có thể diễn ra một lần, lặp hằng tuần, hằng tháng hoặc hằng năm. Lịch tháng/năm lấy ngày của ngày bắt đầu làm mốc lặp. Khi tháng thiếu ngày, chọn về ngày cuối tháng hoặc bỏ qua; quy tắc gốc không bị đổi sau tháng thiếu ngày. Ngày 29/2 được xử lý theo cùng chính sách. Có thể chọn các thứ trong tuần, kết thúc lặp và các mốc nhắc trước.

Mỗi lần diễn ra có kết quả riêng: hoàn thành, bỏ qua hoặc mở lại. Hoàn thành một buổi không dừng chu kỳ lặp. Lịch dùng dương lịch, chưa có lịch âm hoặc quy tắc như “thứ Hai đầu tiên của tháng”.

## Tạo bộ cài Windows

Đóng gói cần **Windows 10/11 64-bit**, **Python 3.13 64-bit** và **NSIS 3.11**. Cài NSIS từ trang chính thức `https://nsis.sourceforge.io/`; nếu máy tổ chức chặn cài đặt, làm việc với IT theo chính sách của máy.

Tại thư mục dự án:

```powershell
powershell -NoProfile -File .\scripts\build_windows.ps1
```

Nếu Python Launcher hoặc NSIS ở vị trí khác:

```powershell
.\scripts\build_windows.ps1 -PythonExe "C:\duong-dan\python.exe" -MakensisPath "C:\Program Files (x86)\NSIS\makensis.exe"
```

Script tạo môi trường `.venv-build`, cài dependency đã ghim phiên bản, chạy `unittest`, tạo EXE bằng PyInstaller, kiểm tra `--self-test` và `--gui-smoke-test` cùng báo cáo JSON, rồi tạo bộ cài NSIS. Kết quả nằm ngay trên máy Windows:

```text
dist\NhacViecAnhHa-Setup-2.0.2-x64.exe
dist\SHA256SUMS.txt
```

Bộ cài chạy theo tài khoản hiện tại, có lựa chọn Desktop và tự chạy khi đăng nhập, không cần quyền quản trị theo cấu hình mặc định. Gỡ cài đặt giữ lại dữ liệu. Bộ cài chưa có chữ ký số; máy áp dụng Application Control có thể cần IT phê duyệt hoặc chữ ký phù hợp.

Trên GitHub, mở Actions → Build Windows installer → Run workflow để dựng lại bộ cài. Workflow chạy cả cài/gỡ im lặng và kiểm tra giữ nguyên tệp dữ liệu đánh dấu trên runner. Artifact của bản 2.0.2 có tên `NhacViecAnhHa-Windows-x64-2.0.2`, chứa bộ cài, checksum và báo cáo tự kiểm tra. Workflow Publish Windows installer xác minh artifact của lần dựng thành công trước khi xuất bản bản phát hành thử nghiệm.

## Phạm vi kiểm tra

**2.0.2**: mã nguồn [897adf3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/897adf34821c12f68951ad75dc2c1ebf9a665362) đã đạt 89 kiểm thử trên Windows; EXE đóng gói đạt kiểm tra nghiệp vụ, GUI và xác nhận PerMonitorV2 của cả tiến trình lẫn cửa sổ. Cùng EXE đó đạt 48 kiểm tra bố cục/ảnh chụp; bộ cài đã qua kiểm tra cài/gỡ, GUI sau cài và giữ nguyên dữ liệu. Bộ 89 kiểm thử và 48 kiểm tra bố cục cũng đạt trên Linux/Xvfb. Các mức Tk tương đương 125%/150%/200% là mô phỏng cỡ chữ và bố cục, tách riêng với DPI thực của màn hình Windows. Xem [phạm vi kiểm tra](docs/kiem-thu.md) và [giải thích DPI](docs/readability.md).

Lịch sử **2.0.1**: mã nguồn [6dc1acf](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/6dc1acf1db2d04e6f9972e11d0fb5801f590496b) đã đạt 77 kiểm thử trên Windows, kiểm tra `--self-test` / `--gui-smoke-test` của EXE, 24 kiểm tra bố cục ở cỡ chữ mặc định và Tk 120 DPI, cùng kiểm tra cài/gỡ giữ nguyên dữ liệu. Xem [lần dựng 39719044251](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719044251) và [chi tiết kiểm thử](docs/kiem-thu.md).

Lịch sử **2.0.0**: mã nguồn [b009740](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/b0097407d3a19f8d5c3e564206af40f9e1531f26) đã đạt 75 kiểm thử trên runner Windows `windows-2022` với Python 3.13 x64 trong [lần dựng 39707130999](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707130999). EXE của bản đó đạt `--self-test` và `--gui-smoke-test`; bộ cài đã qua kiểm tra cài/gỡ im lặng và giữ nguyên dữ liệu đánh dấu. Khay hệ thống, tự chạy khi đăng nhập và thông báo vẫn cần kiểm tra trên máy Windows đích.

Hướng dẫn thao tác: [docs/huong-dan.md](docs/huong-dan.md). Phạm vi yêu cầu và giới hạn: [docs/yeu-cau.md](docs/yeu-cau.md).

Hướng dẫn bố cục và thao tác mới: [docs/giao-dien.md](docs/giao-dien.md).
