"""
WinMsgHub - 现代化主窗口
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QScrollArea, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QSize, QParallelAnimationGroup
from PyQt6.QtGui import QIcon, QPainter, QLinearGradient, QColor, QPen
from utils.logger import get_logger

logger = get_logger(__name__)


class ModernMainWindow(QMainWindow):
    """现代化主窗口 - 蓝色渐变风格"""
    
    closing = pyqtSignal()
    reload_connectors_requested = pyqtSignal()  # 新增信号
    
    def __init__(self, config_manager, database, message_processor, popup_manager=None, scheduler_manager=None, local_mqtt_manager=None):
        super().__init__()
        
        print("=" * 60)
        print("[ModernMainWindow] 初始化 - 版本: 2026-02-03-v3")
        print("[ModernMainWindow] 实时自动保存配置（50ms延迟）")
        print("=" * 60)
        
        self.config_manager = config_manager
        self.database = database
        self.message_processor = message_processor
        self.popup_manager = popup_manager
        self.scheduler_manager = scheduler_manager
        self.local_mqtt_manager = local_mqtt_manager  # 添加本地MQTT管理器
        
        logger.info("=" * 60)
        logger.info("ModernMainWindow 初始化 - 版本: 2026-02-03-v3")
        logger.info("实时自动保存配置（50ms延迟）")
        logger.info("=" * 60)
        
        self._setup_ui()
        self._apply_animations()
        logger.info("现代化主窗口已初始化")
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("WinMsgHub")
        self.setMinimumSize(1200, 800)
        # 设置初始窗口大小
        self.resize(1400, 900)
        
        # 设置窗口图标
        from PyQt6.QtGui import QIcon
        from utils.resource_path import get_resource_path
        icon_path = get_resource_path("resources/icons/WinMsgHub_ICON.ico")
        try:
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.warning(f"设置窗口图标失败: {e}")
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        
        # 左侧导航栏
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 右侧内容区
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)
        
        # 状态栏
        self.statusBar().showMessage("系统就绪 - 等待消息")
        
        # 定时更新状态栏
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status_bar)
        self._status_timer.start(10000)  # 每10秒更新一次
    
    def _create_sidebar(self) -> QFrame:
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #282C34,
                    stop:1 #21252B);
                border: none;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(15)
        sidebar.setLayout(layout)
        
        # Logo和标题区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Logo图标 - 使用ico文件
        logo_label = QLabel()
        from PyQt6.QtGui import QPixmap
        from utils.resource_path import get_resource_path
        logo_pixmap = QPixmap(get_resource_path("resources/icons/WinMsgHub_ICON.ico"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            # 如果图标加载失败，显示文字
            logo_label.setText("WinMsgHub")
            logo_label.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    font-weight: 700;
                    color: #4A9EFF;
                    padding: 0;
                }
            """)
        header_layout.addWidget(logo_label)
        
        # 标题和副标题容器
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        # 标题
        title_label = QLabel("WinMsgHub")
        title_label.setProperty("heading", "h1")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: 700;
                padding: 0;
            }
        """)
        title_container.addWidget(title_label)
        
        # 副标题
        subtitle = QLabel("Windows 消息聚合中心")
        subtitle.setStyleSheet("""
            QLabel {
                color: #ABB2BF;
                font-size: 12px;
                padding: 0;
                font-weight: 500;
            }
        """)
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        layout.addSpacing(30)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("仪表盘", "dashboard", "dashboard_icon"),
            ("消息历史", "history", "history_icon"),
            ("消息源配置", "sources", "sources_icon"),
            ("本地MQTT服务", "local_mqtt", "mqtt_icon"),  # 新增
            ("弹窗设置", "popup", "popup_icon"),
            ("定时弹窗", "scheduler", "timer_icon"),
            ("过滤规则", "filter", "filter_icon"),
            ("数据管理", "data", "data_icon"),
            ("系统设置", "settings", "settings_icon"),
            ("关于", "about", "about_icon"),
        ]
        
        from ui.icon_provider import IconProvider
        
        for text, page_id, icon_method in nav_items:
            btn = self._create_nav_button(text, page_id)
            # 添加图标
            icon_func = getattr(IconProvider, icon_method)
            btn.setIcon(icon_func("#ABB2BF"))
            btn.setIconSize(QSize(20, 20))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 版本信息
        version_label = QLabel("v1.1.3")
        version_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-size: 13px;
                padding: 10px;
                font-weight: 500;
            }
        """)
        layout.addWidget(version_label)
        
        return sidebar

    
    def _create_nav_button(self, text: str, page_id: str) -> QPushButton:
        """创建导航按钮"""
        btn = QPushButton(text)
        btn.setProperty("page_id", page_id)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ABB2BF;
                border: none;
                border-radius: 10px;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(74, 158, 255, 0.15);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: rgba(74, 158, 255, 0.25);
            }
            QPushButton[active="true"] {
                background: rgba(74, 158, 255, 0.2);
                color: #4A9EFF;
                font-weight: 600;
            }
        """)
        btn.clicked.connect(lambda checked=False, pid=page_id: self._on_nav_button_clicked(pid))
        return btn
    
    def _on_nav_button_clicked(self, page_id: str):
        """导航按钮点击事件"""
        print(f"[导航] 按钮被点击: {page_id}")
        logger.info(f"[导航] 按钮被点击: {page_id}")
        self._switch_page(page_id)
    
    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        container.setLayout(layout)
        
        # 页面堆栈
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)
        
        # 创建各个页面
        from ui.pages.dashboard_page import DashboardPage
        from ui.pages.history_page import HistoryPage
        from ui.pages.sources_page import SourcesPage
        from ui.pages.local_mqtt_page import LocalMQTTPage
        from ui.pages.popup_page import PopupPage
        from ui.pages.scheduler_page import SchedulerPage
        from ui.pages.filter_page import FilterPage
        from ui.pages.data_page import DataPage
        from ui.pages.settings_page import SettingsPage
        from ui.pages.about_page import AboutPage
        
        self.pages.addWidget(DashboardPage(self.database, self.message_processor))
        self.pages.addWidget(HistoryPage(self.database, self.message_processor))
        
        # 消息源配置页面 - 连接热重载信号
        sources_page = SourcesPage(self.config_manager, self.message_processor)
        sources_page.reload_requested.connect(self.reload_connectors_requested.emit)
        self.pages.addWidget(sources_page)
        
        # 本地MQTT服务页面
        if self.local_mqtt_manager:
            self.pages.addWidget(LocalMQTTPage(self.local_mqtt_manager))
        else:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout()
            placeholder_layout.addWidget(QLabel("本地MQTT服务未初始化"))
            placeholder.setLayout(placeholder_layout)
            self.pages.addWidget(placeholder)
        
        self.pages.addWidget(PopupPage(self.config_manager, self.popup_manager))
        
        # 定时弹窗页面
        if self.scheduler_manager:
            self.pages.addWidget(SchedulerPage(self.config_manager, self.scheduler_manager))
        else:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout()
            placeholder_layout.addWidget(QLabel("定时弹窗功能未初始化"))
            placeholder.setLayout(placeholder_layout)
            self.pages.addWidget(placeholder)
        
        self.pages.addWidget(FilterPage(self.config_manager, self.message_processor))
        self.pages.addWidget(DataPage(self.config_manager, self.database))
        self.pages.addWidget(SettingsPage(self.config_manager))
        self.pages.addWidget(AboutPage())
        
        # 默认显示仪表盘（不使用动画）
        self.pages.setCurrentIndex(0)
        # 设置第一个按钮为激活状态
        if self.nav_buttons:
            self.nav_buttons[0].setProperty("active", "true")
            self.nav_buttons[0].style().unpolish(self.nav_buttons[0])
            self.nav_buttons[0].style().polish(self.nav_buttons[0])
        
        return container
    
    def _switch_page(self, page_id: str):
        """切换页面"""
        print(f"[页面切换] _switch_page 被调用，目标页面: {page_id}")
        logger.info(f"[页面切换] _switch_page 被调用，目标页面: {page_id}")
        
        try:
            page_map = {
                "dashboard": 0,
                "history": 1,
                "sources": 2,
                "local_mqtt": 3,  # 新增
                "popup": 4,
                "scheduler": 5,
                "filter": 6,
                "data": 7,
                "settings": 8,
                "about": 9,
            }
            
            print(f"[页面切换] page_map 查找完成")
            
            if page_id in page_map:
                print(f"[页面切换] 页面ID有效，开始切换")
                
                # 在切换页面前，强制保存当前页面的配置（如果有force_save方法）
                current_widget = self.pages.currentWidget()
                current_page_name = current_widget.__class__.__name__ if current_widget else "Unknown"
                
                print(f"[页面切换] 当前页面: {current_page_name}")
                logger.info(f"[页面切换] 当前页面: {current_page_name}")
                
                if current_widget and hasattr(current_widget, 'force_save'):
                    try:
                        print(f"[页面切换] 正在保存 {current_page_name} 的配置...")
                        logger.info(f"[页面切换] 正在保存 {current_page_name} 的配置...")
                        current_widget.force_save()
                        print(f"[页面切换] {current_page_name} 配置已保存")
                        logger.info(f"[页面切换] {current_page_name} 配置已保存")
                    except Exception as e:
                        print(f"[页面切换] 保存配置失败: {e}")
                        logger.error(f"[页面切换] 保存 {current_page_name} 配置失败: {e}", exc_info=True)
                else:
                    print(f"[页面切换] {current_page_name} 没有 force_save 方法")
                    logger.info(f"[页面切换] {current_page_name} 没有 force_save 方法")
                
                # 更新按钮状态
                for btn in self.nav_buttons:
                    if btn.property("page_id") == page_id:
                        btn.setProperty("active", "true")
                    else:
                        btn.setProperty("active", "false")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                
                # 直接切换页面（不使用动画）
                self.pages.setCurrentIndex(page_map[page_id])
                print(f"[页面切换] 已切换到: {page_id}")
                logger.info(f"[页面切换] 已切换到: {page_id}")
            else:
                print(f"[页面切换] 未知的页面ID: {page_id}")
                logger.warning(f"[页面切换] 未知的页面ID: {page_id}")
        except Exception as e:
            print(f"[页面切换] 发生异常: {e}")
            logger.error(f"[页面切换] 发生异常: {e}", exc_info=True)
    
    def _update_status_bar(self):
        """更新状态栏信息（异步）"""
        def update_task():
            """后台任务"""
            try:
                # 获取消息总数
                total_messages = len(self.database.get_all_messages())
                
                # 获取连接器状态
                connectors = self.message_processor.get_all_connectors()
                active_connectors = sum(1 for c in connectors.values() if c.is_connected())
                
                return {
                    'total_messages': total_messages,
                    'active_connectors': active_connectors
                }
            except Exception as e:
                logger.error(f"获取状态信息失败: {e}")
                return None
        
        def on_complete(result):
            """更新UI"""
            if result:
                try:
                    if result['active_connectors'] > 0:
                        status = f"系统运行中 | {result['active_connectors']}个消息源已连接 | 共{result['total_messages']}条消息"
                    else:
                        status = f"系统就绪 | 无活动消息源 | 共{result['total_messages']}条消息"
                    
                    self.statusBar().showMessage(status)
                    
                    # 同时更新托盘图标的统计信息
                    if hasattr(self, 'tray_icon'):
                        self.tray_icon.update_stats(result['total_messages'], result['active_connectors'])
                except Exception as e:
                    logger.error(f"更新状态栏失败: {e}")
                    self.statusBar().showMessage("系统运行中")
        
        # 使用异步任务管理器
        if not hasattr(self, '_status_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._status_task_manager = AsyncTaskManager()
        
        self._status_task_manager.run_task(
            "update_status",
            update_task,
            on_finished=on_complete
        )
    
    def _apply_animations(self):
        """应用动画效果"""
        # 窗口淡入动画
        self.setWindowOpacity(0)
        self.show()
        
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(400)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
        # 保存动画引用防止被垃圾回收
        self._fade_animation = animation
    
    def closeEvent(self, event):
        """关闭事件"""
        event.ignore()
        self.hide()
        self.closing.emit()
        logger.info("主窗口已最小化到托盘")
