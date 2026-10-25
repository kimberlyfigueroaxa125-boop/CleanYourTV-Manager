from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class LocalProject:
    root: Path

    @property
    def themes(self) -> Path:
        return self.root / "themes"

    @property
    def addons(self) -> Path:
        return self.root / "addons"

    @property
    def launcher_installer(self) -> Path:
        return self.root / "launcher" / "build-and-install.ps1"

    @property
    def tools(self) -> Path:
        return self.root / "tools"

    def list_directory(self, name: str) -> list[str]:
        folder = self.root / name
        if not folder.is_dir():
            return []
        return sorted(item.name for item in folder.iterdir() if item.is_dir())

    def run_launcher_installer(self) -> subprocess.Popen[str]:
        script = self.launcher_installer
        if not script.is_file():
            raise FileNotFoundError(f"Launcher installer not found: {script}")
        return subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            cwd=self.root,
            text=True,
        )
