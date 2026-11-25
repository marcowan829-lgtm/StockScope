@echo off
chcp 65001 >nul
cd /d "%~dp0"
title StockScope - Intraday diagnostics
where py >nul 2>nul
if %errorlevel%==0 (
  py test_intraday.py
) else (
  python test_intraday.py
)
echo.
pause
