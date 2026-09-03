@echo off
setlocal
set "ROOT=%~dp0"
if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" -m open_compute_basis %*
  exit /b %ERRORLEVEL%
)
python -m open_compute_basis %*
exit /b %ERRORLEVEL%
