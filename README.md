# CleanYourTV Manager

> Unofficial community Windows GUI for managing [CleanYourTV](https://github.com/Gathin23/cleanyourtv) on Android TV.

[![Windows CI](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml/badge.svg)](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml)

CleanYourTV Manager is a desktop companion for users who prefer a graphical interface. The UI is built with **Python + PySide6** and defined in **Qt Designer `.ui` XML** files.

**Independent community project. It is not an official CleanYourTV application.**

## Features

- ADB connection and TV diagnostics.
- Sidebar navigation for Home, Install, Themes, Add-ons, Cleanup, Backups and Settings.
- Browse locally available theme and add-on folders.
- Launch the upstream local installer after confirmation.
- Create timestamped backups of the CleanYourTV source checkout on the PC.
- Separate local-checkout removal from CleanYourTV launcher removal on the TV.
- TV removal flow: enable the stock launcher, request it as Home, verify the Home resolver, and only then attempt to remove `com.gathin.tvhome` for Android user 0.
- The TV removal dialog has **test-only mode selected by default**.
- Visible operation log and confirmation prompts.

> **Development status:** this project is in active development. Theme/add-on pages currently list local folders; automatic installation of every theme/add-on is not implemented. Cleanup does not perform mass package disabling.

## Requirements

- Windows 10/11.
- Python 3.10+.
- Android SDK Platform-Tools (`adb`) in `PATH`, or configure `ADB_PATH`.
- A local CleanYourTV checkout for the upstream installer, themes and add-ons.
- Android TV reachable with ADB/network debugging enabled and debugging authorization approved.

TV compatibility depends on the model and firmware. Test on the actual target device before relying on the workflow.

## Quick start

```powershell
git clone https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager.git
cd CleanYourTV-Manager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

You can instead run `.\run.ps1` to create the environment when needed.

## Configuration

Set the location of your CleanYourTV checkout and the default TV host in PowerShell if desired:

```powershell
$env:CLEANYOURTV_ROOT = 'C:\Users\User\CleanYourTV'
$env:TV_HOST = '192.168.0.118'
# If adb.exe is not in PATH:
$env:ADB_PATH = 'C:\Android\Sdk\platform-tools\adb.exe'
python -m app.main
```

Replace sample paths and IP addresses with your own.

## Removing CleanYourTV from the TV

Use **Home → “Удалить CleanYourTV с ТВ…”**. This is different from deleting the local source folder on the PC.

1. Connect to the TV over ADB and approve the debugging prompt on the TV if requested.
2. Open the TV removal dialog. Select the confirmation checkbox.
3. Leave **“Только проверка (не удалять пакет)”** selected first. Press **“Проверить готовность”** to test the pre-removal checks.
4. The workflow checks that `com.google.android.tvlauncher` exists, enables it, requests `com.google.android.tvlauncher/.MainActivity` as Home, and verifies the HOME activity resolver.
5. If verification fails, the workflow stops and does not try to uninstall CleanYourTV.
6. Only after the readiness check, you may deselect test-only mode and explicitly confirm the destructive action. If the stock Home check passes, the app attempts to remove `com.gathin.tvhome` for user 0 and verifies that the package is no longer listed.

**Important limitations:** Android TV firmware differs by manufacturer. Some systems may reject setting the Home activity or may resolve HOME differently. In that case, the manager should stop and report the error; do not bypass the check by deleting the package manually. The operation only targets `com.gathin.tvhome`; it does not modify MediaTek Live TV, tuner or TV Input packages. It does not factory-reset the TV or undo packages disabled by earlier cleanup actions.

Removing the package for user 0 is not the same as erasing its APK/system image from the firmware. If you need to restore CleanYourTV later, reinstall it using the upstream project's supported process.

## Removing the local CleanYourTV checkout

The **“Удалить локальную копию на ПК…”** action only removes the selected local source folder from the computer. It does not uninstall the launcher from the TV. Create a backup first.

## Pages

- **Home:** connect to the TV, run diagnostics, and open removal workflows.
- **Install:** starts the upstream local PowerShell installer in a separate visible window after confirmation.
- **Themes:** lists folders under the local CleanYourTV `themes` directory. Automatic application is not implemented.
- **Add-ons:** lists folders under the local CleanYourTV `addons` directory.
- **Cleanup:** informational only; it does not perform mass package disabling.
- **Backups:** creates a timestamped local source backup, not a backup of TV firmware/settings.
- **Settings:** documents environment variables.

## Windows executable

Build locally:

```powershell
.\build.ps1
```

GitHub Actions runs lint/tests and builds a Windows executable. Open the [Actions tab](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions), select a successful run and download `CleanYourTV-Manager-Windows`. Until a version is published under Releases, CI artifacts are development builds, not stable releases.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m compileall -q app tests
ruff check app tests
pytest
```

Tests do not replace real Android TV hardware testing.

## Project structure

```text
CleanYourTV-Manager/
├── .github/
├── app/
│   ├── core/
│   │   ├── adb.py
│   │   ├── backup.py
│   │   ├── clean_your_tv.py
│   │   ├── paths.py
│   │   ├── safety.py
│   │   ├── tv_uninstaller.py
│   │   └── uninstaller.py
│   ├── ui/
│   │   ├── MainWindow.ui
│   │   ├── UninstallDialog.ui
│   │   └── TvUninstallDialog.ui
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
- On MediaTek-based TVs, disabling TV-input components can break cable/antenna TV and input switching.
- Read upstream scripts before running unfamiliar cleanup operations.
- A backup of the source project does not back up the actual TV state.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). For device-specific reports, include the TV model, Android/firmware version, manager commit, operation attempted and relevant log output. Do not post passwords, tokens or sensitive debugging data.

## Relationship and licensing

CleanYourTV Manager is an unofficial community project and is not affiliated with or endorsed by CleanYourTV maintainers unless they explicitly state otherwise.

The manager's original code is licensed under the MIT License. CleanYourTV source code, themes, add-ons, artwork and other upstream assets remain governed by their own licenses. Check upstream license and attribution requirements before redistributing such materials.

- Upstream project: https://github.com/Gathin23/cleanyourtv
- This project: https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager
