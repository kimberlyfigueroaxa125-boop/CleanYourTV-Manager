$ErrorActionPreference = 'Stop'

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name CleanYourTV-Manager app\main.py
Write-Host "Build complete: dist\CleanYourTV-Manager\CleanYourTV-Manager.exe"
