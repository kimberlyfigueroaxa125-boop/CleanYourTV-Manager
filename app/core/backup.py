from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


IGNORED = shutil.ignore_patterns(".git", ".venv", "venv", "__pycache__", "*.pyc")


def create_backup(source: Path, destination_root: Path) -> Path:
    if not source.is_dir():
        raise FileNotFoundError(f"CleanYourTV directory not found: {source}")

    destination_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = destination_root / f"cleanyourtv-{stamp}"
    shutil.copytree(source, destination, ignore=IGNORED)
    return destination
