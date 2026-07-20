"""
WinMsgHub - 弹窗设置页面
作者：青云制作_彭明航
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSpinBox, QSlider, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QColorDialog,
    QGroupBox, QGridLayout, QScrollArea, QSizePolicy,
    QListWidget, QInputDialog, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
from ui.svg_icons import SvgIcon
from ui.icon_label import IconLabel


class PopupPreviewWidget(QFrame):
    """弹窗预览组件 - 实时显示弹窗效果"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("previewPopup")
        self.setMinimumSize(400, 120)
        self.setMaximumWidth(600)
        self.setMaximumHeight(800)
        self.current_animation_type = "slide"
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum
        )
        
        # 移除边框
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWidth(0)
        
        # 背景属性
        self._bg_color = QColor(42, 49, 57, 255)
        self._bg_image = None
        self._border_radius = 12
        
        self._setup_ui()
        self._apply_default_style()
    
    def paintEvent(self, event):
        """自定义绘制背景"""
        from PyQt6.QtGui import QPainter, QBrush, QPen, QPixmap, QPainterPath
        from PyQt6.QtCore import Qt, QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 设置透明度
        painter.setOpacity(self._bg_color.alphaF())
        
        # 创建圆角路径
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, self._border_radius, self._border_radius)
        
        # 设置裁剪区域为圆角矩形
        painter.setClipPath(path)
        
        if self._bg_image and os.path.exists(self._bg_image):
            # 绘制背景图（带圆角）
            pixmap = QPixmap(self._bg_image)
            # 缩放图片以适应widget大小
            scaled_pixmap = pixmap.scaled(
                self.width(), 
                self.height(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # 居中绘制
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # 绘制背景色（带圆角）
            painter.setBrush(QBrush(self._bg_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawPath(path)
        
        painter.end()
    
    def resizeEvent(self, event):
        """窗口大小改变时"""
        super().resizeEvent(event)
        self.update()  # 触发重绘
    
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        self.setLayout(layout)
        
        # 顶部：消息源和关闭按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        self.source_label = QLabel("预览")
        self.source_label.setFont(QFont("Microsoft YaHei UI", 9, QFont.Weight.Bold))
        self.source_label.setStyleSheet("""
            color: #4A9EFF;
            background-color: rgba(74, 158, 255, 0.15);
            padding: 3px 8px;
            border-radius: 3px;
        """)
        header_layout.addWidget(self.source_label)
        header_layout.addStretch()
        
        close_btn = QLabel("×")
        close_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        close_btn.setStyleSheet("color: #8A9199; background: transparent;")
        close_btn.setFixedSize(24, 24)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # 标题
        self.title_label = QLabel("这是弹窗标题")
        self.title_label.setFont(QFont("Microsoft YaHei UI", 13, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # 内容
        self.content_label = QLabel("这是弹窗的内容预览文本，您可以实时看到配置的效果。")
        self.content_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.content_label.setStyleSheet("color: #B8BFC6; background: transparent;")
        self.content_label.setWordWrap(True)
        layout.addWidget(self.content_label)
        
        layout.addStretch()
        
        # 时间
        self.time_label = QLabel(datetime.now().strftime('%H:%M:%S'))
        self.time_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.time_label.setStyleSheet("color: #6C757D; background: transparent;")
        layout.addWidget(self.time_label)
    
    def _apply_default_style(self):
        """应用默认样式"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        self.setStyleSheet("""
            #previewPopup {
                background-color: #2A3139;
                border-radius: 12px;
                border: none;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def play_animation(self):
        """播放动画效果"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSequentialAnimationGroup
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        
        # 保存当前位置
        original_pos = self.pos()
        config = getattr(self, 'current_animation_config', {})
        
        # 根据动画类型创建不同的动画
        if self.current_animation_type == "slide":
            # 滑入动画 - 根据配置的方向
            slide_direction = config.get("slide_direction", "right_to_left")
            
            if slide_direction == "right_to_left":
                start_pos = QPoint(original_pos.x() + 200, original_pos.y())
            elif slide_direction == "left_to_right":
                start_pos = QPoint(original_pos.x() - 200, original_pos.y())
            elif slide_direction == "bottom_to_top":
                start_pos = QPoint(original_pos.x(), original_pos.y() + 200)
            else:  # top_to_bottom
                start_pos = QPoint(original_pos.x(), original_pos.y() - 200)
            
            self.move(start_pos)
            
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(400)
            anim.setStartValue(start_pos)
            anim.setEndValue(original_pos)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start()
            self._current_anim = anim
            
        elif self.current_animation_type == "fade":
            # 淡入动画 - 使用QGraphicsOpacityEffect而不是windowOpacity
            fade_start = config.get("fade_start_opacity", 0.0)
            
            # 创建透明度效果
            opacity_effect = QGraphicsOpacityEffect()
            self.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(fade_start)
            
            anim = QPropertyAnimation(opacity_effect, b"opacity")
            anim.setDuration(400)
            anim.setStartValue(fade_start)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # 动画结束后移除效果（恢复正常显示）
            def restore_effect():
                self.setGraphicsEffect(None)
                # 重新应用阴影
                from PyQt6.QtWidgets import QGraphicsDropShadowEffect
                from PyQt6.QtGui import QColor
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(30)
                shadow.setColor(QColor(0, 0, 0, 150))
                shadow.setOffset(0, 5)
                self.setGraphicsEffect(shadow)
            
            anim.finished.connect(restore_effect)
            anim.start()
            self._current_anim = anim
            
        elif self.current_animation_type == "scale":
            # 缩放动画 - 使用真正的缩放变换
            from PyQt6.QtCore import QRect, QSize
            
            scale_start = config.get("scale_start_size", 0.5)
            scale_center = config.get("scale_center", "center")
            
            # 保存原始尺寸
            original_size = self.size()
            original_geometry = self.geometry()
            
            # 计算起始尺寸
            start_width = int(original_size.width() * scale_start)
            start_height = int(original_size.height() * scale_start)
            
            # 根据缩放中心计算起始位置
            # 关键：缩放中心（固定点）的绝对位置必须保持不变
            if scale_center == "center":
                # 中心缩放 - 中心点固定
                center_x = original_geometry.x() + original_size.width() // 2
                center_y = original_geometry.y() + original_size.height() // 2
                start_x = center_x - start_width // 2
                start_y = center_y - start_height // 2
                
            elif scale_center == "top_left":
                # 左上角缩放 - 左上角固定
                start_x = original_geometry.x()
                start_y = original_geometry.y()
                
            elif scale_center == "top_right":
                # 右上角缩放 - 右上角固定
                top_right_x = original_geometry.x() + original_size.width()
                top_right_y = original_geometry.y()
                start_x = top_right_x - start_width
                start_y = top_right_y
                
            elif scale_center == "bottom_left":
                # 左下角缩放 - 左下角固定
                bottom_left_x = original_geometry.x()
                bottom_left_y = original_geometry.y() + original_size.height()
                start_x = bottom_left_x
                start_y = bottom_left_y - start_height
                
            elif scale_center == "bottom_right":
                # 右下角缩放 - 右下角固定
                bottom_right_x = original_geometry.x() + original_size.width()
                bottom_right_y = original_geometry.y() + original_size.height()
                start_x = bottom_right_x - start_width
                start_y = bottom_right_y - start_height
                
            else:
                # 默认中心缩放
                center_x = original_geometry.x() + original_size.width() // 2
                center_y = original_geometry.y() + original_size.height() // 2
                start_x = center_x - start_width // 2
                start_y = center_y - start_height // 2
            
            # 设置起始几何
            self.setGeometry(start_x, start_y, start_width, start_height)
            
            # 创建几何动画
            anim = QPropertyAnimation(self, b"geometry")
            anim.setDuration(400)
            anim.setStartValue(QRect(start_x, start_y, start_width, start_height))
            anim.setEndValue(original_geometry)
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            
            # 动画结束后恢复阴影
            def restore_effect():
                from PyQt6.QtWidgets import QGraphicsDropShadowEffect
                from PyQt6.QtGui import QColor
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(30)
                shadow.setColor(QColor(0, 0, 0, 150))
                shadow.setOffset(0, 5)
                self.setGraphicsEffect(shadow)
            
            anim.finished.connect(restore_effect)
            anim.start()
            self._current_anim = anim
    
    def update_preview(self, width, height, bg_color, opacity, 
                      title_size, title_color,
                      content_size, content_color,
                      source_size, source_color, source_bg_color,
                      time_color, animation_type="slide",
                      title_overflow="ellipsis", content_overflow="wrap",
                      bg_image=None, border_radius=12, animation_config=None,
                      preview_source_text="预览", preview_title_text="这是弹窗标题",
                      preview_content_text="这是弹窗的内容预览文本，您可以实时看到配置的效果。",
                      title_align="left", content_align="left", time_align="left",
                      time_format="%H:%M:%S", custom_font_family=None):
        """更新预览样式"""
        
        # 保存动画类型和配置
        self.current_animation_type = animation_type
        self.current_animation_config = animation_config or {}
        
        # 保存配置的透明度（用于动画恢复）
        self.configured_opacity = opacity
        
        # 设置最小尺寸，但允许根据内容扩展
        self.setMinimumSize(width, height)
        self.setMaximumWidth(max(width, 600))
        self.setMaximumHeight(800)
        
        # 解析背景色
        if bg_color.startswith('#'):
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            alpha = int(max(0.0, min(1.0, opacity)) * 255)
            self._bg_color = QColor(r, g, b, alpha)
        else:
            self._bg_color = QColor(42, 49, 57, 255)
        
        # 设置背景图和圆角
        self._bg_image = bg_image
        self._border_radius = border_radius
        
        # 清除所有样式表，让paintEvent接管
        self.setStyleSheet("""
            #previewPopup {
                background: transparent;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        # 触发重绘
        self.update()
        
        # 重新应用阴影
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        # 确定使用的字体家族
        font_family = custom_font_family if custom_font_family else "Microsoft YaHei UI"
        
        # 更新消息源文本和样式
        self.source_label.setText(preview_source_text)
        self.source_label.setStyleSheet(f"""
            color: {source_color};
            background-color: {source_bg_color};
            padding: 3px 8px;
            border-radius: 3px;
        """)
        self.source_label.setFont(QFont(font_family, source_size, QFont.Weight.Bold))
        
        # 更新标题 - 应用溢出处理和对齐方式
        self.title_label.setText(preview_title_text)
        self.title_label.setStyleSheet(f"color: {title_color}; background: transparent;")
        self.title_label.setFont(QFont(font_family, title_size, QFont.Weight.Bold))
        if title_overflow == "ellipsis":
            self.title_label.setWordWrap(False)
        elif title_overflow == "wrap":
            self.title_label.setWordWrap(True)
        else:  # none
            self.title_label.setWordWrap(False)
        
        # 设置标题对齐方式
        align_map = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight
        }
        self.title_label.setAlignment(align_map.get(title_align, Qt.AlignmentFlag.AlignLeft))
        
        # 更新内容 - 应用溢出处理和对齐方式
        self.content_label.setText(preview_content_text)
        self.content_label.setStyleSheet(f"color: {content_color}; background: transparent;")
        self.content_label.setFont(QFont(font_family, content_size))
        if content_overflow == "ellipsis":
            self.content_label.setWordWrap(False)
        elif content_overflow == "wrap":
            self.content_label.setWordWrap(True)
        else:  # none
            self.content_label.setWordWrap(False)
        
        # 设置内容对齐方式
        self.content_label.setAlignment(align_map.get(content_align, Qt.AlignmentFlag.AlignLeft))
        
        # 更新时间 - 应用格式和对齐方式
        try:
            time_text = datetime.now().strftime(time_format)
        except:
            time_text = datetime.now().strftime('%H:%M:%S')
        
        self.time_label.setText(time_text)
        self.time_label.setStyleSheet(f"color: {time_color}; background: transparent;")
        self.time_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.time_label.setAlignment(align_map.get(time_align, Qt.AlignmentFlag.AlignLeft))
        
        # 强制重新计算布局和大小
        self.layout().activate()
        self.adjustSize()
        self.updateGeometry()
        
        # 确保父容器也更新
        if self.parent():
            self.parent().updateGeometry()


class PopupPage(QWidget):
    """弹窗设置页面 - 配置弹窗样式和行为"""
    
    def __init__(self, config_manager, popup_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.popup_manager = popup_manager
        
        # 创建异步配置管理器
        from core.async_config_manager import AsyncConfigManager
        self.async_config = AsyncConfigManager(config_manager)
        
        # 自动保存定时器（防抖）- 已由AsyncConfigManager处理
        # 预览更新定时器（防抖）
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._update_preview)
        
        self._setup_ui()
        self._load_config()
        self._connect_signals()
        self._update_preview()  # 初始预览
    
    def _setup_ui(self):
        """设置UI - 左右分栏布局"""
        # 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)
        
        # 左侧：配置区域
        left_widget = self._create_left_panel()
        main_layout.addWidget(left_widget, 3)  # 占3份
        
        # 右侧：预览区域
        right_widget = self._create_right_panel()
        main_layout.addWidget(right_widget, 2)  # 占2份
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧配置面板"""
        widget = QWidget()
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 10, 0)
        widget.setLayout(layout)
        
        # 页面标题
        title = QLabel("弹窗设置")
        title.setProperty("heading", "h2")
        layout.addWidget(title)
        
        # 尺寸设置
        size_card = self._create_size_card()
        layout.addWidget(size_card)
        
        # 位置设置
        position_card = self._create_position_card()
        layout.addWidget(position_card)
        
        # 显示设置
        display_card = self._create_display_card()
        layout.addWidget(display_card)
        
        # 样式设置
        style_card = self._create_style_card()
        layout.addWidget(style_card)
        
        # 字体设置
        font_card = self._create_font_card()
        layout.addWidget(font_card)
        
        # 颜色设置
        color_card = self._create_color_card()
        layout.addWidget(color_card)
        
        # 文本对齐设置
        align_card = self._create_align_card()
        layout.addWidget(align_card)
        
        # 时间格式设置
        time_format_card = self._create_time_format_card()
        layout.addWidget(time_format_card)
        
        # 预览文本自定义
        preview_text_card = self._create_preview_text_card()
        layout.addWidget(preview_text_card)
        
        # 按钮区域 - 恢复所有默认设置
        button_layout = QHBoxLayout()
        
        from ui.svg_icons import SvgIcon
        reset_all_btn = QPushButton("  恢复所有默认设置")
        reset_all_btn.setIcon(SvgIcon.get_icon("refresh", "#FFFFFF", 16))
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #C5444F;
                color: white;
                font-weight: 500;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D75661;
            }
            QPushButton:pressed {
                background-color: #B3323D;
            }
        """)
        reset_all_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        # 包装到容器
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        container.setLayout(container_layout)
        
        return container
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧预览面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        
        # 标题
        title = QLabel("实时预览")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 预览背景图设置
        bg_control_layout = QHBoxLayout()
        bg_control_layout.addWidget(QLabel("预览背景:"))
        self.preview_bg_btn = QPushButton("选择背景图")
        self.preview_bg_btn.clicked.connect(self._choose_preview_bg)
        bg_control_layout.addWidget(self.preview_bg_btn)
        self.preview_bg_label = QLabel("默认背景")
        self.preview_bg_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        bg_control_layout.addWidget(self.preview_bg_label)
        self.clear_preview_bg_btn = QPushButton("清除")
        self.clear_preview_bg_btn.setProperty("secondary", "true")
        self.clear_preview_bg_btn.clicked.connect(self._clear_preview_bg)
        bg_control_layout.addWidget(self.clear_preview_bg_btn)
        bg_control_layout.addStretch()
        layout.addLayout(bg_control_layout)
        
        # 预览容器 - 使用更深的背景色突出预览
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet("""
            QFrame {
                background-color: #1A1D23;
                border: none;
                border-radius: 12px;
            }
        """)
        self.preview_container.setMinimumHeight(400)
        
        preview_layout = QVBoxLayout()
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.setContentsMargins(30, 30, 30, 30)
        self.preview_container.setLayout(preview_layout)
        
        # 预览组件
        self.preview_widget = PopupPreviewWidget()
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.preview_container)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 播放动画按钮
        play_anim_btn = QPushButton("  播放动画")
        play_anim_btn.setIcon(SvgIcon.get_icon("play", "#FFFFFF", 16))
        play_anim_btn.setStyleSheet("""
            QPushButton {
                background-color: #98C379;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #88B369;
            }
            QPushButton:pressed {
                background-color: #78A359;
            }
        """)
        play_anim_btn.clicked.connect(self._play_preview_animation)
        button_layout.addWidget(play_anim_btn)
        
        # 实际效果预览按钮
        real_preview_btn = QPushButton("  实际效果预览")
        real_preview_btn.setIcon(SvgIcon.get_icon("zap", "#FFFFFF", 16))
        real_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A8EEF;
            }
            QPushButton:pressed {
                background-color: #2A7EDF;
            }
        """)
        real_preview_btn.clicked.connect(self._show_real_preview)
        button_layout.addWidget(real_preview_btn)
        
        layout.addLayout(button_layout)
        
        # 说明文字
        from ui.icon_label import IconLabel
        hint = IconLabel("lightbulb", "配置会实时反映在预览中", "#6C757D", 14)
        hint.setStyleSheet("color: #6C757D; font-size: 12px;")
        hint.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        layout.addStretch()
        
        # 初始化预览背景图变量
        self.preview_bg_image = None
        
        return widget
    
    def _create_size_card(self) -> QFrame:
        """创建尺寸设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("弹窗基础尺寸")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_size_btn = QPushButton("  恢复默认")
        reset_size_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_size_btn.setProperty("secondary", "true")
        reset_size_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_size_btn.clicked.connect(self._reset_size_defaults)
        header_layout.addWidget(reset_size_btn)
        
        layout.addLayout(header_layout)
        
        # 说明文字
        hint_widget = IconLabel("lightbulb", "这是弹窗的基础尺寸，实际显示时会根据内容自动调整", "#6C757D", 14)
        hint_widget.text_label.setStyleSheet("color: #6C757D; font-size: 12px; padding: 5px 0;")
        hint_widget.text_label.setWordWrap(True)
        hint = hint_widget
        layout.addWidget(hint)
        
        grid = QGridLayout()
        
        # 宽度
        grid.addWidget(QLabel("宽度:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 800)
        self.width_spin.setValue(400)
        self.width_spin.setSuffix(" px")
        grid.addWidget(self.width_spin, 0, 1)
        
        # 高度
        grid.addWidget(QLabel("高度:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(80, 600)
        self.height_spin.setValue(120)
        self.height_spin.setSuffix(" px")
        grid.addWidget(self.height_spin, 1, 1)
        
        layout.addLayout(grid)
        
        # 文本溢出处理
        overflow_label = QLabel("文本溢出处理:")
        overflow_label.setStyleSheet("font-weight: 500; margin-top: 10px;")
        layout.addWidget(overflow_label)
        
        overflow_grid = QGridLayout()
        
        # 标题溢出处理
        overflow_grid.addWidget(QLabel("标题:"), 0, 0)
        self.title_overflow_combo = QComboBox()
        self.title_overflow_combo.addItems(["裁剪", "换行"])
        overflow_grid.addWidget(self.title_overflow_combo, 0, 1)
        
        # 标题最大行数（保存标签和控件的引用，用于显示/隐藏）
        self.title_max_lines_label = QLabel("标题最大行数:")
        overflow_grid.addWidget(self.title_max_lines_label, 0, 2)
        self.title_max_lines_spin = QSpinBox()
        self.title_max_lines_spin.setRange(1, 10)
        self.title_max_lines_spin.setValue(2)
        self.title_max_lines_spin.setSuffix(" 行")
        self.title_max_lines_spin.setToolTip("换行模式下的最大行数，超出部分将被截断")
        overflow_grid.addWidget(self.title_max_lines_spin, 0, 3)
        
        # 内容溢出处理
        overflow_grid.addWidget(QLabel("内容:"), 1, 0)
        self.content_overflow_combo = QComboBox()
        self.content_overflow_combo.addItems(["裁剪", "换行"])
        self.content_overflow_combo.setCurrentIndex(1)  # 默认自动换行
        overflow_grid.addWidget(self.content_overflow_combo, 1, 1)
        
        # 内容最大行数（保存标签和控件的引用，用于显示/隐藏）
        self.content_max_lines_label = QLabel("内容最大行数:")
        overflow_grid.addWidget(self.content_max_lines_label, 1, 2)
        self.content_max_lines_spin = QSpinBox()
        self.content_max_lines_spin.setRange(1, 20)
        self.content_max_lines_spin.setValue(5)
        self.content_max_lines_spin.setSuffix(" 行")
        self.content_max_lines_spin.setToolTip("换行模式下的最大行数，超出部分将被截断")
        overflow_grid.addWidget(self.content_max_lines_spin, 1, 3)
        
        layout.addLayout(overflow_grid)
        
        # 提示信息
        self.overflow_hint = IconLabel("lightbulb", "提示：换行模式下，超过最大行数的文本将被截断不显示", "#6C757D", 14)
        self.overflow_hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
        self.overflow_hint.text_label.setWordWrap(True)
        layout.addWidget(self.overflow_hint)
        
        # 连接信号，根据溢出模式显示/隐藏最大行数配置
        self.title_overflow_combo.currentIndexChanged.connect(self._update_max_lines_visibility)
        self.content_overflow_combo.currentIndexChanged.connect(self._update_max_lines_visibility)
        
        # 初始化显示状态
        self._update_max_lines_visibility()
        
        return card
    
    def _create_position_card(self) -> QFrame:
        """创建位置设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("弹窗位置")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_position_btn = QPushButton("  恢复默认")
        reset_position_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_position_btn.setProperty("secondary", "true")
        reset_position_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_position_btn.clicked.connect(self._reset_position_defaults)
        header_layout.addWidget(reset_position_btn)
        
        layout.addLayout(header_layout)
        
        # 位置选择器（3x3网格，但中心位置留空）
        position_grid = QGridLayout()
        position_grid.setSpacing(10)
        
        positions = [
            ("top_left", "左上", 0, 0),
            ("top_center", "上中", 0, 1),
            ("top_right", "右上", 0, 2),
            ("center_left", "左中", 1, 0),
            ("center_right", "右中", 1, 2),
            ("bottom_left", "左下", 2, 0),
            ("bottom_center", "下中", 2, 1),
            ("bottom_right", "右下", 2, 2),
        ]
        
        self.position_buttons = {}
        for pos_id, pos_label, row, col in positions:
            btn = QPushButton(pos_label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=pos_id: self._select_position(p))
            position_grid.addWidget(btn, row, col)
            self.position_buttons[pos_id] = btn
        
        # 中心位置添加说明标签
        center_label = QLabel("屏幕边缘")
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        position_grid.addWidget(center_label, 1, 1)
        
        layout.addLayout(position_grid)
        
        return card
    
    def _create_display_card(self) -> QFrame:
        """创建显示设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("显示设置")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_display_btn = QPushButton("  恢复默认")
        reset_display_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_display_btn.setProperty("secondary", "true")
        reset_display_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_display_btn.clicked.connect(self._reset_display_defaults)
        header_layout.addWidget(reset_display_btn)
        
        layout.addLayout(header_layout)
        
        grid = QGridLayout()
        
        # 显示时长
        grid.addWidget(QLabel("显示时长:"), 0, 0)
        duration_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1000, 30000)
        self.duration_spin.setValue(5000)
        self.duration_spin.setSingleStep(1000)
        self.duration_spin.setSuffix(" ms")
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        grid.addLayout(duration_layout, 0, 1)
        
        # 动画时长
        grid.addWidget(QLabel("动画时长:"), 1, 0)
        animation_layout = QHBoxLayout()
        self.animation_spin = QSpinBox()
        self.animation_spin.setRange(100, 2000)
        self.animation_spin.setValue(300)
        self.animation_spin.setSingleStep(50)
        self.animation_spin.setSuffix(" ms")
        animation_layout.addWidget(self.animation_spin)
        animation_layout.addStretch()
        grid.addLayout(animation_layout, 1, 1)
        
        # 最多同时显示弹窗数量
        grid.addWidget(QLabel("最多同时显示:"), 2, 0)
        max_popups_layout = QHBoxLayout()
        self.max_popups_spin = QSpinBox()
        self.max_popups_spin.setRange(1, 20)
        self.max_popups_spin.setValue(5)
        self.max_popups_spin.setSuffix(" 个弹窗")
        self.max_popups_spin.setToolTip("同时显示的弹窗数量上限，超过后旧弹窗会自动关闭")
        max_popups_layout.addWidget(self.max_popups_spin)
        max_popups_layout.addStretch()
        grid.addLayout(max_popups_layout, 2, 1)
        
        layout.addLayout(grid)
        
        # 自动复制设置
        auto_copy_group = QGroupBox("智能复制设置")
        auto_copy_layout = QVBoxLayout()
        auto_copy_group.setLayout(auto_copy_layout)
        
        # 启用自动复制
        self.auto_copy_check = QCheckBox("启用智能复制")
        self.auto_copy_check.setToolTip("启用后，会根据下方设置自动提取并复制匹配的内容到剪贴板")
        auto_copy_layout.addWidget(self.auto_copy_check)
        
        # 复制模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("复制模式:")
        mode_label.setStyleSheet("font-weight: bold;")
        mode_layout.addWidget(mode_label)
        
        self.copy_mode_group = QButtonGroup()
        
        self.copy_on_click_radio = QRadioButton("点击弹窗时复制")
        self.copy_on_click_radio.setToolTip("需要点击弹窗才会复制内容")
        self.copy_on_click_radio.setChecked(True)
        self.copy_mode_group.addButton(self.copy_on_click_radio, 0)
        mode_layout.addWidget(self.copy_on_click_radio)
        
        self.copy_auto_radio = QRadioButton("自动复制（无需点击）")
        self.copy_auto_radio.setToolTip("弹窗显示时立即自动复制，无需点击")
        self.copy_mode_group.addButton(self.copy_auto_radio, 1)
        mode_layout.addWidget(self.copy_auto_radio)
        
        mode_layout.addStretch()
        auto_copy_layout.addLayout(mode_layout)
        
        # 复制规则说明
        help_label = QLabel(
            "使用说明：\n"
            "• 点击弹窗时复制：需要点击弹窗才会提取并复制内容\n"
            "• 自动复制：弹窗显示时立即自动复制，无需点击\n"
            "• 可以添加多个规则，按优先级从上到下匹配\n"
            "• 使用正则表达式提取验证码、邮箱、电话等信息\n"
            "• 如果没有规则或都不匹配，则复制完整消息内容\n"
            "• 快速添加：点击下方预设按钮快速添加常用规则\n"
            "注意：智能复制不会触发剪贴板监控的新弹窗"
        )
        help_label.setStyleSheet("""
            QLabel {
                background-color: #1E3A5F;
                color: #ABB2BF;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #4A9EFF;
                font-size: 11px;
                line-height: 1.5;
            }
        """)
        help_label.setWordWrap(True)
        auto_copy_layout.addWidget(help_label)
        
        # 复制规则列表
        rules_label = QLabel("复制规则（按优先级匹配）:")
        rules_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        auto_copy_layout.addWidget(rules_label)
        
        # 规则列表和按钮
        rules_container = QHBoxLayout()
        
        self.copy_rules_list = QListWidget()
        self.copy_rules_list.setAlternatingRowColors(True)
        self.copy_rules_list.setMaximumHeight(300)
        rules_container.addWidget(self.copy_rules_list)
        
        # 规则操作按钮
        rules_buttons = QVBoxLayout()
        
        add_rule_btn = QPushButton("  添加规则")
        add_rule_btn.setIcon(SvgIcon.get_icon("plus", "#98C379", 14))
        add_rule_btn.clicked.connect(self._add_copy_rule)
        rules_buttons.addWidget(add_rule_btn)
        
        edit_rule_btn = QPushButton("  编辑")
        edit_rule_btn.setIcon(SvgIcon.get_icon("edit", "#4A9EFF", 14))
        edit_rule_btn.clicked.connect(self._edit_copy_rule)
        rules_buttons.addWidget(edit_rule_btn)
        
        delete_rule_btn = QPushButton("  删除")
        delete_rule_btn.setIcon(SvgIcon.get_icon("delete", "#E06C75", 14))
        delete_rule_btn.clicked.connect(self._delete_copy_rule)
        rules_buttons.addWidget(delete_rule_btn)
        
        # 添加优先级调整按钮
        move_up_btn = QPushButton("  上移")
        move_up_btn.setIcon(SvgIcon.get_icon("arrow_up", "#ABB2BF", 14))
        move_up_btn.setProperty("secondary", "true")
        move_up_btn.setToolTip("提高选中规则的优先级")
        move_up_btn.clicked.connect(self._move_rule_up)
        rules_buttons.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("  下移")
        move_down_btn.setIcon(SvgIcon.get_icon("arrow_down", "#ABB2BF", 14))
        move_down_btn.setProperty("secondary", "true")
        move_down_btn.setToolTip("降低选中规则的优先级")
        move_down_btn.clicked.connect(self._move_rule_down)
        rules_buttons.addWidget(move_down_btn)
        
        # 预设规则按钮
        preset_label = QLabel("快速添加:")
        preset_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        rules_buttons.addWidget(preset_label)
        
        preset_code_btn = QPushButton("验证码")
        preset_code_btn.setToolTip("匹配独立的4-6位纯数字验证码（前后必须有空格、标点或换行）")
        preset_code_btn.clicked.connect(lambda: self._add_preset_rule("验证码", r"(?:验证码|code|Code|CODE)[:：\s]*(\d{4,6})(?=\s|$|[，。！？、,\.!?])"))
        rules_buttons.addWidget(preset_code_btn)
        
        preset_email_btn = QPushButton("邮箱")
        preset_email_btn.setToolTip("匹配完整的邮箱地址")
        preset_email_btn.clicked.connect(lambda: self._add_preset_rule("邮箱", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"))
        rules_buttons.addWidget(preset_email_btn)
        
        preset_phone_btn = QPushButton("手机号")
        preset_phone_btn.setToolTip("匹配中国大陆手机号（11位，1开头）")
        preset_phone_btn.clicked.connect(lambda: self._add_preset_rule("手机号", r"(?<!\d)1[3-9]\d{9}(?!\d)"))
        rules_buttons.addWidget(preset_phone_btn)
        
        preset_url_btn = QPushButton("网址")
        preset_url_btn.setToolTip("匹配完整的HTTP/HTTPS链接")
        preset_url_btn.clicked.connect(lambda: self._add_preset_rule("网址", r"https?://[^\s\u4e00-\u9fa5]+"))
        rules_buttons.addWidget(preset_url_btn)
        
        rules_buttons.addStretch()
        
        rules_container.addLayout(rules_buttons)
        auto_copy_layout.addLayout(rules_container)
        
        layout.addWidget(auto_copy_group)
        
        return card
    
    def _create_style_card(self) -> QFrame:
        """创建样式设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("样式设置")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_style_btn = QPushButton("  恢复默认")
        reset_style_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_style_btn.setProperty("secondary", "true")
        reset_style_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_style_btn.clicked.connect(self._reset_style_defaults)
        header_layout.addWidget(reset_style_btn)
        
        layout.addLayout(header_layout)
        
        grid = QGridLayout()
        
        # 透明度
        grid.addWidget(QLabel("透明度:"), 0, 0)
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("95%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        opacity_layout.addWidget(self.opacity_label)
        grid.addLayout(opacity_layout, 0, 1)
        
        # 背景颜色
        grid.addWidget(QLabel("背景颜色:"), 1, 0)
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self._choose_bg_color)
        color_layout.addWidget(self.color_btn)
        self.color_preview = QLabel("     ")
        self.color_preview.setStyleSheet("background-color: #ffffff; border: 2px solid #E1E8ED; border-radius: 4px;")
        self.color_preview.setFixedSize(50, 30)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        grid.addLayout(color_layout, 1, 1)
        
        # 背景图片
        grid.addWidget(QLabel("背景图片:"), 2, 0)
        bg_image_layout = QHBoxLayout()
        self.bg_image_btn = QPushButton("选择图片")
        self.bg_image_btn.clicked.connect(self._choose_bg_image)
        bg_image_layout.addWidget(self.bg_image_btn)
        self.bg_image_label = QLabel("未选择")
        self.bg_image_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        bg_image_layout.addWidget(self.bg_image_label)
        self.clear_bg_image_btn = QPushButton("清除")
        self.clear_bg_image_btn.clicked.connect(self._clear_bg_image)
        self.clear_bg_image_btn.setProperty("secondary", "true")
        bg_image_layout.addWidget(self.clear_bg_image_btn)
        bg_image_layout.addStretch()
        grid.addLayout(bg_image_layout, 2, 1)
        
        # 圆角值
        grid.addWidget(QLabel("圆角值:"), 3, 0)
        radius_layout = QHBoxLayout()
        self.border_radius_spin = QSpinBox()
        self.border_radius_spin.setRange(0, 50)
        self.border_radius_spin.setValue(12)
        self.border_radius_spin.setSuffix(" px")
        radius_layout.addWidget(self.border_radius_spin)
        radius_layout.addStretch()
        grid.addLayout(radius_layout, 3, 1)
        
        # 动画类型
        grid.addWidget(QLabel("动画类型:"), 4, 0)
        animation_layout = QHBoxLayout()
        self.animation_combo = QComboBox()
        self.animation_combo.addItems(["滑入 (Slide)", "淡入 (Fade)", "缩放 (Scale)"])
        self.animation_combo.currentIndexChanged.connect(self._on_animation_type_changed)
        animation_layout.addWidget(self.animation_combo)
        animation_layout.addStretch()
        grid.addLayout(animation_layout, 4, 1)
        
        # 音效文件
        grid.addWidget(QLabel("弹窗音效:"), 5, 0)
        sound_layout = QHBoxLayout()
        self.sound_btn = QPushButton("选择音效")
        self.sound_btn.clicked.connect(self._choose_sound)
        sound_layout.addWidget(self.sound_btn)
        self.sound_label = QLabel("未选择")
        self.sound_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        sound_layout.addWidget(self.sound_label)
        self.clear_sound_btn = QPushButton("清除")
        self.clear_sound_btn.clicked.connect(self._clear_sound)
        self.clear_sound_btn.setProperty("secondary", "true")
        sound_layout.addWidget(self.clear_sound_btn)
        self.test_sound_btn = QPushButton("试听")
        self.test_sound_btn.clicked.connect(self._test_sound)
        sound_layout.addWidget(self.test_sound_btn)
        sound_layout.addStretch()
        grid.addLayout(sound_layout, 5, 1)
        
        # 音量控制
        grid.addWidget(QLabel("音效音量:"), 6, 0)
        volume_layout = QHBoxLayout()
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        # 阻塞信号，避免触发自动保存
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(50)
        self.volume_slider.blockSignals(False)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("50%")
        self.volume_label.setStyleSheet("color: #ABB2BF; font-size: 12px; min-width: 40px;")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_label)
        
        volume_layout.addStretch()
        grid.addLayout(volume_layout, 6, 1)
        
        layout.addLayout(grid)
        
        # 动画配置区域（动态显示）
        self.animation_config_widget = QWidget()
        self.animation_config_layout = QVBoxLayout()
        self.animation_config_layout.setContentsMargins(0, 10, 0, 0)
        self.animation_config_widget.setLayout(self.animation_config_layout)
        layout.addWidget(self.animation_config_widget)
        
        # 初始化变量
        self.selected_bg_image = None
        # 初始化默认音效
        from utils.resource_path import get_resource_path
        import os
        default_sound = get_resource_path("resources/sounds/default.mp3")
        if os.path.exists(default_sound):
            self.selected_sound = default_sound
        else:
            self.selected_sound = None
        
        # 创建各种动画配置控件
        self._create_animation_configs()
        
        # 显示默认动画配置
        self._on_animation_type_changed(0)
        
        return card
    
    def _select_position(self, position: str):
        """选择位置"""
        for pos_id, btn in self.position_buttons.items():
            btn.setChecked(pos_id == position)
    
    def _choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 2px solid #E1E8ED; border-radius: 4px;"
            )
            self.selected_color = color.name()
            self._trigger_auto_save()
            self._trigger_preview_update()
    
    def _choose_bg_image(self):
        """选择背景图片"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择背景图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg *.ico);;所有文件 (*.*)"
        )
        if file_path:
            self.selected_bg_image = file_path
            import os
            self.bg_image_label.setText(os.path.basename(file_path))
            self._trigger_auto_save()
            self._trigger_preview_update()
    
    def _clear_bg_image(self):
        """清除背景图片"""
        self.selected_bg_image = None
        self.bg_image_label.setText("未选择")
        self._trigger_auto_save()
        self._trigger_preview_update()
    
    def _choose_sound(self):
        """选择音效文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音效文件",
            "",
            "音频文件 (*.mp3 *.wav *.ogg *.flac *.aac *.m4a *.wma);;所有文件 (*.*)"
        )
        if file_path:
            self.selected_sound = file_path
            import os
            self.sound_label.setText(os.path.basename(file_path))
            self._trigger_auto_save()
    
    def _clear_sound(self):
        """清除音效"""
        self.selected_sound = None
        self.sound_label.setText("未选择")
        self._trigger_auto_save()
    
    def _on_volume_changed(self, value):
        """音量滑块值改变"""
        self.volume_label.setText(f"{value}%")
        self._trigger_auto_save()
    
    def _test_sound(self):
        """试听音效"""
        if not self.selected_sound:
            QMessageBox.information(self, "提示", "请先选择音效文件")
            return
        
        try:
            from ui.sound_manager import SoundManager
            sound_manager = SoundManager.get_instance()
            # 设置音量（0.0 - 1.0）
            volume = self.volume_slider.value() / 100.0
            sound_manager.set_volume(volume)
            sound_manager.play(self.selected_sound)
        except Exception as e:
            QMessageBox.warning(self, "播放失败", f"无法播放音效: {e}")
    
    def _choose_custom_font(self):
        """选择自定义字体"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字体文件",
            "",
            "字体文件 (*.ttf *.otf *.ttc *.woff *.woff2);;所有文件 (*.*)"
        )
        if file_path:
            self.selected_custom_font = file_path
            import os
            self.custom_font_label.setText(os.path.basename(file_path))
            self._trigger_auto_save()
            self._trigger_preview_update()
    
    def _clear_custom_font(self):
        """清除自定义字体"""
        self.selected_custom_font = None
        self.custom_font_label.setText("使用默认字体")
        self._trigger_auto_save()
        self._trigger_preview_update()
    
    def _choose_color(self, color_type):
        """选择颜色"""
        # 对于消息源背景色，支持透明度选择
        if color_type == 'source_bg':
            color = QColorDialog.getColor(options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        else:
            color = QColorDialog.getColor()
            
        if color.isValid():
            if color_type == 'source_bg':
                # 转换为 rgba 格式
                r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
                self.source_bg_color = f"rgba({r}, {g}, {b}, {a/255:.2f})"
                self.source_bg_color_btn.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a}); border: 1px solid #ccc; border-radius: 4px;")
            else:
                color_hex = color.name()
                if color_type == 'title':
                    self.title_color = color_hex
                    self.title_color_btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 4px;")
                elif color_type == 'content':
                    self.content_color = color_hex
                    self.content_color_btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 4px;")
                elif color_type == 'source':
                    self.source_color = color_hex
                    self.source_color_btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 4px;")
                elif color_type == 'time':
                    self.time_color = color_hex
                    self.time_color_btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 4px;")
            self._trigger_auto_save()
            self._trigger_preview_update()
    
    def _create_animation_configs(self):
        """创建各种动画的配置控件"""
        # 滑入动画配置
        self.slide_config = QWidget()
        slide_layout = QGridLayout()
        slide_layout.setContentsMargins(0, 0, 0, 0)
        self.slide_config.setLayout(slide_layout)
        
        slide_layout.addWidget(QLabel("滑入方向:"), 0, 0)
        self.slide_direction_combo = QComboBox()
        self.slide_direction_combo.addItems(["从右向左", "从左向右", "从下往上", "从上往下"])
        self.slide_direction_combo.currentIndexChanged.connect(self._on_config_changed)
        slide_layout.addWidget(self.slide_direction_combo, 0, 1)
        
        # 淡入动画配置
        self.fade_config = QWidget()
        fade_layout = QGridLayout()
        fade_layout.setContentsMargins(0, 0, 0, 0)
        self.fade_config.setLayout(fade_layout)
        
        fade_layout.addWidget(QLabel("起始透明度:"), 0, 0)
        fade_opacity_layout = QHBoxLayout()
        self.fade_start_opacity = QSlider(Qt.Orientation.Horizontal)
        self.fade_start_opacity.setRange(0, 100)
        self.fade_start_opacity.setValue(0)
        self.fade_start_opacity.valueChanged.connect(self._on_config_changed)
        fade_opacity_layout.addWidget(self.fade_start_opacity)
        self.fade_opacity_label = QLabel("0%")
        self.fade_start_opacity.valueChanged.connect(
            lambda v: self.fade_opacity_label.setText(f"{v}%")
        )
        fade_opacity_layout.addWidget(self.fade_opacity_label)
        fade_layout.addLayout(fade_opacity_layout, 0, 1)
        
        # 缩放动画配置
        self.scale_config = QWidget()
        scale_layout = QGridLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        self.scale_config.setLayout(scale_layout)
        
        scale_layout.addWidget(QLabel("起始缩放:"), 0, 0)
        scale_size_layout = QHBoxLayout()
        self.scale_start_size = QSlider(Qt.Orientation.Horizontal)
        self.scale_start_size.setRange(0, 100)
        self.scale_start_size.setValue(50)
        self.scale_start_size.valueChanged.connect(self._on_config_changed)
        scale_size_layout.addWidget(self.scale_start_size)
        self.scale_size_label = QLabel("50%")
        self.scale_start_size.valueChanged.connect(
            lambda v: self.scale_size_label.setText(f"{v}%")
        )
        scale_size_layout.addWidget(self.scale_size_label)
        scale_layout.addLayout(scale_size_layout, 0, 1)
        
        scale_layout.addWidget(QLabel("缩放中心:"), 1, 0)
        self.scale_center_combo = QComboBox()
        self.scale_center_combo.addItems(["中心", "左上", "右上", "左下", "右下"])
        self.scale_center_combo.currentIndexChanged.connect(self._on_config_changed)
        scale_layout.addWidget(self.scale_center_combo, 1, 1)
        
        # 保存所有配置widget
        self.animation_configs = {
            0: self.slide_config,    # slide
            1: self.fade_config,     # fade
            2: self.scale_config     # scale
        }
    
    def _on_animation_type_changed(self, index):
        """动画类型改变时切换配置界面"""
        # 清空当前配置区域
        while self.animation_config_layout.count():
            item = self.animation_config_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 添加对应的配置widget
        if index in self.animation_configs:
            config_widget = self.animation_configs[index]
            self.animation_config_layout.addWidget(config_widget)
            
            # 添加说明标签
            hint_texts = {
                0: "配置滑入动画的方向",
                1: "配置淡入动画的起始透明度",
                2: "配置缩放动画的起始大小和中心点",
                3: "配置弹跳动画的方向和强度",
                4: "配置弹性动画的方向和强度"
            }
            hint_text = hint_texts.get(index, "")
            if hint_text:
                hint = IconLabel("lightbulb", hint_text, "#6C757D", 14)
                hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
            else:
                hint = QLabel("")
            hint.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
            self.animation_config_layout.addWidget(hint)
        
        self._on_config_changed()
    
    def _play_preview_animation(self):
        """播放预览动画"""
        # 播放音效（如果有）
        if self.selected_sound:
            from ui.sound_manager import SoundManager
            sound_manager = SoundManager.get_instance()
            sound_manager.play(self.selected_sound)
        
        # 先更新预览以确保使用最新的配置
        self._update_preview()
        # 然后播放动画
        self.preview_widget.play_animation()
    
    def _choose_preview_bg(self):
        """选择预览背景图"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择预览背景图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg);;所有文件 (*.*)"
        )
        if file_path:
            self.preview_bg_image = file_path
            import os
            self.preview_bg_label.setText(os.path.basename(file_path))
            self._update_preview_container_bg()
    
    def _clear_preview_bg(self):
        """清除预览背景图"""
        self.preview_bg_image = None
        self.preview_bg_label.setText("默认背景")
        self._update_preview_container_bg()
    
    def _update_preview_container_bg(self):
        """更新预览容器背景"""
        if self.preview_bg_image:
            # Qt的QSS不支持background-size，只能使用默认的平铺或拉伸
            self.preview_container.setStyleSheet(f"""
                QFrame {{
                    background-image: url({self.preview_bg_image});
                    border: none;
                    border-radius: 12px;
                }}
            """)
        else:
            self.preview_container.setStyleSheet("""
                QFrame {
                    background-color: #1A1D23;
                    border: none;
                    border-radius: 12px;
                }
            """)
    
    def _add_copy_rule(self):
        """添加复制规则"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel
        
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加复制规则")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 规则名称
        layout.addWidget(QLabel("规则名称:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("例如：验证码、邮箱、手机号")
        layout.addWidget(name_input)
        
        # 正则表达式
        layout.addWidget(QLabel("正则表达式:"))
        pattern_input = QLineEdit()
        pattern_input.setPlaceholderText("例如：\\b\\d{4,8}\\b (留空则复制完整内容)")
        layout.addWidget(pattern_input)
        
        # 提示信息
        from ui.icon_label import IconLabel
        hint = IconLabel("lightbulb", "提示：使用正则表达式匹配需要复制的内容\n如果有捕获组()，将复制第一个捕获组的内容", "#6C757D", 14)
        hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px;")
        hint.text_label.setWordWrap(True)
        layout.addWidget(hint)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text().strip()
            pattern = pattern_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "错误", "规则名称不能为空")
                return
            
            # 名称不能包含冒号（列表项以"名称: 正则"格式存储，冒号会破坏解析）
            if ':' in name or '：' in name:
                QMessageBox.warning(self, "错误", "规则名称不能包含冒号")
                return
            
            # 验证正则表达式
            if pattern:
                try:
                    import re
                    re.compile(pattern)
                except re.error as e:
                    QMessageBox.warning(self, "错误", f"正则表达式无效: {e}")
                    return
            
            # 添加到列表
            rule_text = f"{name}: {pattern if pattern else '完整内容'}"
            self.copy_rules_list.addItem(rule_text)
            self._on_config_changed()
    
    def _edit_copy_rule(self):
        """编辑复制规则"""
        current_item = self.copy_rules_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请先选择要编辑的规则")
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel
        
        # 解析当前规则
        rule_text = current_item.text()
        parts = rule_text.split(": ", 1)
        old_name = parts[0] if len(parts) > 0 else ""
        old_pattern = parts[1] if len(parts) > 1 and parts[1] != "完整内容" else ""
        
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑复制规则")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 规则名称
        layout.addWidget(QLabel("规则名称:"))
        name_input = QLineEdit(old_name)
        name_input.setPlaceholderText("例如：验证码、邮箱、手机号")
        layout.addWidget(name_input)
        
        # 正则表达式
        layout.addWidget(QLabel("正则表达式:"))
        pattern_input = QLineEdit(old_pattern)
        pattern_input.setPlaceholderText("例如：\\b\\d{4,8}\\b (留空则复制完整内容)")
        layout.addWidget(pattern_input)
        
        # 提示信息
        from ui.icon_label import IconLabel
        hint = IconLabel("lightbulb", "提示：使用正则表达式匹配需要复制的内容\n如果有捕获组()，将复制第一个捕获组的内容", "#6C757D", 14)
        hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px;")
        hint.text_label.setWordWrap(True)
        layout.addWidget(hint)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text().strip()
            pattern = pattern_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "错误", "规则名称不能为空")
                return
            
            # 名称不能包含冒号（列表项以"名称: 正则"格式存储，冒号会破坏解析）
            if ':' in name or '：' in name:
                QMessageBox.warning(self, "错误", "规则名称不能包含冒号")
                return
            
            # 验证正则表达式
            if pattern:
                try:
                    import re
                    re.compile(pattern)
                except re.error as e:
                    QMessageBox.warning(self, "错误", f"正则表达式无效: {e}")
                    return
            
            # 更新规则
            rule_text = f"{name}: {pattern if pattern else '完整内容'}"
            current_item.setText(rule_text)
            self._on_config_changed()
    
    def _delete_copy_rule(self):
        """删除复制规则"""
        current_row = self.copy_rules_list.currentRow()
        if current_row >= 0:
            self.copy_rules_list.takeItem(current_row)
            self._on_config_changed()
        else:
            QMessageBox.information(self, "提示", "请先选择要删除的规则")
    
    def _add_preset_rule(self, name: str, pattern: str):
        """添加预设规则"""
        rule_text = f"{name}: {pattern}"
        self.copy_rules_list.addItem(rule_text)
        self._on_config_changed()
    
    def _move_rule_up(self):
        """上移选中的规则（提高优先级）"""
        current_row = self.copy_rules_list.currentRow()
        if current_row > 0:  # 不是第一个
            item = self.copy_rules_list.takeItem(current_row)
            self.copy_rules_list.insertItem(current_row - 1, item)
            self.copy_rules_list.setCurrentRow(current_row - 1)
            self._on_config_changed()
    
    def _move_rule_down(self):
        """下移选中的规则（降低优先级）"""
        current_row = self.copy_rules_list.currentRow()
        if current_row >= 0 and current_row < self.copy_rules_list.count() - 1:  # 不是最后一个
            item = self.copy_rules_list.takeItem(current_row)
            self.copy_rules_list.insertItem(current_row + 1, item)
            self.copy_rules_list.setCurrentRow(current_row + 1)
            self._on_config_changed()
    
    def _load_config(self):
        """加载配置"""
        try:
            # 设置标志，阻止加载配置时触发自动保存
            self._loading_config = True
            
            popup_config = self.config_manager.get("popup", {})
            
            # 尺寸
            self.width_spin.setValue(popup_config.get("width", 400))
            self.height_spin.setValue(popup_config.get("height", 120))
            
            # 文本溢出处理
            title_overflow = popup_config.get("title_text_overflow", "ellipsis")
            overflow_map = {"ellipsis": 0, "wrap": 1}
            self.title_overflow_combo.setCurrentIndex(overflow_map.get(title_overflow, 0))
            
            content_overflow = popup_config.get("content_text_overflow", "wrap")
            self.content_overflow_combo.setCurrentIndex(overflow_map.get(content_overflow, 1))
            
            # 最大行数
            self.title_max_lines_spin.setValue(popup_config.get("title_max_lines", 2))
            self.content_max_lines_spin.setValue(popup_config.get("content_max_lines", 5))
            
            # 位置
            position = popup_config.get("position", "top_right")
            self._select_position(position)
            
            # 显示
            self.duration_spin.setValue(popup_config.get("display_duration", 5000))
            self.animation_spin.setValue(popup_config.get("animation_duration", 400))
            self.max_popups_spin.setValue(popup_config.get("max_popups", 5))
            self.auto_copy_check.setChecked(popup_config.get("auto_copy", False))
            
            # 加载复制模式
            copy_mode = popup_config.get("copy_mode", "on_click")  # on_click 或 auto
            if copy_mode == "auto":
                self.copy_auto_radio.setChecked(True)
            else:
                self.copy_on_click_radio.setChecked(True)
            
            # 加载复制规则
            self.copy_rules_list.clear()
            copy_rules = popup_config.get("copy_rules", [])
            for rule in copy_rules:
                name = rule.get("name", "")
                pattern = rule.get("pattern", "")
                rule_text = f"{name}: {pattern if pattern else '完整内容'}"
                self.copy_rules_list.addItem(rule_text)
            
            # 样式
            opacity = int(popup_config.get("opacity", 0.98) * 100)
            self.opacity_slider.setValue(opacity)
            
            bg_color = popup_config.get("background_color", "#2A3139")
            self.selected_color = bg_color
            self.color_preview.setStyleSheet(
                f"background-color: {bg_color}; border: 2px solid #E1E8ED; border-radius: 4px;"
            )
            
            # 背景图片
            self.selected_bg_image = popup_config.get("background_image", None)
            if self.selected_bg_image:
                import os
                self.bg_image_label.setText(os.path.basename(self.selected_bg_image))
            else:
                self.bg_image_label.setText("未选择")
            
            # 圆角值
            self.border_radius_spin.setValue(popup_config.get("border_radius", 12))
            
            animation_type = popup_config.get("animation_type", "slide")
            animation_map = {"slide": 0, "fade": 1, "scale": 2}
            self.animation_combo.setCurrentIndex(animation_map.get(animation_type, 0))
            
            # 加载动画配置
            anim_config = popup_config.get("animation_config", {})
            
            # 滑入配置
            slide_dir = anim_config.get("slide_direction", "right_to_left")
            slide_dir_map = {"right_to_left": 0, "left_to_right": 1, "bottom_to_top": 2, "top_to_bottom": 3}
            self.slide_direction_combo.setCurrentIndex(slide_dir_map.get(slide_dir, 0))
            
            # 淡入配置
            self.fade_start_opacity.setValue(int(anim_config.get("fade_start_opacity", 0) * 100))
            
            # 缩放配置
            self.scale_start_size.setValue(int(anim_config.get("scale_start_size", 0.5) * 100))
            scale_center = anim_config.get("scale_center", "center")
            scale_center_map = {"center": 0, "top_left": 1, "top_right": 2, "bottom_left": 3, "bottom_right": 4}
            self.scale_center_combo.setCurrentIndex(scale_center_map.get(scale_center, 0))
            
            # 音效
            from utils.resource_path import get_resource_path
            import os
            
            configured_sound = popup_config.get("sound_file")
            
            # 如果配置为空或None，使用默认音效
            if not configured_sound:
                default_sound = get_resource_path("resources/sounds/default.mp3")
                if os.path.exists(default_sound):
                    self.selected_sound = default_sound
                else:
                    self.selected_sound = None
            else:
                # 处理相对路径（从配置文件读取的路径）
                if not os.path.isabs(configured_sound):
                    configured_sound = get_resource_path(configured_sound)
                
                # 检查文件是否存在
                if os.path.exists(configured_sound):
                    self.selected_sound = configured_sound
                else:
                    # 文件不存在，尝试使用默认音效
                    default_sound = get_resource_path("resources/sounds/default.mp3")
                    if os.path.exists(default_sound):
                        self.selected_sound = default_sound
                    else:
                        self.selected_sound = None
            
            if self.selected_sound:
                self.sound_label.setText(os.path.basename(self.selected_sound))
            else:
                self.sound_label.setText("未选择")
            
            # 加载音量配置
            sound_volume = popup_config.get("sound_volume", 50)
            # 阻塞信号，避免触发自动保存
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(sound_volume)
            self.volume_slider.blockSignals(False)
            self.volume_label.setText(f"{sound_volume}%")
            
            # 加载字体配置
            self.title_font_size.setValue(popup_config.get("title_font_size", 13))
            self.content_font_size.setValue(popup_config.get("content_font_size", 10))
            self.source_font_size.setValue(popup_config.get("source_font_size", 9))
            
            # 自定义字体
            self.selected_custom_font = popup_config.get("custom_font_file", None)
            if self.selected_custom_font:
                import os
                self.custom_font_label.setText(os.path.basename(self.selected_custom_font))
            else:
                self.custom_font_label.setText("使用默认字体")
            
            # 加载颜色配置
            self.title_color = popup_config.get("title_color", "#FFFFFF")
            self.title_color_btn.setStyleSheet(f"background-color: {self.title_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            self.content_color = popup_config.get("content_color", "#B8BFC6")
            self.content_color_btn.setStyleSheet(f"background-color: {self.content_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            self.source_color = popup_config.get("source_color", "#4A9EFF")
            self.source_color_btn.setStyleSheet(f"background-color: {self.source_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            # 加载消息源背景色
            self.source_bg_color = popup_config.get("source_bg_color", "rgba(74, 158, 255, 0.15)")
            # 尝试解析 rgba 值用于按钮显示
            try:
                if self.source_bg_color.startswith("rgba"):
                    # 提取 rgba 值
                    import re
                    match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', self.source_bg_color)
                    if match:
                        r, g, b, a = match.groups()
                        a_int = int(float(a) * 255)
                        self.source_bg_color_btn.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a_int}); border: 1px solid #ccc; border-radius: 4px;")
                    else:
                        self.source_bg_color_btn.setStyleSheet(f"background-color: rgba(74, 158, 255, 38); border: 1px solid #ccc; border-radius: 4px;")
                else:
                    self.source_bg_color_btn.setStyleSheet(f"background-color: {self.source_bg_color}; border: 1px solid #ccc; border-radius: 4px;")
            except:
                self.source_bg_color_btn.setStyleSheet(f"background-color: rgba(74, 158, 255, 38); border: 1px solid #ccc; border-radius: 4px;")
            
            self.time_color = popup_config.get("time_color", "#6C757D")
            self.time_color_btn.setStyleSheet(f"background-color: {self.time_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            # 加载文本对齐配置
            title_align = popup_config.get("title_align", "left")
            align_map = {"left": 0, "center": 1, "right": 2}
            self.title_align_combo.setCurrentIndex(align_map.get(title_align, 0))
            
            content_align = popup_config.get("content_align", "left")
            self.content_align_combo.setCurrentIndex(align_map.get(content_align, 0))
            
            time_align = popup_config.get("time_align", "left")
            self.time_align_combo.setCurrentIndex(align_map.get(time_align, 0))
            
            # 加载时间格式配置
            time_format = popup_config.get("time_format", "%H:%M:%S")
            time_format_map = {
                "%H:%M:%S": 0,
                "%H:%M": 1,
                "%Y-%m-%d %H:%M:%S": 2,
                "%Y-%m-%d %H:%M": 3,
                "%m-%d %H:%M": 4,
                "%Y年%m月%d日 %H:%M:%S": 5,
                "%I:%M:%S %p": 6,
                "%I:%M %p": 7
            }
            self.time_format_combo.setCurrentIndex(time_format_map.get(time_format, 0))
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置失败: {e}")
        finally:
            # 清除标志，恢复自动保存
            self._loading_config = False
    
    def _connect_signals(self):
        """连接所有控件的信号"""
        # 尺寸控件
        self.width_spin.valueChanged.connect(self._on_config_changed)
        self.height_spin.valueChanged.connect(self._on_config_changed)
        self.title_overflow_combo.currentIndexChanged.connect(self._on_config_changed)
        self.content_overflow_combo.currentIndexChanged.connect(self._on_config_changed)
        self.title_max_lines_spin.valueChanged.connect(self._on_config_changed)
        self.content_max_lines_spin.valueChanged.connect(self._on_config_changed)
        
        # 位置按钮
        for btn in self.position_buttons.values():
            btn.clicked.connect(self._on_config_changed)
        
        # 显示控件
        self.duration_spin.valueChanged.connect(self._on_config_changed)
        self.animation_spin.valueChanged.connect(self._on_config_changed)
        self.max_popups_spin.valueChanged.connect(self._on_config_changed)
        self.auto_copy_check.stateChanged.connect(self._on_config_changed)
        self.copy_on_click_radio.toggled.connect(self._on_config_changed)
        self.copy_auto_radio.toggled.connect(self._on_config_changed)
        
        # 样式控件
        self.opacity_slider.valueChanged.connect(self._on_config_changed)
        self.animation_combo.currentIndexChanged.connect(self._on_config_changed)
        self.border_radius_spin.valueChanged.connect(self._on_config_changed)
        
        # 字体控件
        self.title_font_size.valueChanged.connect(self._on_config_changed)
        self.content_font_size.valueChanged.connect(self._on_config_changed)
        self.source_font_size.valueChanged.connect(self._on_config_changed)
        
        # 文本对齐控件
        self.title_align_combo.currentIndexChanged.connect(self._on_config_changed)
        self.content_align_combo.currentIndexChanged.connect(self._on_config_changed)
        self.time_align_combo.currentIndexChanged.connect(self._on_config_changed)
        
        # 时间格式控件
        self.time_format_combo.currentIndexChanged.connect(self._on_config_changed)
    
    def _on_config_changed(self):
        """配置改变时触发"""
        self._trigger_auto_save()
        self._trigger_preview_update()
    
    def force_save(self):
        """强制立即保存配置（用于页面切换或程序退出时）"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        logger.info("[弹窗设置] 开始强制保存配置...")
        
        # 停止定时器
        if hasattr(self, 'save_timer'):
            self.save_timer.stop()
            logger.debug("[弹窗设置] 已停止防抖定时器")
        
        # 立即保存（同步）
        try:
            self._auto_save_config()
            logger.info("[弹窗设置] 配置已更新到内存")
        except Exception as e:
            logger.error(f"[弹窗设置] 更新配置到内存失败: {e}", exc_info=True)
        
        # 强制异步配置管理器立即保存到文件
        try:
            self.async_config.force_save()
            logger.info("[弹窗设置] 配置已强制保存到文件")
        except Exception as e:
            logger.error(f"[弹窗设置] 强制保存到文件失败: {e}", exc_info=True)
    
    def _update_max_lines_visibility(self):
        """根据溢出模式更新最大行数配置的可见性"""
        # 标题：只有换行模式（索引1）才显示最大行数
        title_is_wrap = self.title_overflow_combo.currentIndex() == 1
        self.title_max_lines_label.setVisible(title_is_wrap)
        self.title_max_lines_spin.setVisible(title_is_wrap)
        
        # 内容：只有换行模式（索引1）才显示最大行数
        content_is_wrap = self.content_overflow_combo.currentIndex() == 1
        self.content_max_lines_label.setVisible(content_is_wrap)
        self.content_max_lines_spin.setVisible(content_is_wrap)
        
        # 提示信息：只有至少一个是换行模式才显示
        self.overflow_hint.setVisible(title_is_wrap or content_is_wrap)
    
    def _trigger_preview_update(self):
        """触发预览更新（防抖）"""
        self.preview_timer.stop()
        self.preview_timer.start(300)  # 300ms后更新预览，避免过于频繁
    
    def _update_preview(self):
        """更新预览"""
        try:
            # 获取动画类型
            animation_types = ["slide", "fade", "scale"]
            animation_type = animation_types[self.animation_combo.currentIndex()]
            
            # 获取文本溢出处理方式
            overflow_types = ["ellipsis", "wrap"]
            title_overflow = overflow_types[self.title_overflow_combo.currentIndex()]
            content_overflow = overflow_types[self.content_overflow_combo.currentIndex()]
            
            # 获取文本对齐方式
            align_types = ["left", "center", "right"]
            title_align = align_types[self.title_align_combo.currentIndex()]
            content_align = align_types[self.content_align_combo.currentIndex()]
            time_align = align_types[self.time_align_combo.currentIndex()]
            
            # 获取时间格式
            time_formats = [
                "%H:%M:%S",           # 时:分:秒
                "%H:%M",              # 时:分
                "%Y-%m-%d %H:%M:%S",  # 日期+时间
                "%Y-%m-%d %H:%M",     # 日期+时分
                "%m-%d %H:%M",        # 月-日 时:分
                "%Y年%m月%d日 %H:%M:%S",  # 完整日期时间
                "%I:%M:%S %p",        # 12小时制
                "%I:%M %p"            # 12小时制时分
            ]
            time_format = time_formats[self.time_format_combo.currentIndex()]
            
            # 更新时间格式预览
            self._update_time_format_preview()
            
            # 获取预览文本
            preview_source = self.preview_source_input.text() or "预览"
            preview_title = self.preview_title_input.text() or "这是弹窗标题"
            preview_content = self.preview_content_input.toPlainText() or "这是弹窗的内容预览文本，您可以实时看到配置的效果。"
            
            # 构建动画配置
            animation_config = {}
            
            # 滑入配置
            slide_dirs = ["right_to_left", "left_to_right", "bottom_to_top", "top_to_bottom"]
            animation_config["slide_direction"] = slide_dirs[self.slide_direction_combo.currentIndex()]
            
            # 淡入配置
            animation_config["fade_start_opacity"] = self.fade_start_opacity.value() / 100.0
            
            # 缩放配置
            animation_config["scale_start_size"] = self.scale_start_size.value() / 100.0
            scale_centers = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
            animation_config["scale_center"] = scale_centers[self.scale_center_combo.currentIndex()]
            
            # 获取自定义字体
            custom_font_family = None
            if self.selected_custom_font:
                # 加载自定义字体并获取字体家族名称
                from PyQt6.QtGui import QFontDatabase
                font_id = QFontDatabase.addApplicationFont(self.selected_custom_font)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        custom_font_family = font_families[0]
            
            self.preview_widget.update_preview(
                width=self.width_spin.value(),
                height=self.height_spin.value(),
                bg_color=self.selected_color,
                opacity=self.opacity_slider.value() / 100.0,
                title_size=self.title_font_size.value(),
                title_color=self.title_color,
                content_size=self.content_font_size.value(),
                content_color=self.content_color,
                source_size=self.source_font_size.value(),
                source_color=self.source_color,
                source_bg_color=self.source_bg_color,
                time_color=self.time_color,
                animation_type=animation_type,
                title_overflow=title_overflow,
                content_overflow=content_overflow,
                bg_image=self.selected_bg_image,
                border_radius=self.border_radius_spin.value(),
                animation_config=animation_config,
                preview_source_text=preview_source,
                preview_title_text=preview_title,
                preview_content_text=preview_content,
                title_align=title_align,
                content_align=content_align,
                time_align=time_align,
                time_format=time_format,
                custom_font_family=custom_font_family
            )
        except Exception as e:
            print(f"更新预览失败: {e}")
    
    def _trigger_auto_save(self):
        """触发自动保存（使用定时器防抖）"""
        # 如果正在加载配置，不触发保存
        if hasattr(self, '_loading_config') and self._loading_config:
            return
        
        if not hasattr(self, 'save_timer'):
            self.save_timer = QTimer()
            self.save_timer.setSingleShot(True)
            self.save_timer.timeout.connect(self._auto_save_config)
        
        # 防抖延迟500ms，避免频繁保存
        self.save_timer.stop()
        self.save_timer.start(500)  # 从100ms改为500ms
    
    def _auto_save_config(self):
        """自动保存配置（异步）"""
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            
            logger.info("[弹窗设置] 配置已修改，准备自动保存...")
            print("[弹窗设置] 配置已修改，准备自动保存...")
            
            # 添加调试：显示当前音量值
            current_volume = self.volume_slider.value()
            logger.info(f"[弹窗设置] 当前音量滑块值: {current_volume}%")
            
            # 获取选中的位置
            selected_position = None
            for pos_id, btn in self.position_buttons.items():
                if btn.isChecked():
                    selected_position = pos_id
                    break
            
            # 获取动画类型
            animation_types = ["slide", "fade", "scale"]
            animation_type = animation_types[self.animation_combo.currentIndex()]
            
            # 获取文本溢出处理方式
            overflow_types = ["ellipsis", "wrap"]
            title_overflow = overflow_types[self.title_overflow_combo.currentIndex()]
            content_overflow = overflow_types[self.content_overflow_combo.currentIndex()]
            
            # 使用异步配置管理器保存（批量）
            self.async_config.set("popup.width", self.width_spin.value())
            self.async_config.set("popup.height", self.height_spin.value())
            self.async_config.set("popup.title_text_overflow", title_overflow)
            self.async_config.set("popup.content_text_overflow", content_overflow)
            self.async_config.set("popup.title_max_lines", self.title_max_lines_spin.value())
            self.async_config.set("popup.content_max_lines", self.content_max_lines_spin.value())
            self.async_config.set("popup.position", selected_position)
            self.async_config.set("popup.display_duration", self.duration_spin.value())
            self.async_config.set("popup.animation_duration", self.animation_spin.value())
            self.async_config.set("popup.max_popups", self.max_popups_spin.value())
            self.async_config.set("popup.auto_copy", self.auto_copy_check.isChecked())
            
            # 保存复制模式
            copy_mode = "auto" if self.copy_auto_radio.isChecked() else "on_click"
            self.async_config.set("popup.copy_mode", copy_mode)
            
            # 保存复制规则
            copy_rules = []
            for i in range(self.copy_rules_list.count()):
                rule_text = self.copy_rules_list.item(i).text()
                parts = rule_text.split(": ", 1)
                if len(parts) == 2:
                    name = parts[0]
                    pattern = parts[1] if parts[1] != "完整内容" else ""
                    copy_rules.append({"name": name, "pattern": pattern})
            self.async_config.set("popup.copy_rules", copy_rules)
            
            self.async_config.set("popup.opacity", self.opacity_slider.value() / 100.0)
            self.async_config.set("popup.background_color", self.selected_color)
            self.async_config.set("popup.background_image", self.selected_bg_image)
            self.async_config.set("popup.border_radius", self.border_radius_spin.value())
            self.async_config.set("popup.animation_type", animation_type)
            self.async_config.set("popup.sound_file", self.selected_sound)
            self.async_config.set("popup.sound_volume", self.volume_slider.value())
            
            # 保存动画配置
            animation_config = {}
            
            # 滑入配置
            slide_dirs = ["right_to_left", "left_to_right", "bottom_to_top", "top_to_bottom"]
            animation_config["slide_direction"] = slide_dirs[self.slide_direction_combo.currentIndex()]
            
            # 淡入配置
            animation_config["fade_start_opacity"] = self.fade_start_opacity.value() / 100.0
            
            # 缩放配置
            animation_config["scale_start_size"] = self.scale_start_size.value() / 100.0
            scale_centers = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
            animation_config["scale_center"] = scale_centers[self.scale_center_combo.currentIndex()]
            
            self.async_config.set("popup.animation_config", animation_config)
            
            # 保存字体配置
            self.async_config.set("popup.title_font_size", self.title_font_size.value())
            self.async_config.set("popup.content_font_size", self.content_font_size.value())
            self.async_config.set("popup.source_font_size", self.source_font_size.value())
            self.async_config.set("popup.custom_font_file", self.selected_custom_font)
            
            # 保存颜色配置
            self.async_config.set("popup.title_color", self.title_color)
            self.async_config.set("popup.content_color", self.content_color)
            self.async_config.set("popup.source_color", self.source_color)
            self.async_config.set("popup.source_bg_color", self.source_bg_color)
            self.async_config.set("popup.time_color", self.time_color)
            
            # 保存文本对齐配置
            align_types = ["left", "center", "right"]
            self.async_config.set("popup.title_align", align_types[self.title_align_combo.currentIndex()])
            self.async_config.set("popup.content_align", align_types[self.content_align_combo.currentIndex()])
            self.async_config.set("popup.time_align", align_types[self.time_align_combo.currentIndex()])
            
            # 保存时间格式配置
            time_formats = [
                "%H:%M:%S",
                "%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%m-%d %H:%M",
                "%Y年%m月%d日 %H:%M:%S",
                "%I:%M:%S %p",
                "%I:%M %p"
            ]
            self.async_config.set("popup.time_format", time_formats[self.time_format_combo.currentIndex()])
            
            logger.info("[弹窗设置] 配置已更新到内存，等待写入文件...")
            
        except Exception as e:
            print(f"自动保存配置失败: {e}")
            logger.error(f"自动保存配置失败: {e}", exc_info=True)
    
    def _preview_popup(self):
        """预览弹窗"""
        try:
            from data.models import Message
            from ui.notification_popup import NotificationPopup, PopupStyle, PopupPosition
            import time
            
            # 获取选中的位置
            selected_position = "top_right"
            for pos_id, btn in self.position_buttons.items():
                if btn.isChecked():
                    selected_position = pos_id
                    break
            
            # 创建测试消息
            message = Message(
                id="preview",
                source="预览",
                title="这是一个预览弹窗",
                content="这是弹窗的内容预览。您可以在这里看到弹窗的实际效果。",
                timestamp=time.time(),
                metadata={}
            )
            
            # 位置映射
            position_map = {
                "top_left": PopupPosition.TOP_LEFT,
                "top_center": PopupPosition.TOP_CENTER,
                "top_right": PopupPosition.TOP_RIGHT,
                "center_left": PopupPosition.CENTER_LEFT,
                "center": PopupPosition.CENTER,
                "center_right": PopupPosition.CENTER_RIGHT,
                "bottom_left": PopupPosition.BOTTOM_LEFT,
                "bottom_center": PopupPosition.BOTTOM_CENTER,
                "bottom_right": PopupPosition.BOTTOM_RIGHT,
            }
            
            # 创建弹窗样式
            style = PopupStyle(
                width=self.width_spin.value(),
                height=self.height_spin.value(),
                position=position_map.get(selected_position, PopupPosition.TOP_RIGHT),
                opacity=self.opacity_slider.value() / 100.0,
                background_color=self.selected_color,
                display_duration=self.duration_spin.value()
            )
            
            # 显示弹窗
            popup = NotificationPopup(message, style)
            popup.show()
            popup.set_auto_close(self.duration_spin.value())
            
        except Exception as e:
            QMessageBox.warning(self, "预览失败", f"无法显示预览: {e}")
    
    def _create_font_card(self) -> QFrame:
        """创建字体设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("字体设置")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_font_btn = QPushButton("  恢复默认")
        reset_font_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_font_btn.setProperty("secondary", "true")
        reset_font_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_font_btn.clicked.connect(self._reset_font_defaults)
        header_layout.addWidget(reset_font_btn)
        
        layout.addLayout(header_layout)
        
        # 自定义字体
        font_upload_layout = QHBoxLayout()
        font_upload_layout.addWidget(QLabel("自定义字体:"))
        self.custom_font_btn = QPushButton("上传字体")
        self.custom_font_btn.clicked.connect(self._choose_custom_font)
        font_upload_layout.addWidget(self.custom_font_btn)
        self.custom_font_label = QLabel("使用默认字体")
        self.custom_font_label.setStyleSheet("color: #6C757D; font-size: 11px;")
        font_upload_layout.addWidget(self.custom_font_label)
        self.clear_font_btn = QPushButton("清除")
        self.clear_font_btn.clicked.connect(self._clear_custom_font)
        self.clear_font_btn.setProperty("secondary", "true")
        font_upload_layout.addWidget(self.clear_font_btn)
        font_upload_layout.addStretch()
        layout.addLayout(font_upload_layout)
        
        # 说明
        hint = IconLabel("lightbulb", "上传自定义字体后将应用到弹窗所有文本", "#6C757D", 14)
        hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
        layout.addWidget(hint)
        
        grid = QGridLayout()
        
        # 标题字体大小
        grid.addWidget(QLabel("标题字体大小:"), 0, 0)
        self.title_font_size = QSpinBox()
        self.title_font_size.setRange(8, 32)
        self.title_font_size.setValue(13)
        self.title_font_size.setSuffix(" px")
        grid.addWidget(self.title_font_size, 0, 1)
        
        # 内容字体大小
        grid.addWidget(QLabel("内容字体大小:"), 1, 0)
        self.content_font_size = QSpinBox()
        self.content_font_size.setRange(8, 24)
        self.content_font_size.setValue(10)
        self.content_font_size.setSuffix(" px")
        grid.addWidget(self.content_font_size, 1, 1)
        
        # 消息源字体大小
        grid.addWidget(QLabel("消息源字体大小:"), 2, 0)
        self.source_font_size = QSpinBox()
        self.source_font_size.setRange(6, 16)
        self.source_font_size.setValue(9)
        self.source_font_size.setSuffix(" px")
        grid.addWidget(self.source_font_size, 2, 1)
        
        layout.addLayout(grid)
        
        # 初始化变量
        self.selected_custom_font = None
        
        return card
    
    def _create_color_card(self) -> QFrame:
        """创建颜色设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("颜色设置")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_color_btn = QPushButton("  恢复默认")
        reset_color_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_color_btn.setProperty("secondary", "true")
        reset_color_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_color_btn.clicked.connect(self._reset_color_defaults)
        header_layout.addWidget(reset_color_btn)
        
        layout.addLayout(header_layout)
        
        grid = QGridLayout()
        
        # 标题颜色
        grid.addWidget(QLabel("标题颜色:"), 0, 0)
        self.title_color_btn = QPushButton()
        self.title_color_btn.setFixedSize(80, 30)
        self.title_color_btn.clicked.connect(lambda: self._choose_color('title'))
        self.title_color = "#FFFFFF"
        self.title_color_btn.setStyleSheet(f"background-color: {self.title_color}; border: 1px solid #ccc; border-radius: 4px;")
        grid.addWidget(self.title_color_btn, 0, 1)
        
        # 内容颜色
        grid.addWidget(QLabel("内容颜色:"), 1, 0)
        self.content_color_btn = QPushButton()
        self.content_color_btn.setFixedSize(80, 30)
        self.content_color_btn.clicked.connect(lambda: self._choose_color('content'))
        self.content_color = "#B8BFC6"
        self.content_color_btn.setStyleSheet(f"background-color: {self.content_color}; border: 1px solid #ccc; border-radius: 4px;")
        grid.addWidget(self.content_color_btn, 1, 1)
        
        # 消息源颜色
        grid.addWidget(QLabel("消息源颜色:"), 2, 0)
        self.source_color_btn = QPushButton()
        self.source_color_btn.setFixedSize(80, 30)
        self.source_color_btn.clicked.connect(lambda: self._choose_color('source'))
        self.source_color = "#4A9EFF"
        self.source_color_btn.setStyleSheet(f"background-color: {self.source_color}; border: 1px solid #ccc; border-radius: 4px;")
        grid.addWidget(self.source_color_btn, 2, 1)
        
        # 消息源背景色
        grid.addWidget(QLabel("消息源背景色:"), 3, 0)
        self.source_bg_color_btn = QPushButton()
        self.source_bg_color_btn.setFixedSize(80, 30)
        self.source_bg_color_btn.clicked.connect(lambda: self._choose_color('source_bg'))
        self.source_bg_color = "rgba(74, 158, 255, 0.15)"
        # 将 rgba 转换为十六进制用于按钮显示
        self.source_bg_color_btn.setStyleSheet(f"background-color: rgba(74, 158, 255, 38); border: 1px solid #ccc; border-radius: 4px;")
        grid.addWidget(self.source_bg_color_btn, 3, 1)
        
        # 时间颜色
        grid.addWidget(QLabel("时间颜色:"), 4, 0)
        self.time_color_btn = QPushButton()
        self.time_color_btn.setFixedSize(80, 30)
        self.time_color_btn.clicked.connect(lambda: self._choose_color('time'))
        self.time_color = "#6C757D"
        self.time_color_btn.setStyleSheet(f"background-color: {self.time_color}; border: 1px solid #ccc; border-radius: 4px;")
        grid.addWidget(self.time_color_btn, 4, 1)
        
        layout.addLayout(grid)
        
        return card
    
    def _reset_to_defaults(self):
        """恢复所有默认设置"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要恢复所有默认设置吗？这将重置所有弹窗配置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 调用各个部分的恢复默认方法（不显示单独的提示）
            # 基本设置
            self.width_spin.setValue(400)
            self.height_spin.setValue(120)
            self.title_overflow_combo.setCurrentIndex(0)  # 省略号
            self.content_overflow_combo.setCurrentIndex(1)  # 自动换行
            self.title_max_lines_spin.setValue(2)  # 标题最多2行
            self.content_max_lines_spin.setValue(5)  # 内容最多5行
            self._select_position("top_right")
            self.duration_spin.setValue(5000)
            self.animation_spin.setValue(400)
            self.max_popups_spin.setValue(5)  # 最多5个弹窗
            self.auto_copy_check.setChecked(False)
            self.copy_on_click_radio.setChecked(True)  # 默认点击复制模式
            
            # 清空复制规则
            self.copy_rules_list.clear()
            
            # 样式设置
            self.opacity_slider.setValue(98)
            self.selected_color = "#2A3139"
            self.color_preview.setStyleSheet(
                "background-color: #2A3139; border: 2px solid #E1E8ED; border-radius: 4px;"
            )
            self.selected_bg_image = None
            self.bg_image_label.setText("未选择")
            self.border_radius_spin.setValue(12)
            self.animation_combo.setCurrentIndex(0)  # 滑入
            
            # 恢复默认音效
            from utils.resource_path import get_resource_path
            import os
            default_sound = get_resource_path("resources/sounds/default.mp3")
            if os.path.exists(default_sound):
                self.selected_sound = default_sound
                self.sound_label.setText(os.path.basename(default_sound))
            else:
                self.selected_sound = None
                self.sound_label.setText("未选择")
            
            # 恢复默认音量
            self.volume_slider.setValue(50)
            self.volume_label.setText("50%")
            # 手动触发保存，确保音量被保存
            self._trigger_auto_save()
            
            # 动画配置
            self.slide_direction_combo.setCurrentIndex(0)  # 从右向左
            self.fade_start_opacity.setValue(0)  # 0%
            self.scale_start_size.setValue(50)  # 50%
            self.scale_center_combo.setCurrentIndex(0)  # 中心
            
            # 字体设置
            self.title_font_size.setValue(13)
            self.content_font_size.setValue(10)
            self.source_font_size.setValue(9)
            self.selected_custom_font = None
            self.custom_font_label.setText("使用默认字体")
            
            # 颜色设置
            self.title_color = "#FFFFFF"
            self.title_color_btn.setStyleSheet(f"background-color: {self.title_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            self.content_color = "#B8BFC6"
            self.content_color_btn.setStyleSheet(f"background-color: {self.content_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            self.source_color = "#4A9EFF"
            self.source_color_btn.setStyleSheet(f"background-color: {self.source_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            self.source_bg_color = "rgba(74, 158, 255, 0.15)"
            self.source_bg_color_btn.setStyleSheet(f"background-color: rgba(74, 158, 255, 38); border: 1px solid #ccc; border-radius: 4px;")
            
            self.time_color = "#6C757D"
            self.time_color_btn.setStyleSheet(f"background-color: {self.time_color}; border: 1px solid #ccc; border-radius: 4px;")
            
            # 文本对齐设置
            self.title_align_combo.setCurrentIndex(0)  # 左对齐
            self.content_align_combo.setCurrentIndex(0)  # 左对齐
            self.time_align_combo.setCurrentIndex(0)  # 左对齐
            
            # 时间格式设置
            self.time_format_combo.setCurrentIndex(0)  # 时:分:秒
            
            # 预览文本自定义
            self.preview_source_input.setText("预览")
            self.preview_title_input.setText("这是弹窗标题")
            self.preview_content_input.setPlainText("这是弹窗的内容预览文本，您可以实时看到配置的效果。")
            
            # 强制立即保存配置
            self.force_save()
            
            QMessageBox.information(self, "成功", "所有设置已恢复默认")
    
    def _show_real_preview(self):
        """显示实际效果预览 - 在真实屏幕位置弹出"""
        try:
            from data.models import Message
            from ui.notification_popup import NotificationPopup, PopupStyle, PopupPosition
            import time
            
            # 获取选中的位置
            selected_position = "top_right"
            for pos_id, btn in self.position_buttons.items():
                if btn.isChecked():
                    selected_position = pos_id
                    break
            
            # 获取用户自定义的预览文本
            preview_source = self.preview_source_input.text() or "实际预览"
            preview_title = self.preview_title_input.text() or "这是实际效果预览"
            preview_content = self.preview_content_input.toPlainText() or "这是在真实屏幕位置显示的弹窗效果，包含动画和实际样式。"
            
            # 创建测试消息
            message = Message(
                id="real_preview",
                source=preview_source,
                title=preview_title,
                content=preview_content,
                timestamp=time.time(),
                metadata={}
            )
            
            # 位置映射
            position_map = {
                "top_left": PopupPosition.TOP_LEFT,
                "top_center": PopupPosition.TOP_CENTER,
                "top_right": PopupPosition.TOP_RIGHT,
                "center_left": PopupPosition.CENTER_LEFT,
                "center": PopupPosition.CENTER,
                "center_right": PopupPosition.CENTER_RIGHT,
                "bottom_left": PopupPosition.BOTTOM_LEFT,
                "bottom_center": PopupPosition.BOTTOM_CENTER,
                "bottom_right": PopupPosition.BOTTOM_RIGHT,
            }
            
            # 获取动画类型
            animation_types = ["slide", "fade", "scale"]
            animation_type = animation_types[self.animation_combo.currentIndex()]
            
            # 获取文本溢出处理方式
            overflow_types = ["ellipsis", "wrap"]
            title_overflow = overflow_types[self.title_overflow_combo.currentIndex()]
            content_overflow = overflow_types[self.content_overflow_combo.currentIndex()]
            
            # 获取文本对齐方式
            align_types = ["left", "center", "right"]
            title_align = align_types[self.title_align_combo.currentIndex()]
            content_align = align_types[self.content_align_combo.currentIndex()]
            time_align = align_types[self.time_align_combo.currentIndex()]
            
            # 获取时间格式
            time_formats = [
                "%H:%M:%S",
                "%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%m-%d %H:%M",
                "%Y年%m月%d日 %H:%M:%S",
                "%I:%M:%S %p",
                "%I:%M %p"
            ]
            time_format = time_formats[self.time_format_combo.currentIndex()]
            
            # 获取动画配置
            animation_config = {}
            
            # 滑入配置
            slide_dirs = ["right_to_left", "left_to_right", "bottom_to_top", "top_to_bottom"]
            animation_config["slide_direction"] = slide_dirs[self.slide_direction_combo.currentIndex()]
            
            # 淡入配置
            animation_config["fade_start_opacity"] = self.fade_start_opacity.value() / 100.0
            
            # 缩放配置
            animation_config["scale_start_size"] = self.scale_start_size.value() / 100.0
            scale_centers = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
            animation_config["scale_center"] = scale_centers[self.scale_center_combo.currentIndex()]
            
            
            # 创建弹窗样式
            style = PopupStyle(
                width=self.width_spin.value(),
                height=self.height_spin.value(),
                position=position_map.get(selected_position, PopupPosition.TOP_RIGHT),
                opacity=self.opacity_slider.value() / 100.0,
                background_color=self.selected_color,
                background_image=self.selected_bg_image,
                border_radius=self.border_radius_spin.value(),
                animation_type=animation_type,
                animation_duration=self.animation_spin.value(),
                animation_config=animation_config,
                display_duration=self.duration_spin.value(),
                auto_copy=self.auto_copy_check.isChecked(),
                copy_mode="auto" if self.copy_auto_radio.isChecked() else "on_click",
                sound_file=self.selected_sound,
                sound_volume=self.volume_slider.value(),  # 添加音量参数
                max_popups=self.max_popups_spin.value(),  # 添加最大弹窗数量参数
                # 字体配置
                title_font_size=self.title_font_size.value(),
                title_color=self.title_color,
                content_font_size=self.content_font_size.value(),
                content_color=self.content_color,
                source_font_size=self.source_font_size.value(),
                source_color=self.source_color,
                source_bg_color=self.source_bg_color,
                time_color=self.time_color,
                custom_font_file=self.selected_custom_font,
                # 文本溢出处理
                title_text_overflow=title_overflow,
                content_text_overflow=content_overflow,
                # 最大行数
                title_max_lines=self.title_max_lines_spin.value(),
                content_max_lines=self.content_max_lines_spin.value(),
                # 文本对齐方式
                title_align=title_align,
                content_align=content_align,
                time_align=time_align,
                # 时间格式
                time_format=time_format
            )
            
            # 显示弹窗
            popup = NotificationPopup(message, style)
            popup.show()
            popup.set_auto_close(self.duration_spin.value())
            
        except Exception as e:
            QMessageBox.warning(self, "预览失败", f"无法显示实际预览: {e}")

    
    def _create_align_card(self) -> QFrame:
        """创建文本对齐设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("文本对齐")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_align_btn = QPushButton("  恢复默认")
        reset_align_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_align_btn.setProperty("secondary", "true")
        reset_align_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_align_btn.clicked.connect(self._reset_align_defaults)
        header_layout.addWidget(reset_align_btn)
        
        layout.addLayout(header_layout)
        
        grid = QGridLayout()
        
        # 标题对齐
        grid.addWidget(QLabel("标题对齐:"), 0, 0)
        self.title_align_combo = QComboBox()
        self.title_align_combo.addItems(["左对齐", "居中", "右对齐"])
        self.title_align_combo.currentIndexChanged.connect(self._on_config_changed)
        grid.addWidget(self.title_align_combo, 0, 1)
        
        # 内容对齐
        grid.addWidget(QLabel("内容对齐:"), 1, 0)
        self.content_align_combo = QComboBox()
        self.content_align_combo.addItems(["左对齐", "居中", "右对齐"])
        self.content_align_combo.currentIndexChanged.connect(self._on_config_changed)
        grid.addWidget(self.content_align_combo, 1, 1)
        
        # 时间对齐
        grid.addWidget(QLabel("时间对齐:"), 2, 0)
        self.time_align_combo = QComboBox()
        self.time_align_combo.addItems(["左对齐", "居中", "右对齐"])
        self.time_align_combo.currentIndexChanged.connect(self._on_config_changed)
        grid.addWidget(self.time_align_combo, 2, 1)
        
        layout.addLayout(grid)
        
        return card
    
    def _create_time_format_card(self) -> QFrame:
        """创建时间格式设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和恢复按钮
        header_layout = QHBoxLayout()
        title = QLabel("时间格式")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        reset_time_btn = QPushButton("  恢复默认")
        reset_time_btn.setIcon(SvgIcon.get_icon("refresh", "#ABB2BF", 14))
        reset_time_btn.setProperty("secondary", "true")
        reset_time_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
            }
        """)
        reset_time_btn.clicked.connect(self._reset_time_format_defaults)
        header_layout.addWidget(reset_time_btn)
        
        layout.addLayout(header_layout)
        
        # 时间格式选择
        format_layout = QVBoxLayout()
        format_layout.setSpacing(5)
        
        format_label = QLabel("选择时间显示格式:")
        format_label.setStyleSheet("font-weight: 500;")
        format_layout.addWidget(format_label)
        
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems([
            "时:分:秒 (14:30:25)",
            "时:分 (14:30)",
            "日期+时间 (2026-02-01 14:30:25)",
            "日期+时分 (2026-02-01 14:30)",
            "月-日 时:分 (02-01 14:30)",
            "完整日期时间 (2026年02月01日 14:30:25)",
            "12小时制 (02:30:25 PM)",
            "12小时制时分 (02:30 PM)"
        ])
        self.time_format_combo.currentIndexChanged.connect(self._on_config_changed)
        format_layout.addWidget(self.time_format_combo)
        
        # 预览当前格式
        self.time_format_preview = QLabel()
        self.time_format_preview.setStyleSheet("""
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            color: #333;
            font-family: 'Consolas', 'Monaco', monospace;
        """)
        self.time_format_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        format_layout.addWidget(self.time_format_preview)
        
        # 更新预览
        self._update_time_format_preview()
        
        layout.addLayout(format_layout)
        
        hint = IconLabel("lightbulb", "时间格式会实时应用到弹窗中", "#6C757D", 14)
        hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
        layout.addWidget(hint)
        
        return card
    
    def _create_preview_text_card(self) -> QFrame:
        """创建预览文本自定义卡片"""
        from PyQt6.QtWidgets import QLineEdit, QTextEdit
        
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = QLabel("预览文本自定义")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        hint = IconLabel("lightbulb", "自定义预览弹窗中显示的文本内容", "#6C757D", 14)
        hint.text_label.setStyleSheet("color: #6C757D; font-size: 11px; padding: 5px 0;")
        layout.addWidget(hint)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # 消息源文本
        grid.addWidget(QLabel("消息源:"), 0, 0)
        self.preview_source_input = QLineEdit()
        self.preview_source_input.setPlaceholderText("预览")
        self.preview_source_input.setText("预览")
        self.preview_source_input.textChanged.connect(self._on_config_changed)
        grid.addWidget(self.preview_source_input, 0, 1)
        
        # 标题文本
        grid.addWidget(QLabel("标题:"), 1, 0)
        self.preview_title_input = QLineEdit()
        self.preview_title_input.setPlaceholderText("这是弹窗标题")
        self.preview_title_input.setText("这是弹窗标题")
        self.preview_title_input.textChanged.connect(self._on_config_changed)
        grid.addWidget(self.preview_title_input, 1, 1)
        
        layout.addLayout(grid)
        
        # 内容文本（使用多行文本框）
        content_label = QLabel("内容:")
        content_label.setStyleSheet("font-weight: 500; margin-top: 5px;")
        layout.addWidget(content_label)
        
        self.preview_content_input = QTextEdit()
        self.preview_content_input.setPlaceholderText("这是弹窗的内容预览文本，您可以实时看到配置的效果。")
        self.preview_content_input.setText("这是弹窗的内容预览文本，您可以实时看到配置的效果。")
        self.preview_content_input.setMaximumHeight(80)
        self.preview_content_input.textChanged.connect(self._on_config_changed)
        layout.addWidget(self.preview_content_input)
        
        # 重置按钮
        reset_btn = QPushButton("恢复默认文本")
        reset_btn.setProperty("secondary", "true")
        reset_btn.clicked.connect(self._reset_preview_text)
        layout.addWidget(reset_btn)
        
        return card
    
    def _update_time_format_preview(self):
        """更新时间格式预览"""
        formats = [
            "%H:%M:%S",           # 时:分:秒
            "%H:%M",              # 时:分
            "%Y-%m-%d %H:%M:%S",  # 日期+时间
            "%Y-%m-%d %H:%M",     # 日期+时分
            "%m-%d %H:%M",        # 月-日 时:分
            "%Y年%m月%d日 %H:%M:%S",  # 完整日期时间
            "%I:%M:%S %p",        # 12小时制
            "%I:%M %p"            # 12小时制时分
        ]
        
        index = self.time_format_combo.currentIndex()
        if 0 <= index < len(formats):
            try:
                preview_text = datetime.now().strftime(formats[index])
                self.time_format_preview.setText(f"预览: {preview_text}")
            except:
                self.time_format_preview.setText("预览: 格式错误")
    
    def _reset_preview_text(self):
        """重置预览文本为默认值"""
        self.preview_source_input.setText("预览")
        self.preview_title_input.setText("这是弹窗标题")
        self.preview_content_input.setText("这是弹窗的内容预览文本，您可以实时看到配置的效果。")
        self._on_config_changed()
    
    def _reset_size_defaults(self):
        """恢复尺寸设置默认值"""
        self.width_spin.setValue(400)
        self.height_spin.setValue(120)
        self.title_overflow_combo.setCurrentIndex(0)  # 裁剪
        self.content_overflow_combo.setCurrentIndex(1)  # 换行
        self.title_max_lines_spin.setValue(2)
        self.content_max_lines_spin.setValue(5)
        self._on_config_changed()
        QMessageBox.information(self, "成功", "尺寸设置已恢复默认")
    
    def _reset_position_defaults(self):
        """恢复位置设置默认值"""
        self._select_position("top_right")
        self._on_config_changed()
        QMessageBox.information(self, "成功", "位置设置已恢复默认")
    
    def _reset_display_defaults(self):
        """恢复显示设置默认值"""
        self.duration_spin.setValue(5000)
        self.animation_spin.setValue(400)
        self.max_popups_spin.setValue(5)  # 恢复最大弹窗数量
        self.auto_copy_check.setChecked(False)
        self.copy_on_click_radio.setChecked(True)
        self.copy_rules_list.clear()
        self._on_config_changed()
        QMessageBox.information(self, "成功", "显示设置已恢复默认")
    
    def _reset_style_defaults(self):
        """恢复样式设置默认值"""
        self.opacity_slider.setValue(98)
        self.selected_color = "#2A3139"
        self.color_preview.setStyleSheet(
            "background-color: #2A3139; border: 2px solid #E1E8ED; border-radius: 4px;"
        )
        self.selected_bg_image = None
        self.bg_image_label.setText("未选择")
        self.border_radius_spin.setValue(12)
        self.animation_combo.setCurrentIndex(0)  # 滑入
        
        # 恢复默认音效
        from utils.resource_path import get_resource_path
        import os
        default_sound = get_resource_path("resources/sounds/default.mp3")
        if os.path.exists(default_sound):
            self.selected_sound = default_sound
            self.sound_label.setText(os.path.basename(default_sound))
        else:
            self.selected_sound = None
            self.sound_label.setText("未选择")
        
        # 恢复默认音量
        self.volume_slider.setValue(50)
        self.volume_label.setText("50%")
        
        # 动画配置
        self.slide_direction_combo.setCurrentIndex(0)  # 从右向左
        self.fade_start_opacity.setValue(0)  # 0%
        self.scale_start_size.setValue(50)  # 50%
        self.scale_center_combo.setCurrentIndex(0)  # 中心
        
        self._on_config_changed()
        QMessageBox.information(self, "成功", "样式设置已恢复默认")
    
    def _reset_font_defaults(self):
        """恢复字体设置默认值"""
        self.title_font_size.setValue(13)
        self.content_font_size.setValue(10)
        self.source_font_size.setValue(9)
        self.selected_custom_font = None
        self.custom_font_label.setText("使用默认字体")
        self._on_config_changed()
        QMessageBox.information(self, "成功", "字体设置已恢复默认")
    
    def _reset_color_defaults(self):
        """恢复颜色设置默认值"""
        self.title_color = "#FFFFFF"
        self.title_color_btn.setStyleSheet(f"background-color: {self.title_color}; border: 1px solid #ccc; border-radius: 4px;")
        
        self.content_color = "#B8BFC6"
        self.content_color_btn.setStyleSheet(f"background-color: {self.content_color}; border: 1px solid #ccc; border-radius: 4px;")
        
        self.source_color = "#4A9EFF"
        self.source_color_btn.setStyleSheet(f"background-color: {self.source_color}; border: 1px solid #ccc; border-radius: 4px;")
        
        self.source_bg_color = "rgba(74, 158, 255, 0.15)"
        self.source_bg_color_btn.setStyleSheet(f"background-color: rgba(74, 158, 255, 38); border: 1px solid #ccc; border-radius: 4px;")
        
        self.time_color = "#6C757D"
        self.time_color_btn.setStyleSheet(f"background-color: {self.time_color}; border: 1px solid #ccc; border-radius: 4px;")
        
        self._on_config_changed()
        QMessageBox.information(self, "成功", "颜色设置已恢复默认")
    
    def _reset_align_defaults(self):
        """恢复文本对齐设置默认值"""
        self.title_align_combo.setCurrentIndex(0)  # 左对齐
        self.content_align_combo.setCurrentIndex(0)  # 左对齐
        self.time_align_combo.setCurrentIndex(0)  # 左对齐
        self._on_config_changed()
        QMessageBox.information(self, "成功", "文本对齐设置已恢复默认")
    
    def _reset_time_format_defaults(self):
        """恢复时间格式设置默认值"""
        self.time_format_combo.setCurrentIndex(0)  # 时:分:秒
        self._on_config_changed()
        QMessageBox.information(self, "成功", "时间格式设置已恢复默认")
