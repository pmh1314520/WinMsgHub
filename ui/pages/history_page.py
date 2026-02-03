"""
WinMsgHub - 消息历史页面
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QDateEdit, QMessageBox, QTextEdit, QDialog,
    QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from ui.svg_icons import SvgIcon


class MessageDetailDialog(QDialog):
    """消息详情对话框"""
    
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message = message
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("消息详情")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title = QLabel(self.message.title)
        title.setProperty("heading", "h2")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # 元信息
        meta_layout = QHBoxLayout()
        
        source_label = QLabel(f"来源: {self.message.source}")
        source_label.setProperty("secondary", "true")
        meta_layout.addWidget(source_label)
        
        time_str = datetime.fromtimestamp(self.message.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(f"时间: {time_str}")
        time_label.setProperty("secondary", "true")
        meta_layout.addWidget(time_label)
        
        meta_layout.addStretch()
        layout.addLayout(meta_layout)
        
        # 内容
        content_label = QLabel("内容:")
        content_label.setProperty("heading", "h3")
        layout.addWidget(content_label)
        
        content_text = QTextEdit()
        content_text.setPlainText(self.message.content)
        content_text.setReadOnly(True)
        layout.addWidget(content_text)
        
        # 元数据
        if self.message.metadata:
            metadata_label = QLabel("元数据:")
            metadata_label.setProperty("heading", "h3")
            layout.addWidget(metadata_label)
            
            metadata_text = QTextEdit()
            metadata_text.setPlainText(str(self.message.metadata))
            metadata_text.setReadOnly(True)
            metadata_text.setMaximumHeight(100)
            layout.addWidget(metadata_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制内容")
        copy_btn.clicked.connect(self._copy_content)
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setProperty("secondary", "true")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _copy_content(self):
        """复制内容到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.message.content)
        QMessageBox.information(self, "成功", "内容已复制到剪贴板")


