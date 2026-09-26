@echo off
setlocal
rem ExecutionPolicy applies only to this child PowerShell process.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-expanded-search.ps1" %*
exit /b %errorlevel%
