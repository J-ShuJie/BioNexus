@echo off
:: BioNexus智能启动器 v1.2.13 - 增强调试版本
:: 自动处理环境配置和程序启动
:: 一个BAT搞定一切！

:: 启用UTF-8编码，但允许失败
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: 设置调试模式
set "DEBUG_MODE=0"
if "%1"=="--debug" set "DEBUG_MODE=1"
if "%1"=="--console" set "DEBUG_MODE=1"
if "%1"=="-v" set "DEBUG_MODE=1"
if "%1"=="--verbose" set "DEBUG_MODE=1"

:: 创建日志目录和文件
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "DEBUG_LOG=%LOG_DIR%\launcher_debug.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

:: 启动监控函数
call :LOG_INFO "=========================================="
call :LOG_INFO "BioNexus Launcher v1.2.13 启动开始"
call :LOG_INFO "时间: %DATE% %TIME%"
call :LOG_INFO "调试模式: %DEBUG_MODE%"
call :LOG_INFO "工作目录: %SCRIPT_DIR%"
call :LOG_INFO "=========================================="

:: 设置标题和变量
title BioNexus Launcher v1.2.13
set "APP_NAME=BioNexus"
set "APP_VERSION=1.2.13"
set "RUNTIME_DIR=%SCRIPT_DIR%runtime"
set "PYTHON_DIR=%RUNTIME_DIR%\python"
set "PYTHON_MIN_VERSION=3.8"

call :LOG_INFO "变量初始化完成"
call :LOG_INFO "SCRIPT_DIR=%SCRIPT_DIR%"
call :LOG_INFO "RUNTIME_DIR=%RUNTIME_DIR%"
call :LOG_INFO "PYTHON_DIR=%PYTHON_DIR%"

:: 切换到脚本目录
call :LOG_INFO "切换到脚本目录: %SCRIPT_DIR%"
cd /d "%SCRIPT_DIR%"
if %errorlevel% neq 0 (
    call :LOG_ERROR "无法切换到脚本目录"
    call :SHOW_ERROR_AND_EXIT "目录切换失败"
)

:: 清屏并显示启动信息
if %DEBUG_MODE%==0 cls
echo =============================================
echo    %APP_NAME% Launcher v%APP_VERSION%
echo    Professional Bioinformatics Tools Manager
echo =============================================
echo.

:: =============================================================================
:: 阶段1：快速环境检测
:: =============================================================================

call :LOG_INFO "开始环境检测阶段"
echo [INFO] Checking environment...

:: 检查便携式Python
set "PORTABLE_PYTHON=%PYTHON_DIR%\python.exe"
set "PORTABLE_PYTHONW=%PYTHON_DIR%\pythonw.exe"
set "FOUND_PYTHON="
set "PYTHON_TYPE="
set "NEED_SETUP=0"

:: 1. 检查便携式Python是否存在且可用
call :LOG_INFO "检查便携式Python: %PORTABLE_PYTHON%"
if exist "%PORTABLE_PYTHON%" (
    call :LOG_INFO "便携式Python文件存在，验证可用性..."
    call :CHECK_PYTHON_COMMAND "%PORTABLE_PYTHON%"
    if !errorlevel! equ 0 (
        call :LOG_INFO "便携式Python可用，检查PyQt5..."
        call :CHECK_PYQT5 "%PORTABLE_PYTHON%"
        if !errorlevel! equ 0 (
            set "FOUND_PYTHON=%PORTABLE_PYTHON%"
            set "PYTHON_TYPE=portable"
            call :LOG_INFO "便携式环境就绪"
            echo [SUCCESS] Portable environment ready
        ) else (
            call :LOG_WARNING "便携式Python存在但缺少PyQt5"
            echo [INFO] Portable Python found but PyQt5 missing
            set "NEED_SETUP=1"
        )
    ) else (
        call :LOG_ERROR "便携式Python已损坏"
        echo [INFO] Portable Python corrupted
        set "NEED_SETUP=1"
    )
) else (
    call :LOG_INFO "便携式Python不存在，检查系统Python"
    :: 2. 没有便携式Python，检查系统Python
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        :: 检查版本
        for /f "tokens=2" %%a in ('python --version 2^>^&1') do set "PYTHON_VER=%%a"
        
        :: 检查版本是否>=3.8
        echo !PYTHON_VER! | findstr /r "3\.[89]" >nul
        if !errorlevel! equ 0 (
            set "CHECK_OK=1"
        ) else (
            echo !PYTHON_VER! | findstr /r "3\.1[0-9]" >nul
            if !errorlevel! equ 0 (
                set "CHECK_OK=1"
            ) else (
                set "CHECK_OK=0"
            )
        )
        
        if !CHECK_OK! equ 1 (
            :: 版本OK，检查PyQt5
            python -c "import PyQt5" >nul 2>&1
            if !errorlevel! equ 0 (
                set "FOUND_PYTHON=python"
                set "PYTHON_TYPE=system"
                echo [SUCCESS] System Python ready (v!PYTHON_VER!)
            ) else (
                echo [INFO] System Python found but PyQt5 missing
                set "NEED_SETUP=1"
            )
        ) else (
            echo [INFO] System Python too old (v!PYTHON_VER!, need 3.8+)
            set "NEED_SETUP=1"
        )
    ) else (
        echo [INFO] No Python environment found
        set "NEED_SETUP=1"
    )
)

