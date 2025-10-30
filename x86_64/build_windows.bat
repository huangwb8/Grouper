@echo off
REM Build Windows 64-bit .exe with PyInstaller
REM Requires: Python 3.9+, pip install pyinstaller PySide6 openpyxl build

setlocal
set NAME=grouper
set ENTRY=src\grouper\app.py
set ASSETS=x86_64\assets

REM Ensure venv is active (optional)
python -m pip install --upgrade pip >NUL
python -m pip install pyinstaller PySide6 openpyxl >NUL

pyinstaller ^
  --noconfirm ^
  --clean ^
  --name Grouper ^
  --windowed ^
  --paths src ^
  --add-data "%ASSETS%\styles.css;assets" ^
  --add-data "%ASSETS%\backgroud-picture.jpg;assets" ^
  --add-data "%ASSETS%\welcome-picture.jpg;assets" ^
  %ENTRY%

echo.
echo Build complete. Find the EXE under dist\Grouper\Grouper.exe
endlocal
