# CleanYourTV Manager

> Unofficial community Windows GUI for installing and managing [CleanYourTV](https://github.com/Gathin23/cleanyourtv) on Android TV.

[![Build Windows](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml/badge.svg)](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml)

CleanYourTV Manager is a desktop companion for users who want a graphical way to work with a CleanYourTV checkout and an Android TV device. The interface is built with **Python + PySide6** and designed using **Qt Designer `.ui` XML files**.

> **Community project:** this application is independent from the CleanYourTV maintainers unless explicitly stated otherwise.

## ✨ Features

- 📡 Connect to an Android TV device over ADB by IP.
- 🔍 Inspect manufacturer, model and Android version.
- 📦 Start the local CleanYourTV launcher installation workflow.
- 🎨 Detect and manage local CleanYourTV themes.
- 🧩 Detect and manage local CleanYourTV add-ons.
- 💾 Create a local backup before making changes.
- 📝 Show a visible operation log instead of hiding commands in the background.
- 🪟 Build a Windows executable with the included build script.
- 🤖 Build automatically with GitHub Actions.
- 🖌️ Keep the desktop UI editable through Qt Designer XML.

## 🖥️ Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Android SDK Platform-Tools with `adb` available in `PATH`, or an `ADB_PATH` environment variable pointing to `adb.exe`.
- A local CleanYourTV checkout if you want to use the installer integration.
- Network ADB enabled and reachable on the TV.

The manager is designed to work with Android TV devices, but compatibility depends on the device firmware and the CleanYourTV features being used.

## 🚀 Installation

### 1. Clone the repository

```powershell
git clone https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager.git
cd CleanYourTV-Manager
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start the manager

```powershell
python app\main.py
```

## 📺 Connect your TV

Enter the TV's IP address in the application, for example:

```text
192.168.0.118
```

Then press **Connect** and use **Check TV** to verify the ADB connection and device information.

You can also prefill the address from PowerShell:

```powershell
$env:TV_HOST = '192.168.0.118'
```

If ADB is not found automatically, set its path explicitly:

```powershell
$env:ADB_PATH = 'C:\Android\Sdk\platform-tools\adb.exe'
```

## 🧹 CleanYourTV integration

If your CleanYourTV checkout is located at:

```text
C:\Users\User\CleanYourTV
```

set:

```powershell
$env:CLEANYOURTV_ROOT = 'C:\Users\User\CleanYourTV'
```

Then launch the manager normally:

```powershell
python app\main.py
```

The manager is intended to use the existing CleanYourTV tooling instead of silently reimplementing or replacing upstream scripts.

## 🎨 Themes

The **Themes** section is designed to work with the `themes` directory from a CleanYourTV checkout.

A typical structure is:

```text
CleanYourTV/
└── themes/
    ├── aurora/
    ├── glass/
    ├── retro/
    └── ...
```

The manager can inspect the available theme directories. Applying a theme should remain an explicit user action.

## 🧩 Add-ons

The **Add-ons** section is designed around the add-on directories provided by CleanYourTV.

A typical structure is:

```text
CleanYourTV/
└── addons/
    ├── tv-hub/
    ├── capacity-stats/
    ├── weather/
    └── ...
```

Add-ons may have their own requirements. The manager should not pretend that an add-on is compatible with every television without checking its documentation.

## 🛡️ Safety

This project is intended to make potentially destructive TV modifications easier to understand, not easier to perform blindly.

The manager should:

- show the target TV before an operation;
- display commands or actions in the operation log;
- request confirmation before potentially disruptive changes;
- preserve a recovery path where possible;
- avoid blindly disabling Android system packages;
- protect TV input and Live TV services by default.

### Live TV / cable TV

If your television uses MediaTek TV services for terrestrial, cable or other tuner functions, do **not** disable the TV input stack just to remove launcher clutter.

For a device such as the Hyundai H-LED32BS5002, the exact package list depends on its firmware. Verify packages before disabling anything.

## 🔧 Windows build

To build the application locally:

```powershell
.\build.ps1
```

The resulting files are placed under:

```text
dist\
```

GitHub Actions can also build the Windows application from the repository workflow.

## 🧑‍💻 Qt Designer

The main window is stored as an XML `.ui` file:

```text
app\ui\MainWindow.ui
```

You can open it with Qt Designer and change the layout, widgets and text without rewriting the Python UI code.

## 📁 Project structure

```text
CleanYourTV-Manager/
├── .github/
│   └── workflows/
│       └── build-windows.yml
├── app/
│   ├── main.py
│   └── ui/
│       └── MainWindow.ui
├── build.ps1
├── LICENSE
├── README.md
└── requirements.txt
```

## 🧪 Development status

This is an active community project. Some manager functions are currently scaffolding and should be considered experimental until tested against real Android TV hardware.

Before publishing a stable release, test at least:

- ADB connection and reconnect behavior;
- device detection;
- CleanYourTV installation workflow;
- theme application and rollback;
- add-on installation and removal;
- backup and restore;
- failure handling when the TV disconnects;
- launcher recovery;
- preservation of Live TV / tuner services.

## 🤝 Contributing

Pull requests and issue reports are welcome.

When reporting a device-specific problem, include:

- TV model;
- Android/firmware version;
- CleanYourTV version or commit;
- manager version/commit;
- relevant log output;
- the exact operation that failed.

Do not publish passwords, private keys, ADB credentials or other sensitive information in an issue.

## 🔗 Links

- **CleanYourTV:** https://github.com/Gathin23/cleanyourtv
- **CleanYourTV Manager:** https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager

## 📄 License

The original code of CleanYourTV Manager is released under the **MIT License**.

CleanYourTV source code, themes, add-ons, artwork and other upstream assets remain subject to their respective licenses. This project does not change or relicense upstream material. Check the upstream repository before redistributing any CleanYourTV files or assets.