:: =============================================================================
:: 阶段2：自动设置便携式环境（如果需要）
:: =============================================================================

if !NEED_SETUP! equ 1 (
    echo.
    echo [INFO] Setting up portable environment...
    echo [INFO] This is a one-time setup (about 100MB download)
    echo.
    
    :: 创建目录
    if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"
    if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
    
    :: 设置Python版本和下载URL
    set "PYTHON_VERSION=3.11.9"
    set "PYTHON_URL=https://www.python.org/ftp/python/!PYTHON_VERSION!/python-!PYTHON_VERSION!-embed-amd64.zip"
    set "PYTHON_ZIP=%TEMP%\python-embed.zip"
    
    :: 下载Python embeddable
    echo [INFO] Downloading Python !PYTHON_VERSION! (please wait)...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!PYTHON_URL!' -OutFile '!PYTHON_ZIP!' -ErrorAction Stop; exit 0 } catch { exit 1 }}" >nul 2>&1
    
    if !errorlevel! neq 0 (
        echo [ERROR] Download failed. Please check your internet connection.
        echo.
        echo You can manually download Python embeddable from:
        echo !PYTHON_URL!
        echo Extract to: %PYTHON_DIR%
        echo.
        pause
        exit /b 1
    )
    
    :: 解压Python
    echo [INFO] Extracting Python...
    powershell -Command "Expand-Archive -Path '!PYTHON_ZIP!' -DestinationPath '%PYTHON_DIR%' -Force" >nul 2>&1
    
    if not exist "%PORTABLE_PYTHON%" (
        echo [ERROR] Extraction failed!
        pause
        exit /b 1
    )
    
    :: 配置Python
    echo [INFO] Configuring Python...
    
    :: 创建sitecustomize.py
    echo import sys > "%PYTHON_DIR%\sitecustomize.py"
    echo sys.path.append('.') >> "%PYTHON_DIR%\sitecustomize.py"
    echo sys.path.append('./site-packages') >> "%PYTHON_DIR%\sitecustomize.py"
    
    :: 修改._pth文件以启用site包
    if exist "%PYTHON_DIR%\python311._pth" (
        echo. >> "%PYTHON_DIR%\python311._pth"
        echo import site >> "%PYTHON_DIR%\python311._pth"
    )
    
    :: 创建site-packages目录
    if not exist "%PYTHON_DIR%\site-packages" mkdir "%PYTHON_DIR%\site-packages"
    
    :: 安装pip
    echo [INFO] Installing pip...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PYTHON_DIR%\get-pip.py'}" >nul 2>&1
    "%PORTABLE_PYTHON%" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location >nul 2>&1
    
    :: 安装依赖
    echo [INFO] Installing dependencies (this may take a few minutes)...
    if exist "requirements.txt" (
        "%PORTABLE_PYTHON%" -m pip install -r requirements.txt --target "%PYTHON_DIR%\site-packages" --no-warn-script-location --quiet
    ) else (
        :: 至少安装PyQt5
        "%PORTABLE_PYTHON%" -m pip install PyQt5 --target "%PYTHON_DIR%\site-packages" --no-warn-script-location --quiet
    )
    
    :: 清理临时文件
    del "%PYTHON_ZIP%" >nul 2>&1
    del "%PYTHON_DIR%\get-pip.py" >nul 2>&1
    
    :: 验证安装
    "%PORTABLE_PYTHON%" -c "import PyQt5" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Portable environment setup complete!
        set "FOUND_PYTHON=%PORTABLE_PYTHON%"
        set "PYTHON_TYPE=portable"
    ) else (
        echo [ERROR] Setup completed but PyQt5 verification failed
        echo Please check the installation and try again
        pause
        exit /b 1
    )
    
    echo.
)

:: =============================================================================
:: 阶段3：启动应用程序
:: =============================================================================

if not defined FOUND_PYTHON (
    echo [ERROR] No valid Python environment available
    pause
    exit /b 1
)

echo [INFO] Starting %APP_NAME%...

:: 决定启动模式
set "LAUNCH_MODE=hidden"
set "LAUNCH_PYTHON=%FOUND_PYTHON%"

:: 检查是否有pythonw（无窗口版本）
if "%PYTHON_TYPE%"=="portable" (
    if exist "%PORTABLE_PYTHONW%" (
        set "LAUNCH_PYTHON=%PORTABLE_PYTHONW%"
    ) else (
        set "LAUNCH_MODE=hidden-vbs"
    )
) else (
    :: 系统Python，尝试找pythonw
    pythonw --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "LAUNCH_PYTHON=pythonw"
    ) else (
        set "LAUNCH_MODE=hidden-vbs"
    )
)

