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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.adb import AdbClient, AdbError
from app.core.addons import AddonError, AddonInfo, discover_addons, install_addon
from app.core.backup import create_backup
from app.core.clean_your_tv import LocalProject
from app.core.paths import APP_ROOT, find_cleanyourtv
from app.core.themes import ThemeError, ThemeInfo, discover_themes, install_theme, reset_theme
from app.core.tv_uninstaller import TvUninstallError, uninstall_cleanyourtv_from_tv
from app.core.uninstaller import UninstallError, uninstall_local_project

UI_FILE = APP_ROOT / "app" / "ui" / "MainWindow.ui"
UNINSTALL_UI_FILE = APP_ROOT / "app" / "ui" / "UninstallDialog.ui"
TV_UNINSTALL_UI_FILE = APP_ROOT / "app" / "ui" / "TvUninstallDialog.ui"

PAGES = {
    "homeButton": ("Home", "homePage"),
    "installButton": ("Install", "installPage"),
    "themesButton": ("Themes", "themesPage"),
    "addonsButton": ("Add-ons", "addonsPage"),
    "cleanupButton": ("Cleanup", "cleanupPage"),
    "backupButton": ("Backups", "backupPage"),
    "settingsButton": ("Settings", "settingsPage"),
}


def load_ui(path: Path):
    loader = QUiLoader()
    ui_file = QFile(str(path))
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Unable to open UI file: {path}")
    try:
        window = loader.load(ui_file)
    finally:
        ui_file.close()
    if window is None:
        raise RuntimeError(f"Unable to load Qt Designer UI: {path}")
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
            raise RuntimeError("MainWindow.ui is missing a required control.")
        pages: dict[str, QWidget] = {}
        for key, (_, page_name) in PAGES.items():
            page = window.findChild(QWidget, page_name)
            if page is None:
                raise RuntimeError(f"MainWindow.ui is missing page: {page_name}")
            pages[key] = page
    except (OSError, RuntimeError, ValueError) as exc:
        QMessageBox.critical(None, "CleanYourTV Manager", str(exc))
        return 1

    def required(widget_type, name: str):
        widget = window.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"UI control not found: {name}")
        return widget

    def button(name: str) -> QPushButton:
        return required(QPushButton, name)

    def write_log(message: str) -> None:
        log.appendPlainText(message)

    def project(show_warning: bool = True) -> LocalProject | None:
        root = find_cleanyourtv()
        if root is None:
            if show_warning:
                QMessageBox.warning(window, "CleanYourTV", "Local CleanYourTV folder was not found. Set CLEANYOURTV_ROOT.")
            return None
        return LocalProject(root)

    def set_status(message: str, color: str = "#f0b44d") -> None:
        status.setText(message)
        status.setStyleSheet(f"color:{color};font-weight:600;")

    def navigate(key: str) -> None:
        if key not in PAGES or key not in pages:
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
                QMessageBox.warning(window, "TV IP Address", "Enter the TV IP address on the Home page.")
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
            set_status("●  TV unavailable", "#f05b5b")
            return
        try:
            info = client.info()
            set_status(f"●  TV: {info.model or client.host}", "#52d273")
            write_log(f"> Connected: {info.serial}")
            write_log(f"> Manufacturer: {info.manufacturer}")
            write_log(f"> Model: {info.model}")
            write_log(f"> Android: {info.android}")
        except (AdbError, OSError, ValueError) as exc:
            set_status("●  Connection error", "#f05b5b")
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
            set_status("●  TV unavailable", "#f05b5b")
            QMessageBox.warning(window, "TV Check", str(exc))

    def open_install() -> None:
        current = project()
        if current is None:
            return
        script = current.launcher_installer
        if not script.is_file():
            QMessageBox.warning(window, "CleanYourTV", f"Installer not found:\n{script}")
            return
        answer = QMessageBox.question(window, "Launch Installer", "A separate PowerShell window will open with the local CleanYourTV installer. Continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            current.run_launcher_installer()
            write_log(f"> Installer launched from: {script}")
        except (OSError, RuntimeError) as exc:
            write_log(f"> INSTALL ERROR: {exc}")
            QMessageBox.critical(window, "CleanYourTV Installation", str(exc))

    def populate_themes() -> list[ThemeInfo]:
        target = required(QListWidget, "themesList")
        target.clear()
        current = project()
        if current is None:
            target.addItem("Local CleanYourTV folder was not found.")
            return []
        items = discover_themes(current)
        for item in items:
            target.addItem(item.name)
        if not items:
            target.addItem("No installable themes found.")
        write_log(f"> Found {len(items)} installable theme(s).")
        return items

    def populate_addons() -> list[AddonInfo]:
        target = required(QListWidget, "addonsList")
        target.clear()
        current = project()
        if current is None:
            target.addItem("Local CleanYourTV folder was not found.")
            return []
        items = discover_addons(current)
        for item in items:
            target.addItem(item.name)
        if not items:
            target.addItem("No buildable add-ons found.")
        write_log(f"> Found {len(items)} buildable add-on(s).")
        return items

    def selected_theme() -> ThemeInfo | None:
        current = project(False)
        if current is None:
            return None
        item = required(QListWidget, "themesList").currentItem()
        if item is None:
            return None
        return next((theme for theme in discover_themes(current) if theme.name == item.text()), None)

    def selected_addon() -> AddonInfo | None:
        current = project(False)
        if current is None:
            return None
        item = required(QListWidget, "addonsList").currentItem()
        if item is None:
            return None
        return next((addon for addon in discover_addons(current) if addon.name == item.text()), None)

    def apply_selected_theme() -> None:
        current = project()
        if current is None:
            return
        theme = selected_theme()
        if theme is None:
            QMessageBox.warning(window, "Install Theme", "Select a theme first.")
            return
        host = ip_edit.text().strip()
        if not host:
            QMessageBox.warning(window, "Install Theme", "Enter the TV IP address first.")
            return
        answer = QMessageBox.question(window, "Install Theme", f"Install theme '{theme.name}' on the connected TV?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            write_log(f"> Installing theme: {theme.name}")
            output = install_theme(current, theme, host)
            write_log(output)
            QMessageBox.information(window, "Theme Installed", f"Theme '{theme.name}' was installed and Home was restarted.")
        except (ThemeError, OSError) as exc:
            write_log(f"> THEME ERROR: {exc}")
            QMessageBox.critical(window, "Theme Installation Failed", str(exc))

    def reset_theme_on_tv() -> None:
        current = project()
        if current is None:
            return
        host = ip_edit.text().strip()
        if not host:
            QMessageBox.warning(window, "Reset Theme", "Enter the TV IP address first.")
            return
        answer = QMessageBox.question(window, "Reset Theme", "Restore the built-in CleanYourTV theme on the TV?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            output = reset_theme(current, host)
            write_log(output)
            QMessageBox.information(window, "Theme Reset", "The built-in theme has been restored.")
        except (ThemeError, OSError) as exc:
            write_log(f"> THEME RESET ERROR: {exc}")
            QMessageBox.critical(window, "Theme Reset Failed", str(exc))

    def install_selected_addon() -> None:
        addon = selected_addon()
        if addon is None:
            QMessageBox.warning(window, "Install Add-on", "Select an add-on first.")
            return
        client = adb_client()
        if client is None:
            return
        answer = QMessageBox.question(window, "Install Add-on", f"Build and install '{addon.name}' on the connected TV?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            write_log(f"> Building/installing add-on: {addon.name}")
            apk, output = install_addon(client, addon)
            write_log(f"> APK: {apk}")
            write_log(output)
            QMessageBox.information(window, "Add-on Installed", f"'{addon.name}' was installed successfully.\n\nAPK: {apk}")
        except (AddonError, AdbError, OSError, ValueError) as exc:
            write_log(f"> ADD-ON ERROR: {exc}")
            QMessageBox.critical(window, "Add-on Installation Failed", str(exc))

    def refresh_backups() -> None:
        target = window.findChild(QListWidget, "backupsList")
        if target is None:
            return
        target.clear()
        folder = APP_ROOT / "backups"
        if not folder.is_dir():
            target.addItem("No backups yet.")
            return
        items = sorted((path for path in folder.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)
        target.addItems([path.name for path in items] or ["No backups yet."])

    def backup() -> None:
        current = project()
        if current is None:
            return
        try:
            destination = create_backup(current.root, APP_ROOT / "backups")
            write_log(f"> Backup created: {destination}")
            refresh_backups()
            QMessageBox.information(window, "Backup", f"Project backup created:\n{destination}")
        except (OSError, RuntimeError) as exc:
            write_log(f"> BACKUP ERROR: {exc}")
            QMessageBox.critical(window, "Backup", str(exc))

    def uninstall_clean_your_tv_from_tv() -> None:
        client = adb_client()
        if client is None:
            return
        try:
            info = client.info()
            dialog = load_ui(TV_UNINSTALL_UI_FILE)
        except (OSError, RuntimeError, AdbError, ValueError) as exc:
            QMessageBox.critical(window, "Remove CleanYourTV from TV", str(exc))
            return
        device_label = dialog.findChild(QLabel, "deviceLabel")
        confirm = dialog.findChild(QCheckBox, "confirmCheck")
        run_button = dialog.findChild(QPushButton, "runButton")
        cancel_button = dialog.findChild(QPushButton, "cancelButton")
        if not all((device_label, confirm, run_button, cancel_button)):
            QMessageBox.critical(window, "Remove CleanYourTV from TV", "The confirmation dialog is missing required controls.")
            return
        device_label.setText(f"Device: {info.manufacturer} {info.model} | {client.serial}")
        run_button.setEnabled(confirm.isChecked())
        confirm.toggled.connect(run_button.setEnabled)
        cancel_button.clicked.connect(dialog.reject)

        def run_uninstall() -> None:
            if not confirm.isChecked():
                return
            try:
                report = uninstall_cleanyourtv_from_tv(client, confirmed=True, dry_run=False)
                for message in report.messages:
                    write_log(f"> TV removal: {message}")
                if not report.launcher_present:
                    QMessageBox.information(window, "CleanYourTV", "CleanYourTV was not found on the TV.")
                elif report.removed:
                    QMessageBox.information(window, "CleanYourTV Removed", "Google TV Launcher was restored and CleanYourTV was removed for Android user 0.\n\n" + "\n".join(report.messages))
                else:
                    QMessageBox.warning(window, "CleanYourTV", "\n".join(report.messages))
                dialog.accept()
            except (TvUninstallError, AdbError, OSError, ValueError) as exc:
                write_log(f"> TV REMOVAL ERROR: {exc}")
                QMessageBox.critical(window, "Remove CleanYourTV from TV", f"{exc}\n\nRemoval stops if the stock Home verification fails.")

        run_button.clicked.connect(run_uninstall)
        dialog.exec()

    def uninstall_clean_your_tv_locally() -> None:
        current = project()
        if current is None:
            return
        try:
            dialog = load_ui(UNINSTALL_UI_FILE)
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.critical(window, "Remove Local Copy", str(exc))
            return
        path_label = dialog.findChild(QLabel, "pathLabel")
        confirm = dialog.findChild(QCheckBox, "confirmCheck")
        delete_button = dialog.findChild(QPushButton, "deleteButton")
        cancel_button = dialog.findChild(QPushButton, "cancelButton")
        warning_text = dialog.findChild(QLabel, "warningText")
        if not all((path_label, confirm, delete_button, cancel_button, warning_text)):
            QMessageBox.critical(window, "Remove Local Copy", "The confirmation dialog is incomplete.")
            return
        warning_text.setText("Only the local CleanYourTV source folder on this PC will be deleted. The TV will not be changed.")
        path_label.setText(f"PC path: {current.root}")
        confirm.setText("I understand that the local CleanYourTV files will be deleted")
        delete_button.setText("Delete Local Folder")
        delete_button.setEnabled(False)
        confirm.toggled.connect(delete_button.setEnabled)
        cancel_button.clicked.connect(dialog.reject)

        def accept_delete() -> None:
            try:
                removed = uninstall_local_project(current.root, confirmed=bool(confirm.isChecked()))
                write_log(f"> Local project removed: {removed}")
                dialog.accept()
                button("deleteCleanButton").setEnabled(False)
                QMessageBox.information(window, "Removed", "Only the local PC folder was removed. The TV was not changed.")
            except (UninstallError, OSError) as exc:
                write_log(f"> LOCAL REMOVAL ERROR: {exc}")
                QMessageBox.critical(window, "Remove Local Copy", str(exc))

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
    button("themesQuickButton").clicked.connect(lambda: (navigate("themesButton"), populate_themes()))
    button("addonsQuickButton").clicked.connect(lambda: (navigate("addonsButton"), populate_addons()))
    button("refreshThemesButton").clicked.connect(populate_themes)
    button("refreshAddonsButton").clicked.connect(populate_addons)
    button("applyThemeButton").clicked.connect(apply_selected_theme)
    button("backupQuickButton").clicked.connect(backup)
    button("createBackupButton").clicked.connect(backup)
    button("refreshBackupsButton").clicked.connect(refresh_backups)
    button("deleteCleanButton").clicked.connect(uninstall_clean_your_tv_locally)
    button("deleteCleanFromTvButton").clicked.connect(uninstall_clean_your_tv_from_tv)

    themes_layout = window.findChild(QHBoxLayout, "themesActionLayout")
    if themes_layout is not None:
        theme_install = QPushButton("Install Selected Theme")
        theme_install.clicked.connect(apply_selected_theme)
        themes_layout.addWidget(theme_install)
        theme_reset = QPushButton("Reset Theme")
        theme_reset.clicked.connect(reset_theme_on_tv)
        themes_layout.addWidget(theme_reset)

    addons_layout = window.findChild(QVBoxLayout, "addonsLayout")
    if addons_layout is not None:
        addon_install = QPushButton("Build & Install Selected Add-on")
        addon_install.clicked.connect(install_selected_addon)
        addons_layout.insertWidget(3, addon_install)

    themes_text = window.findChild(QLabel, "themesText")
    if themes_text is not None:
        themes_text.setText("Select a theme from the local CleanYourTV repository and install it directly to the connected TV. The upstream theme.ps1 tool handles the on-TV files and Home restart.")
    addons_text = window.findChild(QLabel, "addonsText")
    if addons_text is not None:
        addons_text.setText("Select an add-on from the local CleanYourTV repository. The manager builds its Gradle project when needed, finds the release APK and installs it to the connected TV with ADB.")

    ip_edit.setText(os.environ.get("TV_HOST", ""))
    refresh_backups()
    write_log("> CleanYourTV Manager started")
    write_log("> Themes: select a theme and install it directly to the TV.")
    write_log("> Add-ons: select an add-on, build it when needed, and install its APK.")
    write_log("> TV removal restores and verifies the stock Home before uninstalling.")
    navigate("homeButton")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())