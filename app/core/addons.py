from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .adb import AdbClient, AdbError
from .clean_your_tv import LocalProject


class AddonError(RuntimeError):
    pass


@dataclass(frozen=True)
class AddonInfo:
    name: str
    path: Path


def discover_addons(project: LocalProject) -> list[AddonInfo]:
    if not project.addons.is_dir():
        return []
    result: list[AddonInfo] = []
    for path in sorted(project.addons.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_dir() or not (path / "README.md").is_file():
            continue
        if (path / "app").is_dir() and (
            (path / "gradlew.bat").is_file() or (path / "gradlew").is_file()
        ):
            result.append(AddonInfo(path.name, path))
    return result


def _existing_apk(addon: AddonInfo) -> Path | None:
    output = addon.path / "app" / "build" / "outputs" / "apk"
    if not output.is_dir():
        return None
    candidates = sorted(output.rglob("*.apk"), key=lambda p: p.stat().st_mtime, reverse=True)
    release = [p for p in candidates if "release" in p.parts]
    return (release or candidates)[0] if (release or candidates) else None


def build_addon(addon: AddonInfo) -> Path:
    apk = _existing_apk(addon)
    if apk is not None:
        return apk

    if (addon.path / "gradlew.bat").is_file():
        command = [str(addon.path / "gradlew.bat"), "--no-daemon", "assembleRelease"]
    elif (addon.path / "gradlew").is_file():
        command = [str(addon.path / "gradlew"), "--no-daemon", "assembleRelease"]
    else:
        raise AddonError(f"Gradle wrapper not found in {addon.path}")

    try:
        result = subprocess.run(
            command,
            cwd=addon.path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AddonError("Add-on build timed out after 10 minutes.") from exc

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise AddonError(output or "Add-on build failed.")

    apk = _existing_apk(addon)
    if apk is None:
        raise AddonError("Build completed, but no APK was found in app/build/outputs/apk.")
    return apk


def install_addon(client: AdbClient, addon: AddonInfo) -> tuple[Path, str]:
    try:
        apk = build_addon(addon)
        result = client.run("install", "-r", str(apk), timeout=180)
    except (OSError, AdbError) as exc:
        raise AddonError(str(exc)) from exc

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or "success" not in output.lower():
        raise AddonError(output or "ADB APK installation failed.")
    return apk, output
