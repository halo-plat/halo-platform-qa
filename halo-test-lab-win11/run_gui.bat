@echo off
REM Halo Test Lab launcher (Windows CMD)
set VENV_PY=.venv\Scripts\python.exe

if not exist %VENV_PY% (
  echo Creating venv...
  python -m venv .venv
  if errorlevel 1 exit /b %errorlevel%
)

echo Installing/updating dependencies...
%VENV_PY% -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%

echo Launching GUI...
%VENV_PY% -m halo_test_lab.gui
exit /b %errorlevel%
