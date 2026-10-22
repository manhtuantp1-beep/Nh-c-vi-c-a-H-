# Build on Windows with scripts/build_windows.ps1.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_root = Path(SPECPATH).resolve().parent
datas = [(str(project_root / "README.md"), "."),
         (str(project_root / "docs"), "docs")]
binaries = []
hiddenimports = ["PIL.Image", "PIL.ImageDraw", "PIL.ImageTk", "pystray", "pystray._win32", "winotify"]
for package in ("openpyxl", "winotify"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [str(project_root / "NhoViec.pyw")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NhacViecAnhHa",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="NhacViecAnhHa")
