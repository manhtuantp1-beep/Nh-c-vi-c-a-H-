# Nhắc việc anh Hà — 2.0.4

Ứng dụng desktop được viết mới từ hướng dẫn sử dụng bản 1.7.0 và yêu cầu bổ sung trong cuộc trao đổi. Đây là dự án mã nguồn mới, không phải mã nguồn khôi phục từ bộ cài cũ. Không kèm công việc cá nhân hoặc dữ liệu mẫu tự nạp vào cơ sở dữ liệu thật.

Ứng dụng quản lý công việc, hiển thị lịch tuần/tháng/năm, tạo lịch lặp, nhắc việc, xuất Excel và sao lưu. Giao diện dùng Python Tkinter; dữ liệu dùng SQLite trong tài khoản hiện tại.

## Cài nâng cấp khi ứng dụng đang chạy

Bản 2.0.4 bổ sung kiểm tra trước khi chép tệp: phát hiện chương trình đang giữ tệp bằng Windows Restart Manager và kiểm tra quyền ghi thư mục. Khi chưa thể cập nhật, bộ cài dừng để anh đóng ứng dụng rồi Thử lại hoặc Hủy, thay vì bắt đầu chép một phần. Bộ gỡ cũng kiểm tra trước khi xóa tệp. Chế độ im lặng trả lỗi khi điều kiện chưa đạt; bộ cài không tự ép tắt ứng dụng.

Nếu bộ cài 2.0.3 đang báo không ghi được `_internal\_sqlite3.pyd`, chọn **Abort/Hủy**, lưu nội dung rồi **Thoát hẳn** ứng dụng và chạy lại bộ cài. Nếu không mở được ứng dụng, dùng Task Manager để kết thúc đúng `NhacViecAnhHa.exe` rồi thử lại. Xem [hướng dẫn xử lý từng bước](docs/cai-dat.md).

## Công việc theo deadline và ghi chú

Các tính năng từ 2.0.3 được giữ lại:

- Lịch Tuần/Tháng/Năm tự tổng hợp công việc theo **ngày deadline**. Số việc và số lịch hẹn hiển thị riêng, tránh nhầm một việc với một buổi lịch.
- Bấm ngày để xem tab **Công việc** với cùng thẻ thông tin và các nút Chi tiết, Ghi chú, Bắt đầu, Hoàn thành hoặc Mở lại như trang công việc. Lịch giữ mọi trạng thái, gồm cả đã hoàn thành và đã hủy, để tra cứu; mỗi thẻ ghi rõ trạng thái.
- Mỗi việc có **Ghi chú** riêng để lưu tiến độ và điều cần chú ý. Có thể sửa nhanh bằng nút Ghi chú hoặc sửa trong Chi tiết; ghi chú đi cùng dữ liệu sao lưu và báo cáo Excel.
- Tab **Lịch hẹn** giữ các buổi một lần/lặp, kết quả từng buổi và thao tác nhắc sau.
- Giữ cách hiển thị DPI từ 2.0.2: thanh điều hướng navy, chữ nội dung 12 pt, tên việc 13 pt đậm và thông tin phụ 11 pt, ưu tiên Segoe UI trên Windows.

Hướng dẫn thao tác và nâng cấp: [docs/giao-dien.md](docs/giao-dien.md). Chi tiết chữ và DPI: [docs/readability.md](docs/readability.md).

## Tải và cài trên Windows

**Bộ cài 2.0.4 đã đạt [kiểm tra Windows và nâng cấp từ 2.0.3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40293108356), [được phát hành](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.4-preview.1) và tải lại để đối chiếu SHA256.**

**[Tải bộ cài Nhắc việc anh Hà 2.0.4 — Windows x64](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/NhacViecAnhHa-Setup-2.0.4-x64.exe)** · [Trang phát hành](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.4-preview.1)

Mã nguồn hiện tại là **2.0.4**, dành cho Windows 10/11 x64. [Mã nguồn GitHub](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-).

1. Tải bộ cài và [SHA256SUMS.txt](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/SHA256SUMS.txt) của cùng bản.
2. Lưu công việc hoặc ghi chú đang sửa, sao lưu rồi **Thoát hẳn** ứng dụng. Dấu X chỉ thu nhỏ và chưa đủ để cập nhật.
3. Đối chiếu SHA256, mở bộ cài và làm theo hướng dẫn. Nếu bộ cài yêu cầu đóng chương trình, đóng chương trình được nêu rồi Thử lại; chọn Hủy nếu cần giữ công việc đang mở.
4. Mở Nhắc việc anh Hà từ menu Start hoặc trang cuối của bộ cài. Dùng bộ cài không cần cài Python hoặc NSIS.

