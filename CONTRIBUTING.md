# Contributing to CleanYourTV Manager

Thanks for helping improve the project.

## Before opening a pull request

1. Open an issue first for larger changes.
2. Keep the project focused on managing CleanYourTV safely.
3. Do not bundle upstream CleanYourTV code, themes, add-ons, artwork or other assets unless their license permits redistribution.
4. Keep potentially destructive device operations explicit and reversible.
5. Preserve Live TV / tuner functionality by default.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Run checks:

```powershell
ruff check app tests
pytest
python -m compileall -q app tests
```

Build Windows:

```powershell
.\build.ps1
```

## Pull requests

Please include:

- a short explanation of the change;
- testing performed;
- affected Android TV versions/devices, if applicable;
- screenshots for UI changes.

Never include ADB credentials, private keys, tokens, personal network details or private logs in a pull request.
