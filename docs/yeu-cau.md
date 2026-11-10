# Phạm vi dựng lại mã nguồn

Nguồn tham khảo là tài liệu PDF 14 trang, README và cấu trúc bộ cài 1.7.0 đã cung cấp, cùng các yêu cầu bổ sung về lịch tháng/năm, tổng việc theo deadline, ghi chú từng việc và ba kiểu xem công việc. Bản 2.0.5 thay khối lọc công việc trước đây bằng Lưới/Danh sách/Rộng. Mã nguồn mới không giải biên dịch để tuyên bố khôi phục mã dự án gốc, không kèm dữ liệu cá nhân và không tự chạy bộ cài đã tải lên.

## Nghiệp vụ được xây dựng

- Công việc: tạo/sửa, deadline, phân loại, nội dung/yêu cầu, ghi chú riêng, mã tự động, bắt đầu/tạm dừng/hoàn thành/hủy/mở lại và tìm kiếm theo tên/mã bằng cửa sổ Ctrl+F.
- Cách xem: Lưới mặc định, Danh sách gọn, Rộng; tự đổi số cột theo chỗ trống, giữ cùng dữ liệu khi đổi kiểu. Việc cần làm hiển thị toàn bộ chưa hoàn thành, các trang trạng thái giữ riêng.
- Lịch: xem tuần/tháng/năm; tổng hợp công việc theo ngày deadline, mở thẻ việc trong ngày giống danh sách công việc, tách lịch hẹn; một lần, hằng tuần/tháng/năm; giới hạn chu kỳ, xử lý ngày thiếu, kết quả từng lần, nhắc và hoãn.
- Nhắc việc: thiết lập giờ/ngày trước deadline, nhắc gấp, các mốc lịch, dấu chống trùng được lưu trong SQLite.
- Excel: toàn bộ công việc, buổi lịch theo khoảng và định nghĩa lịch; cột ghi chú, bảng có tên cho PivotTable.
- Dữ liệu: SQLite riêng cho bản dựng mới, sao lưu nhất quán, kiểm tra schema khi khôi phục và giữ bản dự phòng; nâng cấp schema 1 sang 2 trước khi dùng ghi chú, giữ bản trước nâng cấp và tiếp nhận bản sao lưu cũ hợp lệ.
- Phân phối: mã nguồn, dependency đã ghim phiên bản, script PyInstaller/NSIS và workflow build Windows; bản 2.0.4 bổ sung kiểm tra khóa tệp và quyền ghi trước cập nhật/gỡ, không tự ép tắt chương trình.

## Giới hạn thiết kế

- Không tuyên bố tương thích cơ sở dữ liệu bản 1.7.0. Cần bản sao dữ liệu đã được cho phép để xây dựng và kiểm tra bộ chuyển đổi riêng.
- Không có tài khoản đám mây, đồng bộ đa máy hoặc Outlook/Google Calendar.
- Chưa có lịch âm, quy tắc thứ mấy trong tháng, dời một buổi sang ngày khác, checklist theo buổi hoặc đo thời gian làm việc thực tế.
- Giờ là giờ địa phương của máy. Không gửi nhắc đúng giờ khi máy tắt/ngủ hoặc ứng dụng đã thoát.
- Cấu hình build Windows cần được chạy thật trước khi có bộ cài. Tệp `.spec`, `.nsi` và workflow là quy trình tạo bộ cài, chưa phải bằng chứng một `.exe` đã được tạo và kiểm tra.
- Không có chữ ký số, dịch vụ tự động phát hành công khai hoặc bảo đảm chức năng tải tệp của phiên chat.

## Các kiểm tra bắt buộc trước phát hành

1. Bộ kiểm thử nghiệp vụ chạy đủ, không coi zero-test là thành công.
2. Tạo/sửa/chuyển trạng thái, ba kiểu xem và tìm kiếm Ctrl+F trên cơ sở dữ liệu trống; mã trùng phút vẫn riêng biệt. Lưới là mặc định; đổi kiểu không đổi công việc hay ghi chú; vùng bộ lọc cũ không chiếm diện tích.
3. Tổng công việc theo ngày khớp deadline và danh sách ngày, đổi deadline không trùng; ghi chú đúng công việc, nhiều dòng có dấu được giữ. Lịch qua cuối tháng, tháng thiếu ngày, năm nhuận và giới hạn lặp; đánh dấu một buổi không dừng chu kỳ.
4. Thông báo không trùng sau khởi động lại, không nhắc lịch đã hết giờ, hoãn không vượt giờ kết thúc.
5. Excel mở được và chứa đủ dữ liệu và ghi chú; sao lưu/khôi phục nhất quán, từ chối cơ sở dữ liệu không đúng schema.
6. Windows: tạo EXE, chạy tự kiểm tra của EXE, cài/mở/gỡ, dữ liệu cũ không bị xóa, khay hệ thống và tự chạy hoạt động. Nâng cấp khi bản đã phát hành còn giữ thư viện phải dừng trước khi chép; sau đóng chương trình mới cập nhật. Kiểm tra tương tự khi gỡ và khi không có quyền ghi thư mục.
