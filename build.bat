@echo off
chcp 65001 >nul
echo ============================================
echo WinMsgHub 打包脚本
echo 作者：青云制作_彭明航
echo ============================================
echo.

REM 检查是否安装了pyinstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [错误] 未安装 PyInstaller，正在安装...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败！
        pause
        exit /b 1
    )
    echo [成功] PyInstaller 安装完成
    echo.
)

REM 清理旧的打包文件
echo [1/4] 清理旧的打包文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [完成] 清理完成
echo.

REM 开始打包
echo [2/4] 开始打包 WinMsgHub...
echo 这可能需要几分钟时间，请耐心等待...
echo.
pyinstaller WinMsgHub.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo [3/4] 打包完成，正在验证...

REM 检查生成的exe文件
if not exist "dist\WinMsgHub\WinMsgHub.exe" (
    echo [错误] 未找到生成的 WinMsgHub.exe 文件！
    pause
    exit /b 1
)

echo [完成] 验证通过
echo.

REM 显示文件信息
echo [4/4] 打包信息：
echo ----------------------------------------
for %%F in ("dist\WinMsgHub\WinMsgHub.exe") do (
    echo 文件名称: %%~nxF
    echo 文件大小: %%~zF 字节
    echo 文件路径: %%~fF
)
echo ----------------------------------------
echo.

echo ============================================
echo 打包成功！
echo 可执行文件位置: dist\WinMsgHub\WinMsgHub.exe
echo ============================================
echo.
echo 提示：
echo 1. 可以直接运行 dist\WinMsgHub\WinMsgHub.exe
echo 2. 整个 dist\WinMsgHub 文件夹可以打包分发
echo 3. 首次运行会在 %%APPDATA%%\WinMsgHub 创建配置
echo.

pause
