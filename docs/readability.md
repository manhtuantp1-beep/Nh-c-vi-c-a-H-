# Chữ hiển thị và nâng cấp 2.0.2

## Vì sao chữ có thể mờ

Kiểm tra tệp ứng dụng EXE đã phát hành trong bản 2.0.1 cho thấy manifest chưa có khai báo `dpiAware` / `dpiAwareness`. Khi một ứng dụng không nhận biết DPI chạy trên màn hình có tỷ lệ phóng lớn, Windows có thể phóng ảnh của cả cửa sổ; chữ vì thế có thể mờ dù dùng đúng font. Cỡ chữ nhỏ và thông tin phụ màu nhạt cũng làm việc đọc khó hơn.

Bản 2.0.2 thêm manifest PerMonitorV2, khởi tạo chế độ nhận biết DPI trước khi tạo cửa sổ Tk, rồi đặt tỷ lệ Tk theo DPI thực của cửa sổ lúc mở. Chữ nội dung dùng cỡ 12 pt đậm màu, tên công việc 13 pt đậm và thông tin phụ 11 pt. Thanh bên xanh navy tách khỏi các thẻ nội dung trắng; bộ lọc và nút thao tác được sắp xếp theo chỗ trống.

Ứng dụng giữ tỷ lệ hiển thị Windows mà người dùng đã chọn. Bản sửa không thay đổi độ phân giải, thiết lập Scale, ClearType hay cấu hình hiển thị của hệ thống.

## Cài nâng cấp từ 2.0.0 hoặc 2.0.1

1. Trong ứng dụng đang dùng, tạo bản Sao lưu dữ liệu. Ở 2.0.1, mở Dữ liệu và báo cáo → Sao lưu dữ liệu.
2. Chọn Thoát hẳn ứng dụng hoặc Thoát hẳn từ menu khay. Dấu X chỉ thu nhỏ cửa sổ và vẫn để ứng dụng chạy nền.
3. Khi bản 2.0.2 được phát hành trong [Releases](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases), tải `NhacViecAnhHa-Setup-2.0.2-x64.exe` và SHA256 của cùng bản phát hành. Chạy bộ cài vào vị trí cài đặt hiện tại.
4. Mở lại ứng dụng và kiểm tra số phiên bản 2.0.2 ở thanh dưới cùng. Việc khởi động lại giúp cửa sổ nhận chế độ DPI mới từ đầu.

Dữ liệu 2.0.x vẫn dùng `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`, với cùng định dạng cơ sở dữ liệu. Cài nâng cấp giao diện không yêu cầu xóa, nhập lại hoặc khôi phục công việc. Dữ liệu gốc 1.7.0 vẫn nằm riêng và chưa được tự động chuyển vào bản mới.

## Phạm vi xác nhận DPI

Kiểm tra Windows 2.0.2 đang chờ thực thi. Kết quả cuối sẽ được ghi trong [tài liệu kiểm thử](kiem-thu.md), gồm manifest trong EXE, chế độ DPI của tiến trình/cửa sổ và DPI thực khi khởi động.

Các pha Tk tương đương 125%, 150% và 200% kiểm tra việc bố trí thông tin khi font và kích thước điều khiển tăng. Chúng là mô phỏng trong ứng dụng; chúng không đổi Scale của Windows và không thay thế thử nghiệm trên màn hình vật lý ở từng tỷ lệ đó.

Bản này đồng bộ tỷ lệ khi tạo giao diện. Chưa có xác nhận tự điều chỉnh toàn bộ font và bố cục khi kéo cửa sổ đang mở giữa các màn hình có DPI khác nhau. Sau khi thay đổi thiết lập màn hình, thoát hẳn rồi mở lại ứng dụng để lấy DPI lúc khởi động.
