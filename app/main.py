from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
)
from PySide6.QtUiTools import QUiLoader

from app.core.adb import AdbClient, AdbError
from app.core.backup import create_backup
from app.core.clean_your_tv import LocalProject
from app.core.paths import APP_ROOT, find_cleanyourtv
from app.core.uninstaller import UninstallError, uninstall_local_project

UI_FILE = APP_ROOT / "app" / "ui" / "MainWindow.ui"
UNINSTALL_UI_FILE = APP_ROOT / "app" / "ui" / "UninstallDialog.ui"

PAGES = {
    "homeButton": ("Главная", "homePage", "⌂  Главная"),
    "installButton": ("Установка", "installPage", "▣  Установка"),
    "themesButton": ("Темы", "themesPage", "✦  Темы"),
    "addonsButton": ("Аддоны", "addonsPage", "◇  Аддоны"),
    "cleanupButton": ("Очистка", "cleanupPage", "♲  Очистка"),
    "backupButton": ("Резервная копия", "backupPage", "▣  Резервная копия"),
    "settingsButton": ("Настройки", "settingsPage", "⚙  Настройки"),
}


def load_ui(path: Path):
    loader = QUiLoader()
    ui_file = QFile(str(path))
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Не удалось открыть UI: {path}")
    try:
        window = loader.load(ui_file)
    finally:
        ui_file.close()
    if window is None:
        raise RuntimeError(f"Qt Designer UI не удалось загрузить: {path}")
    return window


