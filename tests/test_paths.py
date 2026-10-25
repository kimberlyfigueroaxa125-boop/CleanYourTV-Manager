from pathlib import Path

from app.core.paths import APP_ROOT


def test_app_root_exists() -> None:
    assert isinstance(APP_ROOT, Path)
    assert APP_ROOT.name == "CleanYourTV-Manager"
