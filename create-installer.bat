@echo off

:: Read the current version from version.txt
setlocal enabledelayedexpansion
set /p version=<version.txt

:: Increment the version number (Simple example: increment the second digit)
for /f "tokens=1-2 delims=." %%a in ("!version!") do (
    set /a second=%%b+1
    set new_version=%%a.!second!
)

:: Save the new version back to version.txt
echo !new_version! > version.txt

:: Define the output file name
set output_name=HeaderCommenter_v!new_version!.exe

:: Run PyInstaller with the new version as the output name
pyinstaller --onefile --windowed --name=!output_name! src/editor.py

:: Done
echo Build complete: !output_name!
pause
