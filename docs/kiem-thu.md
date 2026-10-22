# Kết quả kiểm tra mã nguồn 2.0.0

Ngày kiểm tra gần nhất: 22/10/2026. Nền tảng đã chạy: Linux, Python 3.12.14, Tk 9.0.4 trên màn hình ảo Xvfb. Ngày 21/10 đã kiểm tra trong môi trường riêng với dependency ghim trong `requirements.txt`: openpyxl 3.1.5, et-xmlfile 2.0.0, Pillow 11.3.0. Lần kiểm tra lại 22/10 dùng runtime hiện có: openpyxl 3.1.5, Pillow 12.3.0.

| Nhóm | Đạt | Bỏ qua | Thất bại |
| --- | ---: | ---: | ---: |
| SQLite, lịch lặp, nhắc việc, Excel | 47 | 0 | 0 |
| Giao diện lịch và chọn ngày | 10 | 0 | 0 |
| Giao diện công việc và tích hợp cửa sổ chính | 7 | 0 | 0 |
| Khóa một phiên, adapter khay và thông báo | 11 | 0 | 0 |
| Tổng | 75 | 0 | 0 |

Các kiểm tra GUI dùng widget Tkinter thật và cơ sở dữ liệu tạm. Kiểm tra adapter Windows dùng đối tượng thay thế có kiểm soát; chúng không xác nhận khay hoặc thông báo trên Windows thật.

Lệnh đã chạy từ thư mục gốc dự án:

```sh
DISPLAY=:99 python -m unittest discover -s tests -v
python -m nhacviec --self-test --self-test-report /tmp/nhacviec-final-core.json
DISPLAY=:99 python -m nhacviec --gui-smoke-test --self-test-report /tmp/nhacviec-final-gui.json
```

`--self-test` đạt 4 nhóm kiểm tra: công việc và hai bộ lọc; lịch tháng/năm với ngày thiếu; báo cáo Excel và bảng dữ liệu; sao lưu/khôi phục. `--gui-smoke-test` đạt thêm kiểm tra cửa sổ công việc và chuyển Tuần/Tháng/Năm. Mọi phép kiểm tra dùng dữ liệu tạm, không chứa công việc cá nhân và không ghi vào dữ liệu bản 1.7.0.

Các tình huống hồi quy đã kiểm tra gồm việc tạm dừng/mở lại trong nhóm Cần làm, đổi trạng thái không đổi bộ lọc đang chọn, giữ biểu mẫu chưa lưu khi hủy yêu cầu đóng, ngày 31 không bị lệch sau tháng 2, ngày 29/2, nhắc không trùng sau khởi động lại, không gửi dồn buổi đã hết giờ, sửa lịch không tạo thêm buổi quá khứ, bật lại không tạo bù thời gian tạm dừng, sao lưu nhất quán và từ chối cơ sở dữ liệu khác schema.

Chưa chạy: Python 3.13 trên Windows; PyInstaller/NSIS trên Windows; cài/gỡ, tự chạy khi đăng nhập, khay và thông báo Windows thật. Workflow GitHub Actions và script Windows đã được chuẩn bị, chưa được thực thi trong phiên này. Chưa tạo hoặc ký số bộ cài EXE. Chưa có mẫu cơ sở dữ liệu 1.7.0 để viết và kiểm thử chuyển đổi dữ liệu cũ.

Cập nhật 22/10: đóng kết nối SQLite đích trước khi đổi tên tệp sao lưu, tránh lỗi khóa tệp trên Windows. Thêm kiểm thử mô phỏng quy tắc khóa tệp của Windows; đóng tường minh các kết nối SQLite trong fixture kiểm thử. Bộ 75 kiểm thử chạy đạt đầy đủ trên Linux/Xvfb, không có ca bỏ qua. Kiểm thử ứng dụng `--self-test` cũng đạt 4 nhóm kiểm tra.
