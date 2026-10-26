# Cài đặt và xử lý lỗi ghi tệp

## Khi bộ cài báo không ghi được `_sqlite3.pyd`

Lỗi như `Error opening file for writing: D:\NhacViecAnhHaMoi\_internal\_sqlite3.pyd` có thể xuất hiện khi ứng dụng còn chạy và đang dùng thư viện, hoặc thư mục chương trình không cho phép ghi. Dấu X của ứng dụng chỉ thu nhỏ, nên cửa sổ đã đóng vẫn có thể giữ tệp.

1. Trong thông báo lỗi của bộ cài cũ, chọn **Abort/Hủy** để dừng lần cài đang lỗi. Để bộ cài kết thúc rồi mới mở lại; không chọn Ignore/Bỏ qua vì sẽ thiếu tệp cần thiết.
2. Nếu còn mở được ứng dụng, lưu công việc/ghi chú đang sửa và chọn **Thoát hẳn ứng dụng** ở thanh bên hoặc menu khay hệ thống.
3. Nếu không mở được ứng dụng, nhấn **Ctrl+Shift+Esc**, mở **Details/Chi tiết**, chọn đúng **NhacViecAnhHa.exe** rồi **End task/Kết thúc tác vụ**. Kết thúc theo cách này có thể bỏ nội dung chưa lưu, nên ưu tiên bước 2 nếu ứng dụng vẫn dùng được.
4. Chạy [bộ cài 2.0.4](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/NhacViecAnhHa-Setup-2.0.4-x64.exe) và hoàn tất cài đặt. Chỉ mở ứng dụng sau khi bộ cài đã kết thúc.

Nếu vẫn bị khóa, khởi động lại Windows rồi chạy bộ cài trước khi mở ứng dụng. Nếu đã chọn tự chạy khi đăng nhập, ứng dụng có thể mở nền sau khi khởi động lại: hãy Thoát hẳn từ biểu tượng khay hoặc kiểm tra Details trước khi chạy bộ cài.

Nếu lỗi do thư mục trên ổ D không cho phép ghi, ở trang chọn thư mục có thể dùng vị trí chương trình mặc định của tài khoản hiện tại:

```text
%LOCALAPPDATA%\Programs\NhacViecAnhHaMoi
```

Bộ cài có thể nhớ đường dẫn lần trước, nên cần kiểm tra lại ô thư mục khi muốn đổi vị trí. Dù cài chương trình ở vị trí nào, dữ liệu vẫn dùng cùng đường dẫn trong tài khoản:

```text
%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db
```

Không cần xóa cơ sở dữ liệu, thư mục dữ liệu hoặc tự xóa `_internal` để sửa lỗi này. Sau lần cài bị dừng, chạy bộ cài lại đầy đủ để sửa tệp chương trình.

## Cách bộ cài 2.0.4 xử lý trước khi cập nhật

Bản 2.0.4 đã qua [kiểm tra nâng cấp trên Windows](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40293108356) từ bộ cài 2.0.3 đã phát hành. Thay đổi được bổ sung là kiểm tra khóa tệp bằng Windows Restart Manager và khả năng ghi thư mục **trước khi chép tệp ứng dụng**. Khi phát hiện tệp đang được sử dụng, bộ cài yêu cầu đóng chương trình liên quan rồi **Thử lại** hoặc **Hủy**; không tự ép kết thúc chương trình. Anh có thể Hủy để quay lại lưu nội dung đang làm.

Khi điều kiện chưa đạt, chế độ cài im lặng trả mã lỗi thay vì tiếp tục. Bộ gỡ cũng phải kiểm tra trước khi xóa tệp chương trình. Báo cáo 9 tình huống nâng cấp từ đúng bộ cài 2.0.3 đã phát hành đã đạt, gồm ứng dụng đang nạp thư viện thật, khóa độc quyền, tệp chỉ đọc, gỡ khi đang chạy và thành công sau khi đóng. Các phép kiểm tra dùng chế độ im lặng; xem [bằng chứng và phạm vi kiểm tra](kiem-thu.md).

## Nhật ký khi cần kiểm tra thêm

Bộ cài/gỡ 2.0.4 ghi kết quả kiểm tra trước khi thay tệp vào:

```text
%TEMP%\NhacViecAnhHa-Setup-last.log
%TEMP%\NhacViecAnhHa-Uninstall-last.log
```

Mỗi lần chạy sẽ thay nội dung nhật ký tương ứng. Nhật ký ghi bước kiểm tra, mã lỗi và đường dẫn đang bị chặn; có thể mở bằng Notepad để xem lý do nếu đã đóng ứng dụng mà vẫn chưa cài được.

## Nâng cấp dữ liệu

Từ **2.0.3 lên 2.0.4**, dữ liệu giữ **schema 2**, không có bước chuyển đổi lại. Công việc, ghi chú, lịch và cài đặt vẫn nằm trong cơ sở dữ liệu hiện có.

Từ **2.0.0–2.0.2 lên 2.0.4**, lần mở đầu kiểm tra và giữ bản `tasks.pre-upgrade-<ngày-giờ>.db` cùng thư mục rồi nâng cấp schema 1 lên schema 2 để thêm ghi chú. Sau nâng cấp, dùng 2.0.3 trở lên với dữ liệu đó; các bản 2.0.2 trở về trước không đọc schema 2.
