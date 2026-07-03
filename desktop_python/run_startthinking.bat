@echo off
setlocal
cd /d "%~dp0\.."

set OCR_PY=%CD%\.venv-ocr\Scripts\python.exe

if exist "%OCR_PY%" (
  "%OCR_PY%" desktop_python\startthinking.py
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 desktop_python\startthinking.py
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python desktop_python\startthinking.py
  exit /b %errorlevel%
)

set BUNDLED_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" desktop_python\startthinking.py
  exit /b %errorlevel%
)

echo Cannot find Python. Please install Python 3.11+ or add it to PATH.
pause
exit /b 1
