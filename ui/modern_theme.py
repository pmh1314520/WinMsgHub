"""
WinMsgHub (WinMsgHub) - 现代化主题系统
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QObject, pyqtProperty
from PyQt6.QtGui import QColor
from utils.logger import get_logger
from utils.resource_path import get_resource_url

logger = get_logger(__name__)


class ModernTheme:
    """现代化主题 - 蓝灰黑白风格"""
    
    # 主色调 - 蓝色系
    PRIMARY_BLUE = "#4A9EFF"  # 明亮的蓝色
    PRIMARY_BLUE_DARK = "#3A8EEF"  # 深蓝色
    PRIMARY_BLUE_LIGHT = "#6BB0FF"  # 浅蓝色
    ACCENT_BLUE = "#5AA5FF"  # 强调蓝色
    
    # 渐变色
    GRADIENT_START = "#4A9EFF"
    GRADIENT_END = "#5AA5FF"
    
    # 背景色 - 黑灰色系
    BG_PRIMARY = "#1A1D23"  # 主背景（深黑灰）
    BG_SECONDARY = "#21252B"  # 次要背景（黑灰）
    BG_CARD = "#282C34"  # 卡片背景（浅黑灰）
    
    # 文字颜色 - 白灰色系
    TEXT_PRIMARY = "#FFFFFF"  # 主文字（纯白）
    TEXT_SECONDARY = "#ABB2BF"  # 次要文字（浅灰）
    TEXT_HINT = "#5C6370"  # 提示文字（深灰）
    
    # 边框和阴影
    BORDER_COLOR = "#3E4451"  # 边框色（深灰）
    SHADOW_COLOR = "rgba(0, 0, 0, 0.4)"  # 阴影
    
    # 成功/警告/错误色
    SUCCESS_COLOR = "#98C379"  # 绿色
    WARNING_COLOR = "#E5C07B"  # 黄色
    ERROR_COLOR = "#E06C75"  # 红色
    
    @staticmethod
    def get_stylesheet() -> str:
        """获取现代化样式表"""
        return f"""
        /* ========== 全局样式 ========== */
        QWidget {{
            font-family: "Microsoft YaHei UI", "Segoe UI", "微软雅黑", Arial, sans-serif;
            font-size: 13px;
            color: {ModernTheme.TEXT_PRIMARY};
            background-color: {ModernTheme.BG_SECONDARY};
        }}
        
        /* ========== 主窗口 ========== */
        QMainWindow {{
            background-color: {ModernTheme.BG_SECONDARY};
        }}
        
        /* ========== 按钮样式 ========== */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernTheme.GRADIENT_START},
                stop:1 {ModernTheme.GRADIENT_END});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 500;
            font-size: 14px;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernTheme.PRIMARY_BLUE_DARK},
                stop:1 {ModernTheme.ACCENT_BLUE});
        }}
        
        QPushButton:pressed {{
            background: {ModernTheme.PRIMARY_BLUE_DARK};
            padding-top: 13px;
            padding-bottom: 11px;
        }}
        
        QPushButton:disabled {{
            background: {ModernTheme.TEXT_HINT};
            color: white;
        }}
        
        /* 次要按钮 */
        QPushButton[secondary="true"] {{
            background: white;
            color: {ModernTheme.PRIMARY_BLUE};
            border: 2px solid {ModernTheme.PRIMARY_BLUE};
        }}
        
        QPushButton[secondary="true"]:hover {{
            background: {ModernTheme.PRIMARY_BLUE_LIGHT};
            color: white;
            border-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
        }}
        
        /* ========== 输入框样式 ========== */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: white;
            border: 2px solid {ModernTheme.BORDER_COLOR};
            border-radius: 8px;
            padding: 10px 15px;
            color: {ModernTheme.TEXT_PRIMARY};
            selection-background-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {ModernTheme.PRIMARY_BLUE};
            background-color: white;
        }}
        
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
        }}
        
        /* ========== 标签样式 ========== */
        QLabel {{
            color: {ModernTheme.TEXT_PRIMARY};
            background: transparent;
        }}
        
        QLabel[heading="h1"] {{
            font-size: 28px;
            font-weight: 600;
            color: {ModernTheme.TEXT_PRIMARY};
        }}
        
        QLabel[heading="h2"] {{
            font-size: 22px;
            font-weight: 600;
            color: {ModernTheme.TEXT_PRIMARY};
        }}
        
        QLabel[heading="h3"] {{
            font-size: 18px;
            font-weight: 500;
            color: {ModernTheme.TEXT_PRIMARY};
        }}
        
        QLabel[secondary="true"] {{
            color: {ModernTheme.TEXT_SECONDARY};
        }}
        
        /* ========== 卡片样式 ========== */
        QFrame[card="true"] {{
            background-color: {ModernTheme.BG_CARD};
            border-radius: 12px;
            border: 1px solid {ModernTheme.BORDER_COLOR};
        }}
        
        /* ========== 选项卡样式 ========== */
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
        }}
        
        QTabBar::tab {{
            background: transparent;
            color: {ModernTheme.TEXT_SECONDARY};
            padding: 12px 24px;
            margin-right: 4px;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            color: {ModernTheme.PRIMARY_BLUE};
            border-bottom: 3px solid {ModernTheme.PRIMARY_BLUE};
        }}
        
        QTabBar::tab:hover {{
            color: {ModernTheme.PRIMARY_BLUE_LIGHT};
            background: {ModernTheme.BG_SECONDARY};
        }}
        
        /* ========== 列表和表格 ========== */
        QListWidget, QTreeWidget, QTableWidget {{
            background-color: white;
            border: 1px solid {ModernTheme.BORDER_COLOR};
            border-radius: 8px;
            padding: 8px;
            outline: none;
        }}
        
        QListWidget::item, QTreeWidget::item, QTableWidget::item {{
            padding: 12px;
            border-radius: 6px;
            margin: 2px 0;
        }}
        
        QListWidget::item:selected, QTreeWidget::item:selected,
        QTableWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernTheme.PRIMARY_BLUE_LIGHT},
                stop:1 {ModernTheme.ACCENT_BLUE});
            color: white;
        }}
        
        QListWidget::item:hover, QTreeWidget::item:hover,
        QTableWidget::item:hover {{
            background-color: {ModernTheme.BG_SECONDARY};
        }}
        
        /* ========== 滚动条样式 ========== */
        QScrollBar:vertical {{
            border: none;
            background: {ModernTheme.BG_SECONDARY};
            width: 12px;
            margin: 0;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {ModernTheme.PRIMARY_BLUE_LIGHT};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {ModernTheme.PRIMARY_BLUE};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: {ModernTheme.BG_SECONDARY};
            height: 12px;
            margin: 0;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {ModernTheme.PRIMARY_BLUE_LIGHT};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: {ModernTheme.PRIMARY_BLUE};
        }}
        
        /* ========== 复选框和单选框 ========== */
        QCheckBox, QRadioButton {{
            spacing: 8px;
            color: {ModernTheme.TEXT_PRIMARY};
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {ModernTheme.BORDER_COLOR};
            border-radius: 4px;
            background: white;
        }}
        
        QRadioButton::indicator {{
            border-radius: 10px;
        }}
        
        QCheckBox::indicator:checked {{
            background: {ModernTheme.PRIMARY_BLUE};
            border-color: {ModernTheme.PRIMARY_BLUE};
            image: url({get_resource_url('resources/icons/checkbox_checked.svg')});
        }}
        
        QRadioButton::indicator:checked {{
            background: {ModernTheme.PRIMARY_BLUE};
            border-color: {ModernTheme.PRIMARY_BLUE};
            image: url({get_resource_url('resources/icons/radio_checked.svg')});
        }}
        
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
        }}
        
        /* ========== 下拉框 ========== */
        QComboBox {{
            background-color: white;
            border: 2px solid {ModernTheme.BORDER_COLOR};
            border-radius: 8px;
            padding: 10px 15px;
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
        }}
        
        QComboBox:focus {{
            border-color: {ModernTheme.PRIMARY_BLUE};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {ModernTheme.TEXT_SECONDARY};
            margin-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: white;
            border: 2px solid {ModernTheme.PRIMARY_BLUE};
            border-radius: 8px;
            selection-background-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
            padding: 5px;
        }}
        
        /* ========== 分组框 ========== */
        QGroupBox {{
            background-color: white;
            border: 2px solid {ModernTheme.BORDER_COLOR};
            border-radius: 12px;
            margin-top: 20px;
            padding-top: 15px;
            font-weight: 500;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            top: 8px;
            padding: 0 10px;
            background-color: white;
            color: {ModernTheme.PRIMARY_BLUE};
        }}
        
        /* ========== 进度条 ========== */
        QProgressBar {{
            border: none;
            border-radius: 8px;
            background-color: {ModernTheme.BG_SECONDARY};
            height: 16px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernTheme.GRADIENT_START},
                stop:1 {ModernTheme.GRADIENT_END});
            border-radius: 8px;
        }}
        
        /* ========== 滑块 ========== */
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: {ModernTheme.BG_SECONDARY};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {ModernTheme.PRIMARY_BLUE};
            border: none;
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {ModernTheme.PRIMARY_BLUE_DARK};
        }}
        
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ModernTheme.GRADIENT_START},
                stop:1 {ModernTheme.GRADIENT_END});
            border-radius: 3px;
        }}
        
        /* ========== 工具提示 ========== */
        QToolTip {{
            background-color: {ModernTheme.TEXT_PRIMARY};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        }}
        
        /* ========== 菜单 ========== */
        QMenu {{
            background-color: white;
            border: 1px solid {ModernTheme.BORDER_COLOR};
            border-radius: 8px;
            padding: 8px;
        }}
        
        QMenu::item {{
            padding: 10px 30px 10px 20px;
            border-radius: 6px;
        }}
        
        QMenu::item:selected {{
            background-color: {ModernTheme.PRIMARY_BLUE_LIGHT};
            color: white;
        }}
        
        /* ========== 状态栏 ========== */
        QStatusBar {{
            background-color: white;
            color: {ModernTheme.TEXT_SECONDARY};
            border-top: 1px solid {ModernTheme.BORDER_COLOR};
        }}
        """


class AnimationHelper:
    """动画辅助类"""
    
    @staticmethod
    def fade_in(widget, duration=300):
        """淡入动画"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        return animation
    
    @staticmethod
    def fade_out(widget, duration=300):
        """淡出动画"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        return animation
    
    @staticmethod
    def slide_in(widget, direction="left", duration=400):
        """滑入动画"""
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation
