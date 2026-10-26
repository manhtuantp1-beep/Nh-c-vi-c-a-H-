# Giao diện và nâng cấp 2.0.2

## Chữ và bố cục

Bản 2.0.2 dùng thanh điều hướng xanh navy, thẻ nội dung trắng và chữ đậm màu. Cỡ chữ nội dung mặc định 12 pt, tên công việc 13 pt đậm và thông tin phụ 11 pt. Cỡ chữ theo DPI của màn hình lúc mở ứng dụng. Xem [nguyên nhân chữ mờ và cách nâng cấp](readability.md).

## Ảnh từ EXE đóng gói trên Windows

Các ảnh dưới đây dùng DPI thực của cửa sổ trên runner Windows. Nội dung công việc là dữ liệu minh họa tạm thời, không tự thêm vào dữ liệu người dùng.

![Danh sách công việc 2.0.2 trên Windows](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768.png)

![Lịch tháng 2.0.2 trên Windows](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/calendar-month-1366x768.png)

Xem thêm [biểu mẫu công việc](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/task-dialog.png).

Ảnh mô phỏng cỡ chữ và bố cục Tk: [125%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk120dpi.png), [150%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk144dpi.png), [200%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/tasks-1366x768-tk192dpi.png). Các ảnh này không xác nhận thử nghiệm trên màn hình vật lý được đặt Scale Windows ở từng mức tương ứng. Xem [phạm vi kiểm tra DPI](readability.md#phạm-vi-xác-nhận-dpi).

## Không gian làm việc

Thanh bên trái chia thành Công việc và Tiện ích. Mục đang mở có nền sáng hơn và biểu tượng vàng trên thanh xanh navy. Chọn Việc cần làm để xem công việc chưa hoàn thành; các mục Đang thực hiện, Sắp đến hạn, Đã hoàn thành và Đã hủy giúp tra cứu theo trạng thái. Chọn Lịch của anh để chuyển sang lịch.

Giao diện dùng font Unicode thống nhất, ưu tiên Segoe UI trên Windows. Nội dung chính đặt trên nền trắng; trạng thái đang làm dùng xanh lam, hoàn thành dùng xanh lục và quá hạn dùng đỏ kèm chữ để dễ nhận biết.

## Danh sách công việc

Ba ô tổng quan hiển thị số việc chưa bắt đầu, đang thực hiện và đã quá hạn trong nhóm chưa hoàn thành. Các số này phản ánh toàn bộ nhóm đó, không thay đổi theo từ khóa hoặc khoảng ngày đang lọc.

Mỗi công việc nằm trên một hàng: tên, phân loại, mã và nội dung ngắn ở bên trái; trạng thái, hạn hoàn thành và thao tác ở bên phải. Chọn Chi tiết để xem toàn bộ nội dung. Bắt đầu chuyển việc sang đang làm; Hoàn thành chuyển sang danh sách đã hoàn thành.

Ở mục Việc cần làm, Hiển thị có hai lựa chọn:

| Lựa chọn | Công việc được hiển thị |
| --- | --- |
| Tất cả việc chưa hoàn thành | Việc mới và đang làm, gồm việc tạm dừng, mở lại hoặc quá hạn |
| Chưa bắt đầu | Nhóm Cần làm, gồm việc tạm dừng hoặc mở lại |

Nhập tên hoặc mã vào Tìm công việc rồi nhấn Enter hoặc Tìm. Chọn Bộ lọc + để mở sắp xếp theo Deadline/Ngày tạo, chiều giảm dần và khoảng ngày. Chọn Áp dụng để lọc; Xóa lọc để trở về tìm kiếm và sắp xếp mặc định. Thu gọn chỉ ẩn phần điều khiển, không xóa điều kiện lọc; số trên nút Bộ lọc cho biết các điều kiện nâng cao đang dùng.

Khi cửa sổ hẹp hoặc chữ lớn, phần Hiển thị và Tìm công việc được xếp thành hai hàng. Các ô tổng quan tạm ẩn khi mở bộ lọc trong bố cục này để dành chỗ cho danh sách; thu gọn bộ lọc sẽ hiện lại.

## Lịch

Chọn Tuần, Tháng hoặc Năm để đổi góc nhìn. Hôm nay đưa lịch về ngày hiện tại; hai mũi tên chuyển khoảng thời gian. Ngày được chọn có nền xanh; danh sách phía dưới hiển thị các buổi của ngày đó. Ở chế độ Năm, chọn ô tháng để mở lịch tháng.

Thêm lịch mở biểu mẫu mới. Quản lý lịch cho phép sửa lịch gốc hoặc tạm dừng/bật lại. Các thao tác hoàn thành, bỏ qua, mở lại và nhắc sau áp dụng cho buổi được chọn trong danh sách ngày.

## Biểu mẫu và tiện ích

Biểu mẫu công việc tách tên, ngày/giờ đến hạn, phân loại, nội dung và yêu cầu hoàn thành. Phần nội dung có thể cuộn; nút Lưu công việc và Đóng luôn nằm ở chân cửa sổ. Những trường có dấu * là bắt buộc.

Dữ liệu và báo cáo trên thanh bên mở menu Xuất báo cáo Excel, Sao lưu dữ liệu và Khôi phục dữ liệu. Cài đặt nhắc việc và Thông báo đã nhận có mục riêng ngay bên dưới.

| Phím tắt | Thao tác |
| --- | --- |
| Ctrl+N | Tạo công việc từ cửa sổ chính |
| Ctrl+F | Đưa con trỏ vào ô tìm trên trang công việc |
| Ctrl+S | Lưu biểu mẫu công việc hoặc cài đặt nhắc việc |
| Ctrl+Enter | Lưu biểu mẫu lịch |
| Esc | Đóng biểu mẫu; công việc/lịch chưa lưu vẫn có bước xác nhận |

## Nâng cấp từ 2.0.0 hoặc 2.0.1

1. Trong bản đang dùng, chọn Sao lưu dữ liệu và lưu bản sao ở vị trí dễ tìm. Với 2.0.1, mục này nằm trong Dữ liệu và báo cáo.
2. Chọn Thoát hẳn trong ứng dụng hoặc menu khay hệ thống. Đóng cửa sổ bằng dấu X chỉ thu nhỏ ứng dụng và chưa đủ để cập nhật.
3. Tải và chạy [bộ cài 2.0.2](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.2-preview.1/NhacViecAnhHa-Setup-2.0.2-x64.exe). Giữ nguyên thư mục cài đặt đang dùng, rồi hoàn tất cài đặt.
4. Mở ứng dụng và kiểm tra số phiên bản 2.0.2 ở thanh dưới cùng. Công việc, lịch và cài đặt 2.0.x dùng lại cơ sở dữ liệu hiện có tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`.

2.0.2 không đổi định dạng hay vị trí cơ sở dữ liệu so với các bản 2.0.x. Không cần khôi phục dữ liệu chỉ để nâng cấp giao diện. Dữ liệu của ứng dụng gốc 1.7.0 vẫn nằm riêng và chưa được tự động nhập vào bản mới.
