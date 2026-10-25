from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from app.core.adb import AdbClient, AdbError
from app.core.backup import create_backup
from app.core.clean_your_tv import LocalProject
from app.core.paths import APP_ROOT, find_cleanyourtv
from app.core.tv_uninstaller import TvUninstallError, uninstall_cleanyourtv_from_tv
from app.core.uninstaller import UninstallError, uninstall_local_project

UI_FILE = APP_ROOT / "app" / "ui" / "MainWindow.ui"
UNINSTALL_UI_FILE = APP_ROOT / "app" / "ui" / "UninstallDialog.ui"
TV_UNINSTALL_UI_FILE = APP_ROOT / "app" / "ui" / "TvUninstallDialog.ui"

PAGES = {
    "homeButton": ("Главная", "homePage"),
    "installButton": ("Установка", "installPage"),
    "themesButton": ("Темы", "themesPage"),
    "addonsButton": ("Аддоны", "addonsPage"),
    "cleanupButton": ("Очистка", "cleanupPage"),
    "backupButton": ("Резервная копия", "backupPage"),
    "settingsButton": ("Настройки", "settingsPage"),
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
        stack = window.findChild(QStackedWidget, "pageStack")
        log = window.findChild(QPlainTextEdit, "log")
        status = window.findChild(QLabel, "tvStatus")
        title = window.findChild(QLabel, "title")
        ip_edit = window.findChild(QLineEdit, "tvIp")
        if not all((stack, log, status, title, ip_edit)):
            raise RuntimeError("В MainWindow.ui отсутствует обязательный элемент управления.")
        pages: dict[str, QWidget] = {}
        for key, (_, page_name) in PAGES.items():
            page = window.findChild(QWidget, page_name)
            if page is None:
                raise RuntimeError(f"В MainWindow.ui не найдена страница: {page_name}")
            pages[key] = page
    except (OSError, RuntimeError, ValueError) as exc:
        QMessageBox.critical(None, "CleanYourTV Manager", str(exc))
        return 1

    def required(widget_type, name: str):
        widget = window.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"Не найден элемент интерфейса: {name}")
        return widget

    def button(name: str) -> QPushButton:
        return required(QPushButton, name)

    def write_log(message: str) -> None:
        log.appendPlainText(message)

    def project(show_warning: bool = True) -> LocalProject | None:
        root = find_cleanyourtv()
        if root is None:
            if show_warning:
                QMessageBox.warning(window, "CleanYourTV", "Локальная папка CleanYourTV не найдена. Задайте CLEANYOURTV_ROOT.")
            return None
        return LocalProject(root)

    def set_status(message: str, color: str = "#f0b44d") -> None:
        status.setText(message)
        status.setStyleSheet(f"color:{color};font-weight:600;")

    def navigate(key: str) -> None:
        if key not in PAGES or key not in pages:
            write_log(f"> Navigation error: {key}")
            return
        label, _ = PAGES[key]
        stack.setCurrentWidget(pages[key])
        title.setText(label)
        for button_name in PAGES:
            nav_button = window.findChild(QPushButton, button_name)
            if nav_button is not None:
                nav_button.setChecked(button_name == key)
        write_log(f"> Opened page: {label}")

    def adb_client(show_warning: bool = True) -> AdbClient | None:
        host = ip_edit.text().strip()
        if not host:
            if show_warning:
                QMessageBox.warning(window, "IP телевизора", "Введите IP-адрес телевизора на главной странице.")
            return None
        try:
            client = AdbClient(host)
            output = client.connect()
            write_log(output or f"> ADB connected: {client.serial}")
            client.info()
            return client
        except (AdbError, OSError, ValueError) as exc:
            write_log(f"> ADB ERROR: {exc}")
            if show_warning:
                QMessageBox.warning(window, "ADB", str(exc))
            return None

    def connect_tv() -> None:
        client = adb_client()
        if client is None:
            set_status("●  ТВ недоступен", "#f05b5b")
            return
        try:
            info = client.info()
            set_status(f"●  TV: {info.model or client.host}", "#52d273")
            write_log(f"> Connected: {info.serial}")
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
        except (AdbError, OSError, ValueError) as exc:
            set_status("●  Ошибка подключения", "#f05b5b")
            write_log(f"> ADB ERROR: {exc}")
            QMessageBox.warning(window, "ADB", str(exc))

    def check_tv() -> None:
        client = adb_client()
        if client is None:
            return
        try:
            info = client.info()
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
            write_log(f"> ADB: {info.serial} ({info.state})")
            set_status(f"●  TV: {info.model or client.host}", "#52d273")
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
            window, "Запустить установщик",
            "Откроется отдельное окно PowerShell с локальным установщиком CleanYourTV. Продолжить?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
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
        target.addItems(items or ["Каталоги не найдены."])
        write_log(f"> Loaded {len(items)} item(s) from {current.root / kind}")

    def show_items(kind: str) -> None:
        if kind == "themes":
            navigate("themesButton")
            populate_directory("themes", "themesList")
        else:
            navigate("addonsButton")
            populate_directory("addons", "addonsList")

    def apply_theme_help() -> None:
        current = project()
        if current is None:
            return
        docs = current.root / "themes" / "README.md"
        script_candidates = [current.root / "tools" / "theme.ps1", current.root / "tools" / "theme.sh"]
        existing = next((item for item in script_candidates if item.is_file()), None)
        if existing:
            write_log(f"> Theme tool found: {existing}")
            QMessageBox.information(window, "Применение темы", f"Найден инструмент:\n{existing}\n\nПроверьте его параметры и примените тему согласно документации CleanYourTV.")
        else:
            QMessageBox.information(window, "Применение темы", f"Откройте документацию по темам:\n{docs}")

    def refresh_backups() -> None:
        target = window.findChild(QListWidget, "backupsList")
        if target is None:
            return
        target.clear()
        folder = APP_ROOT / "backups"
        if not folder.is_dir():
            target.addItem("Резервных копий пока нет.")
            return
        items = sorted((path for path in folder.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)
        target.addItems([path.name for path in items] or ["Резервных копий пока нет."])

    def backup() -> None:
        current = project()
        if current is None:
            return
        try:
            destination = create_backup(current.root, APP_ROOT / "backups")
            write_log(f"> Backup created: {destination}")
            refresh_backups()
            QMessageBox.information(window, "Резервная копия", f"Создана локальная копия проекта:\n{destination}")
        except (OSError, RuntimeError) as exc:
            write_log(f"> BACKUP ERROR: {exc}")
            QMessageBox.critical(window, "Резервная копия", str(exc))

    def uninstall_clean_your_tv_from_tv() -> None:
        client = adb_client()
        if client is None:
            return
        try:
            info = client.info()
            dialog = load_ui(TV_UNINSTALL_UI_FILE)
        except (OSError, RuntimeError, AdbError, ValueError) as exc:
            QMessageBox.critical(window, "Удаление CleanYourTV с ТВ", str(exc))
            return

        device_label = dialog.findChild(QLabel, "deviceLabel")
        confirm = dialog.findChild(QCheckBox, "confirmCheck")
        test_only = dialog.findChild(QCheckBox, "testOnlyCheck")
        run_button = dialog.findChild(QPushButton, "runButton")
        cancel_button = dialog.findChild(QPushButton, "cancelButton")
        if not all((device_label, confirm, test_only, run_button, cancel_button)):
            QMessageBox.critical(window, "Удаление CleanYourTV с ТВ", "В окне подтверждения отсутствуют нужные элементы.")
            return
        device_label.setText(f"Устройство: {info.manufacturer} {info.model} | {client.serial}")

        def update_button() -> None:
            run_button.setText("Проверить готовность" if test_only.isChecked() else "Восстановить Home и удалить")
            run_button.setEnabled(confirm.isChecked())

        confirm.toggled.connect(update_button)
        test_only.toggled.connect(update_button)
        cancel_button.clicked.connect(dialog.reject)

        def run_uninstall() -> None:
            try:
                report = uninstall_cleanyourtv_from_tv(
                    client,
                    confirmed=bool(confirm.isChecked()),
                    dry_run=bool(test_only.isChecked()),
                )
                for message in report.messages:
                    write_log(f"> TV uninstall: {message}")
                if not report.launcher_present:
                    QMessageBox.information(window, "CleanYourTV", "Пакет CleanYourTV не найден на телевизоре.")
                elif test_only.isChecked():
                    QMessageBox.information(
                        window, "Проверка готовности",
                        "Проверка завершена. В тестовом режиме настройки телевизора не меняются, пакет не удаляется.\n\n"
                        + "\n".join(report.messages),
                    )
                elif report.removed:
                    QMessageBox.information(
                        window, "CleanYourTV удалён",
                        "Google TV Launcher восстановлен, а CleanYourTV удалён с ТВ для пользователя 0.\n\n"
                        + "\n".join(report.messages),
                    )
                else:
                    QMessageBox.warning(window, "CleanYourTV", "\n".join(report.messages))
                dialog.accept()
            except (TvUninstallError, AdbError, OSError, ValueError) as exc:
                write_log(f"> TV UNINSTALL ERROR: {exc}")
                QMessageBox.critical(
                    window, "Удаление CleanYourTV с ТВ",
                    f"{exc}\n\nУдаление останавливается при любой ошибке проверки Home.",
                )

        run_button.clicked.connect(run_uninstall)
        dialog.exec()

    def uninstall_clean_your_tv_locally() -> None:
        current = project()
        if current is None:
            return
        try:
            dialog = load_ui(UNINSTALL_UI_FILE)
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.critical(window, "Удаление локальной копии", str(exc))
            return
        path_label = dialog.findChild(QLabel, "pathLabel")
        confirm = dialog.findChild(QCheckBox, "confirmCheck")
        delete_button = dialog.findChild(QPushButton, "deleteButton")
        cancel_button = dialog.findChild(QPushButton, "cancelButton")
        warning_text = dialog.findChild(QLabel, "warningText")
        if not all((path_label, confirm, delete_button, cancel_button, warning_text)):
            QMessageBox.critical(window, "Удаление локальной копии", "Окно подтверждения неполное.")
            return
        warning_text.setText("Будет удалена только папка исходников CleanYourTV на этом компьютере. Телевизор не изменяется.")
        path_label.setText(f"Путь на ПК: {current.root}")
        confirm.setText("Я понимаю, что локальные файлы CleanYourTV будут удалены")
        delete_button.setText("Удалить папку на ПК")
        delete_button.setEnabled(False)
        confirm.toggled.connect(delete_button.setEnabled)
        cancel_button.clicked.connect(dialog.reject)

        def accept_delete() -> None:
            try:
                removed = uninstall_local_project(current.root, confirmed=bool(confirm.isChecked()))
                write_log(f"> Local project removed: {removed}")
                dialog.accept()
                button("deleteCleanButton").setEnabled(False)
                QMessageBox.information(window, "Удалено", "Удалена только локальная папка на ПК. Телевизор не изменялся.")
            except (UninstallError, OSError) as exc:
                write_log(f"> LOCAL UNINSTALL ERROR: {exc}")
                QMessageBox.critical(window, "Удаление локальной копии", str(exc))

        delete_button.clicked.connect(accept_delete)
        dialog.exec()

    nav_group = QButtonGroup(window)
    nav_group.setExclusive(True)
    for name in PAGES:
        nav_button = button(name)
        nav_group.addButton(nav_button)
        nav_button.clicked.connect(lambda checked=False, key=name: navigate(key))

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
    button("deleteCleanButton").clicked.connect(uninstall_clean_your_tv_locally)
    button("deleteCleanFromTvButton").clicked.connect(uninstall_clean_your_tv_from_tv)

    ip_edit.setText(os.environ.get("TV_HOST", ""))
    refresh_backups()
    write_log("> CleanYourTV Manager started")
    write_log("> Unofficial community GUI; upstream CleanYourTV remains separate.")
    write_log("> TV uninstall dry-run is read-only; destructive mode requires confirmation.")
    navigate("homeButton")

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
