# Windows Shortcut Files (.bat)

These batch files provide quick shortcuts for controlling specific doors.

## How to Use

1. Place the .bat files in the same directory as `net2_toggle_door.exe`
2. Double-click the .bat file to run the command
3. The window will pause after execution so you can see the result

## Included Shortcuts

- **Interactive_Door_Control.bat** - Opens interactive menu to select any door
- **Open_Door_6203980.bat** - Opens door 6203980 (Fordør Terndrupvej)
- **Close_Door_6203980.bat** - Closes door 6203980
- **Open_Door_6612642.bat** - Opens door 6612642
- **Close_Door_6612642.bat** - Closes door 6612642

## Creating Custom Shortcuts

To create a shortcut for a different door:

1. Copy any existing .bat file
2. Edit the file in Notepad
3. Change the door ID number
4. Change "open" to "close" if needed
5. Rename the file to something descriptive

Example content:
```batch
@echo off
net2_toggle_door.exe YOUR_DOOR_ID open
pause
```

## Creating Desktop Shortcuts

To add a shortcut to your desktop:

1. Right-click on any .bat file
2. Select "Send to" → "Desktop (create shortcut)"
3. Right-click the desktop shortcut → "Properties"
4. You can change the icon and name here

## Advanced: Silent Execution (No Pause)

To run without the pause (window closes immediately):

1. Open the .bat file in Notepad
2. Remove the `pause` line
3. Save the file

Or create a VBS wrapper to hide the window completely:
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "Open_Door_6203980.bat", 0
Set WshShell = Nothing
```
Save as `Open_Door_6203980.vbs` and run instead of the .bat file.