class HistoryPage(QWidget):
    """消息历史页面 - 显示和管理历史消息"""
    
    def __init__(self, database, message_processor):
        super().__init__()
        self.database = database
        self.message_processor = message_processor
        self.current_messages = []
        
        # 分页加载参数
        self.page_size = 50  # 每页显示50条
        self.current_page = 0  # 当前页码
        self.is_loading = False  # 是否正在加载
        self.has_more = True  # 是否还有更多数据
        
        # 创建异步数据库访问
        from data.async_database import AsyncDatabase
        self.async_db = AsyncDatabase(database)
        
        # 连接信号
        self.async_db.messages_loaded.connect(self._on_messages_loaded)
        self.async_db.search_completed.connect(self._on_search_completed)
        self.async_db.message_deleted.connect(self._on_message_deleted)
        self.async_db.messages_cleared.connect(self._on_messages_cleared)
        self.async_db.operation_error.connect(self._on_error)
        
        # 监听数据库变化信号（事件驱动，真正的实时更新）
        self.database.data_changed.connect(self._on_data_changed)
        
        self._setup_ui()
        
        # 启动时间更新定时器（降低频率，减少CPU占用）
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_time_display)
        self.time_update_timer.start(5000)  # 每5秒更新一次，减少CPU占用
        
        self._load_messages()
    
    def _update_time_display(self):
        """更新时间显示"""
        # 只在非加载/搜索/过滤状态时更新时间
        current_text = self.update_indicator.text()
        if current_text.startswith("实时更新"):
            self.update_indicator.setText(f"实时更新 ({datetime.now().strftime('%H:%M:%S')})")
    
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
        title = QLabel("消息历史")
        title.setProperty("heading", "h2")
        title_layout.addWidget(title)
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 条消息")
        self.stats_label.setStyleSheet("color: #98C379; font-size: 14px; font-weight: bold;")
        title_layout.addWidget(self.stats_label)
        
        self.update_indicator = QLabel("实时更新")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
        title_layout.addWidget(self.update_indicator)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 搜索和过滤区域
        search_card = self._create_search_card()
        layout.addWidget(search_card)
        
        # 消息列表
        list_card = self._create_list_card()
        layout.addWidget(list_card)
        
        # 操作按钮
        actions_layout = QHBoxLayout()
        
        clear_btn = QPushButton("  清空全部")
        clear_btn.setIcon(SvgIcon.get_icon("delete", "#FFFFFF", 14))
        clear_btn.setStyleSheet("""
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
        clear_btn.clicked.connect(self._clear_all)
        actions_layout.addWidget(clear_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # 不再使用定时器轮询，改为事件驱动
        # 当数据库发生变化时，会自动触发_on_data_changed方法
    
    def _create_search_card(self) -> QFrame:
        """创建搜索卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = QLabel("搜索和过滤")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        search_label = QLabel("关键词:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或内容...")
        self.search_input.returnPressed.connect(self._search_messages)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._search_messages)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # 时间范围
        time_layout = QHBoxLayout()
        
        time_label = QLabel("时间范围:")
        time_layout.addWidget(time_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        time_layout.addWidget(self.start_date)
        
        time_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        time_layout.addWidget(self.end_date)
        
        filter_btn = QPushButton("按时间过滤")
        filter_btn.clicked.connect(self._filter_by_time)
        time_layout.addWidget(filter_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.setProperty("secondary", "true")
        reset_btn.clicked.connect(self._load_messages)
        time_layout.addWidget(reset_btn)
        
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        return card
    
    def _create_list_card(self) -> QFrame:
        """创建消息列表卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题和统计
        header_layout = QHBoxLayout()
        
        title = QLabel("消息列表")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.count_label = QLabel("共 0 条消息")
        self.count_label.setProperty("secondary", "true")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "来源", "标题", "内容预览", "操作"])
        
        # 设置表格样式 - 允许用户调整列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 内容预览自动拉伸
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 操作列固定宽度
        
        # 设置默认列宽
        header.resizeSection(0, 150)  # 时间
        header.resizeSection(1, 120)  # 来源
        header.resizeSection(2, 200)  # 标题
        header.resizeSection(4, 100)  # 操作（固定宽度）
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # 监听垂直滚动条，实现懒加载
        scrollbar = self.table.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll)
        
        layout.addWidget(self.table)
        
        # 加载更多提示标签
        self.load_more_label = QLabel("")
        self.load_more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_more_label.setStyleSheet("color: #ABB2BF; font-size: 12px; padding: 10px;")
        layout.addWidget(self.load_more_label)
        
        return card
    
    def _on_data_changed(self):
        """数据库数据变化时触发（事件驱动）"""
        # 重置分页状态
        self.current_page = 0
        self.has_more = True
        self._load_messages()
        # 更新时间戳显示
        self.update_indicator.setText(f"实时更新 ({datetime.now().strftime('%H:%M:%S')})")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
    
    def _on_scroll(self, value):
        """滚动条滚动事件 - 实现懒加载"""
        scrollbar = self.table.verticalScrollBar()
        # 当滚动到底部80%时，加载更多数据
        if value >= scrollbar.maximum() * 0.8 and not self.is_loading and self.has_more:
            self._load_more_messages()
    
    def _load_more_messages(self):
        """加载更多消息"""
        if self.is_loading or not self.has_more:
            return
        
        self.is_loading = True
        self.load_more_label.setText("正在加载更多...")
        self.load_more_label.setStyleSheet("color: #E5C07B; font-size: 12px; padding: 10px;")
        
        # 计算下一页的起始和结束索引
        start_idx = (self.current_page + 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        # 获取下一页数据
        next_page_messages = self.current_messages[start_idx:end_idx]
        
        if next_page_messages:
            self.current_page += 1
            self._append_messages_to_table(next_page_messages)
            
            # 检查是否还有更多数据
            if end_idx >= len(self.current_messages):
                self.has_more = False
                self.load_more_label.setText("已加载全部消息")
                self.load_more_label.setStyleSheet("color: #98C379; font-size: 12px; padding: 10px;")
            else:
                self.load_more_label.setText(f"已加载 {end_idx}/{len(self.current_messages)} 条")
                self.load_more_label.setStyleSheet("color: #4A9EFF; font-size: 12px; padding: 10px;")
        else:
            self.has_more = False
            self.load_more_label.setText("已加载全部消息")
            self.load_more_label.setStyleSheet("color: #98C379; font-size: 12px; padding: 10px;")
        
        self.is_loading = False
    
    def _load_messages(self):
        """异步加载所有消息"""
        # 显示加载状态
        self.update_indicator.setText("加载中...")
        self.update_indicator.setStyleSheet("color: #E5C07B; font-size: 12px;")
        
        # 重置分页状态
        self.current_page = 0
        self.has_more = True
        self.is_loading = False
        
        # 异步加载
        self.async_db.get_all_messages_async()
    
    def _on_messages_loaded(self, messages):
        """消息加载完成"""
        self.current_messages = messages
        self._update_table()
        self.search_input.clear()
        
        # 更新指示器
        self.update_indicator.setText(f"实时更新 ({datetime.now().strftime('%H:%M:%S')})")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
    
    def _search_messages(self):
        """异步搜索消息"""
        keyword = self.search_input.text().strip()
        if not keyword:
            self._load_messages()
            return
        
        # 显示搜索状态
        self.update_indicator.setText("搜索中...")
        self.update_indicator.setStyleSheet("color: #E5C07B; font-size: 12px;")
        
        # 重置分页状态
        self.current_page = 0
        self.has_more = True
        self.is_loading = False
        
        # 异步搜索
        self.async_db.search_messages_async(keyword)
    
    def _on_search_completed(self, messages):
        """搜索完成"""
        self.current_messages = messages
        self._update_table()
        
        # 更新指示器
        self.update_indicator.setText(f"搜索完成 ({len(messages)} 条)")
        self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
    
    def _filter_by_time(self):
        """按时间范围过滤"""
        # 显示过滤状态
        self.update_indicator.setText("过滤中...")
        self.update_indicator.setStyleSheet("color: #E5C07B; font-size: 12px;")
        
        # 异步加载并过滤
        def on_loaded(messages):
            try:
                start = self.start_date.date().toPyDate()
                end = self.end_date.date().toPyDate()
                
                start_timestamp = datetime.combine(start, datetime.min.time()).timestamp()
                end_timestamp = datetime.combine(end, datetime.max.time()).timestamp()
                
                self.current_messages = [
                    msg for msg in messages
                    if start_timestamp <= msg.timestamp <= end_timestamp
                ]
                
                self._update_table()
                self.update_indicator.setText(f"过滤完成 ({len(self.current_messages)} 条)")
                self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
            except Exception as e:
                self._on_error(f"过滤失败: {e}")
        
        # 临时连接信号
        self.async_db.messages_loaded.disconnect(self._on_messages_loaded)
        self.async_db.messages_loaded.connect(on_loaded)
        self.async_db.get_all_messages_async()
        
        # 恢复原始连接
        def restore_connection():
            self.async_db.messages_loaded.disconnect(on_loaded)
            self.async_db.messages_loaded.connect(self._on_messages_loaded)
        
        QTimer.singleShot(100, restore_connection)
    
    def _update_table(self):
        """更新表格显示（分页加载，优化性能）"""
        # 暂时禁用更新，避免频繁重绘
        self.table.setUpdatesEnabled(False)
        
        try:
            self.table.setRowCount(0)
            
            # 更新统计信息
            total = len(self.current_messages)
            self.stats_label.setText(f"总计: {total} 条消息")
            
            # 重置分页状态
            self.current_page = 0
            self.has_more = total > self.page_size
            
            # 只加载第一页数据
            first_page_messages = self.current_messages[:self.page_size]
            
            if first_page_messages:
                self._append_messages_to_table(first_page_messages)
            
            # 更新计数标签
            loaded_count = min(self.page_size, total)
            if total > self.page_size:
                self.count_label.setText(f"共 {total} 条消息")
                self.load_more_label.setText(f"已加载 {loaded_count}/{total} 条，向下滚动加载更多")
                self.load_more_label.setStyleSheet("color: #4A9EFF; font-size: 12px; padding: 10px;")
            else:
                self.count_label.setText(f"共 {total} 条消息")
                self.load_more_label.setText("已加载全部消息")
                self.load_more_label.setStyleSheet("color: #98C379; font-size: 12px; padding: 10px;")
        
        finally:
            # 恢复更新
            self.table.setUpdatesEnabled(True)
    
    def _append_messages_to_table(self, messages):
        """追加消息到表格（用于分页加载）"""
        start_row = self.table.rowCount()
        
        for idx, message in enumerate(messages):
            row = start_row + idx
            self.table.insertRow(row)
            
            # 时间
            time_str = datetime.fromtimestamp(message.timestamp).strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            self.table.setItem(row, 0, time_item)
            
            # 来源
            source_item = QTableWidgetItem(message.source)
            self.table.setItem(row, 1, source_item)
            
            # 标题
            title_item = QTableWidgetItem(message.title)
            self.table.setItem(row, 2, title_item)
            
            # 内容预览
            preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
            content_item = QTableWidgetItem(preview)
            self.table.setItem(row, 3, content_item)
            
            # 操作按钮
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_widget.setLayout(actions_layout)
            
            view_btn = QPushButton("查看")
            view_btn.setToolTip("查看详情")
            view_btn.setMaximumWidth(60)
            view_btn.clicked.connect(lambda checked, m=message: self._view_message(m))
            actions_layout.addWidget(view_btn)
            
            delete_btn = QPushButton("删除")
            delete_btn.setToolTip("删除")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #C5444F;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #D75661;
                }
                QPushButton:pressed {
                    background-color: #B3323D;
                }
            """)
            delete_btn.clicked.connect(lambda checked, m=message: self._delete_message(m))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 4, actions_widget)
    
    def _view_message(self, message):
        """查看消息详情"""
        dialog = MessageDetailDialog(message, self)
        dialog.exec()
    
    def _delete_message(self, message):
        """异步删除消息"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除消息 '{message.title}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 保存消息引用
            self._deleting_message = message
            # 异步删除
            self.async_db.delete_message_async(message.id)
    
    def _on_message_deleted(self, success):
        """消息删除完成"""
        if success and hasattr(self, '_deleting_message'):
            try:
                self.current_messages.remove(self._deleting_message)
                self._update_table()
                # 不显示成功提示，避免打断用户
            except ValueError:
                pass
            finally:
                delattr(self, '_deleting_message')
    
    def _clear_all(self):
        """异步清空所有消息"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有历史消息吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 显示清空状态
            self.update_indicator.setText("清空中...")
            self.update_indicator.setStyleSheet("color: #E5C07B; font-size: 12px;")
            
            # 异步清空
            self.async_db.clear_all_messages_async()
    
    def _on_messages_cleared(self, success):
        """消息清空完成"""
        if success:
            self.current_messages = []
            self._update_table()
            self.update_indicator.setText("已清空")
            self.update_indicator.setStyleSheet("color: #98C379; font-size: 12px;")
    
    def _on_error(self, error_msg):
        """操作出错"""
        self.update_indicator.setText("操作失败")
        self.update_indicator.setStyleSheet("color: #C5444F; font-size: 12px;")
        QMessageBox.critical(self, "错误", error_msg)
