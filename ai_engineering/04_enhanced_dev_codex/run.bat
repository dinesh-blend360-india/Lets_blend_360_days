@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Resolve paths from this file, so double-clicking works from any directory.
set "PROJECT_DIR=%~dp0"
for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "VENV_DIR=%REPO_ROOT%\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%REPO_ROOT%\ai_engineering\requirements.txt"
set "RESULT=1"
set "PORT=8000"
set "VENV_BROKEN=0"

if not exist "%REQUIREMENTS%" (
    echo ERROR: Shared requirements.txt not found. Keep this folder inside ai_engineering.
    goto finish
)
pushd "%REPO_ROOT%"
if errorlevel 1 (
    echo ERROR: Cannot open the repository root.
    goto finish
)
set "DIRECTORY_PUSHED=1"

echo [1/3] Checking Python environment...
if not exist "%VENV_PYTHON%" goto find_python
"%VENV_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 goto install_dependencies
set "VENV_BROKEN=1"

:find_python
rem Prefer the Windows Python launcher, then PATH, then the usual Python 3.11 location.
set "BOOTSTRAP_PYTHON=py"
set "BOOTSTRAP_ARGS=-3"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 goto prepare_environment
set "BOOTSTRAP_PYTHON=python"
set "BOOTSTRAP_ARGS="
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 goto prepare_environment
set "BOOTSTRAP_PYTHON=%LocalAppData%\Programs\Python\Python311\python.exe"
"%BOOTSTRAP_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 goto prepare_environment
if "%VENV_BROKEN%"=="1" echo ERROR: The existing venv cannot run its configured Python. Install or repair Python 3.11+, then run this file again.
if not "%VENV_BROKEN%"=="1" echo ERROR: Python 3.11 or newer is required. Install Python, then run this file again.
goto finish

:prepare_environment
if exist "%VENV_DIR%\pyvenv.cfg" (
    echo Repairing the existing shared venv...
    "%BOOTSTRAP_PYTHON%" %BOOTSTRAP_ARGS% -m venv --upgrade "%VENV_DIR%"
) else (
    echo Creating the shared venv...
    "%BOOTSTRAP_PYTHON%" %BOOTSTRAP_ARGS% -m venv "%VENV_DIR%"
)
if errorlevel 1 (
    echo ERROR: Could not create or repair the Python environment.
    goto finish
)
"%VENV_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: The shared venv cannot run Python 3.11 or newer.
    goto finish
)

:install_dependencies
if "%~1"=="" goto port_ready
if /I "%~1"=="--check" goto port_ready
"%VENV_PYTHON%" -c "import sys; p=sys.argv[1]; sys.exit(0 if p.isdecimal() and len(p) <= 5 and 1 <= int(p) <= 65535 else 1)" "%~1" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Use run.bat, run.bat --check, or run.bat followed by a port number from 1 to 65535.
    goto finish
)
set "PORT=%~1"

:port_ready
echo [2/3] Installing dependencies from ai_engineering\requirements.txt...
"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS%" --quiet
if errorlevel 1 (
    echo ERROR: Dependency installation failed. Check the error above and your internet connection.
    goto finish
)

if /I "%~1"=="--check" (
    "%VENV_PYTHON%" -c "import fastapi, uvicorn, pydantic, sqlite3, dotenv; print('Setup check passed.')"
    set "RESULT=0"
    if errorlevel 1 set "RESULT=1"
    goto finish
)

echo [3/3] Starting the Task Management API...
echo Open http://127.0.0.1:%PORT%/docs
echo Press Ctrl+C to stop the server.
"%VENV_PYTHON%" -m uvicorn task_api.main:app --app-dir "%PROJECT_DIR%." --host 127.0.0.1 --port %PORT% --reload --reload-dir "%PROJECT_DIR%."
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo ERROR: The server stopped with an error. Check the output above.

:finish
if defined DIRECTORY_PUSHED popd
rem Keep errors visible when this file is double-clicked. --check never pauses.
if not "%RESULT%"=="0" if /I not "%~1"=="--check" pause
endlocal & exit /b %RESULT%
