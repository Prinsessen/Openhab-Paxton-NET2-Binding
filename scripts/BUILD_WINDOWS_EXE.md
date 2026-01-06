# Building Windows Executable for net2_toggle_door

## Prerequisites
1. Windows PC with Python 3.8 or higher installed
2. The following files from this directory:
   - `net2_toggle_door.py`
   - `net2_config.json`
   - `requirements.txt`
   - `build_windows_exe.bat`

## Build Steps

### Option 1: Using the batch file (Easiest)
1. Copy all files to your Windows PC
2. Open Command Prompt in the directory containing the files
3. Run: `build_windows_exe.bat`
4. The executable will be created in the `dist\` folder

### Option 2: Manual build
1. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Build the executable:
   ```
   pyinstaller --onefile --console --name net2_toggle_door net2_toggle_door.py
   ```

3. Find the executable in: `dist\net2_toggle_door.exe`

## Deployment

1. Copy `net2_toggle_door.exe` from the `dist\` folder to your desired location
2. Copy `net2_config.json` to the SAME directory as the .exe
3. Run from Command Prompt:
   ```
   net2_toggle_door.exe
   net2_toggle_door.exe 6203980 open
   net2_toggle_door.exe 6203980 close
   ```

## Notes
- The executable is standalone and does not require Python to be installed
- The `net2_config.json` file MUST be in the same directory as the .exe
- The `.door_state.json` file will be created automatically in the same directory
- File size will be approximately 10-15 MB

## Troubleshooting
- If Windows SmartScreen blocks it, click "More info" → "Run anyway"
- If antivirus flags it, add an exception (false positive is common with PyInstaller)
- Ensure the config file path is correct and readable
