"""
WinMsgHub (WinMsgHub) - 通知弹窗组件
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QScreen, QFont, QColor
from data.models import Message
from utils.logger import get_logger
import logging


logger = logging.getLogger('WinMsgHub')


# 全局弹窗管理器
class PopupStackManager:
    """管理所有活动的弹窗，实现堆叠效果"""
    _instance = None
    _popups: List['NotificationPopup'] = []
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @staticmethod
    def _get_popup_size(popup: 'NotificationPopup') -> tuple:
        """获取弹窗的实际尺寸
        
        Returns:
            (width, height) 元组
        """
        # 始终使用配置尺寸，避免阴影效果导致的尺寸差异
        return (popup.style.width, popup.style.height)
    
    def add_popup(self, popup: 'NotificationPopup'):
        """添加新弹窗到管理器"""
        # 获取最大弹窗数量限制
        max_popups = popup.style.max_popups
        
        # 检查是否超过最大弹窗数量限制
        # 如果当前数量 >= 最大限制，需要先关闭旧弹窗腾出空间
        while len(self._popups) >= max_popups:
            # 关闭最旧的弹窗（列表第一个）
            oldest_popup = self._popups[0]
            logger.info(f"🚫 PopupStackManager: 超过最大弹窗数量({max_popups})，关闭最旧的弹窗: {oldest_popup.message.id}")
            
            # 先从两个列表中移除
            self._popups.remove(oldest_popup)
            
            # 如果弹窗有关联的 PopupManager，也从那里移除
            # 注意：这里需要手动触发 PopupManager 的移除逻辑
            # 因为 close() 是异步的，回调可能还没执行
            if hasattr(oldest_popup, '_popup_manager_ref'):
                popup_manager = oldest_popup._popup_manager_ref
                if popup_manager and oldest_popup in popup_manager.active_popups:
                    popup_manager.active_popups.remove(oldest_popup)
                    logger.debug(f"PopupStackManager: 已从 PopupManager 移除: {oldest_popup.message.id}")
            
            # 最后关闭弹窗
            oldest_popup.close()
        
        # 添加新弹窗
        self._popups.append(popup)
        logger.debug(f"➕ PopupStackManager: 弹窗已添加: {popup.message.id}, 当前数量: {len(self._popups)}/{max_popups}")
        
        # 当有多个弹窗时，需要重新排列旧弹窗
        # 因为新弹窗总是占据固定位置（顶部或底部），旧弹窗需要移动
        if len(self._popups) > 1:
            # 延迟一点执行，让新弹窗先完成动画设置
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda pos=popup.style.position: self._rearrange_popups(affected_position=pos))
    
    def remove_popup(self, popup: 'NotificationPopup'):
        """移除弹窗并重新排列"""
        if popup in self._popups:
            # 记录被移除弹窗的位置
            removed_position = popup.style.position
            
            self._popups.remove(popup)
            
            # 只重新排列受影响的弹窗（同一位置的弹窗）
            self._rearrange_popups(affected_position=removed_position)
    
    def get_target_position(self, popup: 'NotificationPopup') -> QPoint:
        """获取弹窗应该显示的目标位置（考虑堆叠）"""
        screen = QScreen.availableGeometry(popup.screen())
        margin = 20
        spacing = 10
        # availableGeometry已排除任务栏区域，无需再额外预留，
        # 否则底部弹窗会悬空在任务栏上方50px处
        taskbar_height = 0
        
        logger.debug(f"get_target_position: screen=({screen.x()}, {screen.y()}, {screen.width()}x{screen.height()}), position={popup.style.position.value}")
        
        # 根据弹窗位置自动判断堆叠方向
        # 上半部分位置：新消息在顶部（top）
        # 下半部分位置：新消息在底部（bottom）
        position = popup.style.position
        
        # 使用配置的尺寸而不是实际尺寸，避免阴影导致的尺寸差异
        popup_width = popup.style.width
        popup_height = popup.style.height
        
        logger.debug(f"get_target_position: popup_size=({popup_width}x{popup_height}) [使用配置尺寸]")
        
        # 找到相同位置的其他弹窗（排除自己）
        same_position_popups = [p for p in self._popups if p.style.position == popup.style.position and p != popup]
        
        logger.debug(f"get_target_position: 相同位置的其他弹窗数量={len(same_position_popups)}")
        
        # 计算基础位置（使用屏幕的绝对坐标）
        if position == PopupPosition.TOP_RIGHT:
            target_x = screen.x() + screen.width() - popup_width - margin
            # 上半部分：新消息在顶部（最上面的位置）
            # 旧消息会被 _rearrange_popups 移动到下面
            target_y = screen.y() + margin
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.TOP_LEFT:
            target_x = screen.x() + margin
            # 新消息在顶部
            target_y = screen.y() + margin
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.TOP_CENTER:
            target_x = screen.x() + (screen.width() - popup_width) // 2
            # 新消息在顶部
            target_y = screen.y() + margin
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.BOTTOM_RIGHT:
            target_x = screen.x() + screen.width() - popup_width - margin
            # 下半部分：新消息在底部（最下面的位置）
            # 旧消息会被 _rearrange_popups 移动到上面
            target_y = screen.y() + screen.height() - margin - taskbar_height - popup_height
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.BOTTOM_LEFT:
            target_x = screen.x() + margin
            # 新消息在底部
            target_y = screen.y() + screen.height() - margin - taskbar_height - popup_height
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.BOTTOM_CENTER:
            target_x = screen.x() + (screen.width() - popup_width) // 2
            # 新消息在底部
            target_y = screen.y() + screen.height() - margin - taskbar_height - popup_height
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.CENTER:
            target_x = screen.x() + (screen.width() - popup_width) // 2
            target_y = screen.y() + (screen.height() - popup_height) // 2
            # 中心位置不堆叠
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.CENTER_LEFT:
            target_x = screen.x() + margin
            # 中间位置：新消息在顶部
            if same_position_popups:
                # 计算总高度并居中
                total_height = sum(p.style.height for p in same_position_popups) + popup_height
                total_spacing = spacing * len(same_position_popups)
                start_y = screen.y() + (screen.height() - total_height - total_spacing) // 2
                # 新弹窗在最下面
                offset = sum(p.style.height for p in same_position_popups) + spacing * len(same_position_popups)
                target_y = start_y + offset
            else:
                target_y = screen.y() + (screen.height() - popup_height) // 2
            return QPoint(target_x, target_y)
        
        elif position == PopupPosition.CENTER_RIGHT:
            target_x = screen.x() + screen.width() - popup_width - margin
            if same_position_popups:
                total_height = sum(p.style.height for p in same_position_popups) + popup_height
                total_spacing = spacing * len(same_position_popups)
                start_y = screen.y() + (screen.height() - total_height - total_spacing) // 2
                offset = sum(p.style.height for p in same_position_popups) + spacing * len(same_position_popups)
                target_y = start_y + offset
            else:
                target_y = screen.y() + (screen.height() - popup_height) // 2
            return QPoint(target_x, target_y)
        
        # 默认右上角
        return QPoint(screen.x() + screen.width() - popup_width - margin, screen.y() + margin)
    
    def _rearrange_popups(self, affected_position=None):
        """重新排列弹窗位置 - 只移动受影响的弹窗
        
        Args:
            affected_position: 受影响的位置，如果为None则重新排列所有弹窗
        """
        if not self._popups:
            return
        
        # 获取屏幕信息
        screen = QScreen.availableGeometry(self._popups[0].screen())
        margin = 20
        spacing = 10
        # availableGeometry已排除任务栏区域，见get_target_position
        taskbar_height = 0
        
        # 按位置分组
        position_groups = {}
        for popup in self._popups:
            pos = popup.style.position
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(popup)
        
        # 如果指定了affected_position，只处理该位置的弹窗
        positions_to_process = [affected_position] if affected_position else position_groups.keys()
        
        # 为每个位置组排列弹窗
        for position in positions_to_process:
            if position not in position_groups:
                continue
                
            popups = position_groups[position]
            
            # 根据位置自动判断堆叠方向
            # 上半部分位置：新消息在顶部
            is_top_half = position in [
                PopupPosition.TOP_LEFT,
                PopupPosition.TOP_CENTER,
                PopupPosition.TOP_RIGHT
            ]
            
            # 下半部分位置：新消息在底部
            is_bottom_half = position in [
                PopupPosition.BOTTOM_LEFT,
                PopupPosition.BOTTOM_CENTER,
                PopupPosition.BOTTOM_RIGHT
            ]
            
            # 中间位置：新消息在顶部
            is_center = position in [
                PopupPosition.CENTER_LEFT,
                PopupPosition.CENTER_RIGHT
            ]
            
            if position == PopupPosition.TOP_RIGHT:
                current_y = screen.y() + margin
                # 上半部分：新消息在顶部，从最新到最旧排列
                # 最新的弹窗（列表最后一个）应该在最上面
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + screen.width() - popup_width - margin
                    # 跳过最新的弹窗（索引0），因为它正在播放动画
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y += popup_height + spacing
            
            elif position == PopupPosition.TOP_LEFT:
                current_y = screen.y() + margin
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + margin
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y += popup_height + spacing
            
            elif position == PopupPosition.TOP_CENTER:
                current_y = screen.y() + margin
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + (screen.width() - popup_width) // 2
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y += popup_height + spacing
            
            elif position == PopupPosition.BOTTOM_RIGHT:
                current_y = screen.y() + screen.height() - margin - taskbar_height
                # 下半部分：新消息在底部，从最新到最旧（从下往上）排列
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    current_y -= popup_height
                    target_x = screen.x() + screen.width() - popup_width - margin
                    # 跳过最新的弹窗（索引0），因为它正在播放动画
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y -= spacing
            
            elif position == PopupPosition.BOTTOM_LEFT:
                current_y = screen.y() + screen.height() - margin - taskbar_height
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    current_y -= popup_height
                    target_x = screen.x() + margin
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y -= spacing
            
            elif position == PopupPosition.BOTTOM_CENTER:
                current_y = screen.y() + screen.height() - margin - taskbar_height
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    current_y -= popup_height
                    target_x = screen.x() + (screen.width() - popup_width) // 2
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y -= spacing
            
            elif position == PopupPosition.CENTER:
                # 中心位置不堆叠，每个都在中心
                for popup in popups:
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + (screen.width() - popup_width) // 2
                    target_y = screen.y() + (screen.height() - popup_height) // 2
                    popup.move_to(QPoint(target_x, target_y))
            
            elif position == PopupPosition.CENTER_LEFT:
                # 计算总高度时使用实际尺寸
                total_height = sum(self._get_popup_size(p)[1] for p in popups) + spacing * (len(popups) - 1)
                current_y = screen.y() + (screen.height() - total_height) // 2
                # 中间位置：新消息在顶部
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + margin
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y += popup_height + spacing
            
            elif position == PopupPosition.CENTER_RIGHT:
                # 计算总高度时使用实际尺寸
                total_height = sum(self._get_popup_size(p)[1] for p in popups) + spacing * (len(popups) - 1)
                current_y = screen.y() + (screen.height() - total_height) // 2
                popup_order = list(reversed(popups))
                for i, popup in enumerate(popup_order):
                    popup_width, popup_height = self._get_popup_size(popup)
                    target_x = screen.x() + screen.width() - popup_width - margin
                    if i > 0:
                        popup.move_to(QPoint(target_x, current_y))
                    current_y += popup_height + spacing


class PopupPosition(Enum):
    """弹窗位置枚举"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class PopupStyle:
    """弹窗样式配置"""
    width: int = 400
    height: int = 120
    opacity: float = 0.98
    background_color: str = "#2A3139"
    background_image: Optional[str] = None
    border_radius: int = 12
    animation_type: str = "slide"  # slide, fade, scale
    animation_duration: int = 400
    display_duration: int = 5000
    position: PopupPosition = PopupPosition.TOP_RIGHT
    sound_file: Optional[str] = None
    sound_volume: int = 50  # 音量 (0-100)
    auto_copy: bool = False
    copy_mode: str = "on_click"  # on_click 或 auto
    copy_rules: list = None  # 复制规则列表
    max_popups: int = 5  # 最多同时显示的弹窗数量
    
    # 动画配置
    animation_config: dict = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.animation_config is None:
            self.animation_config = {
                "slide_direction": "right_to_left",
                "fade_start_opacity": 0.0,
                "scale_start_size": 0.5,
                "scale_center": "center"
            }
        if self.copy_rules is None:
            self.copy_rules = []
    
    # 字体配置
    title_font_family: str = "Microsoft YaHei UI"
    title_font_size: int = 13
    title_font_bold: bool = True
    title_color: str = "#FFFFFF"
    
    content_font_family: str = "Microsoft YaHei UI"
    content_font_size: int = 10
    content_font_bold: bool = False
    content_color: str = "#B8BFC6"
    
    source_font_family: str = "Microsoft YaHei UI"
    source_font_size: int = 9
    source_font_bold: bool = False
    source_color: str = "#4A9EFF"
    source_bg_color: str = "rgba(74, 158, 255, 0.15)"
    
    time_font_family: str = "Microsoft YaHei UI"
    time_font_size: int = 9
    time_font_bold: bool = False
    time_color: str = "#6C757D"
    
    # 自定义字体文件路径
    custom_font_file: Optional[str] = None
    
    # 文本溢出处理
    title_text_overflow: str = "ellipsis"  # ellipsis, wrap, none
    content_text_overflow: str = "wrap"  # ellipsis, wrap, none
    
    # 最大行数（换行模式下）
    title_max_lines: int = 2  # 标题最大行数
    content_max_lines: int = 5  # 内容最大行数
    
    # 文本对齐方式
    title_align: str = "left"  # left, center, right
    content_align: str = "left"  # left, center, right
    time_align: str = "left"  # left, center, right
    
    # 时间格式
    time_format: str = "%H:%M:%S"  # 时间显示格式


