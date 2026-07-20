"""
WinMsgHub - 消息源配置页面（每种类型独立管理）
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ui.svg_icons import SvgIcon
from ui.icon_label import IconLabel
from utils.logger import get_logger

logger = get_logger(__name__)


class SourcesPage(QWidget):
    """消息源配置页面"""
    
    reload_requested = pyqtSignal()
    
    def __init__(self, config_manager, message_processor):
        super().__init__()
        self.config_manager = config_manager
        self.message_processor = message_processor
        self._setup_ui()
        
        # 不再使用定时器轮询，改为事件驱动
        # 当配置发生变化时，通过reload_requested信号通知
        # 连接器状态变化会自动反映在UI上
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content.setLayout(content_layout)
        
        # 标题
        title = QLabel("消息源配置")
        title.setProperty("heading", "h2")
        content_layout.addWidget(title)
        
        # 选项卡
        tabs = QTabWidget()
        
        # 为每种消息源类型创建独立的管理标签页
        tabs.addTab(self._create_mqtt_manager(), "MQTT")
        tabs.addTab(self._create_websocket_manager(), "WebSocket")
        tabs.addTab(self._create_rss_manager(), "RSS订阅")
        tabs.addTab(self._create_file_monitor_manager(), "文件监控")
        tabs.addTab(self._create_clipboard_manager(), "剪贴板")
        tabs.addTab(self._create_webhook_manager(), "Webhook")
        tabs.addTab(self._create_api_manager(), "API轮询")
        tabs.addTab(self._create_imap_manager(), "IMAP邮件")
        
        content_layout.addWidget(tabs)

    
    def _create_source_manager(self, source_type, display_name):
        """创建通用的消息源管理器（支持多实例）"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 顶部操作栏
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton(f"  添加{display_name}")
        add_btn.setIcon(SvgIcon.get_icon("plus", "#FFFFFF", 14))
        add_btn.clicked.connect(lambda: self._add_source(source_type))
        add_btn.setStyleSheet("background: #4CAF50; color: white; padding: 8px 15px; font-weight: bold;")
        toolbar.addWidget(add_btn)
        
        refresh_btn = QPushButton("  刷新")
        refresh_btn.setIcon(SvgIcon.get_icon("refresh", "#4A9EFF", 14))
        refresh_btn.clicked.connect(lambda: self._refresh_list(source_type))
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        
        count_label = QLabel(f"共 0 个{display_name}")
        count_label.setStyleSheet("color: #98C379; font-weight: bold;")
        toolbar.addWidget(count_label)
        
        layout.addLayout(toolbar)
        
        # 列表
        list_widget = QListWidget()
        list_widget.setAlternatingRowColors(True)
        list_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3A3F4B;
            }
            QListWidget::item:selected {
                background: #2C5F8D;
            }
        """)
        layout.addWidget(list_widget)
        
        # 底部操作按钮
        btn_layout = QHBoxLayout()
        
        edit_btn = QPushButton("  编辑")
        edit_btn.setIcon(SvgIcon.get_icon("edit", "#4A9EFF", 14))
        edit_btn.clicked.connect(lambda: self._edit_source(source_type, list_widget))
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("  删除")
        delete_btn.setIcon(SvgIcon.get_icon("delete", "#FFFFFF", 14))
        delete_btn.clicked.connect(lambda: self._delete_source(source_type, list_widget))
        delete_btn.setStyleSheet("background: #f44336; color: white;")
        btn_layout.addWidget(delete_btn)
        
        toggle_btn = QPushButton("  启用/禁用")
        toggle_btn.setIcon(SvgIcon.get_icon("refresh", "#98C379", 14))
        toggle_btn.clicked.connect(lambda: self._toggle_source(source_type, list_widget))
        btn_layout.addWidget(toggle_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 保存引用
        setattr(self, f'{source_type}_list', list_widget)
        setattr(self, f'{source_type}_count', count_label)
        
        # 加载数据
        self._refresh_list(source_type)
        
        return widget
    
    def _create_single_source_config(self, source_type, display_name):
        """创建单例消息源配置（不支持多实例）"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 说明
        from ui.icon_label import IconLabel
        info = IconLabel("lightbulb", f"{display_name}只需要一个实例即可", "#4A9EFF", 14)
        info.text_label.setWordWrap(True)
        info.setStyleSheet("background: #1E3A5F; padding: 10px; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # 状态显示
        status_layout = QHBoxLayout()
        status_label = QLabel("当前状态:")
        status_layout.addWidget(status_label)
        
        status_value = QLabel("未配置")
        status_value.setStyleSheet("color: #E06C75; font-weight: bold;")
        status_layout.addWidget(status_value)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 配置按钮
        btn_layout = QHBoxLayout()
        
        config_btn = QPushButton(f"  配置{display_name}")
        config_btn.setIcon(SvgIcon.get_icon("settings", "#FFFFFF", 14))
        config_btn.clicked.connect(lambda: self._config_single_source(source_type))
        config_btn.setStyleSheet("background: #4CAF50; color: white; padding: 10px 20px; font-weight: bold;")
        btn_layout.addWidget(config_btn)
        
        toggle_btn = QPushButton("  启用/禁用")
        toggle_btn.setIcon(SvgIcon.get_icon("refresh", "#98C379", 14))
        toggle_btn.clicked.connect(lambda: self._toggle_single_source(source_type))
        btn_layout.addWidget(toggle_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 配置详情
        details_group = QGroupBox("配置详情")
        details_layout = QVBoxLayout()
        
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(200)
        details_layout.addWidget(details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        layout.addStretch()
        
        # 保存引用
        setattr(self, f'{source_type}_status', status_value)
        setattr(self, f'{source_type}_details', details_text)
        
        # 加载数据
        self._refresh_single_source(source_type)
        
        return widget
    
    def _create_mqtt_manager(self):
        return self._create_source_manager('mqtt', 'MQTT消息源')
    
    def _create_websocket_manager(self):
        return self._create_source_manager('websocket', 'WebSocket消息源')
    
    def _create_rss_manager(self):
        return self._create_source_manager('rss', 'RSS订阅源')
    
    def _create_file_monitor_manager(self):
        return self._create_source_manager('file_monitor', '文件监控')
    
    def _create_clipboard_manager(self):
        """创建剪贴板配置（单例）"""
        return self._create_single_source_config('clipboard', '剪贴板监控')
    
    def _create_webhook_manager(self):
        return self._create_source_manager('webhook', 'Webhook服务')
    
    def _create_api_manager(self):
        return self._create_source_manager('api', 'API轮询')
    
    def _create_imap_manager(self):
        return self._create_source_manager('imap', 'IMAP邮件')
    
    def _refresh_list(self, source_type):
        """刷新列表"""
        list_widget = getattr(self, f'{source_type}_list')
        count_label = getattr(self, f'{source_type}_count')
        
        list_widget.clear()
        
        config = self.config_manager.get_all()
        sources = config.get('message_sources', {}).get(source_type, [])
        
        if not isinstance(sources, list):
            sources = []
        
        for idx, source in enumerate(sources):
            name = source.get('name', f'{source_type}_{idx}')
            enabled = source.get('enabled', False)
            status = "已启用" if enabled else "已禁用"
            status_color = "#98C379" if enabled else "#E06C75"
            
            item = QListWidgetItem(f"{name} - {status}")
            item.setData(Qt.ItemDataRole.UserRole, {'index': idx, 'config': source})
            
            if enabled:
                item.setForeground(QColor("#98C379"))
            else:
                item.setForeground(QColor("#6C757D"))
            
            list_widget.addItem(item)
        
        count_label.setText(f"共 {len(sources)} 个")
    
    def _add_source(self, source_type):
        """添加消息源"""
        from ui.dialogs.source_config_dialog import SourceConfigDialog
        
        dialog = SourceConfigDialog(source_type, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            
            if not config.get('name'):
                QMessageBox.warning(self, "警告", "请输入消息源名称！")
                return
            
            all_config = self.config_manager.get_all()
            if 'message_sources' not in all_config:
                all_config['message_sources'] = {}
            if source_type not in all_config['message_sources']:
                all_config['message_sources'][source_type] = []
            
            if not isinstance(all_config['message_sources'][source_type], list):
                all_config['message_sources'][source_type] = []
            
            all_config['message_sources'][source_type].append(config)
            
            self.config_manager.config = all_config
            self.config_manager.save_config()
            
            self.reload_requested.emit()
            self._refresh_list(source_type)
            
            QMessageBox.information(self, "成功", f"已添加并立即生效！")
    
    def _edit_source(self, source_type, list_widget):
        """编辑消息源"""
        from ui.dialogs.source_config_dialog import SourceConfigDialog
        
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要编辑的消息源！")
            return
        
        data = current_item.data(Qt.ItemDataRole.UserRole)
        old_config = data['config']
        
        dialog = SourceConfigDialog(source_type, old_config, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            
            all_config = self.config_manager.get_all()
            
            # 确保配置结构存在
            if 'message_sources' not in all_config:
                all_config['message_sources'] = {}
            if source_type not in all_config['message_sources']:
                all_config['message_sources'][source_type] = []
            
            sources = all_config['message_sources'][source_type]
            
            # 通过配置内容查找并更新（而不是使用索引）
            for i, src in enumerate(sources):
                if src == old_config:
                    sources[i] = new_config
                    break
            
            self.config_manager.config = all_config
            self.config_manager.save_config()
            
            self.reload_requested.emit()
            self._refresh_list(source_type)
            
            QMessageBox.information(self, "成功", "配置已更新并立即生效！")
    
    def _delete_source(self, source_type, list_widget):
        """删除消息源"""
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的消息源！")
            return
        
        data = current_item.data(Qt.ItemDataRole.UserRole)
        index = data['index']
        config = data['config']
        name = config.get('name', '未命名')
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            all_config = self.config_manager.get_all()
            
            # 确保配置结构存在
            if 'message_sources' not in all_config:
                all_config['message_sources'] = {}
            if source_type not in all_config['message_sources']:
                all_config['message_sources'][source_type] = []
            
            sources = all_config['message_sources'][source_type]
            
            # 通过配置内容查找并删除（而不是使用索引，因为索引可能已变化）
            for i, src in enumerate(sources):
                if src == config:
                    del sources[i]
                    break
            
            self.config_manager.config = all_config
            self.config_manager.save_config()
            
            self.reload_requested.emit()
            self._refresh_list(source_type)
            
            QMessageBox.information(self, "成功", f"已删除！")
    
    def _toggle_source(self, source_type, list_widget):
        """启用/禁用消息源"""
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要切换的消息源！")
            return
        
        data = current_item.data(Qt.ItemDataRole.UserRole)
        index = data['index']
        
        all_config = self.config_manager.get_all()
        sources = all_config.get('message_sources', {}).get(source_type, [])
        
        # 防御：配置可能已被其他途径修改，索引可能失效
        if not isinstance(sources, list) or not (0 <= index < len(sources)):
            QMessageBox.warning(self, "警告", "配置已发生变化，请刷新列表后重试！")
            self._refresh_list(source_type)
            return
        
        current_enabled = sources[index].get('enabled', False)
        sources[index]['enabled'] = not current_enabled
        
        self.config_manager.config = all_config
        self.config_manager.save_config()
        
        self.reload_requested.emit()
        self._refresh_list(source_type)
        
        status = "启用" if not current_enabled else "禁用"
        QMessageBox.information(self, "成功", f"已{status}！")
    
    def _refresh_single_source(self, source_type):
        """刷新单例消息源状态"""
        status_label = getattr(self, f'{source_type}_status')
        details_text = getattr(self, f'{source_type}_details')
        
        config = self.config_manager.get_all()
        source_config = config.get('message_sources', {}).get(source_type, {})
        
        # 如果是列表格式，取第一个
        if isinstance(source_config, list):
            source_config = source_config[0] if source_config else {}
        
        if source_config and source_config.get('enabled'):
            status_label.setText("已启用")
            status_label.setStyleSheet("color: #98C379; font-weight: bold;")
        elif source_config:
            status_label.setText("已禁用")
            status_label.setStyleSheet("color: #E5C07B; font-weight: bold;")
        else:
            status_label.setText("未配置")
            status_label.setStyleSheet("color: #E06C75; font-weight: bold;")
        
        # 显示配置详情
        if source_config:
            details = []
            for key, value in source_config.items():
                if key != 'enabled':
                    details.append(f"{key}: {value}")
            details_text.setPlainText("\n".join(details) if details else "无配置信息")
        else:
            details_text.setPlainText("尚未配置")
    
    def _config_single_source(self, source_type):
        """配置单例消息源"""
        from ui.dialogs.source_config_dialog import SourceConfigDialog
        
        try:
            # 先从文件重新加载最新配置
            self.config_manager.reload_config()
            
            # 获取现有配置
            config = self.config_manager.get_all()
            source_list = config.get('message_sources', {}).get(source_type, [])
            
            # 调试日志
            logger.info(f"[Config] 消息源类型: {source_type}")
            logger.info(f"[Config] 配置类型: {type(source_list)}")
            logger.info(f"[Config] 配置内容: {source_list}")
            
            # 确保是列表格式
            if isinstance(source_list, dict):
                source_config = source_list
                logger.info(f"[Config] 检测到字典格式")
            elif isinstance(source_list, list):
                source_config = source_list[0] if source_list else {}
                logger.info(f"[Config] 从列表中获取配置: {source_config}")
            else:
                source_config = {}
                logger.warning(f"[Config] 未知格式，使用空配置")
            
            dialog = SourceConfigDialog(source_type, source_config, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_config = dialog.get_config()
                
                logger.info(f"[Config] 新配置: {new_config}")
                
                # 保存为列表格式（单例也用列表，只是只有一个元素）
                all_config = self.config_manager.get_all()
                if 'message_sources' not in all_config:
                    all_config['message_sources'] = {}
                
                # 保存为列表格式
                all_config['message_sources'][source_type] = [new_config]
                
                logger.info(f"[Config] 保存配置: {all_config['message_sources'][source_type]}")
                
                # 直接更新内存中的配置
                self.config_manager.config = all_config
                # 保存到文件
                self.config_manager.save_config()
                
                logger.info(f"[Config] 配置已保存，触发连接器重新加载")
                
                self.reload_requested.emit()
                self._refresh_single_source(source_type)
                
                QMessageBox.information(self, "成功", "配置已保存并立即生效！")
                
        except Exception as e:
            logger.error(f"[Config] 配置消息源失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"配置失败: {str(e)}")
    
    def _toggle_single_source(self, source_type):
        """启用/禁用单例消息源"""
        try:
            # 先从文件重新加载最新配置
            self.config_manager.reload_config()
            
            config = self.config_manager.get_all()
            source_list = config.get('message_sources', {}).get(source_type, [])
            
            # 调试日志
            logger.info(f"[Toggle] 消息源类型: {source_type}")
            logger.info(f"[Toggle] 配置类型: {type(source_list)}")
            logger.info(f"[Toggle] 配置内容: {source_list}")
            
            # 确保是列表格式
            if isinstance(source_list, dict):
                source_config = source_list
                logger.info(f"[Toggle] 检测到字典格式，转换为配置对象")
            elif isinstance(source_list, list):
                if not source_list:
                    logger.warning(f"[Toggle] 配置列表为空")
                    QMessageBox.warning(self, "警告", "请先配置消息源！")
                    return
                source_config = source_list[0].copy()  # 复制一份，避免直接修改
                logger.info(f"[Toggle] 从列表中获取第一个配置")
            else:
                logger.error(f"[Toggle] 未知的配置格式: {type(source_list)}")
                QMessageBox.warning(self, "警告", "请先配置消息源！")
                return
            
            if not source_config:
                logger.warning(f"[Toggle] 配置对象为空")
                QMessageBox.warning(self, "警告", "请先配置消息源！")
                return
            
            current_enabled = source_config.get('enabled', False)
            source_config['enabled'] = not current_enabled
            
            logger.info(f"[Toggle] 切换状态: {current_enabled} -> {not current_enabled}")
            
            # 重新获取完整配置
            all_config = self.config_manager.get_all()
            # 保存为列表格式
            all_config['message_sources'][source_type] = [source_config]
            
            logger.info(f"[Toggle] 保存配置: {all_config['message_sources'][source_type]}")
            
            # 直接更新内存中的配置
            self.config_manager.config = all_config
            # 保存到文件
            self.config_manager.save_config()
            
            logger.info(f"[Toggle] 配置已保存，触发连接器重新加载")
            
            self.reload_requested.emit()
            self._refresh_single_source(source_type)
            
            status = "启用" if not current_enabled else "禁用"
            QMessageBox.information(self, "成功", f"已{status}！")
        except Exception as e:
            logger.error(f"切换消息源状态失败: {e}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
    
    def force_save(self):
        """强制立即保存配置（用于页面切换或程序退出时）"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            # sources_page的配置是立即保存的，但为了保险，再强制保存一次
            self.config_manager.save_config()
            logger.info("[消息源配置] 配置已强制保存到文件")
        except Exception as e:
            logger.error(f"[消息源配置] 强制保存失败: {e}", exc_info=True)

