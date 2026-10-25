from __future__ import annotations

from dataclasses import dataclass

from .adb import AdbClient

CLEANYOURTV_PACKAGE = "com.gathin.tvhome"
STOCK_LAUNCHER_PACKAGE = "com.google.android.tvlauncher"
STOCK_HOME_ACTIVITY = "com.google.android.tvlauncher/.MainActivity"


class TvUninstallError(RuntimeError):
    """Raised when CleanYourTV cannot be safely removed from the TV."""


@dataclass(frozen=True)
class TvUninstallReport:
    launcher_present: bool
    stock_launcher_enabled: bool
    stock_home_resolved: bool
    removed: bool
    messages: tuple[str, ...]


def package_installed(client: AdbClient, package: str) -> bool:
    """Check whether the APK path is visible to Android's package manager."""
    result = client.run("shell", "pm", "path", package)
    return result.returncode == 0 and "package:" in result.stdout


def package_installed_for_user(client: AdbClient, package: str) -> bool:
    """Check whether the package is installed for Android user 0."""
    result = client.run("shell", "pm", "list", "packages", "--user", "0", package)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise TvUninstallError(output or f"Не удалось проверить установку пакета {package}.")
    return any(line.strip() == f"package:{package}" for line in result.stdout.splitlines())


def package_enabled_for_user(client: AdbClient, package: str) -> bool:
    result = client.run("shell", "pm", "list", "packages", "--user", "0", "-e", package)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise TvUninstallError(output or f"Не удалось проверить состояние пакета {package}.")
    return any(line.strip() == f"package:{package}" for line in result.stdout.splitlines())


def _resolve_home(client: AdbClient) -> str:
    result = client.run(
        "shell", "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.HOME",
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise TvUninstallError("Не удалось проверить текущий Home: " + (output or "неизвестная ошибка"))
    return output


def check_stock_home(client: AdbClient) -> tuple[bool, list[str]]:
    """Read-only preflight; it never changes the TV."""
    if not package_installed(client, STOCK_LAUNCHER_PACKAGE):
        raise TvUninstallError("Стандартный Google TV Launcher не найден. CleanYourTV удалять нельзя.")

    enabled = package_enabled_for_user(client, STOCK_LAUNCHER_PACKAGE)
    messages = [
        "Google TV Launcher включён."
        if enabled
        else "Google TV Launcher установлен, но сейчас отключён. Сухой запуск ничего не изменит."
    ]

    resolved = _resolve_home(client)
    stock_resolves = STOCK_LAUNCHER_PACKAGE in resolved and "MainActivity" in resolved
    messages.append(f"Текущий Home: {resolved or '(пусто)'}")
    return stock_resolves, messages


def restore_stock_home(client: AdbClient) -> list[str]:
    """Enable and select the stock launcher, then verify the HOME resolver."""
    if not package_installed(client, STOCK_LAUNCHER_PACKAGE):
        raise TvUninstallError("Стандартный Google TV Launcher не найден. CleanYourTV удалять нельзя.")

    enable = client.run("shell", "pm", "enable", "--user", "0", STOCK_LAUNCHER_PACKAGE)
    output = (enable.stdout + enable.stderr).strip()
    if enable.returncode != 0:
        raise TvUninstallError("Не удалось включить Google TV Launcher. CleanYourTV не удалён. " + (output or ""))

    set_home = client.run(
        "shell", "cmd", "package", "set-home-activity", "--user", "0", STOCK_HOME_ACTIVITY
    )
    output = (set_home.stdout + set_home.stderr).strip()
    if set_home.returncode != 0:
        raise TvUninstallError("Не удалось назначить Google TV Launcher как Home. CleanYourTV не удалён. " + (output or ""))

    resolved = _resolve_home(client)
    if STOCK_LAUNCHER_PACKAGE not in resolved or "MainActivity" not in resolved:
        raise TvUninstallError(
            "Проверка Home не подтвердила Google TV Launcher. CleanYourTV не удалён. "
            f"Ответ системы: {resolved or '(пусто)'}"
        )
    return [
        "Google TV Launcher включён.",
        "Запрошено назначение стандартного Home.",
        f"Home проверен: {resolved}",
    ]


def uninstall_cleanyourtv_from_tv(
    client: AdbClient, *, confirmed: bool = False, dry_run: bool = True
) -> TvUninstallReport:
    """Check stock Home and optionally uninstall CleanYourTV for Android user 0.

    dry_run=True performs read-only inspection. No settings or packages change.
    """
    if not confirmed:
        raise TvUninstallError("Требуется явное подтверждение удаления с телевизора.")

    client.info()
    messages = [f"Устройство подключено: {client.serial}"]
    present = package_installed_for_user(client, CLEANYOURTV_PACKAGE)
    if not present:
        messages.append(f"{CLEANYOURTV_PACKAGE} не установлен для пользователя 0.")
        return TvUninstallReport(False, False, False, False, tuple(messages))

    if dry_run:
        stock_home, checks = check_stock_home(client)
        messages.extend(checks)
        if stock_home:
            messages.append("Предварительные проверки пройдены. Сухой режим: пакет CleanYourTV не удалён.")
        else:
            messages.append(
                "Готовность не подтверждена. В сухом режиме настройки не менялись, пакет не удалён. "
                "Сначала восстановите штатный Home и повторите проверку."
            )
        return TvUninstallReport(
            launcher_present=True,
            stock_launcher_enabled=package_enabled_for_user(client, STOCK_LAUNCHER_PACKAGE),
            stock_home_resolved=stock_home,
            removed=False,
            messages=tuple(messages),
        )

    messages.extend(restore_stock_home(client))
    result = client.run("shell", "pm", "uninstall", "--user", "0", CLEANYOURTV_PACKAGE)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or "success" not in output.lower():
        raise TvUninstallError(
            "Google TV Launcher восстановлен, но CleanYourTV удалить не удалось: "
            + (output or "неизвестная ошибка")
        )

    # pm path is not sufficient here: the APK may still reside in the system image.
    if package_installed_for_user(client, CLEANYOURTV_PACKAGE):
        raise TvUninstallError(
            "Команда удаления завершилась, но CleanYourTV всё ещё установлен для пользователя 0. "
            "Проверьте состояние вручную."
        )

    messages.append(f"Удалён с ТВ для пользователя 0: {CLEANYOURTV_PACKAGE}")
    return TvUninstallReport(True, True, True, True, tuple(messages))
