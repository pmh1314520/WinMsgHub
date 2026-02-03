"""
WinMsgHub - 图标标签组件
作者：青云制作_彭明航

提供带SVG图标的标签组件，替换Emoji
"""

from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui.svg_icons import SvgIcon


class IconLabel(QWidget):
    """带图标的标签组件"""
    
    def __init__(self, icon_name: str, text: str = "", icon_color: str = "#FFFFFF", 
                 icon_size: int = 16, parent=None):
        """初始化图标标签
        
        Args:
            icon_name: 图标名称
            text: 文本内容
            icon_color: 图标颜色
            icon_size: 图标大小
            parent: 父组件
        """
        super().__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.setLayout(layout)
        
        # 图标
        self.icon_label = QLabel()
        pixmap = SvgIcon.get_pixmap(icon_name, icon_color, icon_size)
        self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)
        
        # 文本
        if text:
            self.text_label = QLabel(text)
            layout.addWidget(self.text_label)
        else:
            self.text_label = None
        
        layout.addStretch()
    
    def setText(self, text: str):
        """设置文本"""
        if self.text_label:
            self.text_label.setText(text)
    
    def setIcon(self, icon_name: str, color: str = "#FFFFFF", size: int = 16):
        """更新图标"""
        pixmap = SvgIcon.get_pixmap(icon_name, color, size)
        self.icon_label.setPixmap(pixmap)
    
    def setStyleSheet(self, style: str):
        """设置样式"""
        if self.text_label:
            self.text_label.setStyleSheet(style)
        super().setStyleSheet(style)


def create_icon_button_text(icon_name: str, text: str, icon_color: str = "#FFFFFF") -> str:
    """创建按钮文本（使用空格分隔图标和文字）
    
    由于QPushButton不能直接嵌入QLabel，我们使用特殊字符作为占位符
    实际使用时需要配合setIcon()方法
    
    Args:
        icon_name: 图标名称
        text: 按钮文本
        icon_color: 图标颜色
        
    Returns:
        格式化的按钮文本
    """
    return f"  {text}"  # 前面留空间给图标
