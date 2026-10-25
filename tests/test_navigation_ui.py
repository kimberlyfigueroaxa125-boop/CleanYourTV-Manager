from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "app" / "ui" / "MainWindow.ui"


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
    ):
        assert control in names
