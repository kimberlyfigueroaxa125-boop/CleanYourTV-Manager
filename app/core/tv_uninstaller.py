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
    result = client.run("shell", "pm", "path", package)
    return result.returncode == 0 and "package:" in result.stdout


def check_stock_home(client: AdbClient) -> tuple[bool, list[str]]:
    """Read-only preflight. Do not change the device."""
    messages: list[str] = []
    if not package_installed(client, STOCK_LAUNCHER_PACKAGE):
        raise TvUninstallError(
            "Стандартный Google TV Launcher не найден. CleanYourTV удалять нельзя."
        )

    enabled_result = client.run(
        "shell", "pm", "list", "packages", "--user", "0", "-e", STOCK_LAUNCHER_PACKAGE
    )
    enabled_text = (enabled_result.stdout + enabled_result.stderr).strip()
    if enabled_result.returncode != 0:
        raise TvUninstallError(
            "Не удалось проверить состояние Google TV Launcher: " + (enabled_text or "неизвестная ошибка")
        )
    enabled = any(
        line.strip() == f"package:{STOCK_LAUNCHER_PACKAGE}"
        for line in enabled_text.splitlines()
    )
    messages.append(
        "Google TV Launcher включён."
        if enabled
        else "Google TV Launcher установлен, но сейчас отключён. Сухой запуск ничего не изменит."
    )

    resolved_result = client.run(
        "shell", "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.HOME",
    )
    resolved = (resolved_result.stdout + resolved_result.stderr).strip()
    if resolved_result.returncode != 0:
        raise TvUninstallError(
            "Не удалось проверить текущий Home: " + (resolved or "неизвестная ошибка")
        )
    stock_resolves = STOCK_LAUNCHER_PACKAGE in resolved and "MainActivity" in resolved
    messages.append(f"Текущий Home: {resolved or '(пусто)'}")
    return stock_resolves, messages


def restore_stock_home(client: AdbClient) -> list[str]:
    """Enable and select stock launcher, then verify the HOME resolver."""
    messages: list[str] = []
    if not package_installed(client, STOCK_LAUNCHER_PACKAGE):
        raise TvUninstallError(
            "Стандартный Google TV Launcher не найден. CleanYourTV удалять нельзя."
        )

    enable = client.run(
        "shell", "pm", "enable", "--user", "0", STOCK_LAUNCHER_PACKAGE
    )
    output = (enable.stdout + enable.stderr).strip()
    if enable.returncode != 0:
        raise TvUninstallError(
            "Не удалось включить Google TV Launcher. CleanYourTV не удалён. "
            + (output or "")
        )
    messages.append("Google TV Launcher включён.")

    set_home = client.run(
        "shell", "cmd", "package", "set-home-activity", "--user", "0",
        STOCK_HOME_ACTIVITY,
    )
    set_output = (set_home.stdout + set_home.stderr).strip()
    if set_home.returncode != 0:
        raise TvUninstallError(
            "Не удалось назначить Google TV Launcher как Home. CleanYourTV не удалён. "
            + (set_output or "")
        )
    messages.append("Запрошено назначение стандартного Home.")

    resolved_result = client.run(
        "shell", "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.HOME",
    )
    resolved = (resolved_result.stdout + resolved_result.stderr).strip()
    if resolved_result.returncode != 0:
        raise TvUninstallError(
            "Не удалось проверить Home. CleanYourTV не удалён. "
            + (resolved or "")
        )
    if STOCK_LAUNCHER_PACKAGE not in resolved or "MainActivity" not in resolved:
        raise TvUninstallError(
            "Проверка Home не подтвердила Google TV Launcher. CleanYourTV не удалён. "
            f"Ответ системы: {resolved or '(пусто)'}"
        )
    messages.append(f"Home проверен: {resolved}")
    return messages


def uninstall_cleanyourtv_from_tv(
    client: AdbClient, *, confirmed: bool = False, dry_run: bool = True
) -> TvUninstallReport:
    """Check stock Home and optionally uninstall CleanYourTV for Android user 0.

    dry_run=True performs only read-only inspection. No settings or packages change.
    """
    if not confirmed:
        raise TvUninstallError("Требуется явное подтверждение удаления с телевизора.")

    client.info()
    messages = [f"Устройство подключено: {client.serial}"]
    present = package_installed(client, CLEANYOURTV_PACKAGE)
    if not present:
        return TvUninstallReport(
            launcher_present=False,
            stock_launcher_enabled=False,
            stock_home_resolved=False,
            removed=False,
            messages=tuple(messages + [f"{CLEANYOURTV_PACKAGE} не найден на ТВ."]),
        )

    if dry_run:
        stock_home, checks = check_stock_home(client)
        messages.extend(checks)
        if not stock_home:
            messages.append(
                "Готовность не подтверждена. В сухом режиме изменения не выполнялись; "
                "для реального удаления сначала восстановите штатный Home вручную."
            )
        else:
            messages.append(
                "Предварительные проверки пройдены. Сухой режим: пакет CleanYourTV не удалён."
            )
        return TvUninstallReport(
            launcher_present=True,
            stock_launcher_enabled=any("Launcher включён" in message for message in checks),
            stock_home_resolved=stock_home,
            removed=False,
            messages=tuple(messages),
        )

    # Destructive mode: restore Home first, then remove only the CleanYourTV launcher.
    messages.extend(restore_stock_home(client))
    result = client.run("shell", "pm", "uninstall", "--user", "0", CLEANYOURTV_PACKAGE)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or "success" not in output.lower():
        raise TvUninstallError(
            "Google TV Launcher восстановлен, но CleanYourTV удалить не удалось: "
            + (output or "неизвестная ошибка")
        )

    if package_installed(client, CLEANYOURTV_PACKAGE):
        raise TvUninstallError(
            "Команда удаления завершилась, но CleanYourTV всё ещё обнаруживается в системе. "
            "Проверьте состояние вручную."
        )

    messages.append(f"Удалён с ТВ для пользователя 0: {CLEANYOURTV_PACKAGE}")
    return TvUninstallReport(
        launcher_present=True,
        stock_launcher_enabled=True,
        stock_home_resolved=True,
        removed=True,
        messages=tuple(messages),
    )
