@echo off
setlocal enabledelayedexpansion
title Installing AEHD Driver

echo ===================================================================
echo   Google Android Emulator Hypervisor Driver (AEHD) Installer
echo ===================================================================
echo.

set "DRIVER_DIR=%LOCALAPPDATA%\Android\Sdk\extras\google\Android_Emulator_Hypervisor_Driver"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo Please right-click install_emulator_driver.bat and select:
    echo   "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/4] Copying aehd.sys kernel driver to System32\drivers...
copy /y "%DRIVER_DIR%\aehd.sys" "%windir%\System32\drivers\aehd.sys"

echo [2/4] Registering driver with pnputil...
pnputil /add-driver "%DRIVER_DIR%\aehd.Inf" /install

echo [3/4] Creating aehd kernel service...
sc stop aehd >nul 2>&1
sc delete aehd >nul 2>&1
sc create aehd type= kernel start= demand binPath= "System32\drivers\aehd.sys" DisplayName= "Android Emulator hypervisor driver Service"

echo [4/4] Starting aehd service...
sc start aehd

echo.
echo ===================================================================
echo Service Status:
sc query aehd
echo ===================================================================
echo.
echo If you see STATE : 4 RUNNING, installation succeeded!
pause
