from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]


def find_adb() -> str | None:
    """Find adb from an explicit path, PATH, or common Android SDK locations."""
    configured = os.environ.get("ADB_PATH", "").strip()
    if configured and Path(configured).is_file():
        return str(Path(configured).resolve())

    on_path = shutil.which("adb")
    if on_path:
        return on_path

    home = Path.home()
    sdk_text = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    sdk = Path(sdk_text) if sdk_text else home / "AppData" / "Local" / "Android" / "Sdk"
    candidates = [
        sdk / "platform-tools" / "adb.exe",
        Path("C:/Android/Sdk/platform-tools/adb.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def find_cleanyourtv() -> Path | None:
    """Locate a local CleanYourTV checkout without assuming a specific username."""
    configured = os.environ.get("CLEANYOURTV_ROOT", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            APP_ROOT / "CleanYourTV",
            APP_ROOT.parent / "CleanYourTV",
            Path.home() / "CleanYourTV",
            Path.home() / "test" / "CleanYourTV",
        ]
    )

    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved.is_dir() and (resolved / "tools").is_dir():
            return resolved
    return None
