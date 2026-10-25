from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .adb import AdbError
from .clean_your_tv import LocalProject


class ThemeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ThemeInfo:
    name: str
    path: Path


def discover_themes(project: LocalProject) -> list[ThemeInfo]:
    if not project.themes.is_dir():
        return []
    result: list[ThemeInfo] = []
    for path in sorted(project.themes.iterdir(), key=lambda p: p.name.lower()):
        if path.is_dir() and (path / "config.json").is_file():
            result.append(ThemeInfo(path.name, path))
    return result


def install_theme(project: LocalProject, theme: ThemeInfo, host: str) -> str:
    if not host.strip():
        raise ThemeError("TV IP address is required.")
    script = project.tools / "theme.ps1"
    if not script.is_file():
        raise ThemeError(f"Theme installer was not found: {script}")
    if not (theme.path / "config.json").is_file():
        raise ThemeError(f"Theme '{theme.name}' has no config.json.")

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-TvHost",
        host.strip(),
        str(theme.path),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=project.tools,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ThemeError("Theme installation timed out after 180 seconds.") from exc
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise ThemeError(output or "Theme installation failed.")
    return output or f"Theme '{theme.name}' installed."


def reset_theme(project: LocalProject, host: str) -> str:
    script = project.tools / "theme.ps1"
    if not script.is_file():
        raise ThemeError(f"Theme installer was not found: {script}")
    command = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-TvHost", host.strip(), "-Reset",
    ]
    result = subprocess.run(
        command, cwd=project.tools, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180, check=False,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise ThemeError(output or "Theme reset failed.")
    return output or "Built-in theme restored."
