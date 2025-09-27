@echo off

:: Read the current version from version.txt
setlocal enabledelayedexpansion
set /p version=<version.txt

:: Define the output file name
set output_name=HeaderCommenter_v!version!.exe

:: Run PyInstaller with the new version as the output name
pyinstaller --onefile --windowed --name=!output_name! src/editor.py

:: Done
echo Build complete: !output_name!
pause
