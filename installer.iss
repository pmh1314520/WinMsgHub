; WinMsgHub 安装脚本
; 使用 Inno Setup 编译此脚本以创建安装程序
; 下载 Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "WinMsgHub"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "青云制作_彭明航"
#define MyAppURL "https://github.com/pmh1314520/WinMsgHub"
#define MyAppExeName "WinMsgHub.exe"

[Setup]
; 应用程序基本信息
AppId={{8F9A2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; 默认安装路径
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; 允许用户选择安装路径
DisableProgramGroupPage=yes

; 输出设置
OutputDir=installer_output
OutputBaseFilename=WinMsgHub_v{#MyAppVersion}_Setup
; 暂时不设置安装程序图标，使用默认图标
; 如果需要自定义图标，请确保路径正确
; SetupIconFile=resources\icons\WinMsgHub_ICON.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; 压缩设置
Compression=lzma2/max
SolidCompression=yes

; 界面设置
WizardStyle=modern

; 权限设置（不需要管理员权限）
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 架构设置
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; 许可协议
LicenseFile=LICENSE

; 卸载设置
; UninstallDisplayIcon 已在输出设置中定义

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动栏快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序文件
Source: "dist\WinMsgHub\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; _internal 文件夹中的所有文件
Source: "dist\WinMsgHub\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; 配置文件示例（可选）
Source: "config\*.json"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
; 资源文件
Source: "resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
; 许可协议
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
; README
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; 快速启动栏快捷方式
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; 安装完成后询问是否运行程序
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除用户数据（可选，默认保留）
; Type: filesandordirs; Name: "{userappdata}\WinMsgHub"

[Code]
var
  UninstallPath: String;

// 检查并卸载旧版本
function UninstallOldVersion(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // 从注册表读取卸载路径
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F9A2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}_is1',
    'UninstallString', UninstallPath) then
  begin
    // 找到了旧版本
    if MsgBox('检测到已安装 WinMsgHub。' #13#13 + 
              '需要先卸载旧版本才能继续安装。' #13#13 + 
              '是否立即卸载旧版本？', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 执行静默卸载
      if not Exec(RemoveQuotes(UninstallPath), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('卸载旧版本失败，请手动卸载后再安装。', mbError, MB_OK);
        Result := False;
      end
      else if ResultCode <> 0 then
      begin
        MsgBox('卸载旧版本失败（错误代码：' + IntToStr(ResultCode) + '），请手动卸载后再安装。', mbError, MB_OK);
        Result := False;
      end;
    end
    else
    begin
      // 用户选择不卸载
      Result := False;
    end;
  end;
  // 如果没有找到旧版本，返回 True 继续安装
end;

// 检查是否已安装旧版本
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // 检查程序是否正在运行
  if CheckForMutexes('WinMsgHub_SingleInstance') then
  begin
    MsgBox('检测到 WinMsgHub 正在运行。' #13#13 '请先关闭程序再继续安装。', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  // 检查并卸载旧版本
  Result := UninstallOldVersion();
end;

// 卸载前检查
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // 检查程序是否正在运行
  if CheckForMutexes('WinMsgHub_SingleInstance') then
  begin
    if MsgBox('检测到 WinMsgHub 正在运行。' #13#13 '请先关闭程序再继续卸载。', mbError, MB_OK) = IDOK then
    begin
      Result := False;
    end;
  end;
end;

// 卸载完成后询问是否删除用户数据
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataPath: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    UserDataPath := ExpandConstant('{userappdata}\WinMsgHub');
    
    if DirExists(UserDataPath) then
    begin
      if MsgBox('是否删除用户数据（配置文件、数据库、日志）？' #13#13 + 
                '路径：' + UserDataPath + #13#13 +
                '选择"是"将删除所有用户数据。' #13 +
                '选择"否"将保留用户数据，以便将来重新安装时使用。', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(UserDataPath, True, True, True);
      end;
    end;
  end;
end;
