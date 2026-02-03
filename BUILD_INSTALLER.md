# WinMsgHub 安装包制作指南

## 📦 准备工作

### 1. 安装 Inno Setup

1. 访问官网下载：https://jrsoftware.org/isdl.php
2. 下载 **Inno Setup 6** (推荐下载 Unicode 版本)
3. 运行安装程序，按默认选项安装即可
4. 默认安装路径：`C:\Program Files (x86)\Inno Setup 6\`

### 2. 确保已打包程序

确保 `dist\WinMsgHub\` 目录下有以下文件：
- `WinMsgHub.exe` - 主程序
- `_internal\` - 依赖文件夹

如果没有，请先运行 `build.bat` 打包程序。

## 🚀 制作安装包

### 方法1：一键构建（推荐）

运行 `build_all.bat`，会自动完成：
1. 打包程序（PyInstaller）
2. 制作安装包（Inno Setup）

### 方法2：单独制作安装包

如果已经打包好程序，只需运行 `build_installer.bat`

### 方法3：手动编译

1. 打开 Inno Setup
2. 点击 `File` -> `Open`
3. 选择 `installer.iss` 文件
4. 点击 `Build` -> `Compile` 或按 `Ctrl+F9`

## 📁 输出文件

安装包会生成在 `installer_output\` 目录：
- `WinMsgHub_v1.0.0_Setup.exe` - 安装程序

## ✨ 安装包特性

### 用户体验
- ✅ 现代化安装界面
- ✅ 中文界面
- ✅ 可选择安装路径
- ✅ 可选创建桌面快捷方式
- ✅ 可选创建快速启动栏快捷方式
- ✅ 安装完成后可选立即运行

### 安全特性
- ✅ 安装前检测程序是否正在运行
- ✅ 卸载前检测程序是否正在运行
- ✅ 不需要管理员权限（安装到用户目录）
- ✅ 支持64位系统

### 卸载功能
- ✅ 完整卸载程序文件
- ✅ 卸载时询问是否删除用户数据
- ✅ 保留用户配置选项（可选）

## 🔧 自定义安装脚本

编辑 `installer.iss` 文件可以修改：

### 基本信息
```pascal
#define MyAppName "WinMsgHub"
#define MyAppVersion "1.0.0"  // 修改版本号
#define MyAppPublisher "青云制作_彭明航"
```

### 安装路径
```pascal
DefaultDirName={autopf}\{#MyAppName}  // 默认：C:\Program Files\WinMsgHub
```

### 包含的文件
在 `[Files]` 部分添加或删除文件

### 快捷方式
在 `[Icons]` 部分自定义快捷方式

## 📝 注意事项

1. **版本号同步**：修改版本号时，需要同时修改：
   - `installer.iss` 中的 `MyAppVersion`
   - `utils/update_checker.py` 中的 `CURRENT_VERSION`

2. **图标文件**：确保 `resources/icons/WinMsgHub_ICON.ico` 存在

3. **许可协议**：确保 `LICENSE` 文件存在

4. **用户数据**：用户数据存储在 `%APPDATA%\WinMsgHub\`，卸载时可选择保留

## 🎯 发布流程

1. 更新版本号（3个地方）
2. 运行 `build_all.bat` 生成安装包
3. 测试安装包
4. 上传到 GitHub Releases
5. 用户下载安装

## 🐛 常见问题

### Q: 提示"未找到 Inno Setup"
**A:** 请确保 Inno Setup 安装在默认路径，或修改 `build_installer.bat` 中的 `INNO_PATH` 变量

### Q: 编译失败
**A:** 检查以下内容：
- `dist\WinMsgHub\` 目录是否存在
- `LICENSE` 文件是否存在
- `resources\icons\WinMsgHub_ICON.ico` 是否存在

### Q: 安装包太大
**A:** 可以在 `installer.iss` 中调整压缩设置：
```pascal
Compression=lzma2/max  // 最大压缩
SolidCompression=yes   // 固实压缩
```

### Q: 需要管理员权限
**A:** 默认不需要管理员权限。如果需要，修改：
```pascal
PrivilegesRequired=admin
```

## 📚 更多资源

- Inno Setup 官方文档：https://jrsoftware.org/ishelp/
- Inno Setup 中文教程：https://www.cnblogs.com/
- 示例脚本：`C:\Program Files (x86)\Inno Setup 6\Examples\`
