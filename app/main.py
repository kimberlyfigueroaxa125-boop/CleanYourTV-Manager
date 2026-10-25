from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox, QLineEdit, QLabel, QPlainTextEdit, QPushButton

from app.core.adb import AdbClient, AdbError
from app.core.backup import create_backup
from app.core.clean_your_tv import LocalProject
from app.core.paths import APP_ROOT, find_cleanyourtv

UI_FILE = APP_ROOT / "app" / "ui" / "MainWindow.ui"


def load_ui():
    loader = QUiLoader()
    ui_file = QFile(str(UI_FILE))
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Не удалось открыть UI: {UI_FILE}")
    try:
        window = loader.load(ui_file)
    finally:
        ui_file.close()
    if window is None:
        raise RuntimeError("Qt Designer UI не удалось загрузить.")
    return window


def main() -> int:
    app = QApplication(sys.argv)
    try:
        window = load_ui()
    except Exception as exc:
        QMessageBox.critical(None, "CleanYourTV Manager", str(exc))
        return 1

    log = window.findChild(QPlainTextEdit, "log")
    status = window.findChild(QLabel, "tvStatus")
    title = window.findChild(QLabel, "title")
    ip_edit = window.findChild(QLineEdit, "tvIp")

    def button(name: str) -> QPushButton:
        item = window.findChild(QPushButton, name)
        if item is None:
            raise RuntimeError(f"UI button not found: {name}")
        return item

    def write_log(text: str) -> None:
        if log is not None:
            log.appendPlainText(text)

    def project() -> LocalProject | None:
        root = find_cleanyourtv()
        if root is None:
            QMessageBox.warning(
                window,
                "CleanYourTV",
                "Папка CleanYourTV не найдена. Задайте CLEANYOURTV_ROOT или разместите проект рядом с менеджером.",
            )
            return None
        return LocalProject(root)

    def connect_tv() -> None:
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Введите IP-адрес телевизора.")
            return
        try:
            client = AdbClient(ip)
            output = client.connect()
            write_log(f"> ADB connect {client.serial}")
            write_log(output or "> connected")
            status.setText("●  TV подключён")
            status.setStyleSheet("color:#52d273;font-weight:600;")
        except (AdbError, OSError) as exc:
            write_log(f"> ADB ERROR: {exc}")
            status.setText("●  Ошибка подключения")
            status.setStyleSheet("color:#f05b5b;font-weight:600;")
            QMessageBox.warning(window, "ADB", str(exc))

    def check_tv() -> None:
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Сначала введите IP-адрес.")
            return
        try:
            info = AdbClient(ip).info()
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
            write_log(f"> ADB: {info.serial} ({info.state})")
            status.setText(f"●  TV: {info.model}")
            status.setStyleSheet("color:#52d273;font-weight:600;")
        except (AdbError, OSError) as exc:
            write_log(f"> CHECK ERROR: {exc}")
            QMessageBox.warning(window, "Проверка ТВ", str(exc))

    def open_install() -> None:
        current = project()
        if current is None:
            return
        if not current.launcher_installer.is_file():
            QMessageBox.warning(window, "CleanYourTV", f"Не найден установщик:\n{current.launcher_installer}")
            return
        write_log(f"> CleanYourTV root: {current.root}")
        write_log(f"> Starting installer: {current.launcher_installer}")
        write_log("> PowerShell installer remains visible so its confirmations and errors are not hidden.")
        current.run_launcher_installer()

    def show_items(kind: str) -> None:
        current = project()
        if current is None:
            return
        items = current.list_directory(kind)
        write_log(f"> {kind}: {len(items)} item(s)")
        for item in items[:100]:
            write_log(f"  • {item}")

    def backup() -> None:
        current = project()
        if current is None:
            return
        try:
            destination = create_backup(current.root, APP_ROOT / "backups")
            write_log(f"> Backup created: {destination}")
            QMessageBox.information(window, "Резервная копия", f"Создана копия:\n{destination}")
        except OSError as exc:
            write_log(f"> BACKUP ERROR: {exc}")
            QMessageBox.critical(window, "Резервная копия", str(exc))

    def navigate(name: str, label: str) -> None:
        if title is not None:
            title.setText(label)
        write_log(f"> Opened: {label}")

    button("connectButton").clicked.connect(connect_tv)
    button("checkButton").clicked.connect(check_tv)
    button("installCleanButton").clicked.connect(open_install)
    button("themesQuickButton").clicked.connect(lambda: show_items("themes"))
    button("addonsQuickButton").clicked.connect(lambda: show_items("addons"))
    button("backupQuickButton").clicked.connect(backup)

    navigation = {
        "homeButton": "Главная",
        "installButton": "Установка",
        "themesButton": "Темы",
        "addonsButton": "Аддоны",
        "cleanupButton": "Очистка",
        "backupButton": "Резервная копия",
        "settingsButton": "Настройки",
    }
    for name, label in navigation.items():
        button(name).clicked.connect(lambda checked=False, n=name, l=label: navigate(n, l))

    ip_edit.setText(os.environ.get("TV_HOST", ""))
    write_log("> CleanYourTV Manager started")
    write_log("> Unofficial community GUI; upstream CleanYourTV remains separate.")
    write_log("> No Android package is disabled automatically.")

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
