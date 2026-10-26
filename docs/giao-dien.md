# Giao diện và nâng cấp 2.0.3

## Chữ và bố cục

Bản 2.0.3 dùng thanh điều hướng xanh navy, thẻ nội dung trắng và chữ đậm màu. Cỡ chữ nội dung mặc định 12 pt, tên công việc 13 pt đậm và thông tin phụ 11 pt. Cỡ chữ theo DPI của màn hình lúc mở ứng dụng. Xem [nguyên nhân chữ mờ và cách nâng cấp](readability.md).

## Ảnh từ EXE đóng gói trên Windows

Các ảnh 2.0.3 dưới đây được tạo từ chính EXE đóng gói trên Windows và đã tải lại từ bản phát hành để xem. Chúng dùng dữ liệu minh họa tạm thời, không tự thêm vào dữ liệu người dùng. Pha native ghi DPI thực của cửa sổ trên runner là 96.

![Danh sách công việc 2.0.3 trên Windows](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/tasks-1366x768.png)

![Lịch tháng 2.0.3 trên Windows](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/calendar-tasks-1366x768.png)

Xem thêm [cửa sổ ghi chú](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/notes-dialog.png) và [biểu mẫu công việc](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/task-dialog.png).

Ảnh mô phỏng cỡ chữ và bố cục Tk: [125%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/tasks-1366x768-tk120dpi.png), [150%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/tasks-1366x768-tk144dpi.png), [200%](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/tasks-1366x768-tk192dpi.png). Các ảnh này không xác nhận thử nghiệm trên màn hình vật lý được đặt Scale Windows ở từng mức tương ứng. Xem [phạm vi kiểm tra DPI](readability.md#phạm-vi-xác-nhận-dpi).

## Không gian làm việc

Thanh bên trái chia thành Công việc và Tiện ích. Mục đang mở có nền sáng hơn và biểu tượng vàng trên thanh xanh navy. Chọn Việc cần làm để xem công việc chưa hoàn thành; các mục Đang thực hiện, Sắp đến hạn, Đã hoàn thành và Đã hủy giúp tra cứu theo trạng thái. Chọn Lịch của anh để chuyển sang lịch.

Giao diện dùng font Unicode thống nhất, ưu tiên Segoe UI trên Windows. Nội dung chính đặt trên nền trắng; trạng thái đang làm dùng xanh lam, hoàn thành dùng xanh lục và quá hạn dùng đỏ kèm chữ để dễ nhận biết.

## Danh sách công việc

Ba ô tổng quan hiển thị số việc chưa bắt đầu, đang thực hiện và đã quá hạn trong nhóm chưa hoàn thành. Các số này phản ánh toàn bộ nhóm đó, không thay đổi theo từ khóa hoặc khoảng ngày đang lọc.

Mỗi công việc nằm trên một hàng: tên, phân loại, mã và nội dung ngắn ở bên trái; trạng thái, hạn hoàn thành và thao tác ở bên phải. Chọn Chi tiết để xem toàn bộ nội dung. Phần xem trước Ghi chú giúp nhận biết tiến độ và điều cần chú ý; nút Ghi chú mở trình sửa riêng, lưu bằng Lưu ghi chú hoặc Ctrl+S. Ghi chú không thay thế Nội dung công việc, Yêu cầu hoàn thành hay lý do tạm dừng. Bắt đầu chuyển việc sang đang làm; Hoàn thành chuyển sang danh sách đã hoàn thành.

Ở mục Việc cần làm, Hiển thị có hai lựa chọn:

| Lựa chọn | Công việc được hiển thị |
| --- | --- |
| Tất cả việc chưa hoàn thành | Việc mới và đang làm, gồm việc tạm dừng, mở lại hoặc quá hạn |
| Chưa bắt đầu | Nhóm Cần làm, gồm việc tạm dừng hoặc mở lại |

Nhập tên hoặc mã vào Tìm công việc rồi nhấn Enter hoặc Tìm. Chọn Bộ lọc + để mở sắp xếp theo Deadline/Ngày tạo, chiều giảm dần và khoảng ngày. Chọn Áp dụng để lọc; Xóa lọc để trở về tìm kiếm và sắp xếp mặc định. Thu gọn chỉ ẩn phần điều khiển, không xóa điều kiện lọc; số trên nút Bộ lọc cho biết các điều kiện nâng cao đang dùng.

Khi cửa sổ hẹp hoặc chữ lớn, phần Hiển thị và Tìm công việc được xếp thành hai hàng. Các ô tổng quan tạm ẩn khi mở bộ lọc trong bố cục này để dành chỗ cho danh sách; thu gọn bộ lọc sẽ hiện lại.

## Lịch

Chọn Tuần, Tháng hoặc Năm để đổi góc nhìn. Hôm nay đưa lịch về ngày hiện tại; hai mũi tên chuyển khoảng thời gian. Lịch tự lấy công việc theo **ngày deadline**, không yêu cầu tạo thêm lịch hẹn.

Mỗi ngày hiển thị số việc đến hạn và số lịch hẹn riêng. Công việc tính tất cả trạng thái, gồm đã hoàn thành và đã hủy để tra cứu lịch sử; trạng thái luôn hiện trên thẻ. Ví dụ ba việc có deadline 28/10 thì ngày 28/10 ghi 3 việc, bất kể ngày tạo. Đổi deadline sang 29/10 sẽ cập nhật tổng ở cả hai ngày. Mỗi việc chỉ được tính một lần.

Bấm ngày để mở chi tiết ngay phía dưới. Tạo công việc từ lịch sẽ điền sẵn ngày deadline đang chọn; anh vẫn có thể sửa ngày/giờ trước khi lưu. Tab Công việc mặc định dùng đúng thẻ như Việc cần làm: tên, phân loại, mã, deadline, nội dung, ghi chú và các nút Chi tiết, Ghi chú, Bắt đầu, Hoàn thành hoặc Mở lại theo trạng thái. Thao tác cập nhật chính công việc đó và tổng lịch được tải lại. Ở chế độ Năm, chọn ô tháng để mở lịch tháng. Khi chiều cao cửa sổ thấp, phần lưới lịch thu gọn khoảng cách; nếu vẫn không đủ chỗ, anh có thể cuộn lưới lịch để xem các ngày, trong khi phần công việc ngày được chọn vẫn có vùng riêng phía dưới.

Tab Lịch hẹn giữ các buổi được tạo bằng Thêm lịch. Quản lý lịch cho phép sửa lịch gốc hoặc tạm dừng/bật lại. Các thao tác hoàn thành, bỏ qua, mở lại và nhắc sau áp dụng cho buổi đang chọn trong tab này; kết quả buổi không chuyển trạng thái công việc khác.

## Biểu mẫu và tiện ích

Biểu mẫu công việc tách tên, ngày/giờ đến hạn, phân loại, nội dung, yêu cầu hoàn thành và ghi chú riêng cho tiến độ hoặc chú ý. Phần nội dung có thể cuộn; nút Lưu công việc và Đóng luôn nằm ở chân cửa sổ. Những trường có dấu * là bắt buộc.

Dữ liệu và báo cáo trên thanh bên mở menu Xuất báo cáo Excel, Sao lưu dữ liệu và Khôi phục dữ liệu. Cài đặt nhắc việc và Thông báo đã nhận có mục riêng ngay bên dưới.

| Phím tắt | Thao tác |
| --- | --- |
| Ctrl+N | Tạo công việc từ cửa sổ chính |
| Ctrl+F | Đưa con trỏ vào ô tìm trên trang công việc |
| Ctrl+S | Lưu công việc, ghi chú hoặc cài đặt nhắc việc |
| Ctrl+Enter | Lưu biểu mẫu lịch |
| Esc | Đóng biểu mẫu; công việc/ghi chú/lịch chưa lưu vẫn có bước xác nhận |

## Nâng cấp từ 2.0.0–2.0.2

1. Trong bản đang dùng, chọn Sao lưu dữ liệu và lưu bản sao ở vị trí dễ tìm. Với 2.0.1, mục này nằm trong Dữ liệu và báo cáo.
2. Chọn Thoát hẳn trong ứng dụng hoặc menu khay hệ thống. Đóng cửa sổ bằng dấu X chỉ thu nhỏ ứng dụng và chưa đủ để cập nhật.
3. Tải và chạy [bộ cài 2.0.3](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.3-preview.1/NhacViecAnhHa-Setup-2.0.3-x64.exe). Giữ nguyên thư mục cài đặt đang dùng, rồi hoàn tất cài đặt.
4. Mở ứng dụng và kiểm tra số phiên bản 2.0.3 ở thanh dưới cùng. Công việc, lịch và cài đặt 2.0.x dùng lại cơ sở dữ liệu hiện có tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`.

2.0.3 tự nâng cấp schema 1 lên schema 2 để thêm ghi chú, giữ nguyên vị trí và dữ liệu hiện có. Trước nâng cấp, ứng dụng kiểm tra dữ liệu và giữ bản `tasks.pre-upgrade-<ngày-giờ>.db` cùng thư mục. Không cần khôi phục hoặc nhập lại công việc. Sau nâng cấp, dùng 2.0.3 trở lên vì các bản cũ không đọc schema 2. Chức năng Khôi phục vẫn nhận bản sao hợp lệ từ 2.0.0–2.0.2; tệp sao lưu nguồn được giữ nguyên. Dữ liệu của ứng dụng gốc 1.7.0 vẫn nằm riêng và chưa được tự động nhập vào bản mới.
