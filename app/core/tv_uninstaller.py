from __future__ import annotations

from dataclasses import dataclass

from .adb import AdbClient, AdbError

CLEANYOURTV_PACKAGE = "com.gathin.tvhome"
STOCK_LAUNCHER_PACKAGE = "com.google.android.tvlauncher"
STOCK_HOME_ACTIVITY = "com.google.android.tvlauncher/.MainActivity"

# Keep TV functionality and the manufacturer's input stack untouched.
PROTECTED_PACKAGES = frozenset({
    "com.mediatek.tvinput",
    "com.mediatek.wwtv.setupwizard",
    "com.mediatek.wwtv.webview",
    "com.mediatek.wwtv.tvcenter",
})


class TvUninstallError(RuntimeError):
    """Raised when CleanYourTV cannot be safely removed from the TV."""


@dataclass(frozen=True)
class TvUninstallReport:
    launcher_present: bool
    stock_launcher_enabled: bool
    stock_home_resolved: bool
    removed: bool
    messages: tuple[str, ...]


def _checked(client: AdbClient, *args: str) -> str:
    result = client.run(*args)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise TvUninstallError(output or f"ADB command failed: {' '.join(args)}")
    return result.stdout.strip()


def package_installed(client: AdbClient, package: str) -> bool:
    result = client.run("shell", "pm", "path", package)
    return result.returncode == 0 and "package:" in result.stdout


def restore_stock_home(client: AdbClient) -> tuple[bool, list[str]]:
    """Enable and select stock launcher, then verify the HOME resolver."""
    messages: list[str] = []
    if not package_installed(client, STOCK_LAUNCHER_PACKAGE):
        raise TvUninstallError(
            "Стандартный Google TV Launcher не найден. CleanYourTV удалять нельзя."
        )

    # Commands are separated so a failed operation is not hidden by shell chaining.
    _checked(client, "shell", "pm", "enable", "--user", "0", STOCK_LAUNCHER_PACKAGE)
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

    resolved = _checked(
        client,
        "shell", "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.HOME",
    )
    # Some Android builds print multiple lines; require the expected package/activity
    # to appear in the resolver output instead of trusting set-home's exit code alone.
    if STOCK_LAUNCHER_PACKAGE not in resolved or "MainActivity" not in resolved:
        raise TvUninstallError(
            "Проверка Home не подтвердила Google TV Launcher. CleanYourTV не удалён. "
            f"Ответ системы: {resolved or '(пусто)'}"
        )
    messages.append(f"Home проверен: {resolved}")
    return True, messages


def uninstall_cleanyourtv_from_tv(
    client: AdbClient, *, confirmed: bool = False
) -> TvUninstallReport:
    """Restore and verify stock Home before uninstalling CleanYourTV for user 0.

    This does not touch the local source checkout or any other Android package.
    """
    if not confirmed:
        raise TvUninstallError("Требуется явное подтверждение удаления с телевизора.")

    client.info()  # Require an authorised, reachable ADB device first.
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

    # Verify standard Home before attempting any package removal.
    restored, home_messages = restore_stock_home(client)
    messages.extend(home_messages)
    if not restored:
        raise TvUninstallError("Стандартный Home не подтверждён; удаление остановлено.")

    result = client.run("shell", "pm", "uninstall", "--user", "0", CLEANYOURTV_PACKAGE)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or "success" not in output.lower():
        raise TvUninstallError(
            "Google TV Launcher восстановлен, но CleanYourTV удалить не удалось: "
            + (output or "неизвестная ошибка")
        )

    # Verify postcondition before reporting success.
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
