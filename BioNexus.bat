@echo off
chcp 65001 >nul
title BioNexus Launcher

:: Change to the directory where this batch file is located
cd /d "%~dp0"

:: Ensure logs directory and define launcher log file
if not exist "logs" mkdir logs
set "LAUNCHER_LOG=logs\launcher_debug.log"

:: Force UTF-8 for Python stdout/stderr to avoid GBK encoding errors
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo ==========================================
echo    BioNexus Launcher v1.2.17
echo    Bioinformatics Tools Manager
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python not found on system
    echo [INFO] Checking for portable Python installation...

    :: Check if portable Python exists
    if exist "python_portable\python.exe" (
        echo [INFO] Found portable Python installation
        set "PATH=%CD%\python_portable;%CD%\python_portable\Scripts;%PATH%"
    ) else (
        echo [INFO] Python not found, downloading latest version...
        echo [INFO] This may take a few minutes, please wait...
        echo.

        :: Create temp directory
        if not exist "temp" mkdir temp

        :: Download latest Python embeddable package
        echo [INFO] Step 1/5: Downloading Python embeddable package...
        powershell -ExecutionPolicy Bypass -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip' -OutFile 'temp\python.zip' -UseBasicParsing } catch { Write-Host 'Download failed'; exit 1 }"

        if not exist "temp\python.zip" (
            echo [ERROR] Failed to download Python
            echo Please install Python manually from: https://www.python.org/downloads/
            echo.
            echo [ERROR] Failed to download Python >> "%LAUNCHER_LOG%"
            exit /b 1
        )

        :: Extract Python
        echo [INFO] Step 2/5: Extracting Python...
        powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path 'temp\python.zip' -DestinationPath 'python_portable' -Force"

        :: Enable pip support
        echo [INFO] Step 3/5: Configuring Python...
        powershell -ExecutionPolicy Bypass -Command "$pthFile = Get-ChildItem 'python_portable\*._pth' | Select-Object -First 1; if ($pthFile) { $content = Get-Content $pthFile.FullName; $content = $content -replace '#import site', 'import site'; $content | Set-Content $pthFile.FullName }"

        :: Download get-pip.py
        echo [INFO] Step 4/5: Downloading pip installer...
        powershell -ExecutionPolicy Bypass -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'temp\get-pip.py' -UseBasicParsing } catch { Write-Host 'Download failed'; exit 1 }"

        :: Install pip
        echo [INFO] Step 5/5: Installing pip...
        python_portable\python.exe temp\get-pip.py --quiet --no-warn-script-location

        :: Clean up
        if exist "temp" rd /s /q temp

        :: Update PATH
        set "PATH=%CD%\python_portable;%CD%\python_portable\Scripts;%PATH%"

        echo [SUCCESS] Python installed successfully
        echo.
    )
)

:: Show Python version
echo [INFO] Detected Python version:
python --version

:: Check dependencies
echo [INFO] Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyQt5 not found, installing dependencies...
    echo [INFO] Installing dependencies, please wait...
    pip install -r requirements.txt >> "%LAUNCHER_LOG%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo Please run manually: pip install -r requirements.txt
        echo.
        echo [ERROR] Dependency installation failed >> "%LAUNCHER_LOG%"
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully
) else (
    echo [SUCCESS] PyQt5 is installed
)

echo.
echo [INFO] Starting BioNexus...
echo.

:: Launch application (log stdout/stderr)
python main.py >> "%LAUNCHER_LOG%" 2>&1

:: Record exit code to log and exit without pause so console always closes
set "APP_EXIT=%ERRORLEVEL%"
echo [INFO] Program exited with code %APP_EXIT% >> "%LAUNCHER_LOG%"
exit /b %APP_EXIT%
