# CleanYourTV Manager

> Unofficial community Windows GUI for installing and managing [CleanYourTV](https://github.com/Gathin23/cleanyourtv) on Android TV.

[![Windows CI](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml/badge.svg)](https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager/actions/workflows/build-windows.yml)

CleanYourTV Manager is a desktop companion for users who want a graphical way to work with a CleanYourTV checkout and an Android TV device. The interface is built with **Python + PySide6** and designed using **Qt Designer `.ui` XML files**.

> **Community project:** this application is independent from the CleanYourTV maintainers unless explicitly stated otherwise.

## ✨ Current features

- 📡 Connect to an Android TV device over ADB by IP.
- 🔍 Inspect manufacturer, model, Android version and ADB state.
- 📦 Start the local CleanYourTV launcher installation workflow.
- 🎨 Inspect the themes available in a local CleanYourTV checkout.
- 🧩 Inspect the add-ons available in a local CleanYourTV checkout.
- 💾 Create timestamped local project backups.
- 📝 Show a visible operation log instead of hiding commands in the background.
- 🛡️ Avoid automatic package disabling and keep potentially destructive actions explicit.
- 🪟 Build a Windows executable with the included PyInstaller spec and PowerShell script.
- 🤖 Run linting, tests and Windows packaging in GitHub Actions.
- 🖌️ Keep the desktop UI editable through Qt Designer XML.

### Planned

- Dedicated theme previews and apply/rollback workflow.
- Add-on installation/removal with per-add-on documentation checks.
- Safe package inventory and explicit debloat profiles.
- One-click backup restore.
- Better launcher recovery and device reconnect handling.
- Signed release packages and versioned GitHub Releases.

## 🖥️ Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Android SDK Platform-Tools with `adb` available in `PATH`, or an `ADB_PATH` environment variable pointing to `adb.exe`.
- A local CleanYourTV checkout if you want to use the installer, theme and add-on integration.
- Network ADB enabled and reachable on the TV.

Compatibility depends on the device firmware and the CleanYourTV features being used.

## 🚀 Installation from source

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

The manager uses the existing CleanYourTV tooling instead of silently reimplementing or replacing upstream scripts.

## 🎨 Themes and 🧩 add-ons

The manager reads the local `themes` and `addons` directories from a CleanYourTV checkout and reports what is available.

Typical structure:

```text
CleanYourTV/
├── themes/
│   ├── aurora/
│   ├── glass/
│   └── ...
└── addons/
    ├── tv-hub/
    ├── capacity-stats/
    └── ...
```

The current release does **not** silently install or modify a theme or add-on. Applying and installing these components is deliberately kept explicit while compatibility and rollback handling are developed.

## 🛡️ Safety

This project is intended to make potentially destructive TV modifications easier to understand, not easier to perform blindly.

The manager should:

- show the target TV before an operation;
- display actions in the operation log;
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

The resulting executable is placed under:

```text
dist\CleanYourTV-Manager.exe
```

The PyInstaller specification explicitly includes the Qt `.ui` files so the packaged application does not depend on the source checkout for its interface.

GitHub Actions runs linting, tests and the Windows build on pushes and pull requests.

## 🧪 Development checks

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run:

```powershell
ruff check app tests
pytest
python -m compileall -q app tests
```

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
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
│       └── build-windows.yml
├── app/
│   ├── core/
│   │   ├── adb.py
│   │   ├── backup.py
│   │   ├── clean_your_tv.py
│   │   └── paths.py
│   ├── main.py
│   └── ui/
│       └── MainWindow.ui
├── tests/
├── CleanYourTV-Manager.spec
├── build.ps1
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## 🤝 Contributing

Pull requests and issue reports are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

When reporting a device-specific problem, include:

- TV model;
- Android/firmware version;
- CleanYourTV version or commit;
- manager version/commit;
- relevant log output;
- the exact operation that failed.

Do not publish passwords, private keys, ADB credentials or other sensitive information in an issue.

## 🔐 Security

See [SECURITY.md](SECURITY.md) for responsible vulnerability reporting.

## 🔗 Links

- **CleanYourTV:** https://github.com/Gathin23/cleanyourtv
- **CleanYourTV Manager:** https://github.com/kimberlyfigueroaxa125-boop/CleanYourTV-Manager

## 📄 License

The original code of CleanYourTV Manager is released under the **MIT License**.

CleanYourTV source code, themes, add-ons, artwork and other upstream assets remain subject to their respective licenses. This project does not change or relicense upstream material. Check the upstream repository before redistributing any CleanYourTV files or assets.
