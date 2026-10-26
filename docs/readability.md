# Chữ hiển thị và nâng cấp 2.0.4

## Vì sao chữ có thể mờ

Kiểm tra tệp ứng dụng EXE đã phát hành trong bản 2.0.1 cho thấy manifest chưa có khai báo `dpiAware` / `dpiAwareness`. Khi một ứng dụng không nhận biết DPI chạy trên màn hình có tỷ lệ phóng lớn, Windows có thể phóng ảnh của cả cửa sổ; chữ vì thế có thể mờ dù dùng đúng font. Cỡ chữ nhỏ và thông tin phụ màu nhạt cũng làm việc đọc khó hơn.

Bản 2.0.2 thêm manifest PerMonitorV2, khởi tạo chế độ nhận biết DPI trước khi tạo cửa sổ Tk, rồi đặt tỷ lệ Tk theo DPI thực của cửa sổ lúc mở. Chữ nội dung dùng cỡ 12 pt đậm màu, tên công việc 13 pt đậm và thông tin phụ 11 pt. Thanh bên xanh navy tách khỏi các thẻ nội dung trắng; bộ lọc và nút thao tác được sắp xếp theo chỗ trống.

Manifest trong chính EXE ứng dụng lấy từ bộ cài 2.0.2 đã phát hành cũng đã được đối chiếu, xác nhận khai báo PerMonitorV2 và tắt cơ chế phóng ảnh GDI của ứng dụng.

Bản 2.0.3 giữ cách nhận biết DPI và font này, đồng thời thêm lịch theo deadline và ghi chú. Kết quả EXE 2.0.3 được ghi riêng trong [phạm vi kiểm tra](kiem-thu.md), không suy ra từ kết quả của 2.0.2.

Ứng dụng giữ tỷ lệ hiển thị Windows mà người dùng đã chọn. Bản sửa không thay đổi độ phân giải, thiết lập Scale, ClearType hay cấu hình hiển thị của hệ thống.

## Cài nâng cấp lên 2.0.4

1. Trong ứng dụng đang dùng, tạo bản Sao lưu dữ liệu. Ở 2.0.1, mở Dữ liệu và báo cáo → Sao lưu dữ liệu.
2. Chọn Thoát hẳn ứng dụng hoặc Thoát hẳn từ menu khay. Dấu X chỉ thu nhỏ cửa sổ và vẫn để ứng dụng chạy nền.
3. Sau khi bản 2.0.4 được xác nhận phát hành, tải [bộ cài 2.0.4](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/NhacViecAnhHa-Setup-2.0.4-x64.exe) và [SHA256SUMS.txt](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.4-preview.1/SHA256SUMS.txt) của cùng bản phát hành. Chạy bộ cài vào vị trí cài đặt hiện tại.
4. Mở lại ứng dụng và kiểm tra số phiên bản 2.0.4 ở thanh dưới cùng. Việc khởi động lại giúp cửa sổ nhận chế độ DPI mới từ đầu.

Dữ liệu vẫn dùng `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`. Từ 2.0.3 lên 2.0.4 giữ schema 2, không nâng cấp lại dữ liệu. Nếu nâng cấp từ 2.0.0–2.0.2, lần mở đầu kiểm tra dữ liệu, giữ bản `tasks.pre-upgrade-<ngày-giờ>.db` cùng thư mục và nâng cấp schema 1 lên schema 2 để thêm ghi chú. Không cần xóa, nhập lại hoặc khôi phục công việc. Sau nâng cấp, tiếp tục dùng 2.0.3 trở lên; bản 2.0.2 trở về trước không đọc schema 2. Dữ liệu gốc 1.7.0 vẫn nằm riêng và chưa được tự động chuyển vào bản mới.

## Phạm vi xác nhận DPI

2.0.4 giữ phần DPI của 2.0.3; kết quả dựng và kiểm tra EXE 2.0.4 đang chờ xác nhận riêng trong [kết quả kiểm tra](kiem-thu.md). Nếu bộ cài báo lỗi ghi tệp, dùng [hướng dẫn cài đặt](cai-dat.md).

Bản 2.0.3 đã vượt qua [lần dựng Windows 40289470721](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40289470721), gồm 116 kiểm thử, tự kiểm tra EXE/GUI và xác nhận PerMonitorV2 của tiến trình/cửa sổ trước và sau khi cài. Báo cáo ảnh của EXE đóng gói có 64 kiểm tra, 65 PNG, pha native ghi DPI thực 96. Bộ cài [đã phát hành](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.3-preview.1) và đối chiếu SHA256 sau khi tải lại.

Bản 2.0.2 đã vượt qua [lần dựng Windows 40255800533](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/40255800533), gồm 89 kiểm thử và kiểm tra EXE đóng gói. Kiểm tra GUI và chụp ảnh xác nhận tiến trình lẫn cửa sổ thực ở chế độ PerMonitorV2; báo cáo ghi DPI của cửa sổ và tỷ lệ Tk lúc khởi động. Ứng dụng sau khi cài cũng đã qua kiểm tra GUI và PerMonitorV2. Xem [chi tiết kiểm thử](kiem-thu.md).

Các pha Tk tương đương 125%, 150% và 200% kiểm tra việc bố trí thông tin khi font và kích thước điều khiển tăng. Chúng là mô phỏng trong ứng dụng; chúng không đổi Scale của Windows và không thay thế thử nghiệm trên màn hình vật lý ở từng tỷ lệ đó.

Bản này đồng bộ tỷ lệ khi tạo giao diện. Chưa có xác nhận tự điều chỉnh toàn bộ font và bố cục khi kéo cửa sổ đang mở giữa các màn hình có DPI khác nhau. Sau khi thay đổi thiết lập màn hình, thoát hẳn rồi mở lại ứng dụng để lấy DPI lúc khởi động.
