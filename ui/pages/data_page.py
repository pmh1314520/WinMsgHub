"""
WinMsgHub - 数据管理页面
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QMessageBox, QFileDialog,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont as QGuiFont, QPainterPath, QFont
import json
from pathlib import Path
from datetime import datetime, timedelta
from ui.icon_label import IconLabel
from ui.svg_icons import SvgIcon


class DataPage(QWidget):
    """数据管理页面 - 导入导出和数据清理"""
    
    def __init__(self, config_manager, database):
        super().__init__()
        self.config_manager = config_manager
        self.database = database
        
        # 创建异步任务管理器
        from utils.async_worker import AsyncTaskManager
        self.task_manager = AsyncTaskManager()
        
        # 缓存消息数据，避免频繁查询数据库
        self._cached_messages = []
        self._last_update_time = None
        
        # 监听数据库变化信号（事件驱动，真正的实时更新）
        self.database.data_changed.connect(self._on_data_changed)
        
        self._setup_ui()
        
        # 启动时间更新定时器（每秒更新一次时间显示）
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_time_display)
        self.time_update_timer.start(1000)  # 每1秒更新一次
        
        # 初始加载数据
        self._load_messages_async()
    
    def _update_time_display(self):
        """更新时间显示"""
        self.update_indicator.setText(f"● 实时更新 ({datetime.now().strftime('%H:%M:%S')})")
    
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
        
        # 页面标题
        title_layout = QHBoxLayout()
        title = IconLabel("chart", "数据管理")
        title.setProperty("heading", "h2")
        title_layout.addWidget(title)
        
        # 实时更新指示器
        self.update_indicator = QLabel("● 实时更新")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
        title_layout.addWidget(self.update_indicator)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 数据统计卡片
        stats_card = self._create_stats_card()
        layout.addWidget(stats_card)
        
        # 图表区域
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # 消息来源饼图
        pie_chart_card = self._create_pie_chart_card()
        charts_layout.addWidget(pie_chart_card)
        
        # 消息趋势折线图
        line_chart_card = self._create_line_chart_card()
        charts_layout.addWidget(line_chart_card)
        
        layout.addLayout(charts_layout)
        
        # 操作区域
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)
        
        # 配置管理卡片
        config_card = self._create_config_card()
        actions_layout.addWidget(config_card)
        
        # 历史管理卡片
        history_card = self._create_history_card()
        actions_layout.addWidget(history_card)
        
        layout.addLayout(actions_layout)
        
        # 数据库管理卡片
        database_card = self._create_database_card()
        layout.addWidget(database_card)
        
        layout.addStretch()
    
    def _create_stats_card(self) -> QFrame:
        """创建数据统计卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("trend_up", "实时统计")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 统计信息网格
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # 消息总数
        msg_frame = self._create_stat_item("message", "消息总数", "0", "#4A9EFF")
        self.msg_count_label = msg_frame.findChild(QLabel, "value")
        stats_layout.addWidget(msg_frame, 0, 0)
        
        # 今日消息
        today_frame = self._create_stat_item("today", "今日消息", "0", "#98C379")
        self.today_count_label = today_frame.findChild(QLabel, "value")
        stats_layout.addWidget(today_frame, 0, 1)
        
        # 数据库大小
        db_frame = self._create_stat_item("database", "数据库大小", "0 KB", "#E5C07B")
        self.db_size_label = db_frame.findChild(QLabel, "value")
        stats_layout.addWidget(db_frame, 0, 2)
        
        # 配置文件大小
        config_frame = self._create_stat_item("config", "配置大小", "0 KB", "#C678DD")
        self.config_size_label = config_frame.findChild(QLabel, "value")
        stats_layout.addWidget(config_frame, 0, 3)
        
        layout.addLayout(stats_layout)
        
        return card
    
    def _create_stat_item(self, icon_name: str, label: str, value: str, color: str) -> QFrame:
        """创建统计项"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #282C34;
                border-radius: 12px;
                padding: 12px 15px;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        
        # 图标和标签（水平排列）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap(icon_name, color, 24))
        icon_label.setStyleSheet("border: none; background: transparent;")
        header_layout.addWidget(icon_label)
        
        # 添加标签文字
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px; color: #ABB2BF; font-weight: 500; border: none; background: transparent;")
        header_layout.addWidget(label_widget)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color}; border: none; background: transparent; margin-top: 3px;")
        layout.addWidget(value_label)
        
        return frame
    
    def _create_pie_chart_card(self) -> QFrame:
        """创建消息来源饼图卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("chart", "消息来源分布")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 创建自定义饼图组件
        self.pie_chart = PieChartWidget()
        self.pie_chart.setMinimumHeight(300)
        layout.addWidget(self.pie_chart)
        
        return card
    
    def _create_line_chart_card(self) -> QFrame:
        """创建消息趋势折线图卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("trend_up", "消息趋势（最近7天）")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 创建自定义折线图组件
        self.line_chart = LineChartWidget()
        self.line_chart.setMinimumHeight(300)
        layout.addWidget(self.line_chart)
        
        return card
    
    def _create_config_card(self) -> QFrame:
        """创建配置管理卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("settings", "配置管理")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("导出和导入应用配置，方便在多台设备间同步设置")
        info.setProperty("secondary", "true")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        export_config_btn = QPushButton("  导出软件配置")
        export_config_btn.setIcon(SvgIcon.get_icon("upload", "#FFFFFF", 16))
        export_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #5FA04E;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #71B260;
            }
            QPushButton:pressed {
                background-color: #4D8E3C;
            }
        """)
        export_config_btn.clicked.connect(self._export_config)
        button_layout.addWidget(export_config_btn)
        
        import_config_btn = QPushButton("  导入软件配置")
        import_config_btn.setIcon(SvgIcon.get_icon("download", "#FFFFFF", 16))
        import_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B7FDB;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
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
        import_config_btn.clicked.connect(self._import_config)
        button_layout.addWidget(import_config_btn)
        
        layout.addLayout(button_layout)
        
        return card
    
    def _create_history_card(self) -> QFrame:
        """创建历史管理卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("history", "历史记录管理")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("导出历史消息或清空历史记录")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        export_history_btn = QPushButton("  导出消息历史")
        export_history_btn.setIcon(SvgIcon.get_icon("upload", "#FFFFFF", 16))
        export_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #5FA04E;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #71B260;
            }
            QPushButton:pressed {
                background-color: #4D8E3C;
            }
        """)
        export_history_btn.clicked.connect(self._export_history)
        button_layout.addWidget(export_history_btn)
        
        clear_history_btn = QPushButton("  清空消息历史")
        clear_history_btn.setIcon(SvgIcon.get_icon("delete", "#FFFFFF", 16))
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #C5444F;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
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
        clear_history_btn.clicked.connect(self._clear_history)
        button_layout.addWidget(clear_history_btn)
        
        layout.addLayout(button_layout)
        
        return card
    
    def _create_database_card(self) -> QFrame:
        """创建数据库管理卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("database", "数据库管理")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("优化数据库性能和清理无用数据")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        button_layout = QHBoxLayout()
        
        optimize_btn = QPushButton("  优化数据库")
        optimize_btn.setIcon(SvgIcon.get_icon("tool", "#FFFFFF", 16))
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B7FDB;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
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
        optimize_btn.clicked.connect(self._optimize_database)
        button_layout.addWidget(optimize_btn)
        
        vacuum_btn = QPushButton("  清理空间")
        vacuum_btn.setIcon(SvgIcon.get_icon("clean", "#FFFFFF", 16))
        vacuum_btn.setStyleSheet("""
            QPushButton {
                background-color: #5FA04E;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #71B260;
            }
            QPushButton:pressed {
                background-color: #4D8E3C;
            }
        """)
        vacuum_btn.clicked.connect(self._vacuum_database)
        button_layout.addWidget(vacuum_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return card
    
    def _on_data_changed(self):
        """数据库数据变化时触发（事件驱动）"""
        # 重新加载消息数据
        self._load_messages_async()
    
    def _load_messages_async(self):
        """异步加载消息数据"""
        def load_task():
            """后台加载任务"""
            try:
                return self.database.get_all_messages()
            except Exception as e:
                print(f"加载消息失败: {e}")
                return []
        
        def on_complete(messages):
            """加载完成，更新缓存并刷新UI"""
            self._cached_messages = messages
            self._update_stats_from_cache()
            # 更新时间戳显示
            self.update_indicator.setText(f"● 实时更新 ({datetime.now().strftime('%H:%M:%S')})")
        
        # 异步加载
        self.task_manager.run_task(
            "load_messages",
            load_task,
            on_finished=on_complete
        )
    
    def _update_stats_from_cache(self):
        """从缓存数据更新统计（在主线程执行）"""
        try:
            messages = self._cached_messages
            
            # 消息总数
            msg_count = len(messages)
            self.msg_count_label.setText(str(msg_count))
            
            # 今日消息数
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_timestamp = today_start.timestamp()
            today_messages = [msg for msg in messages if msg.timestamp >= today_timestamp]
            today_count = len(today_messages)
            self.today_count_label.setText(str(today_count))
            
            # 数据库大小
            if hasattr(self.database, 'db_path') and self.database.db_path != ":memory:":
                db_path = Path(self.database.db_path)
                if db_path.exists():
                    db_size = db_path.stat().st_size
                    self.db_size_label.setText(self._format_size(db_size))
                else:
                    self.db_size_label.setText("0 KB")
            else:
                self.db_size_label.setText("内存数据库")
            
            # 配置文件大小
            config_file = self.config_manager.config_file
            if config_file.exists():
                config_size = config_file.stat().st_size
                self.config_size_label.setText(self._format_size(config_size))
            else:
                self.config_size_label.setText("0 KB")
            
            # 统计各来源消息数（饼图）
            source_counts = {}
            for msg in messages:
                source = msg.source
                source_counts[source] = source_counts.get(source, 0) + 1
            self.pie_chart.set_data(source_counts)
            
            # 统计每天的消息数（折线图）
            daily_counts = []
            for i in range(7):
                day = datetime.now() - timedelta(days=6-i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                count = sum(1 for msg in messages 
                           if day_start.timestamp() <= msg.timestamp < day_end.timestamp())
                daily_counts.append(count)
            self.line_chart.set_data(daily_counts)
            
        except Exception as e:
            print(f"更新统计失败: {e}")
    
    def _update_stats(self):
        """同步更新统计信息（用于初始加载）"""
        try:
            # 消息总数
            msg_count = self.database.get_message_count()
            self.msg_count_label.setText(str(msg_count))
            
            # 今日消息数
            today_count = self._get_today_message_count()
            self.today_count_label.setText(str(today_count))
            
            # 数据库大小
            if hasattr(self.database, 'db_path') and self.database.db_path != ":memory:":
                db_path = Path(self.database.db_path)
                if db_path.exists():
                    db_size = db_path.stat().st_size
                    self.db_size_label.setText(self._format_size(db_size))
                else:
                    self.db_size_label.setText("0 KB")
            else:
                self.db_size_label.setText("内存数据库")
            
            # 配置文件大小
            config_file = self.config_manager.config_file
            if config_file.exists():
                config_size = config_file.stat().st_size
                self.config_size_label.setText(self._format_size(config_size))
            else:
                self.config_size_label.setText("0 KB")
            
            # 更新图表
            self._update_pie_chart()
            self._update_line_chart()
            
            # 更新指示器
            self.update_indicator.setText(f"● 实时更新 ({datetime.now().strftime('%H:%M:%S')})")
            
        except Exception as e:
            print(f"更新统计信息失败: {e}")
    
    def _get_today_message_count(self) -> int:
        """获取今日消息数"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_timestamp = today_start.timestamp()
            
            # 获取今天的消息
            messages = self.database.get_all_messages()
            today_messages = [msg for msg in messages if msg.timestamp >= today_timestamp]
            return len(today_messages)
        except:
            return 0
    
    def _update_pie_chart(self):
        """更新饼图"""
        try:
            # 获取所有消息
            messages = self.database.get_all_messages()
            
            # 统计各来源消息数
            source_counts = {}
            for msg in messages:
                source = msg.source
                source_counts[source] = source_counts.get(source, 0) + 1
            
            # 更新饼图数据
            self.pie_chart.set_data(source_counts)
        except Exception as e:
            print(f"更新饼图失败: {e}")
    
    def _update_line_chart(self):
        """更新折线图"""
        try:
            # 获取最近7天的消息数
            messages = self.database.get_all_messages()
            
            # 统计每天的消息数
            daily_counts = []
            for i in range(7):
                day = datetime.now() - timedelta(days=6-i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                count = sum(1 for msg in messages 
                           if day_start.timestamp() <= msg.timestamp < day_end.timestamp())
                daily_counts.append(count)
            
            # 更新折线图数据
            self.line_chart.set_data(daily_counts)
        except Exception as e:
            print(f"更新折线图失败: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    
    def _export_config(self):
        """导出配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出配置",
                f"WinMsgHub_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json)"
            )
            
            if file_path:
                config_data = self.config_manager.get_all()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", f"配置已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出配置失败: {e}")
    
    def _import_config(self):
        """导入配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "导入配置",
                "",
                "JSON文件 (*.json)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self,
                    "确认导入",
                    "导入配置将覆盖当前设置，是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # 保存配置
                    self.config_manager.config = config_data
                    self.config_manager.save_config()
                    
                    QMessageBox.information(
                        self,
                        "成功",
                        "配置已导入！\n请重启应用以使新配置生效。"
                    )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入配置失败: {e}")
    
    def _export_history(self):
        """导出历史"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出历史",
                f"WinMsgHub_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json)"
            )
            
            if file_path:
                messages = self.database.get_all_messages()
                
                # 转换为可序列化的格式
                messages_data = []
                for msg in messages:
                    messages_data.append({
                        "id": msg.id,
                        "source": msg.source,
                        "title": msg.title,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "metadata": msg.metadata
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(messages_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self,
                    "成功",
                    f"已导出 {len(messages)} 条消息到:\n{file_path}"
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出历史失败: {e}")
    
    def _clear_history(self):
        """清空历史"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有历史消息吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database.clear_all_messages()
                self._update_stats()
                QMessageBox.information(self, "成功", "历史消息已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空历史失败: {e}")
    
    def _optimize_database(self):
        """优化数据库"""
        try:
            # 删除旧消息
            retention_days = self.config_manager.get("history.retention_days", 30)
            deleted = self.database.delete_old_messages(retention_days)
            
            self._update_stats()
            QMessageBox.information(
                self,
                "优化完成",
                f"已删除 {deleted} 条超过 {retention_days} 天的旧消息"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"优化数据库失败: {e}")
    
    def _vacuum_database(self):
        """清理数据库空间"""
        try:
            if hasattr(self.database, 'db_path') and self.database.db_path != ":memory:":
                conn = self.database._get_connection()
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                conn.commit()
                self.database._close_connection(conn)
                
                self._update_stats()
                QMessageBox.information(self, "成功", "数据库空间清理完成")
            else:
                QMessageBox.information(self, "提示", "内存数据库无需清理")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理数据库失败: {e}")


# 自定义饼图组件
class PieChartWidget(QWidget):
    """自定义饼图组件 - 支持鼠标悬停提示"""
    
    def __init__(self):
        super().__init__()
        self.data = {}
        self.colors = ["#4A9EFF", "#98C379", "#E5C07B", "#C678DD", "#56B6C2", "#E06C75"]
        self.pie_segments = []  # 存储每个扇形的信息
        self.hovered_segment = -1  # 当前悬停的扇形索引
        self.setMouseTracking(True)  # 启用鼠标跟踪
    
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
        
        # 计算角度（从右侧开始，逆时针）
        import math
        angle = math.atan2(-dy, dx)  # 注意y轴是反的
        angle_deg = math.degrees(angle)
        if angle_deg < 0:
            angle_deg += 360
        
        # 查找对应的扇形
        total = sum(self.data.values())
        start_angle = 0
        for i, (label, value) in enumerate(self.data.items()):
            segment_angle = value / total * 360
            end_angle = start_angle + segment_angle
            
            # 检查鼠标是否在这个扇形内
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
            # 没有数据时显示提示
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
            # 计算角度
            angle = int(value / total * 360 * 16)  # Qt uses 1/16th degree
            
            # 绘制扇形
            color = QColor(self.colors[i % len(self.colors)])
            
            # 如果是悬停的扇形，增加亮度
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


# 自定义折线图组件
class LineChartWidget(QWidget):
    """自定义折线图组件"""
    
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
            # 没有数据时显示提示
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
        painter.drawLine(margin, rect.height() - margin, rect.width() - margin, rect.height() - margin)  # X轴
        painter.drawLine(margin, margin, margin, rect.height() - margin)  # Y轴
        
        # 绘制网格线
        painter.setPen(QPen(QColor("#3A3F4B"), 1, Qt.PenStyle.DashLine))
        for i in range(5):
            y = margin + (chart_height // 4) * i
            painter.drawLine(margin, y, rect.width() - margin, y)
        
        # 绘制数据点和线
        if len(self.data) > 1:
            path = QPainterPath()
            
            # 计算第一个点
            x = margin
            y = rect.height() - margin - (self.data[0] / max_value * chart_height)
            path.moveTo(x, y)
            
            # 绘制线
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
        
        # X轴标签
        for i in range(len(self.data)):
            x = margin + (chart_width / (len(self.data) - 1)) * i if len(self.data) > 1 else margin + chart_width // 2
            painter.drawText(int(x - 10), rect.height() - margin + 20, f"{i+1}")
        
        # Y轴标签
        for i in range(5):
            y = margin + (chart_height // 4) * i
            value = int(max_value * (1 - i / 4))
            painter.drawText(5, int(y + 5), str(value))
