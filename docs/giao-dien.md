# Giao diện và nâng cấp 2.0.5

## Chữ và bố cục

Bản 2.0.5 dùng ba kiểu xem công việc và giữ cách hiển thị chữ đã có: thanh điều hướng xanh navy, thẻ nội dung trắng và chữ đậm màu. Cỡ chữ nội dung mặc định 12 pt, tên công việc 13 pt đậm và thông tin phụ 11 pt. Cỡ chữ theo DPI của màn hình lúc mở ứng dụng. Xem [nguyên nhân chữ mờ và cách nâng cấp](readability.md).

## Ảnh từ EXE Windows đã phát hành

Các ảnh 2.0.5 dưới đây được tạo từ chính EXE đóng gói, dùng dữ liệu tổng hợp tạm thời và đã được tải lại để xem. Pha native ghi DPI cửa sổ là 96; xem [bằng chứng kiểm tra](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/42762773298) và [phạm vi kiểm tra](kiem-thu.md).

![Lưới mặc định](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/tasks-1366x768.png)

Xem thêm [Danh sách](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/tasks-list-1366x768.png), [Rộng](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/tasks-wide-1366x768.png), [Lịch](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/calendar-tasks-1366x768.png) và [Ghi chú](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/notes-dialog.png).

## Không gian làm việc

Thanh bên trái chia thành Công việc và Tiện ích. Mục đang mở có nền sáng hơn và biểu tượng vàng trên thanh xanh navy. Chọn Việc cần làm để xem công việc chưa hoàn thành; các mục Đang thực hiện, Sắp đến hạn, Đã hoàn thành và Đã hủy giúp tra cứu theo trạng thái. Chọn Lịch của anh để chuyển sang lịch.

Giao diện dùng font Unicode thống nhất, ưu tiên Segoe UI trên Windows. Nội dung chính đặt trên nền trắng; trạng thái đang làm dùng xanh lam, hoàn thành dùng xanh lục và quá hạn dùng đỏ kèm chữ để dễ nhận biết.

## Danh sách công việc

Tiêu đề, ba ô tổng quan và nút Tạo công việc nằm phía trên. Ba ô đếm việc chưa bắt đầu, đang thực hiện và quá hạn trong toàn bộ nhóm chưa hoàn thành. Khối Hiển thị/Tìm công việc/Bộ lọc cùng hàng đếm và ghi chú cũ đã được bỏ, dành chỗ cho danh sách.

Chọn kiểu xem ở thanh gọn ngay trên các thẻ:

| Kiểu xem | Cách dùng |
| --- | --- |
| Lưới | Mặc định khi mở ứng dụng; thẻ chia cột theo chỗ trống và về một cột ở cửa sổ hẹp |
| Danh sách | Các hàng gọn để tra cứu nhiều việc |
| Rộng | Mỗi thẻ chiếm chiều ngang như trước |

Cả ba kiểu giữ cùng công việc, trạng thái, deadline, nội dung và ghi chú. Lựa chọn dùng chung khi chuyển các trang công việc trong phiên hiện tại; lần mở mới bắt đầu ở Lưới. Mục Việc cần làm hiển thị mọi việc chưa hoàn thành, gồm chưa bắt đầu, đang làm, tạm dừng, mở lại và quá hạn. Đã hoàn thành và Đã hủy có trang riêng.

Chọn Chi tiết để xem toàn bộ nội dung. Nút Ghi chú mở trình sửa riêng, lưu bằng Lưu ghi chú hoặc Ctrl+S. Ghi chú không thay thế Nội dung công việc, Yêu cầu hoàn thành hay lý do tạm dừng. Bắt đầu chuyển việc sang đang làm; Hoàn thành chuyển sang danh sách đã hoàn thành.

Nhấn **Ctrl+F** để mở cửa sổ tìm theo tên hoặc mã. Nhấn Tìm/Enter để áp dụng; Xóa tìm kiếm để trở về toàn bộ nhóm. Khi đang tìm, dòng mô tả dưới tiêu đề cho biết từ khóa; sửa hoặc xóa bằng Ctrl+F. Không có bộ lọc tìm kiếm chiếm diện tích trong trang.

## Lịch

Chọn Tuần, Tháng hoặc Năm để đổi góc nhìn. Hôm nay đưa lịch về ngày hiện tại; hai mũi tên chuyển khoảng thời gian. Lịch tự lấy công việc theo **ngày deadline**, không yêu cầu tạo thêm lịch hẹn.

Mỗi ngày hiển thị số việc đến hạn và số lịch hẹn riêng. Công việc tính tất cả trạng thái, gồm đã hoàn thành và đã hủy để tra cứu lịch sử; trạng thái luôn hiện trên thẻ. Ví dụ ba việc có deadline 28/10 thì ngày 28/10 ghi 3 việc, bất kể ngày tạo. Đổi deadline sang 29/10 sẽ cập nhật tổng ở cả hai ngày. Mỗi việc chỉ được tính một lần.

