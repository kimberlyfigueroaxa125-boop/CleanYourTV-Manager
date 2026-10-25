import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "app" / "ui" / "MainWindow.ui"
TV_UNINSTALL_UI = ROOT / "app" / "ui" / "TvUninstallDialog.ui"


def test_main_window_xml_is_well_formed():
    root = ET.parse(UI).getroot()
    assert root.tag == "ui"


def test_sidebar_buttons_have_matching_stacked_pages():
    root = ET.parse(UI).getroot()
    names = {node.attrib.get("name") for node in root.iter("widget")}
    assert "pageStack" in names

    expected = {
        "homeButton": "homePage",
        "installButton": "installPage",
        "themesButton": "themesPage",
        "addonsButton": "addonsPage",
        "cleanupButton": "cleanupPage",
        "backupButton": "backupPage",
        "settingsButton": "settingsPage",
    }
    for button, page in expected.items():
        assert button in names
        assert page in names


def test_pages_contain_expected_controls():
    root = ET.parse(UI).getroot()
    names = {node.attrib.get("name") for node in root.iter("widget")}
    for control in (
        "connectButton",
        "checkButton",
        "installPageButton",
        "themesList",
        "addonsList",
        "createBackupButton",
        "backupsList",
        "deleteCleanButton",
        "deleteCleanFromTvButton",
    ):
        assert control in names


def test_tv_uninstall_dialog_requires_confirmation_and_has_no_dry_run_checkbox():
    root = ET.parse(TV_UNINSTALL_UI).getroot()
    widgets = {node.attrib.get("name"): node for node in root.iter("widget")}
    assert "confirmCheck" in widgets
    assert "runButton" in widgets
    assert "cancelButton" in widgets
    assert "testOnlyCheck" not in widgets
