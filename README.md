# CleanYourTV Manager

Unofficial community Windows GUI for managing a CleanYourTV installation on Android TV. The desktop interface is built with PySide6 and designed in Qt Designer `.ui` XML files.

> This project is independent from the CleanYourTV maintainers unless explicitly stated otherwise.

## Features

- ADB connection to an Android TV device by IP
- Device manufacturer, model and Android version diagnostics
- Guided access to the local CleanYourTV launcher installer
- Local theme and add-on directory inspection
- Local project backup before changes
- Visible operation log
- Windows executable build script
- GitHub Actions-ready repository structure

## Requirements

- Windows 10/11
- Python 3.10+ recommended
- Android SDK Platform-Tools (`adb`) in `PATH`, or `ADB_PATH` pointing to `adb.exe`
- A local CleanYourTV checkout for installer integration
- Network ADB enabled on the TV

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app\main.py
```

To point the manager at your existing CleanYourTV checkout:

```powershell
$env:CLEANYOURTV_ROOT = 'C:\Users\User\CleanYourTV'
```

You can also set `TV_HOST` to prefill the TV IP address.

## Windows build

```powershell
.\build.ps1
```

The build output is placed under `dist\`.

## Safety

The manager does not blindly disable Android system packages. TV input and Live TV services must be protected by default. Launcher or package changes should remain explicit and provide a recovery path.

For devices that use MediaTek TV services, do not disable the TV input stack when Live TV/cable reception is required.

## Relationship to CleanYourTV

CleanYourTV Manager is an unofficial community project. It is not affiliated with or endorsed by the CleanYourTV maintainers. CleanYourTV source code, themes, add-ons, artwork and other upstream assets remain subject to their own licenses. Do not redistribute upstream files without checking their license and attribution requirements.

Upstream project: https://github.com/Gathin23/cleanyourtv

## License

The manager's original code is released under the MIT License. Upstream CleanYourTV content remains under its own license.
