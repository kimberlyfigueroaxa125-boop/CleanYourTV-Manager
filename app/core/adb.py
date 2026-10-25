from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .paths import find_adb


@dataclass(frozen=True)
class DeviceInfo:
    serial: str
    manufacturer: str
    model: str
    android: str
    state: str


class AdbError(RuntimeError):
    pass


class AdbClient:
    def __init__(self, host: str, port: int = 5555) -> None:
        self.host = host.strip()
        self.port = port
        self.serial = f"{self.host}:{self.port}"

    @property
    def adb(self) -> str:
        path = find_adb()
        if not path:
            raise AdbError("ADB не найден. Установите Android SDK Platform-Tools или задайте ADB_PATH.")
        return path

    def run(self, *args: str, timeout: int = 15) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.adb, "-s", self.serial, *args],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB timeout after {timeout}s") from exc

    def connect(self) -> str:
        result = subprocess.run(
            [self.adb, "connect", self.serial],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise AdbError(output or "ADB connect failed")
        return output

    def info(self) -> DeviceInfo:
        state = self.run("get-state")
        if state.returncode != 0 or state.stdout.strip() != "device":
            raise AdbError(state.stderr.strip() or "Устройство не находится в состоянии device")

        def prop(name: str) -> str:
            result = self.run("shell", "getprop", name)
            return result.stdout.strip() if result.returncode == 0 else "unknown"

        return DeviceInfo(
            serial=self.serial,
            manufacturer=prop("ro.product.manufacturer"),
            model=prop("ro.product.model"),
            android=prop("ro.build.version.release"),
            state="device",
        )

    def shell(self, command: str) -> str:
        result = self.run("shell", "sh", "-c", command)
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise AdbError(output or "Remote shell command failed")
        return output
