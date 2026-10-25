$ErrorActionPreference = 'Stop'

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean CleanYourTV-Manager.spec

Write-Host "Build complete: dist\CleanYourTV-Manager\CleanYourTV-Manager.exe" -ForegroundColor Green
