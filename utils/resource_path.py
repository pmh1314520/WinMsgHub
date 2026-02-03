"""
WinMsgHub - 资源路径工具
作者：青云制作_彭明航

用于获取资源文件的正确路径，支持开发环境和PyInstaller打包后的环境
"""

import sys
import os
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径
    
    在开发环境中，返回相对于项目根目录的路径
    在PyInstaller打包后，返回临时解压目录中的路径
    
    Args:
        relative_path: 相对路径，如 'resources/icons/app.ico'
        
    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹，路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，使用项目根目录
        base_path = Path(__file__).parent.parent
    
    return str(Path(base_path) / relative_path)


def get_resource_url(relative_path: str) -> str:
    """
    获取资源文件的URL格式路径（用于QSS样式表）
    
    Args:
        relative_path: 相对路径，如 'resources/icons/checkbox_checked.svg'
        
    Returns:
        资源文件的URL格式路径
    """
    abs_path = get_resource_path(relative_path)
    # Windows路径需要转换为URL格式
    url_path = abs_path.replace('\\', '/')
    return url_path
