from pathlib import Path

from app.core import paths


def test_app_root_exists() -> None:
    assert paths.APP_ROOT.name == "CleanYourTV-Manager"


def test_find_adb_prefers_valid_configured_path(monkeypatch, tmp_path: Path):
    adb = tmp_path / "adb.exe"
    adb.write_text("", encoding="utf-8")
    monkeypatch.setenv("ADB_PATH", str(adb))
    monkeypatch.setattr(paths.shutil, "which", lambda _name: None)
    assert paths.find_adb() == str(adb.resolve())


def test_find_adb_uses_path_when_not_configured(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(paths.shutil, "which", lambda _name: str(tmp_path / "adb"))
    assert paths.find_adb() == str(tmp_path / "adb")


def test_find_cleanyourtv_uses_configured_root(monkeypatch, tmp_path: Path):
    root = tmp_path / "CleanYourTV"
    (root / "tools").mkdir(parents=True)
    monkeypatch.setenv("CLEANYOURTV_ROOT", str(root))
    assert paths.find_cleanyourtv() == root.resolve()


def test_find_cleanyourtv_ignores_non_checkout(monkeypatch, tmp_path: Path):
    root = tmp_path / "not-a-checkout"
    root.mkdir()
    monkeypatch.setenv("CLEANYOURTV_ROOT", str(root))
    assert paths.find_cleanyourtv() is None
