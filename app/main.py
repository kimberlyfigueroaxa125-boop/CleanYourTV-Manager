from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QFile, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox

APP_ROOT = Path(__file__).resolve().parents[1]
UI_FILE = APP_ROOT / "app" / "ui" / "MainWindow.ui"


def find_adb() -> str | None:
    configured = os.environ.get("ADB_PATH")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("adb")


def find_cleanyourtv() -> Path | None:
    candidates = [
        Path(os.environ.get("CLEANYOURTV_ROOT", "")),
        APP_ROOT / "CleanYourTV",
        APP_ROOT.parent / "CleanYourTV",
        Path.home() / "CleanYourTV",
        Path("C:/Users/User/CleanYourTV"),
    ]
    for path in candidates:
        if str(path) and path.exists() and (path / "tools").exists():
            return path
    return None


def run_process(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main() -> int:
    app = QApplication(sys.argv)
    loader = QUiLoader()
    ui_file = QFile(str(UI_FILE))
    if not ui_file.open(QFile.ReadOnly):
        QMessageBox.critical(None, "CleanYourTV Manager", f"Не удалось открыть UI: {UI_FILE}")
        return 1
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        QMessageBox.critical(None, "CleanYourTV Manager", "Qt Designer UI не удалось загрузить.")
        return 1

    log = window.findChild(type(window.log), "log")
    status = window.findChild(type(window.tvStatus), "tvStatus")
    ip_edit = window.findChild(type(window.tvIp), "tvIp")

    def write_log(text: str) -> None:
        log.appendPlainText(text)

    def adb_cmd(ip: str, *args: str) -> subprocess.CompletedProcess[str]:
        adb = find_adb()
        if not adb:
            raise RuntimeError("ADB не найден. Установите Android SDK Platform-Tools или задайте ADB_PATH.")
        return run_process([adb, "-s", f"{ip}:5555", *args])

    def connect_tv() -> None:
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Введите IP-адрес телевизора.")
            return
        adb = find_adb()
        if not adb:
            QMessageBox.warning(window, "ADB", "ADB не найден. Установите Platform-Tools.")
            return
        write_log(f"> ADB connect {ip}:5555")
        result = run_process([adb, "connect", f"{ip}:5555"])
        output = (result.stdout + result.stderr).strip()
        write_log(output or "> no output")
        if result.returncode == 0 and ("connected" in output.lower() or "already" in output.lower()):
            status.setText("●  TV подключён")
            status.setStyleSheet("color:#52d273;font-weight:600;")
        else:
            status.setText("●  Ошибка подключения")
            status.setStyleSheet("color:#f05b5b;font-weight:600;")

    def check_tv() -> None:
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Сначала введите IP-адрес.")
            return
        try:
            model = adb_cmd(ip, "shell", "getprop", "ro.product.model")
            manufacturer = adb_cmd(ip, "shell", "getprop", "ro.product.manufacturer")
            android = adb_cmd(ip, "shell", "getprop", "ro.build.version.release")
            if model.returncode == 0:
                write_log(f"> Manufacturer: {manufacturer.stdout.strip() or 'unknown'}")
                write_log(f"> Model: {model.stdout.strip() or 'unknown'}")
                write_log(f"> Android: {android.stdout.strip() or 'unknown'}")
                status.setText(f"●  TV: {model.stdout.strip() or 'Connected'}")
                status.setStyleSheet("color:#52d273;font-weight:600;")
            else:
                write_log(f"> ADB check failed: {model.stderr.strip()}")
        except Exception as exc:
            write_log(f"> ERROR: {exc}")
            QMessageBox.warning(window, "Проверка ТВ", str(exc))

    def open_install() -> None:
        root = find_cleanyourtv()
        if not root:
            QMessageBox.warning(window, "CleanYourTV", "Локальная папка CleanYourTV не найдена. Задайте CLEANYOURTV_ROOT или положите проект рядом с менеджером.")
            return
        script = root / "launcher" / "build-and-install.ps1"
        if not script.exists():
            QMessageBox.warning(window, "CleanYourTV", f"Не найден установщик launcher:\n{script}")
            return
        write_log(f"> CleanYourTV root: {root}")
        write_log(f"> Installer found: {script}")
        write_log("> Вызов установщика намеренно оставлен явным, чтобы PowerShell показывал его подтверждения и ошибки.")
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], cwd=root)

    def show_info(kind: str) -> None:
        root = find_cleanyourtv()
        if not root:
            write_log(f"> {kind}: CleanYourTV root not found")
            return
        folder = root / kind
        if folder.exists():
            items = sorted(p.name for p in folder.iterdir())
            write_log(f"> {kind}: {len(items)} items")
            for item in items[:50]:
                write_log(f"  - {item}")
        else:
            write_log(f"> {kind}: folder not found: {folder}")

    def backup() -> None:
        root = find_cleanyourtv()
        if not root:
            QMessageBox.warning(window, "Резервная копия", "Папка CleanYourTV не найдена.")
            return
        backup_dir = APP_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        destination = backup_dir / "cleanyourtv-project-copy"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(root, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv"))
        write_log(f"> Backup created: {destination}")

    def navigate(button_name: str) -> None:
        buttons = ["homeButton", "installButton", "themesButton", "addonsButton", "cleanupButton", "backupButton", "settingsButton"]
        for name in buttons:
            button = window.findChild(type(window.homeButton), name)
            if button:
                button.setChecked(name == button_name and button.isCheckable())
        labels = {
            "homeButton": "Главная",
            "installButton": "Установка",
            "themesButton": "Темы",
            "addonsButton": "Аддоны",
            "cleanupButton": "Очистка",
            "backupButton": "Резервная копия",
            "settingsButton": "Настройки",
        }
        window.title.setText(labels.get(button_name, "CleanYourTV Manager"))
        write_log(f"> Opened: {labels.get(button_name, button_name)}")

    window.connectButton.clicked.connect(connect_tv)
    window.checkButton.clicked.connect(check_tv)
    window.installCleanButton.clicked.connect(open_install)
    window.themesQuickButton.clicked.connect(lambda: show_info("themes"))
    window.addonsQuickButton.clicked.connect(lambda: show_info("addons"))
    window.backupQuickButton.clicked.connect(backup)
    window.homeButton.clicked.connect(lambda: navigate("homeButton"))
    window.installButton.clicked.connect(lambda: navigate("installButton"))
    window.themesButton.clicked.connect(lambda: navigate("themesButton"))
    window.addonsButton.clicked.connect(lambda: navigate("addonsButton"))
    window.cleanupButton.clicked.connect(lambda: navigate("cleanupButton"))
    window.backupButton.clicked.connect(lambda: navigate("backupButton"))
    window.settingsButton.clicked.connect(lambda: navigate("settingsButton"))

    ip_edit.setText(os.environ.get("TV_HOST", ""))
    write_log("> CleanYourTV Manager started")
    write_log("> This is an unofficial community GUI; upstream CleanYourTV remains separate.")
    write_log("> No package is disabled automatically.")

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
