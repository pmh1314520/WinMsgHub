@echo off
chcp 65001 >nul
echo ========================================
echo WinMsgHub 完整构建工具
echo 作者：青云制作_彭明�?
echo ========================================
echo.
echo 此脚本将执行以下操作�?
echo 1. 使用 PyInstaller 打包程序
echo 2. 使用 Inno Setup 制作安装�?
echo.
pause

echo.
echo ========================================
echo 步骤 1/2：打包程�?
echo ========================================
call build.bat
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 程序打包失败�?
    pause
    exit /b 1
)

echo.
echo ========================================
echo 步骤 2/2：制作安装包
echo ========================================
call build_installer.bat
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 安装包制作失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成�?
echo ========================================
echo.
echo 程序文件：dist\WinMsgHub\WinMsgHub.exe
echo 安装包：installer_output\WinMsgHub_v1.1.4_Setup.exe
echo.
pause
