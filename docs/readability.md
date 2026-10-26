# Chữ hiển thị và nâng cấp 2.0.2

## Vì sao chữ có thể mờ

Kiểm tra tệp ứng dụng EXE đã phát hành trong bản 2.0.1 cho thấy manifest chưa có khai báo `dpiAware` / `dpiAwareness`. Khi một ứng dụng không nhận biết DPI chạy trên màn hình có tỷ lệ phóng lớn, Windows có thể phóng ảnh của cả cửa sổ; chữ vì thế có thể mờ dù dùng đúng font. Cỡ chữ nhỏ và thông tin phụ màu nhạt cũng làm việc đọc khó hơn.

Bản 2.0.2 thêm manifest PerMonitorV2, khởi tạo chế độ nhận biết DPI trước khi tạo cửa sổ Tk, rồi đặt tỷ lệ Tk theo DPI thực của cửa sổ lúc mở. Chữ nội dung dùng cỡ 12 pt đậm màu, tên công việc 13 pt đậm và thông tin phụ 11 pt. Thanh bên xanh navy tách khỏi các thẻ nội dung trắng; bộ lọc và nút thao tác được sắp xếp theo chỗ trống.

Manifest trong chính EXE ứng dụng lấy từ bộ cài 2.0.2 đã phát hành cũng đã được đối chiếu, xác nhận khai báo PerMonitorV2 và tắt cơ chế phóng ảnh GDI của ứng dụng.

Ứng dụng giữ tỷ lệ hiển thị Windows mà người dùng đã chọn. Bản sửa không thay đổi độ phân giải, thiết lập Scale, ClearType hay cấu hình hiển thị của hệ thống.

## Cài nâng cấp từ 2.0.0 hoặc 2.0.1

1. Trong ứng dụng đang dùng, tạo bản Sao lưu dữ liệu. Ở 2.0.1, mở Dữ liệu và báo cáo → Sao lưu dữ liệu.
2. Chọn Thoát hẳn ứng dụng hoặc Thoát hẳn từ menu khay. Dấu X chỉ thu nhỏ cửa sổ và vẫn để ứng dụng chạy nền.
3. Tải [bộ cài 2.0.2](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/NhacViecAnhHa-Setup-2.0.2-x64.exe) và [SHA256SUMS.txt](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/SHA256SUMS.txt) của cùng bản phát hành. Chạy bộ cài vào vị trí cài đặt hiện tại.
4. Mở lại ứng dụng và kiểm tra số phiên bản 2.0.2 ở thanh dưới cùng. Việc khởi động lại giúp cửa sổ nhận chế độ DPI mới từ đầu.

Dữ liệu 2.0.x vẫn dùng `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`, với cùng định dạng cơ sở dữ liệu. Cài nâng cấp giao diện không yêu cầu xóa, nhập lại hoặc khôi phục công việc. Dữ liệu gốc 1.7.0 vẫn nằm riêng và chưa được tự động chuyển vào bản mới.

## Phạm vi xác nhận DPI

Bản 2.0.2 đã vượt qua [lần dựng Windows 40255800533](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40255800533), gồm 89 kiểm thử và kiểm tra EXE đóng gói. Kiểm tra GUI và chụp ảnh xác nhận tiến trình lẫn cửa sổ thực ở chế độ PerMonitorV2; báo cáo ghi DPI của cửa sổ và tỷ lệ Tk lúc khởi động. Ứng dụng sau khi cài cũng đã qua kiểm tra GUI và PerMonitorV2. Xem [chi tiết kiểm thử](kiem-thu.md).

Các pha Tk tương đương 125%, 150% và 200% kiểm tra việc bố trí thông tin khi font và kích thước điều khiển tăng. Chúng là mô phỏng trong ứng dụng; chúng không đổi Scale của Windows và không thay thế thử nghiệm trên màn hình vật lý ở từng tỷ lệ đó.

Bản này đồng bộ tỷ lệ khi tạo giao diện. Chưa có xác nhận tự điều chỉnh toàn bộ font và bố cục khi kéo cửa sổ đang mở giữa các màn hình có DPI khác nhau. Sau khi thay đổi thiết lập màn hình, thoát hẳn rồi mở lại ứng dụng để lấy DPI lúc khởi động.
