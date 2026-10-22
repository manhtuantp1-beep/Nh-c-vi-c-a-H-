# Nhắc việc anh Hà — mã nguồn dựng mới 2.0.0

Ứng dụng desktop được viết mới từ hướng dẫn sử dụng bản 1.7.0 và yêu cầu bổ sung trong cuộc trao đổi. Đây là dự án mã nguồn mới, không phải mã nguồn khôi phục từ bộ cài cũ. Không kèm công việc cá nhân hoặc dữ liệu mẫu tự nạp vào cơ sở dữ liệu thật.

Ứng dụng quản lý công việc, hiển thị lịch tuần/tháng/năm, tạo lịch lặp, nhắc việc, xuất Excel và sao lưu. Giao diện dùng Python Tkinter; dữ liệu dùng SQLite trong tài khoản hiện tại.

## Tải và cài trên Windows

**[Tải bộ cài Nhắc việc anh Hà 2.0.0 — Windows x64](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.0-preview.1/NhacViecAnhHa-Setup-2.0.0-x64.exe)**

Bộ cài dành cho Windows 10/11 x64, đã được dựng và kiểm tra tự động trên runner Windows `windows-2022`. [Bản phát hành thử nghiệm 2.0.0](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.0-preview.1) có bộ cài, checksum và hai báo cáo tự kiểm tra. Mã nguồn: [GitHub](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-).

1. Tải bộ cài ở liên kết trên và [SHA256SUMS.txt](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.0-preview.1/SHA256SUMS.txt).
2. Đối chiếu SHA256, mở bộ cài và làm theo hướng dẫn. Dùng bộ cài không cần cài Python hoặc NSIS.
3. Mở Nhắc việc anh Hà từ menu Start hoặc trang cuối của bộ cài. Dữ liệu mới nằm riêng tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`.

SHA256 của bộ cài: `5abf9b9ab560b3a58ad1c4e9a394de3664de6fe382d27a29e6e481cb9e4c8cef`.

Bộ cài chưa ký số; Windows có thể hiển thị cảnh báo SmartScreen. Khay hệ thống, thông báo Windows và tự chạy khi đăng nhập cần được kiểm tra thêm trên máy sử dụng thực tế.

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
dist\NhacViecAnhHa-Setup-2.0.0-x64.exe
dist\SHA256SUMS.txt
```

Bộ cài chạy theo tài khoản hiện tại, có lựa chọn Desktop và tự chạy khi đăng nhập, không cần quyền quản trị theo cấu hình mặc định. Gỡ cài đặt giữ lại dữ liệu. Bộ cài chưa có chữ ký số; máy áp dụng Application Control có thể cần IT phê duyệt hoặc chữ ký phù hợp.

Trên GitHub, mở Actions → Build Windows installer → Run workflow để dựng lại bộ cài. Workflow chạy cả cài/gỡ im lặng và kiểm tra giữ nguyên tệp dữ liệu đánh dấu trên runner. [Lần dựng Windows thành công ngày 22/10/2026](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707130999) đã tạo artifact chứa bộ cài, checksum và hai báo cáo tự kiểm tra. Workflow Publish Windows installer xác minh artifact của lần dựng thành công trước khi xuất bản bản phát hành thử nghiệm.

## Phạm vi kiểm tra

Bản mã nguồn [b009740](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/b0097407d3a19f8d5c3e564206af40f9e1531f26) đã đạt 75 kiểm thử trên runner Windows `windows-2022` với Python 3.13 x64. EXE đã đạt `--self-test` và `--gui-smoke-test`; bộ cài NSIS đã qua kiểm tra cài/gỡ im lặng và giữ nguyên dữ liệu đánh dấu. Khay hệ thống, tự chạy khi đăng nhập và thông báo vẫn cần kiểm tra trên máy Windows đích.

Hướng dẫn thao tác: [docs/huong-dan.md](docs/huong-dan.md). Phạm vi yêu cầu và giới hạn: [docs/yeu-cau.md](docs/yeu-cau.md).

Kết quả kiểm tra mã nguồn và bộ cài: [docs/kiem-thu.md](docs/kiem-thu.md). Bộ 75 kiểm thử cũng đã đạt trên Linux, bao gồm GUI Tkinter với SQLite thật.
