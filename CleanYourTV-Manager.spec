from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH)
hiddenimports = collect_submodules("PySide6")

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "app" / "ui" / "MainWindow.ui"), "app/ui"),
        (str(root / "app" / "ui" / "UninstallDialog.ui"), "app/ui"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CleanYourTV-Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
