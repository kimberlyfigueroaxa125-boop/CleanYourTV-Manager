from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parents[1]
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


def run_adb(ip: str, *args: str):
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
        try:
            result = subprocess.run(
                ["adb", "connect", f"{ip}:5555"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
        except FileNotFoundError:
            QMessageBox.critical(window, "ADB", "ADB не найден. Установите Android SDK Platform-Tools.")
            return
        except Exception as exc:
            QMessageBox.critical(window, "ADB", str(exc))
            return
        output = (result.stdout + result.stderr).strip()
        write_log(output or "> no output")
        status.setText("●  TV подключён" if result.returncode == 0 else "●  Ошибка подключения")

    def check_tv():
        ip = ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(window, "IP телевизора", "Сначала введите IP-адрес.")
            return
        try:
            result = run_adb(ip, "shell", "getprop", "ro.product.model")
        except FileNotFoundError:
            QMessageBox.critical(window, "ADB", "ADB не найден.")
            return
        model = result.stdout.strip()
        if result.returncode == 0 and model:
            write_log(f"> Model: {model}")
            status.setText(f"●  TV: {model}")
        else:
            write_log(f"> ADB check failed: {result.stderr.strip()}")

    def install_placeholder():
        write_log("> CleanYourTV installer integration is not connected yet.")
        QMessageBox.information(
            window,
            "Установка",
            "Следующим этапом подключим официальный набор инструментов CleanYourTV.\n"
            "Пока программа не выполняет опасных изменений на телевизоре.",
        )

    window.connectButton.clicked.connect(connect_tv)
    window.checkButton.clicked.connect(check_tv)
    window.installCleanButton.clicked.connect(install_placeholder)
    window.themesQuickButton.clicked.connect(lambda: write_log("> Theme manager: next module"))
    window.addonsQuickButton.clicked.connect(lambda: write_log("> Add-on manager: next module"))

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
