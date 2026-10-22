"""Run with python -m nhacviec; no user database is opened during self-tests."""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import traceback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nhắc việc anh Hà — bản dựng mới")
    parser.add_argument("--data-dir", type=Path, help="Thư mục dữ liệu riêng của bản dựng mới")
    parser.add_argument("--minimized", action="store_true", help="Khởi động thu nhỏ")
    parser.add_argument("--self-test", action="store_true", help="Kiểm tra bản đóng gói bằng dữ liệu tạm")
    parser.add_argument("--gui-smoke-test", action="store_true", help="Kiểm tra cửa sổ bằng dữ liệu tạm")
    parser.add_argument("--self-test-report", type=Path, help="Ghi kết quả kiểm tra dạng JSON")
    args = parser.parse_args(argv)
    if args.self_test or args.gui_smoke_test:
        report = {"passed": False, "gui": args.gui_smoke_test}
        try:
            from .selftest import run_self_test
            report.update(run_self_test(gui=args.gui_smoke_test))
            result = 0
        except Exception:
            report["error"] = traceback.format_exc()
            result = 1
        if args.self_test_report:
            args.self_test_report.parent.mkdir(parents=True, exist_ok=True)
            args.self_test_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if sys.stdout is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return result

    from .storage import Storage, default_database_path
    data_dir = (args.data_dir or default_database_path().parent.parent).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    log_dir = data_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(log_dir / "lifecycle.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s")
    import tkinter as tk
    from tkinter import messagebox
    from .platform_support import InstanceLock
    lock = InstanceLock(data_dir)
    root = None
    store = None
    try:
        root = tk.Tk()
        root.withdraw()
        if not lock.acquire():
            messagebox.showinfo("Ứng dụng đang chạy", "Nhắc việc anh Hà đang chạy. Mở lại cửa sổ từ khay hệ thống hoặc thanh tác vụ Windows.", parent=root)
            return 0
        from .app import NhacViecApp
        store = Storage(data_dir / "data" / "tasks.db")
        app = NhacViecApp(root, store, data_dir)
        app.instance_lock = lock
        root.deiconify()
        if args.minimized:
            root.after(250, app.minimize)
        logging.info("Khởi động ứng dụng; data_dir=%s", data_dir)
        root.mainloop()
        return 0
    except Exception as exc:
        logging.exception("Không thể khởi động")
        try:
            messagebox.showerror("Không thể mở ứng dụng", f"{exc}\n\nNhật ký: {log_dir / 'lifecycle.log'}", parent=root)
        except tk.TclError:
            pass
        return 1
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:
                pass
        lock.close()
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass
        logging.getLogger().removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
