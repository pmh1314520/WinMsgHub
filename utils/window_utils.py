"""
WinMsgHub - 窗口工具函数
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import sys
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from utils.logger import get_logger

logger = get_logger(__name__)


def set_dark_titlebar(widget):
    """
    在Windows上设置窗口为暗色标题栏
    
    Args:
        widget: QWidget或其子类（QMainWindow、QDialog等）
    """
    if sys.platform != 'win32':
        return
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # 获取窗口句柄
        hwnd = int(widget.winId())
        
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 build 19041+)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        
        # 设置为暗色模式 (1 = 暗色, 0 = 亮色)
        value = ctypes.c_int(1)
        
        # 调用DwmSetWindowAttribute
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
        
        if result == 0:
            logger.debug(f"已设置窗口暗色标题栏: {widget.__class__.__name__}")
        else:
            logger.warning(f"设置暗色标题栏失败，错误码: {result}")
            
    except Exception as e:
        logger.warning(f"设置暗色标题栏失败: {e}")


def show_message_box(parent, title, text, icon=QMessageBox.Icon.Information, buttons=QMessageBox.StandardButton.Ok):
    """
    显示带暗色标题栏的消息框
    
    Args:
        parent: 父窗口
        title: 标题
        text: 内容
        icon: 图标类型
        buttons: 按钮
        
    Returns:
        用户点击的按钮
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    
    # 设置暗色标题栏
    QTimer.singleShot(0, lambda: set_dark_titlebar(msg_box))
    
    return msg_box.exec()
