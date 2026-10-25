# CleanYourTV Manager

Unofficial community Windows GUI for managing a CleanYourTV installation on Android TV.

> This project is independent from the CleanYourTV maintainers unless explicitly stated otherwise.

## Goals

- ADB connection to an Android TV device
- Device and CleanYourTV diagnostics
- Guided installation/update workflow
- Theme browser and installer
- Add-on browser and installer
- Package inspection and safe cleanup helpers
- Backup and restore before potentially disruptive changes
- Visible logs and confirmation dialogs

## UI

The desktop interface is built with **PySide6 / Qt Widgets** and designed in **Qt Designer `.ui` XML files**.

## Safety

The manager should never blindly disable Android system packages. TV input and Live TV services must be protected by default. Any launcher or package change should show what will change and provide a recovery path.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app\main.py
```

## License

The manager's original code is released under the MIT License. CleanYourTV itself and any upstream assets remain subject to their own licenses. Do not redistribute upstream files without checking their license and attribution requirements.
