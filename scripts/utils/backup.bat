@echo off
REM Script backup MongoDB database (Windows)

set BACKUP_DIR=backups
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_FILE=%BACKUP_DIR%\market_backup_%TIMESTAMP%

echo 💾 Creating MongoDB backup...

REM Tạo thư mục backup nếu chưa có
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Backup MongoDB
docker-compose exec -T mongodb mongodump --username admin --password password --authenticationDatabase admin --db market --archive > "%BACKUP_FILE%.archive"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Backup created successfully: %BACKUP_FILE%.archive
    echo.
    echo 📁 Backup location: %BACKUP_FILE%.archive
) else (
    echo ❌ Backup failed!
    exit /b 1
)