:: 检查调试模式
if "%1"=="--debug" set "LAUNCH_MODE=visible"
if "%1"=="--console" set "LAUNCH_MODE=visible"

:: 根据模式启动
if "!LAUNCH_MODE!"=="visible" (
    :: 调试模式，显示控制台
    "%LAUNCH_PYTHON%" main.py %*
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Application exited with error code: !errorlevel!
        pause
    )
) else if "!LAUNCH_MODE!"=="hidden" (
    :: 使用pythonw隐藏控制台
    start "" "%LAUNCH_PYTHON%" main.py %*
    echo [SUCCESS] %APP_NAME% launched successfully!
    timeout /t 2 >nul
) else (
    :: 使用VBScript隐藏控制台
    echo CreateObject("Wscript.Shell"^).Run "cmd /c """"%LAUNCH_PYTHON%"""" main.py %*", 0, False > "%TEMP%\launch_bionexus.vbs"
    start "" wscript "%TEMP%\launch_bionexus.vbs"
    echo [SUCCESS] %APP_NAME% launched successfully!
    timeout /t 2 >nul
    del "%TEMP%\launch_bionexus.vbs" >nul 2>&1
)

call :LOG_INFO "程序正常退出"
endlocal
exit /b 0

:: =============================================================================
:: 日志和错误处理函数
:: =============================================================================

:LOG_INFO
:: 记录信息日志
echo [%TIME%] [INFO] %~1 >> "%DEBUG_LOG%" 2>nul
if %DEBUG_MODE%==1 echo [INFO] %~1
exit /b 0

:LOG_ERROR
:: 记录错误日志
echo [%TIME%] [ERROR] %~1 >> "%DEBUG_LOG%" 2>nul
echo [ERROR] %~1
exit /b 0

:LOG_WARNING
:: 记录警告日志
echo [%TIME%] [WARNING] %~1 >> "%DEBUG_LOG%" 2>nul
if %DEBUG_MODE%==1 echo [WARNING] %~1
exit /b 0

:SHOW_ERROR_AND_EXIT
:: 显示错误并退出
call :LOG_ERROR "%~1"
echo.
echo ===== BioNexus 启动失败 =====
echo 错误: %~1
echo 请查看日志文件: %DEBUG_LOG%
echo.
if exist "%DEBUG_LOG%" (
    echo 最近的日志内容:
    echo ------------------------
    for /f "skip=0 tokens=*" %%a in ('more +0 "%DEBUG_LOG%"') do echo %%a
    echo ------------------------
)
echo.
echo 按任意键退出...
pause >nul
exit /b 1

:CHECK_PYTHON_COMMAND
:: 检查Python命令是否可用
set "PYTHON_CMD=%~1"
call :LOG_INFO "测试Python命令: %PYTHON_CMD%"

"%PYTHON_CMD%" --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do (
        call :LOG_INFO "找到Python版本: %%v"
        set "FOUND_VERSION=%%v"
    )
    exit /b 0
) else (
    call :LOG_WARNING "Python命令不可用: %PYTHON_CMD%"
    exit /b 1
)

:CHECK_PYQT5
:: 检查PyQt5是否可用
set "PYTHON_CMD=%~1"
call :LOG_INFO "检查PyQt5依赖: %PYTHON_CMD%"

"%PYTHON_CMD%" -c "import PyQt5; print('PyQt5 OK')" >nul 2>&1
if %errorlevel% equ 0 (
    call :LOG_INFO "PyQt5依赖检查通过"
    exit /b 0
) else (
    call :LOG_WARNING "PyQt5依赖缺失"
    exit /b 1
)

:DOWNLOAD_AND_EXTRACT_PYTHON
:: 下载并解压Python
call :LOG_INFO "开始下载Python embeddable版本..."
echo [INFO] 正在下载Python，请稍候...

:: 使用PowerShell下载，增加错误处理
powershell -Command "& { try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%' -TimeoutSec 60; Write-Host 'Download completed' } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 } }" 2>"%LOG_DIR%\download_error.log"

if %errorlevel% neq 0 (
    call :LOG_ERROR "Python下载失败，查看详细错误: %LOG_DIR%\download_error.log"
    if exist "%LOG_DIR%\download_error.log" (
        echo 下载错误详情:
        type "%LOG_DIR%\download_error.log"
    )
    call :SHOW_ERROR_AND_EXIT "Python下载失败，请检查网络连接"
)

call :LOG_INFO "下载完成，开始解压..."
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force" 2>"%LOG_DIR%\extract_error.log"

if %errorlevel% neq 0 (
    call :LOG_ERROR "Python解压失败"
    if exist "%LOG_DIR%\extract_error.log" type "%LOG_DIR%\extract_error.log"
    call :SHOW_ERROR_AND_EXIT "Python解压失败"
)

call :LOG_INFO "Python安装完成"
exit /b 0