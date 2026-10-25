from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parent
UI_FILE = ROOT / "ui" / "MainWindow.ui"


def load_ui():
    loader = QUiLoader()
    ui_file = QFile(str(UI_FILE))
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Cannot open UI: {UI_FILE}")
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        raise RuntimeError("Qt Designer UI could not be loaded")
    return window


def adb_command(ip: str, *args: str):
    return subprocess.run(
        ["adb", "-s", f"{ip}:5555", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main():
    app = QApplication(sys.argv)
    try:
        window = load_ui()
    except Exception as exc:
        QMessageBox.critical(None, "CleanYourTV Manager", str(exc))
        return 1

    log = window.findChild(type(window.log), "log")
    status = window.findChild(type(window.tvStatus), "tvStatus")
    ip_edit = window.findChild(type(window.tvIp), "tvIp")

    def write_log(text: str):
        log.appendPlainText(text)

    def connect_tv():
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Введите IP-адрес телевизора.")
            return
        write_log(f"> ADB connect {ip}:5555")
        result = subprocess.run(
            ["adb", "connect", f"{ip}:5555"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout + result.stderr).strip()
        write_log(output or "> no output")
        if result.returncode == 0:
            status.setText("●  TV подключён")
        else:
            status.setText("●  Ошибка подключения")

    def check_tv():
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Сначала введите IP-адрес.")
            return
        result = adb_command(ip, "shell", "getprop", "ro.product.model")
        model = result.stdout.strip()
        if result.returncode == 0 and model:
            write_log(f"> Model: {model}")
            status.setText(f"●  TV: {model}")
        else:
            write_log(f"> ADB check failed: {result.stderr.strip()}")

    window.connectButton.clicked.connect(connect_tv)
    window.checkButton.clicked.connect(check_tv)
    window.installCleanButton.clicked.connect(
        lambda: write_log("> Installer integration: coming next")
    )
    window.themesQuickButton.clicked.connect(
        lambda: write_log("> Theme manager: coming next")
    )
    window.addonsQuickButton.clicked.connect(
        lambda: write_log("> Add-on manager: coming next")
    )

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
