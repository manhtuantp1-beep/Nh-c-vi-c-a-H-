# Hướng dẫn sử dụng bản dựng mới

Giao diện hiện tại: 2.0.2. Xem [bố cục, phím tắt và cách nâng cấp từ 2.0.x](giao-dien.md), cùng [thay đổi về DPI và chữ hiển thị](readability.md).

## Bắt đầu

Mở ứng dụng sau khi chạy mã nguồn hoặc cài bộ cài Windows. Lần đầu, danh sách trống. Tạo công việc mới và thử một lịch ngắn để kiểm tra nhắc việc trên máy của mình.

## Công việc

Nhập tên, deadline theo `dd/mm/yyyy` và giờ `hh:mm`. Phân loại, nội dung và yêu cầu là thông tin bổ sung. Mã công việc được tạo tự động và khác deadline.

Ở mục Việc cần làm, dùng hai lựa chọn:

| Lựa chọn | Phạm vi |
| --- | --- |
| Tất cả việc chưa hoàn thành | Cần làm và Đang thực hiện; có cả việc quá hạn |
| Chưa bắt đầu | Cần làm, bao gồm việc đã tạm dừng hoặc được mở lại |

Bắt đầu chuyển việc sang Đang thực hiện. Tạm dừng đưa về Cần làm. Hoàn thành và Hủy chuyển sang danh sách tương ứng và dừng nhắc. Mở lại đưa về Cần làm. Tìm theo tên/mã; chọn Bộ lọc + để mở sắp xếp và khoảng ngày khi cần.

## Lịch

Chọn Tuần, Tháng hoặc Năm để xem cùng một bộ lịch. Chế độ Năm có 12 ô tháng với số buổi và các ngày có lịch; bấm ô tháng để mở lịch Tháng, rồi bấm ngày để xem các buổi diễn ra. Tạo lịch với tên, ngày bắt đầu, giờ bắt đầu/kết thúc, phân loại và nội dung. Giờ kết thúc phải sau giờ bắt đầu trong cùng ngày.

- Một lần: dùng đúng ngày bắt đầu.
- Hằng tuần: chọn các thứ và ngày bắt đầu áp dụng.
- Hằng tháng: lặp theo ngày trong tháng của ngày bắt đầu.
- Hằng năm: lặp theo ngày/tháng của ngày bắt đầu.

Chọn ngày kết thúc lặp nếu cần. Với ngày 31 hoặc 29/2, chọn về ngày cuối tháng hoặc bỏ qua tháng/năm không có ngày đó. Đánh dấu hoàn thành/bỏ qua chỉ áp dụng cho một buổi. Tạm dừng lịch ngăn các lần diễn ra mới; bật lại không tạo bù các buổi trong thời gian đã dừng. Sửa lịch gốc áp dụng cho các buổi sắp tới, giữ các buổi đã bắt đầu hoặc xác nhận và không tạo thêm buổi quá khứ. Chưa có giao diện dời riêng một buổi sang ngày khác.

Lịch có thể nhắc trước theo phút và theo các mốc ngày. Hoãn 10 phút chỉ thực hiện khi mốc mới chưa vượt giờ kết thúc. Xuất Excel không tạo thêm buổi trong cơ sở dữ liệu.

## Nhắc việc

Thiết lập giờ nhắc hằng ngày và số ngày trước deadline. Mặc định là 09:00 và 7 ngày. Chỉ công việc Cần làm/Đang thực hiện được nhắc; có nhắc gấp trong giờ cuối trước deadline. Thông báo được lưu dấu đã gửi để tránh gửi trùng sau khi khởi động lại.

Giữ ứng dụng đang chạy, máy bật và thức, tài khoản đang đăng nhập. Kiểm tra giờ/múi giờ máy và quyền thông báo Windows. Đóng cửa sổ để thu nhỏ; dùng Thoát hẳn để dừng ứng dụng. Khả năng khay hệ thống và thông báo Windows cần được kiểm tra trên máy đích. Khi mở lại, các lịch đã hết giờ không bị gửi dồn thông báo.

Khi thông báo Windows không gửi được, ứng dụng mở cửa sổ nhắc trong ứng dụng. Bấm trực tiếp thông báo Windows để mở app chưa được triển khai; dùng biểu tượng khay, menu Mở ứng dụng hoặc Thông báo gần nhất. Windows có thể ẩn thông báo đã được gửi khi bật Do not disturb.

## Excel

Mở Dữ liệu và báo cáo → Xuất báo cáo Excel. Chọn khoảng ngày cho các lần diễn ra của lịch. Báo cáo luôn chứa toàn bộ công việc, các buổi lịch trong khoảng đã chọn và định nghĩa lịch gốc. Tạo PivotTable từ bảng dữ liệu trên một sheet riêng khi cần. Excel đã xuất không tự đồng bộ với ứng dụng; báo cáo không thay thế bản sao lưu cơ sở dữ liệu.

## Sao lưu và khôi phục

Mở Dữ liệu và báo cáo → Sao lưu dữ liệu để tạo bản sao SQLite nhất quán. Giữ nhiều bản có ngày tháng tại nơi an toàn. Khôi phục dữ liệu trong cùng menu chỉ nhận bản sao lưu của bản dựng mới, thay thế toàn bộ dữ liệu và giữ một bản sao trước khi thay thế. Không dùng chức năng này để nạp cơ sở dữ liệu 1.7.0 chưa được xác nhận tương thích.

Khi sao chép thủ công, Thoát hẳn rồi mới chép `tasks.db` trong `%USERPROFILE%\NhacViecAnhHaMoi\data`. Dữ liệu không đồng bộ giữa các máy; mỗi tài khoản có cơ sở dữ liệu riêng.

## Gỡ cài đặt

Thoát hẳn và sao lưu trước. Gỡ qua Windows Settings hoặc lối tắt Gỡ cài đặt. Bộ gỡ chỉ xử lý tệp ứng dụng được cài, giữ nguyên thư mục dữ liệu của cả bản dựng mới lẫn bản 1.7.0.
