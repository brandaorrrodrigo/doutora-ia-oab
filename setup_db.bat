@echo off
echo ============================================================
echo  JURIS_IA - DATABASE SETUP
echo ============================================================
echo.
echo This script will create the local PostgreSQL database.
echo You will be prompted for the PostgreSQL 'postgres' user password.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo Creating database 'juris_ia'...
psql -U postgres -c "CREATE DATABASE juris_ia;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database created
) else (
    echo [INFO] Database may already exist or error occurred
)

echo.
echo Creating user 'juris_ia_user'...
psql -U postgres -c "CREATE USER juris_ia_user WITH PASSWORD 'changeme123';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] User created
) else (
    echo [INFO] User may already exist or error occurred
)

echo.
echo Granting privileges...
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE juris_ia TO juris_ia_user;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Privileges granted
) else (
    echo [ERROR] Failed to grant privileges
)

echo.
echo ============================================================
echo  DATABASE SETUP COMPLETE
echo ============================================================
echo.
echo Next step: Initialize tables by running:
echo   python init_database.py
echo.
pause