Dữ liệu vẫn nằm tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`, tách khỏi thư mục chương trình. **Từ 2.0.3 lên 2.0.4 không đổi schema và không nâng cấp lại dữ liệu.** Nếu đang dùng 2.0.0–2.0.2, lần mở đầu kiểm tra dữ liệu, giữ bản `tasks.pre-upgrade-<ngày-giờ>.db` cùng thư mục và nâng cấp lên schema 2 để thêm ghi chú. Sau nâng cấp, tiếp tục dùng **2.0.3 trở lên**; bản 2.0.2 trở về trước không đọc schema mới.

Mã nguồn đã kiểm thử: [24ac989](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/24ac98957eb3eac213cbe18d0556ed92856989eb). Kích thước bộ cài **17.139.363 byte**, SHA256 `cf0a834749e0303bac1fbb70bd223b9dfbf0b579eeb6728ef911c0a4494b2653`. Tệp tải lại khớp `SHA256SUMS.txt`. Bằng chứng của 2.0.3 và các bản trước được giữ trong [phạm vi kiểm tra](docs/kiem-thu.md).

Bộ cài chưa ký số. Khay hệ thống, thông báo Windows và tự chạy khi đăng nhập cần được kiểm tra thêm trên máy sử dụng thực tế. [Cách xử lý lỗi ghi tệp khi cài](docs/cai-dat.md).

Ảnh từ EXE Windows 2.0.4: [Công việc](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/tasks-1366x768.png) · [Lịch theo ngày](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/calendar-tasks-1366x768.png) · [Ghi chú](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/notes-dialog.png). Ảnh dùng dữ liệu minh họa tạm thời; báo cáo EXE xác nhận 64 kiểm tra bố cục và 65 PNG, DPI thực của cửa sổ ở pha native là 96.

Ảnh mô phỏng font/bố cục Tk: [125%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/tasks-1366x768-tk120dpi.png) · [150%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/tasks-1366x768-tk144dpi.png) · [200%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/tasks-1366x768-tk192dpi.png). Mô phỏng trong ứng dụng không xác nhận Windows đã đổi Scale sang từng mức đó.

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

Trên Linux, đường dẫn tương ứng là `~/NhacViecAnhHaMoi/data/tasks.db`. Cơ sở dữ liệu được tạo trống lần đầu. Bản mới không ghi vào `~/NhacViecAnhHa/data/tasks.db` của bản 1.7.0. Chức năng khôi phục nhận cơ sở dữ liệu hợp lệ của bản dựng mới, gồm schema 1 từ 2.0.0–2.0.2 và schema 2 từ 2.0.3. Bản sao schema 1 được đọc, kiểm tra và nâng cấp trên tệp tạm trước khi thay dữ liệu hiện tại; tệp nguồn không bị sửa. Chưa có mẫu cơ sở dữ liệu 1.7.0 để xác nhận chuyển đổi. Không đổi tên cơ sở dữ liệu bản 1.7.0 rồi chép đè vào bản mới.

## Hai lựa chọn công việc

- **Tất cả việc chưa hoàn thành:** nhóm Cần làm cùng Đang thực hiện, bao gồm việc quá hạn.
- **Chưa bắt đầu:** nhóm Cần làm hiện tại; việc tạm dừng hoặc mở lại cũng trở về nhóm này.
- Việc hoàn thành và hủy có danh sách riêng. Quá hạn là dấu hiệu theo deadline, không tạo thêm công việc trùng.

## Lịch tuần, tháng, năm

Các chế độ xem dùng chung công việc theo ngày deadline và các lịch hẹn. Số công việc trên một ngày gồm Cần làm, Đang thực hiện, Đã hoàn thành và Đã hủy; chuyển trạng thái không tạo thêm mục. Đổi deadline sẽ chuyển việc sang ngày mới. Bấm ngày để xem thông tin và thao tác trên chính công việc đang có; không cần tạo thêm lịch hẹn.

Lịch hẹn có thể diễn ra một lần, lặp hằng tuần, hằng tháng hoặc hằng năm. Lịch tháng/năm lấy ngày của ngày bắt đầu làm mốc lặp. Khi tháng thiếu ngày, chọn về ngày cuối tháng hoặc bỏ qua; quy tắc gốc không bị đổi sau tháng thiếu ngày. Ngày 29/2 được xử lý theo cùng chính sách. Có thể chọn các thứ trong tuần, kết thúc lặp và các mốc nhắc trước.

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
dist\NhacViecAnhHa-Setup-2.0.4-x64.exe
dist\SHA256SUMS.txt
```

Bộ cài chạy theo tài khoản hiện tại, có lựa chọn Desktop và tự chạy khi đăng nhập, không cần quyền quản trị theo cấu hình mặc định. Gỡ cài đặt giữ lại dữ liệu. Bộ cài chưa có chữ ký số; máy áp dụng Application Control có thể cần IT phê duyệt hoặc chữ ký phù hợp.

