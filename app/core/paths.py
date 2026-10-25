from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]


def find_adb() -> str | None:
    configured = os.environ.get("ADB_PATH", "").strip()
    if configured and Path(configured).is_file():
        return configured

    candidates = [
        shutil_path / "adb.exe"
        for shutil_path in _platform_tools_candidates()
        if (shutil_path / "adb.exe").is_file()
    ]
    return str(candidates[0]) if candidates else None


def _platform_tools_candidates() -> list[Path]:
    home = Path.home()
    sdk = Path(os.environ.get("ANDROID_SDK_ROOT", os.environ.get("ANDROID_HOME", home / "AppData" / "Local" / "Android" / "Sdk")))
    return [
        sdk / "platform-tools",
        Path("C:/Android/Sdk/platform-tools"),
    ]


def find_cleanyourtv() -> Path | None:
    configured = os.environ.get("CLEANYOURTV_ROOT", "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([
        APP_ROOT / "CleanYourTV",
        APP_ROOT.parent / "CleanYourTV",
        Path.home() / "CleanYourTV",
        Path("C:/Users/User/CleanYourTV"),
    ])

    for path in candidates:
        if path.is_dir() and (path / "tools").is_dir():
            return path.resolve()
    return None
