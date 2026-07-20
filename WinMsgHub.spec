# -*- mode: python ; coding: utf-8 -*-
"""
WinMsgHub PyInstaller 打包配置
作者：青云制作_彭明航
"""

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 需要包含的数据文件
datas = [
    ('resources', 'resources'),  # 图标、音效等资源文件
    ('config/default_config.json', 'config'),  # 默认配置
    ('config/example_mqtt_config.json', 'config'),  # MQTT示例配置
    ('config/example_multi_sources.json', 'config'),  # 多消息源示例配置
]

# 使用 collect_all 自动收集 amqtt 的所有模块、数据和二进制文件
amqtt_datas, amqtt_binaries, amqtt_hiddenimports = collect_all('amqtt')
datas += amqtt_datas

# 需要包含的隐藏导入（PyInstaller可能检测不到的模块）
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'pygame',  # 弹窗音效播放（sound_manager中延迟导入）
    'paho.mqtt.client',
    # amqtt的依赖库
    'passlib',
    'passlib.context',
    'passlib.hash',
    'passlib.handlers',
    'passlib.handlers.bcrypt',
    'passlib.handlers.pbkdf2',
    'passlib.handlers.sha2_crypt',
    'transitions',
    'transitions.core',
    'transitions.extensions',
    'docopt',
    'yaml',
    'dacite',
    'typer',
    # websockets库（amqtt的WebSocket支持需要）
    'websockets',
    'websockets.client',
    'websockets.server',
    'websockets.protocol',
    'websockets.extensions',
    'websockets.legacy',
    'websockets.legacy.client',
    'websockets.legacy.server',
    # 其他依赖
    'cryptography',
    'feedparser',
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    'websocket',
    'pyperclip',
    'psutil',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
] + amqtt_hiddenimports  # 添加 amqtt 自动收集的隐藏导入

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'hypothesis',
        'coverage',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        # 本机可能同时安装了PySide6，项目只用PyQt6，
        # 必须排除以免两套Qt绑定被同时打包（体积翻倍且DLL冲突）
        'PySide6',
        'shiboken6',
        'PyQt5',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WinMsgHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/WinMsgHub_ICON.ico',  # 应用图标
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WinMsgHub',
)
