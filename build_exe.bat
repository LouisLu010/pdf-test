@echo off
setlocal enabledelayedexpansion

rem Build a standalone Windows exe (no Python required to run).
set APP_NAME=pdf-annotator

pyinstaller --noconfirm --clean --windowed --onefile --name "!APP_NAME!" main.py

echo.
echo Build complete. The exe is at dist\!APP_NAME!.exe
echo Distribute dist\!APP_NAME!.exe to end users; they do not need Python installed.

endlocal
