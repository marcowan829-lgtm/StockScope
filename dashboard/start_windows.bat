@echo off
chcp 65001 >nul
cd /d "%~dp0"
title StockScope - 美股分析仪表盘

echo ======================================
echo StockScope 美股分析仪表盘
echo 当前文件夹：%CD%
echo ======================================
echo.

REM Prefer the Windows Python launcher; fall back to python.exe.
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    set "PY=python"
)

echo [1/3] 检查 Python...
%PY% --version
if errorlevel 1 goto python_failed

echo.
echo [2/3] 安装/检查依赖（首次运行需要联网，可能需要几分钟）...
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto install_failed

echo.
echo [3/3] 启动网页仪表盘...
echo 如果看到 Local URL，请在浏览器打开该地址。关闭本窗口会停止仪表盘。
echo.
%PY% -m streamlit run app.py
set "APP_EXIT=%errorlevel%"
echo.
echo Streamlit 已退出，退出代码：%APP_EXIT%
echo 如有报错，请拍下上方信息，或复制发送给 ChatGPT。
pause
exit /b %APP_EXIT%

:python_failed
echo.
echo 错误：无法通过 %PY% 调用 Python。请确认 Python 已安装并加入 PATH。
echo 你可以在 cmd 中测试：python --version
pause
exit /b 1

:install_failed
echo.
echo 错误：依赖安装失败。上方应有具体错误信息，请拍照或复制后发送。
echo 常见原因：网络连接、pip 下载失败，或当前 Python 版本与某个依赖不兼容。
pause
exit /b 1
