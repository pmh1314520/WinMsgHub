@echo off
chcp 65001 >nul
echo ========================================
echo WinMsgHub 安装包制作工具
echo 作者：青云制作_彭明航
echo ========================================
echo.

REM 检查 Inno Setup 是否已安装
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist "%INNO_PATH%" (
    echo [错误] 未找到 Inno Setup！
    echo.
    echo 请先安装 Inno Setup 6：
    echo 下载地址：https://jrsoftware.org/isdl.php
    echo.
    echo 安装完成后，请重新运行此脚本。
    pause
    exit /b 1
)

echo [1/3] 检查打包文件...
if not exist "dist\WinMsgHub\WinMsgHub.exe" (
    echo [错误] 未找到打包后的程序文件！
    echo 请先运行 build.bat 打包程序。
    pause
    exit /b 1
)
echo ✓ 打包文件检查完成

echo.
echo [2/3] 编译安装脚本...
"%INNO_PATH%" "installer.iss"

if %ERRORLEVEL% NEQ 0 (
    echo [错误] 安装包编译失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 安装包生成完成！
echo.
echo 输出目录：installer_output\
echo 安装包文件：WinMsgHub_v1.0.0_Setup.exe
echo.
echo ========================================
echo 安装包制作完成！
echo ========================================
pause