Trên GitHub, mở Actions → Build Windows installer → Run workflow để dựng lại bộ cài. Workflow chạy cả cài/gỡ im lặng và kiểm tra giữ nguyên tệp dữ liệu đánh dấu trên runner. Artifact của bản 2.0.4 có tên `NhacViecAnhHa-Windows-x64-2.0.4`, chứa bộ cài, checksum và báo cáo tự kiểm tra. Workflow Publish Windows installer xác minh artifact của lần dựng thành công trước khi xuất bản bản phát hành thử nghiệm.

## Phạm vi kiểm tra

**2.0.4**: [lần dựng Windows 40293108356](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40293108356) đạt 116 kiểm thử, tự kiểm tra EXE/GUI, 64 kiểm tra bố cục/65 PNG, cài/gỡ và kiểm tra nâng cấp từ bản 2.0.3 đã phát hành khi thư viện đang bị giữ. Bộ cài/gỡ dừng trước khi thay tệp bị khóa, thành công sau khi đóng chương trình; dữ liệu được giữ. Báo cáo [9 tình huống nâng cấp](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/installer-upgrade-test.json) đạt, gồm mã 32 khi bản cũ đang chạy hoặc thư viện bị khóa, mã 5 khi thư viện chỉ đọc và mã 0 sau khi đóng. [Lần xuất bản 40294506634](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40294506634) tạo 14 tệp; bộ cài tải lại khớp SHA256. Xem [chi tiết](docs/kiem-thu.md).

Lịch sử **2.0.3**: mã nguồn [69da6b3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/69da6b32efd7fef51ddeb04f80fcf64da4caa66a) đạt toàn bộ 116 kiểm thử trên Linux/Xvfb, tự kiểm tra nghiệp vụ và GUI, cùng 64 kiểm tra bố cục/65 ảnh PNG. Ma trận lịch tháng sáu hàng có dữ liệu đạt 24 tổ hợp. [Lần dựng Windows 40289470721](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40289470721) cũng đạt 116 kiểm thử, tự kiểm tra EXE/GUI/PerMonitorV2, 64 kiểm tra bố cục/65 PNG và cài/gỡ giữ dữ liệu. [Bản phát hành](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.3-preview.1) có 13 tệp; bộ cài tải lại khớp SHA256. Xem [lần xuất bản 40289806541](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40289806541). Xem [kết quả kiểm tra](docs/kiem-thu.md).

Lịch sử **2.0.2**: mã nguồn [897adf3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/897adf34821c12f68951ad75dc2c1ebf9a665362) đã đạt 89 kiểm thử trên Windows; EXE đóng gói đạt kiểm tra nghiệp vụ, GUI và xác nhận PerMonitorV2 của cả tiến trình lẫn cửa sổ. Cùng EXE đó đạt 48 kiểm tra bố cục/ảnh chụp; bộ cài đã qua kiểm tra cài/gỡ, GUI sau cài và giữ nguyên dữ liệu. Bộ 89 kiểm thử và 48 kiểm tra bố cục cũng đạt trên Linux/Xvfb. Các mức Tk tương đương 125%/150%/200% là mô phỏng cỡ chữ và bố cục, tách riêng với DPI thực của màn hình Windows. Xem [phạm vi kiểm tra](docs/kiem-thu.md) và [giải thích DPI](docs/readability.md).

Lịch sử **2.0.1**: mã nguồn [6dc1acf](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/6dc1acf1db2d04e6f9972e11d0fb5801f590496b) đã đạt 77 kiểm thử trên Windows, kiểm tra `--self-test` / `--gui-smoke-test` của EXE, 24 kiểm tra bố cục ở cỡ chữ mặc định và Tk 120 DPI, cùng kiểm tra cài/gỡ giữ nguyên dữ liệu. Xem [lần dựng 39719044251](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719044251) và [chi tiết kiểm thử](docs/kiem-thu.md).

Lịch sử **2.0.0**: mã nguồn [b009740](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/b0097407d3a19f8d5c3e564206af40f9e1531f26) đã đạt 75 kiểm thử trên runner Windows `windows-2022` với Python 3.13 x64 trong [lần dựng 39707130999](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707130999). EXE của bản đó đạt `--self-test` và `--gui-smoke-test`; bộ cài đã qua kiểm tra cài/gỡ im lặng và giữ nguyên dữ liệu đánh dấu. Khay hệ thống, tự chạy khi đăng nhập và thông báo vẫn cần kiểm tra trên máy Windows đích.

Hướng dẫn thao tác: [docs/huong-dan.md](docs/huong-dan.md). Phạm vi yêu cầu và giới hạn: [docs/yeu-cau.md](docs/yeu-cau.md).

Hướng dẫn bố cục và thao tác mới: [docs/giao-dien.md](docs/giao-dien.md).