class NotificationPopup(QWidget):
    """
    通知弹窗窗口 - 现代化设计
    
    验证需求：
    - 3.1: 显示弹窗
    - 3.2: 保持置顶
    - 3.3: 指定位置显示
    - 3.5: 播放音效
    - 3.6: 自动复制
    - 3.7: 点击关闭
    """
    
    closed = pyqtSignal()  # 关闭信号
    
    def __init__(self, message: Message, style: PopupStyle):
        super().__init__()
        self.message = message
        self.style = style
        self.manager = PopupStackManager.get_instance()
        self._setup_ui()
        # 不在 __init__ 中调用 _setup_animation()，而是在 show() 中调用
        # 这样可以确保窗口尺寸已经正确设置
        
        logger.debug(f"创建弹窗: {message.id}")
    
    def _setup_ui(self):
        """设置UI - 现代化深色主题"""
        # 加载自定义字体（如果有）
        custom_font_family = None
        if self.style.custom_font_file:
            custom_font_family = self._load_custom_font(self.style.custom_font_file)
            if custom_font_family:
                # 应用自定义字体到所有文本
                self.style.title_font_family = custom_font_family
                self.style.content_font_family = custom_font_family
                self.style.source_font_family = custom_font_family
                logger.info(f"已应用自定义字体: {custom_font_family}")
        
        # 设置窗口标志：无边框、置顶、工具窗口（需求3.2）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint  # 绕过窗口管理器，避免额外的框架
        )
        
        # 设置窗口属性
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置窗口透明度
        self.setWindowOpacity(self.style.opacity)
        
        # 主容器
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(main_container)
        
        # 内部布局
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(20, 15, 20, 15)
        inner_layout.setSpacing(8)
        main_container.setLayout(inner_layout)
        
        # 顶部：标题和关闭按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # 消息源标签（小标签）
        source_label = QLabel(self.message.source)
        source_font = QFont(
            self.style.source_font_family,
            self.style.source_font_size,
            QFont.Weight.Bold if self.style.source_font_bold else QFont.Weight.Normal
        )
        source_label.setFont(source_font)
        source_label.setStyleSheet(f"""
            QLabel {{
                color: {self.style.source_color};
                background-color: {self.style.source_bg_color};
                padding: 3px 8px;
                border-radius: 3px;
            }}
        """)
        header_layout.addWidget(source_label)
        
        header_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8A9199;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        inner_layout.addLayout(header_layout)
        
        # 标题
        title_label = QLabel(self.message.title)
        title_font = QFont(
            self.style.title_font_family,
            self.style.title_font_size,
            QFont.Weight.Bold if self.style.title_font_bold else QFont.Weight.Normal
        )
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.style.title_color};
                padding: 0;
            }}
        """)
        # 应用文本对齐
        align_map = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight
        }
        title_label.setAlignment(align_map.get(self.style.title_align, Qt.AlignmentFlag.AlignLeft))
        # 应用文本溢出处理
        if self.style.title_text_overflow == "ellipsis":
            title_label.setWordWrap(False)
            # 使用Qt的省略号功能
            title_label.setTextFormat(Qt.TextFormat.PlainText)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.style.title_color};
                    padding: 0;
                }}
            """)
        elif self.style.title_text_overflow == "wrap":
            title_label.setWordWrap(True)
            # 使用CSS限制最大行数
            max_lines = getattr(self.style, 'title_max_lines', 2)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.style.title_color};
                    padding: 0;
                }}
            """)
            # 设置最大高度来限制行数
            line_height = self.style.title_font_size * 1.2  # 行高约为字体大小的1.2倍
            max_height = int(line_height * max_lines)
            title_label.setMaximumHeight(max_height)
        inner_layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel(self.message.content)
        content_font = QFont(
            self.style.content_font_family,
            self.style.content_font_size,
            QFont.Weight.Bold if self.style.content_font_bold else QFont.Weight.Normal
        )
        content_label.setFont(content_font)
        # 应用文本对齐
        content_label.setAlignment(align_map.get(self.style.content_align, Qt.AlignmentFlag.AlignLeft))
        # 应用文本溢出处理
        if self.style.content_text_overflow == "ellipsis":
            content_label.setWordWrap(False)
            # 使用Qt的省略号功能
            content_label.setTextFormat(Qt.TextFormat.PlainText)
            content_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.style.content_color};
                    padding: 0;
                    line-height: 1.5;
                }}
            """)
        elif self.style.content_text_overflow == "wrap":
            content_label.setWordWrap(True)
            # 使用CSS限制最大行数
            max_lines = getattr(self.style, 'content_max_lines', 5)
            content_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.style.content_color};
                    padding: 0;
                    line-height: 1.5;
                }}
            """)
            # 设置最大高度来限制行数
            line_height = self.style.content_font_size * 1.5  # 行高为字体大小的1.5倍
            max_height = int(line_height * max_lines)
            content_label.setMaximumHeight(max_height)
        inner_layout.addWidget(content_label)
        
        inner_layout.addStretch()
        
        # 底部：时间戳
        from datetime import datetime
        # 使用配置的时间格式
        try:
            timestamp_str = datetime.fromtimestamp(self.message.timestamp).strftime(self.style.time_format)
        except (ValueError, OSError, OverflowError):
            # 时间格式无效或时间戳异常时逐级降级，绝不让弹窗因此显示失败
            try:
                timestamp_str = datetime.fromtimestamp(self.message.timestamp).strftime('%H:%M:%S')
            except (ValueError, OSError, OverflowError):
                timestamp_str = datetime.now().strftime('%H:%M:%S')
        time_label = QLabel(timestamp_str)
        time_font = QFont(
            self.style.time_font_family,
            self.style.time_font_size,
            QFont.Weight.Bold if self.style.time_font_bold else QFont.Weight.Normal
        )
        time_label.setFont(time_font)
        # 应用文本对齐
        time_label.setAlignment(align_map.get(self.style.time_align, Qt.AlignmentFlag.AlignLeft))
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.style.time_color};
                padding: 0;
            }}
        """)
        inner_layout.addWidget(time_label)
        
        # 设置整体背景和阴影
        if self.style.background_image:
            # 使用背景图片
            main_container.setStyleSheet(f"""
                #mainContainer {{
                    background-image: url({self.style.background_image});
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: cover;
                    border: none;
                    border-radius: {self.style.border_radius}px;
                }}
            """)
        else:
            # 使用背景颜色
            main_container.setStyleSheet(f"""
                #mainContainer {{
                    background-color: {self.style.background_color};
                    border: none;
                    border-radius: {self.style.border_radius}px;
                }}
            """)
        
        # 添加阴影效果（优化：减小模糊半径，避免圆角处露出黑色）
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)  # 从30减小到15
        shadow.setColor(QColor(0, 0, 0, 80))  # 从100减小到80，降低透明度
        shadow.setOffset(0, 3)  # 从5减小到3，减小偏移
        main_container.setGraphicsEffect(shadow)
        
        # 保存阴影参数，用于位置计算时的补偿
        self._shadow_blur = 15
        self._shadow_offset_y = 3
        
        # 设置弹窗尺寸
        # 不使用 setFixedSize，让窗口根据内容自适应
        # 但设置最小尺寸以确保内容不会太小
        self.setMinimumSize(self.style.width, self.style.height)
        # 设置最大尺寸，避免窗口过大
        self.setMaximumSize(self.style.width, self.style.height + 100)  # 允许一些额外空间给阴影
    
    def _load_custom_font(self, font_file: str) -> Optional[str]:
        """加载自定义字体
        
        Args:
            font_file: 字体文件路径
            
        Returns:
            str: 字体家族名称，失败返回None
        """
        try:
            from PyQt6.QtGui import QFontDatabase
            from pathlib import Path
            
            font_path = Path(font_file)
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font_family = font_families[0]
                        logger.info(f"成功加载自定义字体: {font_family} (文件: {font_file})")
                        return font_family
                    else:
                        logger.warning(f"字体文件无效，未找到字体家族: {font_file}")
                else:
                    logger.warning(f"加载字体失败: {font_file}")
            else:
                logger.warning(f"字体文件不存在: {font_file}")
        except Exception as e:
            logger.error(f"加载自定义字体失败: {e}")
        
        return None
    
    def _play_sound(self, sound_file: str):
        """播放音效 - 使用单例音效管理器"""
        try:
            from ui.sound_manager import SoundManager
            sound_manager = SoundManager.get_instance()
            # 设置音量（0-100转换为0.0-1.0）
            volume = self.style.sound_volume / 100.0
            sound_manager.set_volume(volume)
            sound_manager.play(sound_file)
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
    
    def _setup_animation(self):
        """设置动画 - 使用用户配置"""
        # 获取屏幕几何信息
        screen = QScreen.availableGeometry(self.screen())
        
        # 记录窗口实际尺寸
        actual_size = self.size()
        logger.debug(f"_setup_animation: 配置尺寸=({self.style.width}x{self.style.height}), 实际尺寸=({actual_size.width()}x{actual_size.height()})")
        
        # 根据位置计算结束位置
        end_pos = self._calculate_position(screen)
        logger.debug(f"_setup_animation: 计算的结束位置=({end_pos.x()}, {end_pos.y()})")
        
        # 获取动画配置
        anim_config = self.style.animation_config or {}
        
        # 使用配置的尺寸而不是窗口的实际尺寸，避免首次显示时尺寸不准确
        popup_width = self.style.width
        popup_height = self.style.height
        
        # 根据动画类型和配置计算起始位置
        if self.style.animation_type == "slide":
            # 滑入动画 - 根据配置的方向
            direction = anim_config.get("slide_direction", "right_to_left")
            if direction == "right_to_left":
                start_pos = QPoint(screen.width(), end_pos.y())
            elif direction == "left_to_right":
                start_pos = QPoint(-popup_width, end_pos.y())
            elif direction == "bottom_to_top":
                start_pos = QPoint(end_pos.x(), screen.height())
            elif direction == "top_to_bottom":
                start_pos = QPoint(end_pos.x(), -popup_height)
            else:
                start_pos = end_pos
            
            logger.debug(f"_setup_animation: 滑入动画，起始位置=({start_pos.x()}, {start_pos.y()}), 结束位置=({end_pos.x()}, {end_pos.y()})")
        
        elif self.style.animation_type == "fade":
            # 淡入动画 - 在目标位置淡入
            start_pos = end_pos
            start_opacity = anim_config.get("fade_start_opacity", 0.0)
            # 注意：不在这里设置透明度，因为show()方法中已经设置了
            logger.debug(f"_setup_animation: 淡入动画，位置=({end_pos.x()}, {end_pos.y()}), 起始透明度={start_opacity}")
        
        elif self.style.animation_type == "scale":
            # 缩放动画 - 真正的几何缩放
            anim_config = self.style.animation_config
            scale_start = anim_config.get("scale_start_size", 0.5)
            scale_center = anim_config.get("scale_center", "center")
            
            # 计算起始尺寸
            start_width = int(self.style.width * scale_start)
            start_height = int(self.style.height * scale_start)
            
            # 根据缩放中心计算起始位置和结束位置
            # 关键：缩放中心（固定点）的绝对位置必须保持不变
            if scale_center == "center":
                # 中心缩放 - 中心点固定
                # 中心点位置：(end_pos.x() + width/2, end_pos.y() + height/2)
                center_x = end_pos.x() + self.style.width // 2
                center_y = end_pos.y() + self.style.height // 2
                start_x = center_x - start_width // 2
                start_y = center_y - start_height // 2
                
            elif scale_center == "top_left":
                # 左上角缩放 - 左上角固定
                # 左上角位置：(end_pos.x(), end_pos.y())
                start_x = end_pos.x()
                start_y = end_pos.y()
                
            elif scale_center == "top_right":
                # 右上角缩放 - 右上角固定
                # 右上角位置：(end_pos.x() + width, end_pos.y())
                top_right_x = end_pos.x() + self.style.width
                top_right_y = end_pos.y()
                start_x = top_right_x - start_width
                start_y = top_right_y
                
            elif scale_center == "bottom_left":
                # 左下角缩放 - 左下角固定
                # 左下角位置：(end_pos.x(), end_pos.y() + height)
                bottom_left_x = end_pos.x()
                bottom_left_y = end_pos.y() + self.style.height
                start_x = bottom_left_x
                start_y = bottom_left_y - start_height
                
            elif scale_center == "bottom_right":
                # 右下角缩放 - 右下角固定
                # 右下角位置：(end_pos.x() + width, end_pos.y() + height)
                bottom_right_x = end_pos.x() + self.style.width
                bottom_right_y = end_pos.y() + self.style.height
                start_x = bottom_right_x - start_width
                start_y = bottom_right_y - start_height
                
            else:
                # 默认中心缩放
                center_x = end_pos.x() + self.style.width // 2
                center_y = end_pos.y() + self.style.height // 2
                start_x = center_x - start_width // 2
                start_y = center_y - start_height // 2
            
            from PyQt6.QtCore import QRect
            start_geometry = QRect(start_x, start_y, start_width, start_height)
            end_geometry = QRect(end_pos.x(), end_pos.y(), self.style.width, self.style.height)
            
            # 详细的调试信息
            logger.debug(f"_setup_animation: 缩放动画详细信息:")
            logger.debug(f"  缩放中心: {scale_center}")
            logger.debug(f"  起始缩放比例: {scale_start}")
            logger.debug(f"  结束位置: ({end_pos.x()}, {end_pos.y()})")
            logger.debug(f"  结束尺寸: {self.style.width}x{self.style.height}")
            logger.debug(f"  起始尺寸: {start_width}x{start_height}")
            logger.debug(f"  起始位置: ({start_x}, {start_y})")
            logger.debug(f"  起始几何: {start_geometry}")
            logger.debug(f"  结束几何: {end_geometry}")
            
            # 关键修复：缩放动画期间需要移除尺寸限制，否则窗口无法改变大小
            # 使用 setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX) 来移除固定尺寸
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)  # Qt的最大尺寸
            
            # 设置起始几何形状
            self.setGeometry(start_geometry)
            
            # 创建几何动画
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(self.style.animation_duration)
            self.animation.setStartValue(start_geometry)
            self.animation.setEndValue(end_geometry)
            self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
            
            # 动画结束后恢复尺寸限制并确保位置正确
            def restore_size_constraints():
                # 先设置几何形状，确保位置和尺寸正确
                self.setGeometry(end_geometry)
                # 然后恢复固定尺寸
                self.setFixedSize(self.style.width, self.style.height)
                logger.debug(f"_setup_animation: 缩放动画结束，恢复尺寸限制并确保位置正确")
            
            self.animation.finished.connect(restore_size_constraints)
            
            logger.debug(f"_setup_animation: 缩放动画设置完成")
            
            # 不需要单独的位置动画，直接返回
            return
        
        else:
            start_pos = end_pos
            logger.debug(f"_setup_animation: 默认动画，位置=({end_pos.x()}, {end_pos.y()})")
        
        # 创建位置动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(self.style.animation_duration)
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        
        # 设置缓动曲线
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 如果需要透明度动画（仅用于fade）
        if self.style.animation_type == "fade":
            self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
            self.opacity_animation.setDuration(self.style.animation_duration)
            start_opacity = anim_config.get("fade_start_opacity", 0.0)
            self.opacity_animation.setStartValue(start_opacity)
            self.opacity_animation.setEndValue(self.style.opacity)
            self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 动画结束后确保位置正确（针对非缩放动画）
        def ensure_final_position():
            self.move(end_pos)
            logger.debug(f"_setup_animation: 动画结束，确保最终位置=({end_pos.x()}, {end_pos.y()})")
        
        self.animation.finished.connect(ensure_final_position)
    
    def _calculate_position(self, screen) -> QPoint:
        """计算弹窗位置（考虑堆叠）"""
        # 使用堆叠管理器计算目标位置
        pos = self.manager.get_target_position(self)
        logger.debug(f"计算弹窗位置: position={self.style.position.value}, size=({self.style.width}x{self.style.height}), target_pos=({pos.x()}, {pos.y()})")
        return pos
    
    def move_to(self, pos: QPoint):
        """平滑移动到指定位置"""
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setStartValue(self.pos())
        anim.setEndValue(pos)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        # 保存动画引用，防止被垃圾回收
        self._move_animation = anim
    
    def show(self):
        """显示弹窗（带动画）"""
        logger.debug(f"[{self.message.id}] 开始显示弹窗")
        
        # 播放音效（需求3.5）- 使用单例音效管理器
        if self.style.sound_file:
            self._play_sound(self.style.sound_file)
        
        logger.debug(f"[{self.message.id}] 先显示窗口以获取实际尺寸")
        # 先显示窗口（透明），让Qt计算实际尺寸
        self.setWindowOpacity(0)
        super().show()
        
        # 强制处理事件，确保窗口尺寸已经计算完成
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # 再次强制处理，确保窗口完全渲染
        QApplication.processEvents()
        
        logger.debug(f"[{self.message.id}] 窗口实际尺寸: {self.width()}x{self.height()}")
        
        # 等待一小段时间，确保窗口完全初始化
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, lambda: self._continue_show())
    
    def _continue_show(self):
        """继续显示弹窗（延迟执行，确保窗口尺寸正确）"""
        logger.debug(f"[{self.message.id}] 继续显示弹窗")
        logger.debug(f"[{self.message.id}] 当前窗口尺寸: {self.width()}x{self.height()}")
        
        logger.debug(f"[{self.message.id}] 添加到管理器")
        # 添加到管理器，这样 get_target_position 会考虑已有的弹窗
        self.manager.add_popup(self)
        
        logger.debug(f"[{self.message.id}] 设置动画")
        # 设置动画（此时会计算正确的位置）
        self._setup_animation()
        
        # 根据动画类型设置初始状态
        if self.style.animation_type == "fade":
            # 淡入动画：先移动到目标位置，设置为透明
            target_pos = self._calculate_position(QScreen.availableGeometry(self.screen()))
            self.move(target_pos)
            start_opacity = self.style.animation_config.get("fade_start_opacity", 0.0)
            self.setWindowOpacity(start_opacity)
            logger.debug(f"[{self.message.id}] 淡入动画：位置=({target_pos.x()}, {target_pos.y()}), 起始透明度={start_opacity}")
        elif self.style.animation_type == "slide":
            # 滑入动画：移动到起始位置，设置正常透明度
            if hasattr(self.animation, 'startValue'):
                start_pos = self.animation.startValue()
                self.move(start_pos)
                self.setWindowOpacity(self.style.opacity)
                logger.debug(f"[{self.message.id}] 滑入动画：起始位置=({start_pos.x()}, {start_pos.y()})")
        elif self.style.animation_type == "scale":
            # 缩放动画：已在_setup_animation中设置了几何形状
            # 设置正常透明度
            self.setWindowOpacity(self.style.opacity)
            logger.debug(f"[{self.message.id}] 缩放动画：已设置几何形状")
        else:
            # 其他动画：移动到目标位置
            target_pos = self._calculate_position(QScreen.availableGeometry(self.screen()))
            self.move(target_pos)
            self.setWindowOpacity(self.style.opacity)
            logger.debug(f"[{self.message.id}] 默认动画：位置=({target_pos.x()}, {target_pos.y()})")
        
        logger.debug(f"[{self.message.id}] 播放动画")
        # 播放动画
        self.animation.start()
        
        # 如果有透明度动画，也播放
        if hasattr(self, 'opacity_animation'):
            self.opacity_animation.start()
        
        # 自动复制模式：弹窗显示时立即复制
        if self.style.auto_copy and self.style.copy_mode == "auto":
            logger.debug(f"[{self.message.id}] 自动复制模式，立即复制内容")
            self._smart_copy_to_clipboard()
        
        logger.debug(f"[{self.message.id}] 弹窗显示完成")
    
    def mousePressEvent(self, event):
        """处理点击事件（需求3.6, 3.7）"""
        # 点击复制模式：点击弹窗时复制（需求3.6）
        if self.style.auto_copy and self.style.copy_mode == "on_click":
            self._smart_copy_to_clipboard()
        
        # 关闭弹窗（需求3.7）
        self.close()
    
    def _smart_copy_to_clipboard(self):
        """智能复制到剪贴板 - 支持正则表达式规则"""
        try:
            from PyQt6.QtWidgets import QApplication
            import re
            
            # 获取复制规则
            copy_rules = self.style.copy_rules if hasattr(self.style, 'copy_rules') else []
            
            content_to_copy = None
            
            # 如果有规则，按优先级匹配
            if copy_rules:
                for rule in copy_rules:
                    pattern = rule.get("pattern", "")
                    if pattern:
                        # 使用正则表达式匹配
                        try:
                            match = re.search(pattern, self.message.content)
                            if match:
                                # 如果有捕获组，使用第一个捕获组，否则使用整个匹配
                                content_to_copy = match.group(1) if match.groups() else match.group(0)
                                logger.debug(f"使用规则 '{rule.get('name')}' 匹配到: {content_to_copy}")
                                break
                        except re.error as e:
                            logger.error(f"正则表达式错误 ({pattern}): {e}")
                            continue
            
            # 如果没有匹配到任何规则，复制完整内容
            if content_to_copy is None:
                content_to_copy = self.message.content
            
            # 通知剪贴板连接器忽略下一次变化（避免循环触发）
            try:
                from data.connectors.clipboard_connector import ClipboardConnector
                ClipboardConnector.mark_ignore_next_change()
                logger.debug("已标记忽略下一次剪贴板变化")
            except Exception as e:
                logger.warning(f"无法标记忽略剪贴板变化: {e}")
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(content_to_copy)
            logger.info(f"✅ 智能复制成功: {content_to_copy[:50]}{'...' if len(content_to_copy) > 50 else ''}")
            
        except Exception as e:
            logger.error(f"智能复制到剪贴板失败: {e}")
    
    def _copy_to_clipboard(self, text: str):
        """复制到剪贴板（保留旧方法以兼容）"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logger.debug("内容已复制到剪贴板")
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")
    
    def set_auto_close(self, duration: int):
        """设置自动关闭定时器"""
        QTimer.singleShot(duration, self.close)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 从管理器移除
        self.manager.remove_popup(self)
        self.closed.emit()
        super().closeEvent(event)
