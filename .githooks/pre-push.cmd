@echo off
setlocal EnableDelayedExpansion

set "HOOK_DIR=%~dp0"
set "REMOTE_NAME=%~1"
if "%REMOTE_NAME%"=="" set "REMOTE_NAME=origin"
set "BASE_BRANCH=%AUTO_MANUAL_BASE_BRANCH%"
if "%BASE_BRANCH%"=="" set "BASE_BRANCH=main"

pushd "%HOOK_DIR%\.." >nul 2>nul || exit /b 1

if exist "%CD%\.venv\Scripts\python.exe" (
    "%CD%\.venv\Scripts\python.exe" scripts\git_branch_guard.py pre-push --repo-root "%CD%" --remote "%REMOTE_NAME%" --base-branch "%BASE_BRANCH%"
    set "EXIT_CODE=%ERRORLEVEL%"
    popd >nul
    exit /b %EXIT_CODE%
)

if exist "%CD%\.venv\bin\python" (
    "%CD%\.venv\bin\python" scripts\git_branch_guard.py pre-push --repo-root "%CD%" --remote "%REMOTE_NAME%" --base-branch "%BASE_BRANCH%"
    set "EXIT_CODE=%ERRORLEVEL%"
    popd >nul
    exit /b %EXIT_CODE%
)

if defined PYTHON (
    "%PYTHON%" scripts\git_branch_guard.py pre-push --repo-root "%CD%" --remote "%REMOTE_NAME%" --base-branch "%BASE_BRANCH%"
    set "EXIT_CODE=!ERRORLEVEL!"
    popd >nul
    exit /b !EXIT_CODE!
)

where python >nul 2>nul
if not errorlevel 1 (
    python scripts\git_branch_guard.py pre-push --repo-root "%CD%" --remote "%REMOTE_NAME%" --base-branch "%BASE_BRANCH%"
    set "EXIT_CODE=!ERRORLEVEL!"
    popd >nul
    exit /b !EXIT_CODE!
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 scripts\git_branch_guard.py pre-push --repo-root "%CD%" --remote "%REMOTE_NAME%" --base-branch "%BASE_BRANCH%"
    set "EXIT_CODE=!ERRORLEVEL!"
    popd >nul
    exit /b !EXIT_CODE!
)

echo [pre-push] Python 3 is required to run the repo branch guard. 1>&2
popd >nul
exit /b 1
