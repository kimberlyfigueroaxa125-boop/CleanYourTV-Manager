from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.tv_uninstaller import (
    CLEANYOURTV_PACKAGE,
    STOCK_LAUNCHER_PACKAGE,
    TvUninstallError,
    package_installed,
    restore_stock_home,
    uninstall_cleanyourtv_from_tv,
)


class FakeAdb:
    serial = "192.0.2.1:5555"

    def __init__(self, *, stock=True, clean=True, resolver=None, set_home_rc=0, uninstall_success=True):
        self.stock = stock
        self.clean = clean
        self.resolver = resolver or "com.google.android.tvlauncher/.MainActivity"
        self.set_home_rc = set_home_rc
        self.uninstall_success = uninstall_success
        self.calls = []

    def info(self):
        return SimpleNamespace(manufacturer="Example", model="TV")

    def run(self, *args, **kwargs):
        self.calls.append(args)
        if args[:2] == ("shell", "pm") and args[2] == "path":
            package = args[3]
            present = self.stock if package == STOCK_LAUNCHER_PACKAGE else self.clean
            return SimpleNamespace(returncode=0 if present else 1, stdout="package:/x.apk" if present else "", stderr="")
        if args[:4] == ("shell", "pm", "enable", "--user"):
            return SimpleNamespace(returncode=0, stdout="Package enabled", stderr="")
        if "set-home-activity" in args:
            return SimpleNamespace(returncode=self.set_home_rc, stdout="", stderr="set home failed" if self.set_home_rc else "")
        if "resolve-activity" in args:
            return SimpleNamespace(returncode=0, stdout=self.resolver, stderr="")
        if "uninstall" in args:
            success = self.uninstall_success
            if success:
                self.clean = False
            return SimpleNamespace(returncode=0 if success else 1, stdout="Success" if success else "", stderr="" if success else "Failure")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_requires_explicit_confirmation():
    adb = FakeAdb()
    with pytest.raises(TvUninstallError, match="подтверждение"):
        uninstall_cleanyourtv_from_tv(adb, confirmed=False)
    assert not any("uninstall" in call for call in adb.calls)


def test_stops_when_stock_launcher_missing():
    adb = FakeAdb(stock=False)
    with pytest.raises(TvUninstallError, match="не найден"):
        uninstall_cleanyourtv_from_tv(adb, confirmed=True)
    assert not any("uninstall" in call for call in adb.calls)


def test_stops_when_home_resolver_does_not_confirm_stock_launcher():
    adb = FakeAdb(resolver="com.gathin.tvhome/.MainActivity")
    with pytest.raises(TvUninstallError, match="Home"):
        uninstall_cleanyourtv_from_tv(adb, confirmed=True)
    assert not any("uninstall" in call for call in adb.calls)


def test_does_not_touch_tv_input_packages():
    adb = FakeAdb()
    uninstall_cleanyourtv_from_tv(adb, confirmed=True)
    commands = [" ".join(call) for call in adb.calls]
    assert not any("com.mediatek." in command for command in commands)


def test_removes_only_clean_tv_package_after_home_verified():
    adb = FakeAdb()
    report = uninstall_cleanyourtv_from_tv(adb, confirmed=True)
    assert report.removed
    assert any(CLEANYOURTV_PACKAGE in call for call in adb.calls)
    assert not adb.clean


def test_restore_home_raises_when_set_home_fails():
    adb = FakeAdb(set_home_rc=1)
    with pytest.raises(TvUninstallError, match="назначить"):
        restore_stock_home(adb)
