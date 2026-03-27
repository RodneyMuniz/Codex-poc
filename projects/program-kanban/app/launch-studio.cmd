@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch-studio.ps1" -OpenBrowser
endlocal
