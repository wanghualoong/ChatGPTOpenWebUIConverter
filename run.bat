@echo off
set SCRIPT_DIR=%~dp0
if exist "%SystemRoot%\py.exe" (
  py -3 "%SCRIPT_DIR%bootstrap.py" %*
) else (
  python "%SCRIPT_DIR%bootstrap.py" %*
)
