"""
WinMsgHub - 主题管理器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import sys
from enum import Enum
from PyQt6.QtWidgets import QApplication
from utils.logger import get_logger


logger = get_logger(__name__)


class ThemeMode(Enum):
    """主题模式"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeManager:
    """
    主题管理器
    
    验证需求：
    - 5.1: 支持三种主题模式
    - 5.2: 默认使用跟随系统主题
    - 5.3: 检测Windows系统主题
    - 5.5: 快速切换主题
    - 5.6: 不使用紫色
    """
    
    def __init__(self, app: QApplication):
        """
        初始化主题管理器
        
        Args:
            app: QApplication实例
        """
        self.app = app
        self.current_mode = ThemeMode.SYSTEM
        
        logger.info("主题管理器已初始化")
    
    def set_theme(self, mode: ThemeMode):
        """
        设置主题
        
        Args:
            mode: 主题模式
        """
        self.current_mode = mode
        
        if mode == ThemeMode.SYSTEM:
            actual_theme = self._detect_system_theme()
        else:
            actual_theme = mode
        
        self._apply_theme(actual_theme)
        logger.info(f"主题已设置为: {mode.value}")
    
    def _detect_system_theme(self) -> ThemeMode:
        """检测Windows系统主题"""
        try:
            if sys.platform == 'win32':
                import winreg
                
                # 读取注册表判断系统是否使用暗色主题
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                
                # 0=暗色, 1=亮色
                return ThemeMode.LIGHT if value == 1 else ThemeMode.DARK
            else:
                # 非Windows系统默认使用亮色主题
                return ThemeMode.LIGHT
                
        except Exception as e:
            logger.warning(f"检测系统主题失败，使用默认亮色主题: {e}")
            return ThemeMode.LIGHT
    
    def _apply_theme(self, theme: ThemeMode):
        """应用主题样式"""
        if theme == ThemeMode.DARK:
            stylesheet = self._load_dark_stylesheet()
        else:
            stylesheet = self._load_light_stylesheet()
        
        self.app.setStyleSheet(stylesheet)
        logger.debug(f"已应用{theme.value}主题")
    
    def _load_light_stylesheet(self) -> str:
        """加载亮色主题样式表"""
        return """
        QWidget {
            background-color: #f5f5f5;
            color: #333333;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
        }
        
        QMainWindow {
            background-color: #ffffff;
        }
        
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            border-radius: 4px;
            color: #333333;
        }
        
        QPushButton:hover {
            background-color: #e8e8e8;
            border-color: #999999;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 3px;
            color: #333333;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #4CAF50;
        }
        
        QLabel {
            color: #333333;
        }
        
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QListWidget, QTreeWidget, QTableWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #f0f0f0;
            width: 10px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        """
    
    def _load_dark_stylesheet(self) -> str:
        """加载暗色主题样式表（不使用紫色，需求5.6）"""
        return """
        QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
        }
        
        QMainWindow {
            background-color: #1e1e1e;
        }
        
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            color: #e0e0e0;
        }
        
        QPushButton:hover {
            background-color: #4a4a4a;
            border-color: #777777;
        }
        
        QPushButton:pressed {
            background-color: #2d2d2d;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 3px;
            color: #e0e0e0;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #4CAF50;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QListWidget, QTreeWidget, QTableWidget {
            background-color: #2b2b2b;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #2b2b2b;
            width: 10px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #777777;
        }
        """
