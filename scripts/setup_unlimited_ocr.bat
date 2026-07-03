@echo off
setlocal
cd /d "%~dp0\.."
powershell.exe -ExecutionPolicy Bypass -File scripts\setup_unlimited_ocr.ps1
