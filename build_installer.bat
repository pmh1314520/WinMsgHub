@echo off
chcp 65001 >nul
echo ========================================
echo WinMsgHub 安装包制作工�?
echo 作者：青云制作_彭明�?
echo ========================================
echo.

REM 检�?Inno Setup 是否已安�?
set "INNO_PATH=D:\Inno Setup 6\ISCC.exe"

if not exist "%INNO_PATH%" (
    REM 尝试默认路径
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_PATH%" (
    echo [错误] 未找�?Inno Setup�?
    echo.
    echo ┌─────────────────────────────────────�?
    echo �? 请先安装 Inno Setup 6              �?
    echo └─────────────────────────────────────�?
    echo.
    echo 📥 下载地址�?
    echo    https://jrsoftware.org/isdl.php
    echo.
    echo 📖 安装教程�?
    echo    请查�?INSTALL_INNO_SETUP.md 文件
    echo.
    echo 💡 提示�?
    echo    1. 下载并安�?Inno Setup 6
    echo    2. 使用默认安装路径
    echo    3. 安装完成后重新运行此脚本
    echo.
    echo 按任意键打开下载页面...
    pause >nul
    start https://jrsoftware.org/isdl.php
    exit /b 1
)

echo [1/3] 检查打包文�?..
if not exist "dist\WinMsgHub\WinMsgHub.exe" (
    echo [错误] 未找到打包后的程序文件！
    echo.
    echo 请先运行以下命令打包程序�?
    echo    build.bat
    echo.
    echo 或者运行一键构建：
    echo    build_all.bat
    echo.
    pause
    exit /b 1
)
echo �?打包文件检查完�?

echo.
echo [2/3] 编译安装脚本...
echo 正在使用 Inno Setup 编译...
"%INNO_PATH%" "installer.iss"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 安装包编译失败！
    echo.
    echo 可能的原因：
    echo 1. installer.iss 脚本有错�?
    echo 2. 缺少必要的文件（LICENSE、图标等�?
    echo 3. 路径配置不正�?
    echo.
    echo 请检查上方的错误信息�?
    pause
    exit /b 1
)

echo.
echo [3/3] 安装包生成完成！
echo.
echo ┌─────────────────────────────────────�?
echo �? �?安装包制作成功！                �?
echo └─────────────────────────────────────�?
echo.
echo 📁 输出目录：installer_output\
echo 📦 安装包文件：WinMsgHub_v1.1.3_Setup.exe
echo 📏 文件大小�?
dir /b installer_output\*.exe 2>nul | findstr /i "setup.exe" >nul && for %%F in (installer_output\*Setup.exe) do echo    %%~zF 字节
echo.
echo 💡 下一步：
echo    1. 测试安装�?
echo    2. 上传�?GitHub Releases
echo    3. 分享给用�?
echo.
echo ========================================
pause

