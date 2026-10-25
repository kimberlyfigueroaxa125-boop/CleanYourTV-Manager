# CleanYourTV Manager

> Unofficial community Windows GUI for installing and managing [CleanYourTV](https://github.com/Gathin23/cleanyourtv) on Android TV.

[![Windows CI](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml/badge.svg)](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml)

CleanYourTV Manager is a desktop companion for users who prefer a graphical interface instead of running every task manually. The UI is built with **Python + PySide6** and defined in **Qt Designer `.ui` XML** files.

**This is an independent community project, not an official CleanYourTV application.**

## Features

- ADB connection to an Android TV device by IP address.
- Read-only diagnostics: manufacturer, model, Android version and connection state.
- Sidebar navigation with dedicated Home, Install, Themes, Add-ons, Cleanup, Backups and Settings pages.
- Detect local CleanYourTV theme and add-on folders.
- Launch the upstream launcher's local PowerShell installer after confirmation.
- Create timestamped local copies of the CleanYourTV checkout.
- Explicit confirmation before deleting a local checkout.
- Visible operation log and error messages.
- Windows executable build workflow.
- Editable Qt Designer XML interface.

> **Development status:** this project is still in active development. Theme and add-on pages currently list local folders; they do not claim to install every theme/add-on automatically. The cleanup page does not disable Android packages.

## UI

The main interface is defined in [app/ui/MainWindow.ui](app/ui/MainWindow.ui). Edit it with Qt Designer. The local project deletion confirmation is defined in [app/ui/UninstallDialog.ui](app/ui/UninstallDialog.ui).

## Requirements

- Windows 10 or Windows 11.
- Python 3.10+ (CI currently uses Python 3.12).
- Android SDK Platform-Tools with `adb` in `PATH`, or set `ADB_PATH` to the full path of `adb.exe`.
- A local CleanYourTV checkout to use its installer, themes and add-ons.
- A TV with ADB/network debugging enabled and reachable on the local network.

Compatibility depends on TV model, Android version and manufacturer firmware. A successful connection does not guarantee every CleanYourTV feature is compatible with that TV.

## Quick start (Windows)

Clone the repository:

```powershell
git clone https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager.git
cd CleanYourTV-Manager
```

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run from the repository root using module mode:

```powershell
python -m app.main
```

Or use the helper script, which creates the virtual environment if needed:

```powershell
.\run.ps1
```

If PowerShell blocks local scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

## Configure the CleanYourTV checkout

If the upstream repository is located at `C:\Users\User\CleanYourTV`, set:

```powershell
$env:CLEANYOURTV_ROOT = 'C:\Users\User\CleanYourTV'
```

Use the actual path on your PC. The manager checks that the directory contains a `tools` folder before treating it as a CleanYourTV checkout.

## Configure ADB

If `adb` is already in `PATH`, no extra setting is needed. Otherwise:

```powershell
$env:ADB_PATH = 'C:\Android\Sdk\platform-tools\adb.exe'
```

To prefill the TV IP in the GUI:

```powershell
$env:TV_HOST = '192.168.0.118'
```

Replace the sample IP with the TV's current IP. Enable network/ADB debugging on the TV and approve the debugging prompt if shown. This version uses the default network ADB port 5555; alternate pairing flows may require further support.

## Pages

- **Home:** connect and run basic device diagnostics.
- **Install:** starts the upstream local PowerShell installer in a separate visible window after confirmation. Review the script's prompts and output.
- **Themes:** shows folders under the local CleanYourTV `themes` directory. Automatic application is not yet implemented in the manager.
- **Add-ons:** shows folders under the local CleanYourTV `addons` directory.
- **Cleanup:** informational only. It does **not** disable or remove Android packages.
- **Backups:** creates a timestamped local copy of the source project. It is not a backup of Android TV firmware, settings or installed apps.
- **Settings:** documents environment variables used by the app.

## Removing the local CleanYourTV checkout

The delete action applies only to the **local source folder on the PC**. It does not uninstall the launcher from the TV or restore Android packages. A confirmation dialog is required. Create a backup first.

## Windows executable

Build locally:

```powershell
.\build.ps1
```

GitHub Actions runs lint/tests and builds a Windows executable. Open the [Actions tab](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions), select a successful run and download the `CleanYourTV-Manager-Windows` artifact. Until a version is published under Releases, CI artifacts are development builds, not stable releases.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m compileall -q app tests
ruff check app tests
pytest
```

Tests cover XML structure and page IDs, path discovery, safety helpers and local backup behavior. They do not replace tests against real Android TV hardware.

## Project structure

```text
CleanYourTV-Manager/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── app/
│   ├── core/
│   │   ├── adb.py
│   │   ├── backup.py
│   │   ├── clean_your_tv.py
│   │   ├── paths.py
│   │   ├── safety.py
│   │   └── uninstaller.py
│   ├── ui/
│   │   ├── MainWindow.ui
│   │   └── UninstallDialog.ui
│   └── main.py
├── tests/
├── CleanYourTV-Manager.spec
├── build.ps1
├── run.ps1
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Safety

- The manager does not automatically disable Android packages.
- Do not disable system launcher, TV Input, tuner, setup wizard or Live TV components unless you understand how to recover the device.
- On MediaTek-based TVs, disabling the TV-input stack may break cable/antenna TV and input switching.
- Read upstream scripts before running unfamiliar cleanup operations.
- A backup of the source project does not back up the actual TV state.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). For device-specific reports, include the TV model, Android/firmware version, manager commit, operation attempted and relevant log output. Do not post passwords, tokens or sensitive debugging data.

## Relationship and licensing

CleanYourTV Manager is an unofficial community project and is not affiliated with or endorsed by the CleanYourTV maintainers unless they explicitly state otherwise.

The manager's original code is licensed under the MIT License. CleanYourTV source code, themes, add-ons, artwork and other upstream assets remain governed by their own licenses. Do not redistribute upstream content without checking original license and attribution requirements.

- Upstream project: https://github.com/Gathin23/cleanyourtv
- This project: https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager
