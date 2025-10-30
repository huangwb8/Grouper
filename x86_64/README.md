# Windows Build and Assets

- Place background image at `x86_64/assets/backgroud-picture.jpg`.
- Place welcome image at `x86_64/assets/welcome-picture.jpg`.
- Customize styles in `x86_64/assets/styles.css`.

Build steps (PowerShell or CMD):

1. `python -m venv .venv && .venv\\Scripts\\activate`
2. `pip install -e .[dev]` (or `pip install PySide6 openpyxl`)
3. `x86_64\\build_windows.bat`

The EXE is created at `dist/Grouper/Grouper.exe`.