def main() -> int:
    app = QApplication(sys.argv)
    try:
        window = load_ui(UI_FILE)
    except Exception as exc:
        QMessageBox.critical(None, "CleanYourTV Manager", str(exc))
        return 1

    def required(widget_type, name: str):
        widget = window.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"Не найден элемент интерфейса: {name}")
        return widget

    try:
        log = required(QPlainTextEdit, "log")
        status = required(QLabel, "tvStatus")
        title = required(QLabel, "title")
        ip_edit = required(QLineEdit, "tvIp")
        stack = required(QStackedWidget, "pageStack")
    except RuntimeError as exc:
        QMessageBox.critical(window, "CleanYourTV Manager", str(exc))
        return 1

    def button(name: str) -> QPushButton:
        return required(QPushButton, name)

    def write_log(message: str) -> None:
        log.appendPlainText(message)

    def project(show_warning: bool = True) -> LocalProject | None:
        root = find_cleanyourtv()
        if root is None:
            if show_warning:
                QMessageBox.warning(
                    window,
                    "CleanYourTV",
                    "Папка CleanYourTV не найдена. Задайте CLEANYOURTV_ROOT или разместите исходный проект рядом с менеджером.",
                )
            return None
        return LocalProject(root)

    def set_status(message: str, color: str = "#f0b44d") -> None:
        status.setText(message)
        status.setStyleSheet(f"color:{color};font-weight:600;")

    def navigate(button_name: str) -> None:
        if button_name not in PAGES:
            return
        label, page_name, _ = PAGES[button_name]
        page = window.findChild(type(window), page_name)
        # The loader creates page widgets as QWidget, not as the main window type.
        from PySide6.QtWidgets import QWidget
        page = window.findChild(QWidget, page_name)
        if page is None:
            write_log(f"> Navigation error: page not found: {page_name}")
            return
        index = stack.indexOf(page)
        if index < 0:
            write_log(f"> Navigation error: page not in stack: {page_name}")
            return
        stack.setCurrentIndex(index)
        title.setText(label)
        for name in PAGES:
            nav_button = window.findChild(QPushButton, name)
            if nav_button is not None:
                nav_button.setChecked(name == button_name)
        write_log(f"> Opened page: {label}")

    def connect_tv() -> None:
        host = ip_edit.text().strip()
        if not host:
            QMessageBox.warning(window, "IP телевизора", "Введите IP-адрес телевизора.")
            return
        try:
            client = AdbClient(host)
            output = client.connect()
            info = client.info()
            set_status(f"●  TV: {info.model or host}", "#52d273")
            write_log(f"> Connected: {info.serial}")
            write_log(output or "> ADB connected")
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
        except (AdbError, OSError, ValueError) as exc:
            set_status("●  Ошибка подключения", "#f05b5b")
            write_log(f"> ADB ERROR: {exc}")
            QMessageBox.warning(window, "ADB", str(exc))

    def check_tv() -> None:
        host = ip_edit.text().strip()
        if not host:
            QMessageBox.warning(window, "IP телевизора", "Сначала введите IP-адрес.")
            return
        try:
            info = AdbClient(host).info()
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
            write_log(f"> ADB: {info.serial} ({info.state})")
            set_status(f"●  TV: {info.model or host}", "#52d273")
        except (AdbError, OSError, ValueError) as exc:
            write_log(f"> CHECK ERROR: {exc}")
            set_status("●  ТВ недоступен", "#f05b5b")
            QMessageBox.warning(window, "Проверка ТВ", str(exc))

    def open_install() -> None:
        current = project()
        if current is None:
            return
        script = current.launcher_installer
        if not script.is_file():
            QMessageBox.warning(window, "CleanYourTV", f"Не найден установщик:\n{script}")
            return
        answer = QMessageBox.question(
            window,
            "Запустить установщик",
            "Откроется отдельное окно PowerShell с исходным установщиком CleanYourTV. Продолжить?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            current.run_launcher_installer()
            write_log(f"> Installer launched from: {script}")
        except (OSError, RuntimeError) as exc:
            write_log(f"> INSTALL ERROR: {exc}")
            QMessageBox.critical(window, "Установка CleanYourTV", str(exc))

    def populate_directory(kind: str, list_name: str) -> None:
        target = required(QListWidget, list_name)
        target.clear()
        current = project()
        if current is None:
            target.addItem("Не найдена локальная папка CleanYourTV.")
            return
        items = current.list_directory(kind)
        if not items:
            target.addItem("Каталоги не найдены.")
        else:
            target.addItems(items)
        write_log(f"> Loaded {len(items)} item(s) from {current.root / kind}")

    def show_items(kind: str) -> None:
        target_page = "themesButton" if kind == "themes" else "addonsButton"
        navigate(target_page)
        populate_directory(kind, "themesList" if kind == "themes" else "addonsList")

    def apply_theme_help() -> None:
        current = project()
        if current is None:
            return
        script_candidates = [
            current.root / "tools" / "theme.ps1",
            current.root / "tools" / "theme.sh",
        ]
        existing = next((item for item in script_candidates if item.is_file()), None)
        if existing:
            QMessageBox.information(
                window,
                "Применение темы",
                f"Найден инструмент темы:\n{existing}\n\nПроверьте его README/справку и примените тему в соответствии с документацией CleanYourTV.",
            )
            write_log(f"> Theme tool found: {existing}")
        else:
            QMessageBox.information(
                window,
                "Применение темы",
                f"Инструмент применения темы не найден автоматически. Откройте документацию в:\n{current.root / 'themes' / 'README.md'}",
            )

    def backup() -> None:
        current = project()
        if current is None:
            return
        try:
            destination = create_backup(current.root, APP_ROOT / "backups")
            write_log(f"> Backup created: {destination}")
            refresh_backups()
            QMessageBox.information(window, "Резервная копия", f"Создана копия проекта:\n{destination}")
        except (OSError, RuntimeError) as exc:
            write_log(f"> BACKUP ERROR: {exc}")
            QMessageBox.critical(window, "Резервная копия", str(exc))

    def refresh_backups() -> None:
        target = window.findChild(QListWidget, "backupsList")
        if target is None:
            return
        target.clear()
        folder = APP_ROOT / "backups"
        if folder.is_dir():
            items = sorted((p for p in folder.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
            target.addItems([p.name for p in items] or ["Резервных копий пока нет."])
        else:
            target.addItem("Резервных копий пока нет.")

    def uninstall_clean_your_tv() -> None:
        current = project()
        if current is None:
            return
        try:
            dialog = load_ui(UNINSTALL_UI_FILE)
        except Exception as exc:
            QMessageBox.critical(window, "Удаление CleanYourTV", str(exc))
            return
        path_label = dialog.findChild(QLabel, "pathLabel")
        confirm = dialog.findChild(QCheckBox, "confirmCheck")
        delete_button = dialog.findChild(QPushButton, "deleteButton")
        cancel_button = dialog.findChild(QPushButton, "cancelButton")
        if not all((path_label, confirm, delete_button, cancel_button)):
            QMessageBox.critical(window, "Удаление CleanYourTV", "Не удалось загрузить элементы окна удаления.")
            return

        path_label.setText(f"Путь: {current.root}")
        delete_button.setEnabled(False)
        confirm.toggled.connect(delete_button.setEnabled)
        cancel_button.clicked.connect(dialog.reject)

        def accept_delete() -> None:
            try:
                removed = uninstall_local_project(current.root, confirmed=True)
                write_log(f"> Local CleanYourTV checkout removed: {removed}")
                dialog.accept()
                button("deleteCleanButton").setEnabled(False)
                QMessageBox.information(
                    window,
                    "Локальные файлы удалены",
                    "Удалена только папка проекта на ПК. Телевизор и Android-пакеты не изменялись.",
                )
            except (UninstallError, OSError) as exc:
                write_log(f"> UNINSTALL ERROR: {exc}")
                QMessageBox.critical(window, "Удаление CleanYourTV", str(exc))

        delete_button.clicked.connect(accept_delete)
        dialog.exec()

    def navigate_by_label(label: str) -> None:
        for name, (page_label, _, _) in PAGES.items():
            if page_label == label:
                navigate(name)
                return

    for name, (label, _, _) in PAGES.items():
        button(name).clicked.connect(lambda checked=False, key=name: navigate(key))

    button("connectButton").clicked.connect(connect_tv)
    button("checkButton").clicked.connect(check_tv)
    button("installCleanButton").clicked.connect(open_install)
    button("installPageButton").clicked.connect(open_install)
    button("themesQuickButton").clicked.connect(lambda: show_items("themes"))
    button("addonsQuickButton").clicked.connect(lambda: show_items("addons"))
    button("refreshThemesButton").clicked.connect(lambda: populate_directory("themes", "themesList"))
    button("refreshAddonsButton").clicked.connect(lambda: populate_directory("addons", "addonsList"))
    button("applyThemeButton").clicked.connect(apply_theme_help)
    button("backupQuickButton").clicked.connect(backup)
    button("createBackupButton").clicked.connect(backup)
    button("refreshBackupsButton").clicked.connect(refresh_backups)
    button("deleteCleanButton").clicked.connect(uninstall_clean_your_tv)

    ip_edit.setText(os.environ.get("TV_HOST", ""))
    refresh_backups()
    write_log("> CleanYourTV Manager started")
    write_log("> Unofficial community GUI; upstream CleanYourTV remains separate.")
    write_log("> Sidebar navigation is connected to real pages.")
    write_log("> No Android package is disabled automatically.")

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