Bấm ngày để mở chi tiết ngay phía dưới. Tạo công việc từ lịch sẽ điền sẵn ngày deadline đang chọn; anh vẫn có thể sửa ngày/giờ trước khi lưu. Tab Công việc trong lịch tiếp tục dùng thẻ Rộng với cùng thông tin: tên, phân loại, mã, deadline, nội dung, ghi chú và các nút Chi tiết, Ghi chú, Bắt đầu, Hoàn thành hoặc Mở lại theo trạng thái. Thao tác cập nhật chính công việc đó và tổng lịch được tải lại. Ở chế độ Năm, chọn ô tháng để mở lịch tháng. Khi chiều cao cửa sổ thấp, phần lưới lịch thu gọn khoảng cách; nếu vẫn không đủ chỗ, anh có thể cuộn lưới lịch để xem các ngày, trong khi phần công việc ngày được chọn vẫn có vùng riêng phía dưới.

Tab Lịch hẹn giữ các buổi được tạo bằng Thêm lịch. Quản lý lịch cho phép sửa lịch gốc hoặc tạm dừng/bật lại. Các thao tác hoàn thành, bỏ qua, mở lại và nhắc sau áp dụng cho buổi đang chọn trong tab này; kết quả buổi không chuyển trạng thái công việc khác.

## Biểu mẫu và tiện ích

Biểu mẫu công việc tách tên, ngày/giờ đến hạn, phân loại, nội dung, yêu cầu hoàn thành và ghi chú riêng cho tiến độ hoặc chú ý. Phần nội dung có thể cuộn; nút Lưu công việc và Đóng luôn nằm ở chân cửa sổ. Những trường có dấu * là bắt buộc.

Dữ liệu và báo cáo trên thanh bên mở menu Xuất báo cáo Excel, Sao lưu dữ liệu và Khôi phục dữ liệu. Cài đặt nhắc việc và Thông báo đã nhận có mục riêng ngay bên dưới.

| Phím tắt | Thao tác |
| --- | --- |
| Ctrl+N | Tạo công việc từ cửa sổ chính |
| Ctrl+F | Mở cửa sổ tìm công việc riêng |
| Ctrl+S | Lưu công việc, ghi chú hoặc cài đặt nhắc việc |
| Ctrl+Enter | Lưu biểu mẫu lịch |
| Esc | Đóng biểu mẫu; công việc/ghi chú/lịch chưa lưu vẫn có bước xác nhận |

## Nâng cấp lên 2.0.5

1. Trong bản đang dùng, chọn Sao lưu dữ liệu và lưu bản sao ở vị trí dễ tìm. Với 2.0.1, mục này nằm trong Dữ liệu và báo cáo.
2. Chọn Thoát hẳn trong ứng dụng hoặc menu khay hệ thống. Đóng cửa sổ bằng dấu X chỉ thu nhỏ ứng dụng và chưa đủ để cập nhật.
3. Tải và chạy [bộ cài 2.0.5](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/windows-2.0.5-preview.1/NhacViecAnhHa-Setup-2.0.5-x64.exe). Giữ nguyên thư mục cài đặt đang dùng, rồi hoàn tất cài đặt.
4. Mở ứng dụng và kiểm tra số phiên bản 2.0.5 ở thanh dưới cùng. Công việc, lịch và cài đặt 2.0.x dùng lại cơ sở dữ liệu hiện có tại `%USERPROFILE%\NhacViecAnhHaMoi\data\tasks.db`.

Từ 2.0.3–2.0.4 lên 2.0.5 giữ schema 2, không nâng cấp lại cơ sở dữ liệu. Khi nâng cấp từ 2.0.0–2.0.2, ứng dụng tự nâng cấp schema 1 lên schema 2 để thêm ghi chú, giữ nguyên vị trí và dữ liệu hiện có. Trước nâng cấp, ứng dụng kiểm tra dữ liệu và giữ bản `tasks.pre-upgrade-<ngày-giờ>.db` cùng thư mục. Không cần khôi phục hoặc nhập lại công việc. Sau nâng cấp, dùng 2.0.3 trở lên vì các bản cũ không đọc schema 2. Chức năng Khôi phục vẫn nhận bản sao hợp lệ từ 2.0.0–2.0.2; tệp sao lưu nguồn được giữ nguyên. Dữ liệu của ứng dụng gốc 1.7.0 vẫn nằm riêng và chưa được tự động nhập vào bản mới.

Khi gặp lỗi ghi tệp hoặc yêu cầu đóng ứng dụng trong lúc cài, xem [cách xử lý](cai-dat.md).

Muốn dùng dữ liệu từ một bản sao lưu khác, mở Dữ liệu và báo cáo → Khôi phục dữ liệu và chọn tệp trên máy. Cài đè chương trình tự nó không thay dữ liệu hiện tại bằng một tệp sao lưu khác.
