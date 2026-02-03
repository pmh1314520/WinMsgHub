"""
WinMsgHub - 仪表盘页面
作者：青云制作_彭明航
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QPushButton, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont as QGuiFont, QPainterPath, QFont
from datetime import datetime, timedelta
from utils.logger import get_logger
from ui.icon_label import IconLabel
from ui.svg_icons import SvgIcon

logger = get_logger(__name__)


class DashboardPage(QWidget):
    """仪表盘页面 - 显示统计信息和图表"""
    
    def __init__(self, database, message_processor):
        super().__init__()
        self.database = database
        self.message_processor = message_processor
        
        # 记录程序启动时间
        self.start_time = time.time()
        
        # 创建异步数据库访问
        from data.async_database import AsyncDatabase
        self.async_db = AsyncDatabase(database)
        
        # 连接信号
        self.async_db.messages_loaded.connect(self._on_messages_loaded_for_stats)
        self.async_db.operation_error.connect(self._on_error)
        
        # 监听数据库变化信号（事件驱动，真正的实时更新）
        self.database.data_changed.connect(self._on_data_changed)
        
        # 缓存数据
        self._cached_messages = []
        self._last_refresh_time = None
        
        self._setup_ui()
        
        # 启动时间更新定时器（每秒更新一次时间显示）
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_time_display)
        self.time_update_timer.start(1000)  # 每1秒更新一次
        
        # 初始加载一次数据
        self._refresh_stats()
    
    def _update_time_display(self):
        """更新时间显示和系统信息"""
        self.update_indicator.setText(f"● 实时更新 ({datetime.now().strftime('%H:%M:%S')})")
        # 同时更新系统信息（消息源状态和运行时间）
        self._update_system_info()
        self._update_runtime()
    
    def _on_data_changed(self):
        """数据库数据变化时触发（事件驱动）"""
        self._refresh_stats()
        # 更新时间戳显示
        self._update_time_display()
    
    def _on_messages_loaded_for_stats(self, messages):
        """消息加载完成，更新统计"""
        self._cached_messages = messages
        self._update_stats_from_cache()
    
    def _on_error(self, error_msg):
        """操作出错"""
        print(f"仪表盘错误: {error_msg}")
    
    def _setup_ui(self):
        """设置UI"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content = QWidget()
        scroll.setWidget(content)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        content.setLayout(layout)
        
        # 页面标题和实时更新指示器
        title_layout = QHBoxLayout()
        title = IconLabel("chart", "仪表盘")
        title.setProperty("heading", "h2")
        title_layout.addWidget(title)
        
        self.update_indicator = QLabel("● 实时更新")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
        title_layout.addWidget(self.update_indicator)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 统计卡片网格
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        # 今日消息数
        self.today_card = self._create_stat_card(
            "今日消息",
            "0",
            "#4A9EFF",
            "trend_up"
        )
        stats_grid.addWidget(self.today_card, 0, 0)
        
        # 总消息数
        self.total_card = self._create_stat_card(
            "总消息数",
            "0",
            "#98C379",
            "message"
        )
        stats_grid.addWidget(self.total_card, 0, 1)
        
        # 连接状态
        self.status_card = self._create_stat_card(
            "连接状态",
            "正常",
            "#E5C07B",
            "check"
        )
        stats_grid.addWidget(self.status_card, 0, 2)
        
        # 过滤规则数
        self.filter_card = self._create_stat_card(
            "过滤规则",
            "0",
            "#C678DD",
            "settings"
        )
        stats_grid.addWidget(self.filter_card, 0, 3)
        
        layout.addLayout(stats_grid)
        
        # 图表区域
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # 消息趋势图
        trend_card = self._create_trend_chart_card()
        charts_layout.addWidget(trend_card)
        
        # 消息来源分布图
        source_card = self._create_source_chart_card()
        charts_layout.addWidget(source_card)
        
        layout.addLayout(charts_layout)
        
        # 快速操作区
        quick_actions = self._create_quick_actions()
        layout.addWidget(quick_actions)
        
        # 系统信息卡片
        system_info = self._create_system_info_card()
        layout.addWidget(system_info)
        
        layout.addStretch()
        
        # 刷新数据
        self._refresh_stats()
    
    def _create_stat_card(self, title: str, value: str, color: str, icon: str = None) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        card.setStyleSheet(f"""
            QFrame[card="true"] {{
                background-color: #282C34;
                border-radius: 12px;
                border-left: 4px solid {color};
                padding: 12px 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        card.setLayout(layout)
        
        # 标题和图标
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(SvgIcon.get_pixmap(icon, color, 24))
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: #ABB2BF;
                font-weight: 500;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: 700;
                color: {color};
                margin-top: 3px;
            }}
        """)
        layout.addWidget(value_label)
        
        return card
    
    def _create_trend_chart_card(self) -> QFrame:
        """创建消息趋势图卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = QLabel("📈 消息趋势（最近7天）")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 创建折线图组件
        self.trend_chart = TrendChartWidget()
        self.trend_chart.setMinimumHeight(250)
        layout.addWidget(self.trend_chart)
        
        return card
    
    def _create_source_chart_card(self) -> QFrame:
        """创建消息来源分布图卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = QLabel("📊 消息来源分布")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 创建饼图组件
        self.source_chart = SourcePieChartWidget()
        self.source_chart.setMinimumHeight(250)
        layout.addWidget(self.source_chart)
        
        return card

    
    def _create_quick_actions(self) -> QFrame:
        """创建快速操作区"""
        frame = QFrame()
        frame.setProperty("card", "true")
        
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        title = QLabel("⚡ 快速操作")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        # 测试弹窗按钮
        test_btn = QPushButton("  测试弹窗")
        test_btn.setIcon(SvgIcon.get_icon("bell", "#FFFFFF", 16))
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B7FDB;
                color: white;
                font-weight: 500;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3D8FED;
            }
            QPushButton:pressed {
                background-color: #1A6FC9;
            }
        """)
        test_btn.clicked.connect(self._test_popup)
        buttons_layout.addWidget(test_btn)
        
        # 清空历史按钮
        clear_btn = QPushButton("  清空历史")
        clear_btn.setIcon(SvgIcon.get_icon("delete", "#FFFFFF", 16))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
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
        clear_btn.clicked.connect(self._clear_history)
        buttons_layout.addWidget(clear_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return frame
    
    def _create_system_info_card(self) -> QFrame:
        """创建系统信息卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = QLabel("💻 系统信息")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info_layout = QGridLayout()
        info_layout.setSpacing(15)
        
        # 运行时间
        runtime_label = IconLabel("uptime", "运行时间:")
        runtime_label.setStyleSheet("color: #ABB2BF; font-size: 13px;")
        info_layout.addWidget(runtime_label, 0, 0)
        
        self.runtime_value = QLabel("计算中...")
        self.runtime_value.setStyleSheet("color: #4A9EFF; font-size: 13px; font-weight: 500;")
        info_layout.addWidget(self.runtime_value, 0, 1)
        
        # 数据库大小
        db_label = IconLabel("storage", "数据库大小:")
        db_label.setStyleSheet("color: #ABB2BF; font-size: 13px;")
        info_layout.addWidget(db_label, 0, 2)
        
        self.db_size_value = QLabel("计算中...")
        self.db_size_value.setStyleSheet("color: #98C379; font-size: 13px; font-weight: 500;")
        info_layout.addWidget(self.db_size_value, 0, 3)
        
        # 消息源状态
        sources_label = IconLabel("source", "消息源:")
        sources_label.setStyleSheet("color: #ABB2BF; font-size: 13px;")
        info_layout.addWidget(sources_label, 1, 0)
        
        self.sources_value = QLabel("检测中...")
        self.sources_value.setStyleSheet("color: #E5C07B; font-size: 13px; font-weight: 500;")
        info_layout.addWidget(self.sources_value, 1, 1)
        
        # 版本信息和检查更新按钮
        version_label = IconLabel("version", "版本:")
        version_label.setStyleSheet("color: #ABB2BF; font-size: 13px;")
        info_layout.addWidget(version_label, 1, 2)
        
        version_container = QWidget()
        version_layout = QHBoxLayout()
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(10)
        version_container.setLayout(version_layout)
        
        from utils.update_checker import UpdateChecker
        version_value = QLabel(f"v{UpdateChecker.get_current_version()}")
        version_value.setStyleSheet("color: #C678DD; font-size: 13px; font-weight: 500;")
        version_layout.addWidget(version_value)
        
        # 检查更新按钮
        self.check_update_btn = QPushButton("检查更新")
        self.check_update_btn.setStyleSheet("""
            QPushButton {
                background: rgba(74, 158, 255, 0.15);
                color: #4A9EFF;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 10px;
                border: 1px solid rgba(74, 158, 255, 0.3);
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(74, 158, 255, 0.25);
                border: 1px solid rgba(74, 158, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(74, 158, 255, 0.35);
            }
            QPushButton:disabled {
                background: rgba(74, 158, 255, 0.05);
                color: #6A7A8F;
                border: 1px solid rgba(74, 158, 255, 0.1);
            }
        """)
        self.check_update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_update_btn.clicked.connect(self._check_for_updates)
        version_layout.addWidget(self.check_update_btn)
        version_layout.addStretch()
        
        info_layout.addWidget(version_container, 1, 3)
        
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(3, 1)
        
        layout.addLayout(info_layout)
        
        return card
    
    def _refresh_stats(self):
        """异步刷新统计数据"""
        # 避免频繁刷新
        from datetime import datetime
        now = datetime.now()
        if self._last_refresh_time:
            elapsed = (now - self._last_refresh_time).total_seconds()
            if elapsed < 3:  # 3秒内不重复刷新
                return
        
        self._last_refresh_time = now
        
        # 异步加载消息
        self.async_db.get_all_messages_async()
    
    def _update_stats_from_cache(self):
        """从缓存数据更新统计（异步计算）"""
        from utils.async_worker import AsyncTaskManager
        
        if not hasattr(self, '_stats_task_manager'):
            self._stats_task_manager = AsyncTaskManager()
        
        def calculate_stats():
            """后台计算统计数据"""
            try:
                messages = self._cached_messages
                
                # 获取总消息数
                total = len(messages)
                
                # 获取今日消息数
                from datetime import datetime
                today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
                today_messages = [m for m in messages if m.timestamp >= today_start]
                today_count = len(today_messages)
                
                # 获取过滤规则数
                filter_count = 0
                if hasattr(self.message_processor, 'filter_engine') and hasattr(self.message_processor.filter_engine, 'rules'):
                    filter_count = len(self.message_processor.filter_engine.rules)
                elif hasattr(self.message_processor, 'config_manager'):
                    filter_rules = self.message_processor.config_manager.get("filters.rules", [])
                    filter_count = len(filter_rules)
                
                # 统计最近7天的消息数
                daily_counts = []
                for i in range(7):
                    day = datetime.now() - timedelta(days=6-i)
                    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                    day_end = day_start + timedelta(days=1)
                    
                    count = sum(1 for msg in messages 
                               if day_start.timestamp() <= msg.timestamp < day_end.timestamp())
                    daily_counts.append(count)
                
                # 统计各来源消息数
                source_counts = {}
                for msg in messages:
                    source = msg.source
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                return {
                    'total': total,
                    'today_count': today_count,
                    'filter_count': filter_count,
                    'daily_counts': daily_counts,
                    'source_counts': source_counts
                }
            except Exception as e:
                print(f"计算统计失败: {e}")
                return None
        
        def update_ui(result):
            """主线程更新UI"""
            if not result:
                return
            
            try:
                # 更新总消息数
                total_label = self.total_card.findChild(QLabel, "value")
                if total_label:
                    total_label.setText(str(result['total']))
                
                # 更新今日消息数
                today_label = self.today_card.findChild(QLabel, "value")
                if today_label:
                    today_label.setText(str(result['today_count']))
                
                # 更新过滤规则数
                filter_label = self.filter_card.findChild(QLabel, "value")
                if filter_label:
                    filter_label.setText(str(result['filter_count']))
                
                # 更新图表
                self.trend_chart.set_data(result['daily_counts'])
                self.source_chart.set_data(result['source_counts'])
                
                # 更新系统信息
                self._update_system_info()
                
                # 更新指示器
                self.update_indicator.setText(f"● 实时更新 ({datetime.now().strftime('%H:%M:%S')})")
                
            except Exception as e:
                print(f"更新UI失败: {e}")
        
        # 异步执行计算
        self._stats_task_manager.run_task(
            "calculate_stats",
            calculate_stats,
            on_finished=update_ui
        )
    
    def _update_runtime(self):
        """更新运行时间显示"""
        try:
            # 计算运行时长（秒）
            elapsed_seconds = int(time.time() - self.start_time)
            
            # 转换为天、小时、分钟、秒
            days = elapsed_seconds // 86400
            hours = (elapsed_seconds % 86400) // 3600
            minutes = (elapsed_seconds % 3600) // 60
            seconds = elapsed_seconds % 60
            
            # 构建显示文本
            if days > 0:
                runtime_text = f"{days}天{hours}小时{minutes}分"
            elif hours > 0:
                runtime_text = f"{hours}小时{minutes}分{seconds}秒"
            elif minutes > 0:
                runtime_text = f"{minutes}分{seconds}秒"
            else:
                runtime_text = f"{seconds}秒"
            
            self.runtime_value.setText(runtime_text)
            
        except Exception as e:
            logger.error(f"更新运行时间失败: {e}", exc_info=True)
    
    def _update_system_info(self):
        """更新系统信息"""
        try:
            # 更新数据库大小
            if hasattr(self.database, 'db_path') and self.database.db_path != ":memory:":
                from pathlib import Path
                db_path = Path(self.database.db_path)
                if db_path.exists():
                    db_size = db_path.stat().st_size
                    if db_size < 1024:
                        size_str = f"{db_size} B"
                    elif db_size < 1024 * 1024:
                        size_str = f"{db_size / 1024:.2f} KB"
                    else:
                        size_str = f"{db_size / (1024 * 1024):.2f} MB"
                    self.db_size_value.setText(size_str)
                else:
                    self.db_size_value.setText("0 KB")
            else:
                self.db_size_value.setText("内存数据库")
            
            # 更新消息源状态
            enabled_sources = []
            try:
                # 从message_processor获取所有连接器
                connectors = self.message_processor.get_all_connectors()
                
                # 统计每种类型的启用数量（使用集合去重）
                enabled_types = set()
                
                for name, connector in connectors.items():
                    # 检查连接器是否已连接
                    if not connector.is_connected():
                        continue
                    
                    # 从连接器名称中提取类型（格式：type_name）
                    # 需要处理特殊情况：file_monitor（两个单词）
                    if '_' in name:
                        parts = name.split('_', 1)  # 只分割第一个下划线
                        connector_type = parts[0]
                        
                        # 特殊处理：如果是file，检查是否是file_monitor
                        if connector_type == 'file' and len(parts) > 1 and parts[1].startswith('monitor'):
                            connector_type = 'file_monitor'
                    else:
                        # 没有下划线，直接使用整个名称
                        connector_type = name
                    
                    # 添加到集合（自动去重）
                    enabled_types.add(connector_type)
                
                # 构建显示文本（只显示类型，不显示数量）
                type_names = {
                    'mqtt': 'MQTT',
                    'websocket': 'WebSocket',
                    'api': 'API',
                    'webhook': 'Webhook',
                    'imap': 'IMAP',
                    'rss': 'RSS',
                    'file': '文件监控',
                    'file_monitor': '文件监控',
                    'clipboard': '剪贴板'
                }
                
                # 转换为显示名称（去重）
                display_names_set = set()
                for connector_type in enabled_types:
                    display_name = type_names.get(connector_type, connector_type)
                    display_names_set.add(display_name)
                
                enabled_sources = list(display_names_set)
                    
            except Exception as e:
                logger.error(f"获取连接器状态失败: {e}", exc_info=True)
            
            if enabled_sources:
                self.sources_value.setText(", ".join(enabled_sources))
            else:
                self.sources_value.setText("无启用")
            
        except Exception as e:
            print(f"更新系统信息失败: {e}")
    
    def _test_popup(self):
        """测试弹窗"""
        from data.models import Message
        from ui.notification_popup import NotificationPopup, PopupStyle, PopupPosition
        import time
        
        message = Message(
            id="test",
            source="测试",
            title="测试弹窗",
            content="这是一条测试消息，用于验证弹窗功能。",
            timestamp=time.time(),
            metadata={}
        )
        
        style = PopupStyle(
            position=PopupPosition.TOP_RIGHT,
            display_duration=5000
        )
        
        popup = NotificationPopup(message, style)
        popup.show()
        popup.set_auto_close(5000)
    
    def _clear_history(self):
        """清空历史"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空所有历史消息吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 清空数据库
                for msg in self.database.get_all_messages():
                    self.database.delete_message(msg.id)
                self._refresh_stats()
                QMessageBox.information(self, "成功", "历史消息已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空失败: {e}")
    
    def _check_for_updates(self):
        """检查更新"""
        from PyQt6.QtCore import QThread, pyqtSignal
        from utils.update_checker import UpdateChecker
        
        # 创建更新检查线程
        class UpdateCheckThread(QThread):
            update_checked = pyqtSignal(object)
            
            def run(self):
                update_info = UpdateChecker.check_update()
                self.update_checked.emit(update_info)
        
        # 禁用按钮
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("检查中...")
        
        # 启动检查
        self._check_thread = UpdateCheckThread()
        self._check_thread.update_checked.connect(self._on_update_checked)
        self._check_thread.start()
    
    def _on_update_checked(self, update_info):
        """更新检查完成"""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        from utils.update_checker import UpdateChecker
        
        # 恢复按钮
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("检查更新")
        
        if update_info is None:
            # 已是最新版本
            msg = QMessageBox(self)
            msg.setWindowTitle("检查更新")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("当前已是最新版本！")
            msg.setInformativeText(f"当前版本：v{UpdateChecker.get_current_version()}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #282C34;
                }
                QMessageBox QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #4A9EFF;
                    color: white;
                    font-weight: 600;
                    padding: 8px 20px;
                    border-radius: 6px;
                    border: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #5AAAFF;
                }
            """)
            msg.exec()
        else:
            # 发现新版本
            msg = QMessageBox(self)
            msg.setWindowTitle("发现新版本")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"发现新版本 v{update_info['latest_version']}！")
            
            details = f"当前版本：v{update_info['current_version']}\n"
            details += f"最新版本：v{update_info['latest_version']}\n\n"
            details += "更新内容：\n"
            details += update_info.get('release_notes', '暂无更新说明')
            
            msg.setInformativeText("是否前往下载页面？")
            msg.setDetailedText(details)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            yes_btn = msg.button(QMessageBox.StandardButton.Yes)
            yes_btn.setText("前往下载")
            no_btn = msg.button(QMessageBox.StandardButton.No)
            no_btn.setText("稍后再说")
            
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #282C34;
                }
                QMessageBox QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                }
                QTextEdit {
                    background-color: #1E2127;
                    color: #ABB2BF;
                    border: 1px solid #3A4149;
                    border-radius: 6px;
                    padding: 10px;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: #4A9EFF;
                    color: white;
                    font-weight: 600;
                    padding: 8px 20px;
                    border-radius: 6px;
                    border: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #5AAAFF;
                }
            """)
            
            result = msg.exec()
            if result == QMessageBox.StandardButton.Yes:
                download_url = update_info.get('download_url', UpdateChecker.get_releases_url())
                QDesktopServices.openUrl(QUrl(download_url))


# 自定义折线图组件
class TrendChartWidget(QWidget):
    """消息趋势折线图组件"""
    
    def __init__(self):
        super().__init__()
        self.data = []
    
    def set_data(self, data: list):
        """设置数据"""
        self.data = data
        self.update()
    
    def paintEvent(self, event):
        """绘制折线图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data:
            painter.setPen(QColor("#ABB2BF"))
            painter.setFont(QGuiFont("Microsoft YaHei UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            return
        
        # 计算绘图区域
        rect = self.rect()
        margin = 50
        chart_width = rect.width() - 2 * margin
        chart_height = rect.height() - 2 * margin
        
        # 计算最大值
        max_value = max(self.data) if self.data else 10
        if max_value == 0:
            max_value = 10
        
        # 绘制坐标轴
        painter.setPen(QPen(QColor("#ABB2BF"), 2))
        painter.drawLine(margin, rect.height() - margin, rect.width() - margin, rect.height() - margin)
        painter.drawLine(margin, margin, margin, rect.height() - margin)
        
        # 绘制网格线
        painter.setPen(QPen(QColor("#3A3F4B"), 1, Qt.PenStyle.DashLine))
        for i in range(5):
            y = margin + (chart_height // 4) * i
            painter.drawLine(margin, y, rect.width() - margin, y)
        
        # 绘制数据点和线
        if len(self.data) > 1:
            path = QPainterPath()
            
            x = margin
            y = rect.height() - margin - (self.data[0] / max_value * chart_height)
            path.moveTo(x, y)
            
            for i in range(1, len(self.data)):
                x = margin + (chart_width / (len(self.data) - 1)) * i
                y = rect.height() - margin - (self.data[i] / max_value * chart_height)
                path.lineTo(x, y)
            
            painter.setPen(QPen(QColor("#4A9EFF"), 3))
            painter.drawPath(path)
            
            # 绘制数据点
            painter.setBrush(QColor("#4A9EFF"))
            for i, value in enumerate(self.data):
                x = margin + (chart_width / (len(self.data) - 1)) * i if len(self.data) > 1 else margin + chart_width // 2
                y = rect.height() - margin - (value / max_value * chart_height)
                painter.drawEllipse(QPointF(x, y), 5, 5)
        
        # 绘制标签
        painter.setPen(QColor("#ABB2BF"))
        painter.setFont(QGuiFont("Microsoft YaHei UI", 9))
        
        # X轴标签（日期）
        for i in range(len(self.data)):
            x = margin + (chart_width / (len(self.data) - 1)) * i if len(self.data) > 1 else margin + chart_width // 2
            day = datetime.now() - timedelta(days=6-i)
            label = day.strftime("%m/%d")
            painter.drawText(int(x - 15), rect.height() - margin + 20, label)
        
        # Y轴标签
        for i in range(5):
            y = margin + (chart_height // 4) * i
            value = int(max_value * (1 - i / 4))
            painter.drawText(5, int(y + 5), str(value))


# 自定义饼图组件
class SourcePieChartWidget(QWidget):
    """消息来源饼图组件 - 支持鼠标悬停提示"""
    
    def __init__(self):
        super().__init__()
        self.data = {}
        self.colors = ["#4A9EFF", "#98C379", "#E5C07B", "#C678DD", "#56B6C2", "#E06C75"]
        self.hovered_segment = -1
        self.setMouseTracking(True)
    
    def set_data(self, data: dict):
        """设置数据"""
        self.data = data
        self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.data:
            return
        
        # 计算鼠标位置相对于饼图中心的角度
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 120
        center_x = rect.width() // 2
        center_y = rect.height() // 2 - 40
        
        # 鼠标相对于中心的位置
        dx = event.pos().x() - center_x
        dy = event.pos().y() - center_y
        distance = (dx**2 + dy**2)**0.5
        
        # 检查是否在饼图范围内
        if distance > size // 2:
            if self.hovered_segment != -1:
                self.hovered_segment = -1
                self.update()
                self.setToolTip("")
            return
        
        # 计算角度
        import math
        angle = math.atan2(-dy, dx)
        angle_deg = math.degrees(angle)
        if angle_deg < 0:
            angle_deg += 360
        
        # 查找对应的扇形
        total = sum(self.data.values())
        start_angle = 0
        for i, (label, value) in enumerate(self.data.items()):
            segment_angle = value / total * 360
            end_angle = start_angle + segment_angle
            
            if start_angle <= angle_deg < end_angle:
                if self.hovered_segment != i:
                    self.hovered_segment = i
                    percentage = value / total * 100
                    self.setToolTip(f"{label}\n次数: {value}\n占比: {percentage:.1f}%")
                    self.update()
                return
            
            start_angle = end_angle
        
        if self.hovered_segment != -1:
            self.hovered_segment = -1
            self.update()
            self.setToolTip("")
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hovered_segment != -1:
            self.hovered_segment = -1
            self.update()
            self.setToolTip("")
    
    def paintEvent(self, event):
        """绘制饼图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data:
            painter.setPen(QColor("#ABB2BF"))
            painter.setFont(QGuiFont("Microsoft YaHei UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            return
        
        # 计算总数
        total = sum(self.data.values())
        if total == 0:
            return
        
        # 绘制饼图
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 120  # 减少边距，增大饼图
        center_x = rect.width() // 2
        center_y = rect.height() // 2 - 40  # 稍微向上移动
        
        start_angle = 0
        for i, (label, value) in enumerate(self.data.items()):
            angle = int(value / total * 360 * 16)
            
            color = QColor(self.colors[i % len(self.colors)])
            
            # 悬停时增加亮度
            if i == self.hovered_segment:
                color = color.lighter(120)
            
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#21252B"), 2))
            painter.drawPie(
                center_x - size//2, center_y - size//2,
                size, size,
                start_angle, angle
            )
            
            start_angle += angle
        
        # 获取前两名数据
        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        top_two = sorted_data[:2]
        
        # 绘制前两名信息
        info_y = center_y + size//2 + 40
        painter.setFont(QGuiFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))
        
        for idx, (label, value) in enumerate(top_two):
            color_idx = list(self.data.keys()).index(label)
            color = QColor(self.colors[color_idx % len(self.colors)])
            percentage = value / total * 100
            
            # 绘制颜色块
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            y_pos = info_y + idx * 35
            painter.drawRoundedRect(center_x - 150, y_pos, 20, 20, 4, 4)
            
            # 绘制文字
            painter.setPen(QColor("#FFFFFF"))
            text = f"{label}: {value}次 ({percentage:.1f}%)"
            painter.drawText(center_x - 120, y_pos + 15, text)
