"""
WinMsgHub - 按钮样式工具
作者：青云制作_彭明航
提供统一的按钮样式和交互效果
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt


class ButtonStyles:
    """按钮样式工具类"""
    
    # 颜色方案
    COLORS = {
        "blue": {
            "normal": "#2B7FDB",
            "hover": "#3D8FED",
            "pressed": "#1A6FC9"
        },
        "green": {
            "normal": "#5FA04E",
            "hover": "#71B260",
            "pressed": "#4D8E3C"
        },
        "red": {
            "normal": "#C5444F",
            "hover": "#D75661",
            "pressed": "#B3323D"
        },
        "yellow": {
            "normal": "#C99A3E",
            "hover": "#DBAC50",
            "pressed": "#B7882C"
        },
        "purple": {
            "normal": "#9B59B6",
            "hover": "#AD6FC7",
            "pressed": "#8944A4"
        }
    }
    
    @staticmethod
    def get_button_style(color_name: str, size: str = "medium") -> str:
        """
        获取按钮样式
        
        Args:
            color_name: 颜色名称 (blue, green, red, yellow, purple)
            size: 尺寸 (small, medium, large)
        
        Returns:
            CSS样式字符串
        """
        colors = ButtonStyles.COLORS.get(color_name, ButtonStyles.COLORS["blue"])
        
        # 根据尺寸设置padding
        padding_map = {
            "small": "6px 12px",
            "medium": "8px 16px",
            "large": "10px 20px"
        }
        padding = padding_map.get(size, padding_map["medium"])
        
        return f"""
            QPushButton {{
                background-color: {colors['normal']};
                color: white;
                font-weight: 500;
                padding: {padding};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {colors['hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['pressed']};
            }}
            QPushButton:disabled {{
                background-color: #4A4F5A;
                color: #7F8C8D;
            }}
        """
    
    @staticmethod
    def create_button(text: str, color: str = "blue", size: str = "medium") -> QPushButton:
        """
        创建带样式的按钮
        
        Args:
            text: 按钮文本
            color: 颜色名称
            size: 尺寸
        
        Returns:
            配置好的QPushButton
        """
        btn = QPushButton(text)
        btn.setStyleSheet(ButtonStyles.get_button_style(color, size))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn
    
    @staticmethod
    def apply_style(button: QPushButton, color: str = "blue", size: str = "medium"):
        """
        为现有按钮应用样式
        
        Args:
            button: QPushButton实例
            color: 颜色名称
            size: 尺寸
        """
        button.setStyleSheet(ButtonStyles.get_button_style(color, size))
        button.setCursor(Qt.CursorShape.PointingHandCursor)


# 便捷函数
def create_blue_button(text: str, size: str = "medium") -> QPushButton:
    """创建蓝色按钮（主要操作）"""
    return ButtonStyles.create_button(text, "blue", size)


def create_green_button(text: str, size: str = "medium") -> QPushButton:
    """创建绿色按钮（成功、保存、导出）"""
    return ButtonStyles.create_button(text, "green", size)


def create_red_button(text: str, size: str = "medium") -> QPushButton:
    """创建红色按钮（危险、删除）"""
    return ButtonStyles.create_button(text, "red", size)


def create_yellow_button(text: str, size: str = "medium") -> QPushButton:
    """创建黄色按钮（警告、切换）"""
    return ButtonStyles.create_button(text, "yellow", size)


def create_purple_button(text: str, size: str = "medium") -> QPushButton:
    """创建紫色按钮（特殊操作）"""
    return ButtonStyles.create_button(text, "purple", size)
