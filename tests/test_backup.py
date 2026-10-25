from pathlib import Path

from app.core.backup import create_backup


def test_create_backup(tmp_path: Path) -> None:
    source = tmp_path / "CleanYourTV"
    source.mkdir()
    (source / "example.txt").write_text("hello", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "config").write_text("ignored", encoding="utf-8")

    destination = create_backup(source, tmp_path / "backups")

    assert destination.is_dir()
    assert (destination / "example.txt").read_text(encoding="utf-8") == "hello"
    assert not (destination / ".git").exists()
