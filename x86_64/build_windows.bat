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
  --onefile ^
  --strip ^
  --name Grouper ^
  --windowed ^
  --paths src ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebEngineQuick ^
  --exclude-module PySide6.QtWebEngine ^
  --exclude-module PySide6.QtWebView ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQuickWidgets ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtTest ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.Qt3DRender ^
  --exclude-module PySide6.Qt3DInput ^
  --exclude-module PySide6.Qt3DExtras ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtDataVisualization ^
  --exclude-module PySide6.QtPdf ^
  --exclude-module PySide6.QtPdfWidgets ^
  --exclude-module PySide6.QtNfc ^
  --exclude-module PySide6.QtPositioning ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtMultimediaWidgets ^
  --exclude-module PySide6.QtNetworkAuth ^
  --exclude-module PySide6.QtRemoteObjects ^
  --add-data "%ASSETS%\styles.css;assets" ^
  --add-data "%ASSETS%\backgroud-picture.jpg;assets" ^
  --add-data "%ASSETS%\welcome-picture.jpg;assets" ^
  %ENTRY%

echo.
echo Build complete. Find the standalone EXE under dist\Grouper.exe
endlocal
