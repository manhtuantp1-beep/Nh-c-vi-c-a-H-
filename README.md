# Nhắc việc anh Hà — mã nguồn dựng mới 2.0.0

Ứng dụng desktop được viết mới từ hướng dẫn sử dụng bản 1.7.0 và yêu cầu bổ sung trong cuộc trao đổi. Đây là dự án mã nguồn mới, không phải mã nguồn khôi phục từ bộ cài cũ. Không kèm công việc cá nhân hoặc dữ liệu mẫu tự nạp vào cơ sở dữ liệu thật.

Ứng dụng quản lý công việc, hiển thị lịch tuần/tháng/năm, tạo lịch lặp, nhắc việc, xuất Excel và sao lưu. Giao diện dùng Python Tkinter; dữ liệu dùng SQLite trong tài khoản hiện tại.

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

Có sẵn workflow `.github/workflows/windows-build.yml`. Khi đưa **dự án này** lên GitHub, mở Actions → Build Windows installer → Run workflow. Workflow chạy cả cài/gỡ im lặng và kiểm tra giữ nguyên tệp dữ liệu đánh dấu trên runner. Nếu workflow thành công, artifact chứa bộ cài, checksum và báo cáo tự kiểm tra. Việc tạo file workflow trong mã nguồn không có nghĩa đã chạy build hoặc đã tạo artifact trên GitHub.

## Phạm vi kiểm tra

Mã nguồn và các kiểm thử nghiệp vụ có thể được kiểm tra trong môi trường phát triển Linux. Quy trình Windows và các kiểm tra trong GitHub Actions được chuẩn bị để chạy trên Windows; không coi chúng đã chạy chỉ vì các tệp cấu hình tồn tại. Cần kiểm tra cài/mở/gỡ, khay hệ thống, tự chạy và thông báo trên máy Windows đích trước khi phát hành cho người khác.

Hướng dẫn thao tác: [docs/huong-dan.md](docs/huong-dan.md). Phạm vi yêu cầu và giới hạn: [docs/yeu-cau.md](docs/yeu-cau.md).

Kết quả kiểm tra mã nguồn: [docs/kiem-thu.md](docs/kiem-thu.md). Bản hiện tại đã chạy đạt 75 kiểm thử trên Linux, bao gồm GUI Tkinter với SQLite thật. Đây không phải kết quả kiểm chứng bộ cài Windows.
