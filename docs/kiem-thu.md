# Kết quả kiểm tra mã nguồn và bộ cài

## Bản 2.0.1 — giao diện mới

Ngày 22/10/2026: bản 2.0.1 đạt 77 kiểm thử trên Linux/Xvfb, hai kiểm tra ứng dụng `--self-test` / `--gui-smoke-test`, cùng 24 kiểm tra bố cục và 24 ảnh chụp ở 1120×720, 1366×768, cỡ chữ mặc định và Tk 120 DPI. Các kiểm tra hồi quy mới xác nhận văn bản dài không bị cắt khi thay đổi kích thước và nút lưu luôn hiển thị khi cuộn biểu mẫu.

Trên Windows, [lần dựng GitHub Actions 39719044251](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719044251) đã thành công với mã nguồn [6dc1acf1db2d04e6f9972e11d0fb5801f590496b](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/6dc1acf1db2d04e6f9972e11d0fb5801f590496b), runner `windows-2022` và Python 3.13 x64. Lần dựng đã chạy đạt 77 kiểm thử, tạo EXE bằng PyInstaller và chạy thành công hai kiểm tra `--self-test` / `--gui-smoke-test` của EXE. Kiểm tra giao diện đạt 24 tình huống bố cục ở cỡ chữ mặc định và Tk 120 DPI. Bộ cài NSIS đã qua kiểm tra cài/gỡ im lặng, chạy tự kiểm tra sau khi cài và giữ nguyên các tệp dữ liệu đánh dấu.

[Bản phát hành Windows 2.0.1](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.1-preview.1) đã được xuất bản từ artifact đã kiểm chứng qua [workflow phát hành 39719246638](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39719246638). Bản phát hành có tám tệp, gồm bộ cài, SHA256, báo cáo kiểm tra và ảnh giao diện Windows. Bộ cài `NhacViecAnhHa-Setup-2.0.1-x64.exe` có kích thước 17.070.511 byte, SHA256 `4590f51fd53842366c219f12613a79fd47dbf3986c52211408575cb93e3da38c`.

Các kết quả này xác nhận quá trình dựng và các kiểm tra tự động; khay hệ thống, thông báo Windows và tự chạy khi đăng nhập vẫn cần kiểm tra trên máy sử dụng thực tế. Bộ cài chưa ký số.

## Lịch sử bản 2.0.0

Ngày kiểm tra gần nhất: 22/10/2026. Trên Windows, [lần dựng GitHub Actions 39707130999](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707130999) đã thành công với mã nguồn [b0097407d3a19f8d5c3e564206af40f9e1531f26](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/tree/b0097407d3a19f8d5c3e564206af40f9e1531f26), runner `windows-2022`, Python 3.13 x64 và dependency đã ghim trong `requirements-build.txt`.

Lịch sử Linux: Python 3.12.14, Tk 9.0.4 trên màn hình ảo Xvfb. Ngày 21/10 đã kiểm tra trong môi trường riêng với dependency ghim trong `requirements.txt`: openpyxl 3.1.5, et-xmlfile 2.0.0, Pillow 11.3.0. Lần kiểm tra lại 22/10 dùng runtime hiện có: openpyxl 3.1.5, Pillow 12.3.0.

Bộ kiểm thử dưới đây đã đạt đầy đủ trên Linux/Xvfb và trong lần dựng Windows nêu trên:

| Nhóm | Đạt | Bỏ qua | Thất bại |
| --- | ---: | ---: | ---: |
| SQLite, lịch lặp, nhắc việc, Excel | 47 | 0 | 0 |
| Giao diện lịch và chọn ngày | 10 | 0 | 0 |
| Giao diện công việc và tích hợp cửa sổ chính | 7 | 0 | 0 |
| Khóa một phiên, adapter khay và thông báo | 11 | 0 | 0 |
| Tổng | 75 | 0 | 0 |

Các kiểm tra GUI dùng widget Tkinter thật và cơ sở dữ liệu tạm. Kiểm tra adapter Windows dùng đối tượng thay thế có kiểm soát; chúng không xác nhận khay hoặc thông báo trên Windows thật.

Lệnh đã chạy trên Linux từ thư mục gốc dự án:

```sh
DISPLAY=:99 python -m unittest discover -s tests -v
python -m nhacviec --self-test --self-test-report /tmp/nhacviec-final-core.json
DISPLAY=:99 python -m nhacviec --gui-smoke-test --self-test-report /tmp/nhacviec-final-gui.json
```

`--self-test` đạt 4 nhóm kiểm tra: công việc và hai bộ lọc; lịch tháng/năm với ngày thiếu; báo cáo Excel và bảng dữ liệu; sao lưu/khôi phục. `--gui-smoke-test` đạt thêm kiểm tra cửa sổ công việc và chuyển Tuần/Tháng/Năm. Mọi phép kiểm tra dùng dữ liệu tạm, không chứa công việc cá nhân và không ghi vào dữ liệu bản 1.7.0.

Các tình huống hồi quy đã kiểm tra gồm việc tạm dừng/mở lại trong nhóm Cần làm, đổi trạng thái không đổi bộ lọc đang chọn, giữ biểu mẫu chưa lưu khi hủy yêu cầu đóng, ngày 31 không bị lệch sau tháng 2, ngày 29/2, nhắc không trùng sau khởi động lại, không gửi dồn buổi đã hết giờ, sửa lịch không tạo thêm buổi quá khứ, bật lại không tạo bù thời gian tạm dừng, sao lưu nhất quán và từ chối cơ sở dữ liệu khác schema.

Lần dựng Windows đã chạy đạt 75 kiểm thử, tạo EXE bằng PyInstaller 6.16.0, chạy thành công `--self-test` và `--gui-smoke-test` của EXE, rồi tạo bộ cài bằng NSIS 3.11. Kiểm tra cài đặt/gỡ cài đặt im lặng đã đạt; EXE sau khi cài vượt qua tự kiểm tra và các tệp dữ liệu đánh dấu trong thư mục của cả bản mới lẫn bản 1.7.0 được giữ nguyên. Hai báo cáo JSON và SHA256 được lưu cùng bộ cài trong artifact.

[Bản phát hành thử nghiệm Windows 2.0.0](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/tag/windows-2.0.0-preview.1) đã được xuất bản từ artifact của lần dựng này qua [workflow phát hành 39707344668](https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/actions/runs/39707344668). Bản phát hành có bốn tệp: bộ cài, `SHA256SUMS.txt`, `self-test.json` và `gui-smoke-test.json`. Bộ cài có kích thước 17.048.630 byte, SHA256 `5abf9b9ab560b3a58ad1c4e9a394de3664de6fe382d27a29e6e481cb9e4c8cef`.

Chưa kiểm tra khay hệ thống, thông báo Windows và tự chạy khi đăng nhập trên máy sử dụng thực tế. Bộ cài chưa ký số. Chưa có mẫu cơ sở dữ liệu 1.7.0 để viết và kiểm thử chuyển đổi dữ liệu cũ.

Cập nhật 22/10: đóng kết nối SQLite đích trước khi đổi tên tệp sao lưu, tránh lỗi khóa tệp trên Windows. Thêm kiểm thử mô phỏng quy tắc khóa tệp của Windows; đóng tường minh các kết nối SQLite trong fixture kiểm thử. Bộ 75 kiểm thử chạy đạt đầy đủ trên Linux/Xvfb, không có ca bỏ qua. Kiểm thử ứng dụng `--self-test` cũng đạt 4 nhóm kiểm tra.
