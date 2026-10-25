from __future__ import annotations

import shutil
from pathlib import Path


class UninstallError(RuntimeError):
    """Raised when the local CleanYourTV project cannot be removed safely."""


def uninstall_local_project(root: Path, *, confirmed: bool = False) -> Path:
    """Remove only the locally selected CleanYourTV project directory.

    This never sends commands to the TV and never deletes Android packages.
    The GUI must explicitly confirm the destructive action.
    """
    root = root.expanduser().resolve()
    if root == Path(root.anchor) or len(root.parts) < 3:
        raise UninstallError(f"Refusing to remove an unsafe path: {root}")
    if not root.exists():
        raise UninstallError(f"CleanYourTV folder does not exist: {root}")
    if not root.is_dir():
        raise UninstallError(f"CleanYourTV path is not a directory: {root}")

    markers = ("launcher", "tools", "README.md", "hyundai-clean.txt", "hyundai-debloat.txt")
    if not any((root / marker).exists() for marker in markers):
        raise UninstallError(
            "The selected folder does not look like a CleanYourTV project. Refusing to delete it."
        )
    if not confirmed:
        raise UninstallError("Explicit confirmation is required before uninstalling.")

    shutil.rmtree(root)
    return root
