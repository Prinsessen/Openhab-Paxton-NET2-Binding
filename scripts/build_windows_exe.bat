@echo off
REM Build script for creating Windows executable from net2_toggle_door.py
REM 
REM Prerequisites:
REM   1. Install Python 3.8 or higher
REM   2. Install PyInstaller: pip install pyinstaller
REM   3. Install dependencies: pip install -r requirements.txt
REM
REM Usage: Run this script in the same directory as net2_toggle_door.py

echo Building net2_toggle_door.exe...
echo.

REM Install dependencies if needed
pip install -r requirements.txt
pip install pyinstaller

REM Build the executable
pyinstaller --onefile --console --name net2_toggle_door net2_toggle_door.py

echo.
echo Build complete!
echo Executable location: dist\net2_toggle_door.exe
echo.
echo Don't forget to copy net2_config.json to the same directory as the .exe
echo.
pause
