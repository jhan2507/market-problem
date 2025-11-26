@echo off
REM Script quản lý version (Windows)

set VERSION_FILE=..\VERSION

if "%1"=="get" (
    if exist "%VERSION_FILE%" (
        type "%VERSION_FILE%"
    ) else (
        echo 0.0.0
    )
    exit /b 0
)

if "%1"=="set" (
    if "%2"=="" (
        echo ❌ Usage: scripts\version.bat set ^<version^>
        echo    Example: scripts\version.bat set 1.2.3
        exit /b 1
    )
    echo %2 > "%VERSION_FILE%"
    echo ✅ Version set to %2
    exit /b 0
)

if "%1"=="show" (
    if exist "%VERSION_FILE%" (
        echo Current version:
        type "%VERSION_FILE%"
    ) else (
        echo Current version: 0.0.0
    )
    exit /b 0
)

echo Usage: scripts\version.bat {get^|set^|show}
echo.
echo Commands:
echo   get              - Get current version
echo   set ^<version^>    - Set version (e.g., 1.2.3)
echo   show             - Show current version

