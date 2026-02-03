"""
消息源配置对话框
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QCursor
import json


class SourceConfigDialog(QDialog):
    """消息源配置对话框"""
    
    def __init__(self, source_type, source_config=None, parent=None):
        super().__init__(parent)
        self.source_type = source_type
        self.source_config = source_config or {}
        self.fields = {}
        self._setup_ui()
        if source_config:
            self._load_config()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"配置 {self.source_type} 消息源")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)
        form_layout = QFormLayout()
        content.setLayout(form_layout)
        
        # 通用字段
        self.fields['enabled'] = QCheckBox("启用")
        self.fields['enabled'].setChecked(True)
        form_layout.addRow("", self.fields['enabled'])
        
        self.fields['name'] = QLineEdit()
        self.fields['name'].setPlaceholderText("为此消息源起个名字")
        form_layout.addRow("名称*:", self.fields['name'])
        
        # 根据类型添加特定字段
        self._add_type_specific_fields(form_layout)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _add_type_specific_fields(self, layout):
        """添加特定类型的字段"""
        if self.source_type == "mqtt":
            # 根据本地MQTT服务状态决定默认Broker地址
            default_broker = self._get_default_mqtt_broker()
            
            self.fields['broker'] = QLineEdit()
            if default_broker:
                self.fields['broker'].setText(default_broker)
            self.fields['broker'].setPlaceholderText("mqtt.example.com")
            layout.addRow("Broker*:", self.fields['broker'])
            
            self.fields['port'] = QSpinBox()
            self.fields['port'].setRange(1, 65535)
            self.fields['port'].setValue(1883)  # 默认端口改为1883
            layout.addRow("端口:", self.fields['port'])
            
            self.fields['username'] = QLineEdit()
            self.fields['username'].setPlaceholderText("选填")
            layout.addRow("用户名:", self.fields['username'])
            
            self.fields['password'] = QLineEdit()
            self.fields['password'].setEchoMode(QLineEdit.EchoMode.Password)
            self.fields['password'].setPlaceholderText("选填")
            layout.addRow("密码:", self.fields['password'])
            
            self.fields['topic'] = QLineEdit()
            self.fields['topic'].setText("/WMH")  # 默认主题
            self.fields['topic'].setPlaceholderText("topic/name")
            layout.addRow("主题*:", self.fields['topic'])
            
            self.fields['use_tls'] = QCheckBox("使用TLS加密")
            self.fields['use_tls'].setChecked(False)  # 本地MQTT不需要TLS
            layout.addRow("", self.fields['use_tls'])
            
            # 添加JSON模板
            self._add_json_template(layout, "MQTT")

        
        elif self.source_type == "websocket":
            self.fields['url'] = QLineEdit()
            self.fields['url'].setPlaceholderText("wss://example.com/ws")
            layout.addRow("URL*:", self.fields['url'])
            
            self.fields['ping_interval'] = QSpinBox()
            self.fields['ping_interval'].setRange(1, 300)
            self.fields['ping_interval'].setValue(30)
            layout.addRow("心跳间隔(秒):", self.fields['ping_interval'])
            
            self.fields['reconnect'] = QCheckBox("自动重连")
            self.fields['reconnect'].setChecked(True)
            layout.addRow("", self.fields['reconnect'])
            
            # 添加JSON模板
            self._add_json_template(layout, "WebSocket")
        
        elif self.source_type == "rss":
            self.fields['url'] = QLineEdit()
            self.fields['url'].setPlaceholderText("https://example.com/feed.xml")
            layout.addRow("RSS URL*:", self.fields['url'])
            
            self.fields['poll_interval'] = QSpinBox()
            self.fields['poll_interval'].setRange(60, 3600)
            self.fields['poll_interval'].setValue(300)
            layout.addRow("轮询间隔(秒):", self.fields['poll_interval'])
            
            # 添加格式说明
            self._add_format_hint(layout, "RSS", 
                "自动解析 RSS/Atom feed\n"
                "无需特殊格式，自动提取标题和内容")
        
        elif self.source_type == "file_monitor":
            path_layout = QHBoxLayout()
            self.fields['path'] = QLineEdit()
            self.fields['path'].setPlaceholderText("C:\\logs")
            path_layout.addWidget(self.fields['path'])
            
            browse_btn = QPushButton("浏览...")
            browse_btn.clicked.connect(self._browse_folder)
            path_layout.addWidget(browse_btn)
            layout.addRow("监控路径*:", path_layout)
            
            self.fields['recursive'] = QCheckBox("递归监控子文件夹")
            layout.addRow("", self.fields['recursive'])
            
            self.fields['file_patterns'] = QLineEdit()
            self.fields['file_patterns'].setPlaceholderText("*.log, *.txt")
            layout.addRow("文件类型:", self.fields['file_patterns'])
            
            self.fields['watch_create'] = QCheckBox("监控文件创建")
            self.fields['watch_create'].setChecked(True)
            layout.addRow("", self.fields['watch_create'])
            
            self.fields['watch_modify'] = QCheckBox("监控文件修改")
            self.fields['watch_modify'].setChecked(True)
            layout.addRow("", self.fields['watch_modify'])
            
            self.fields['watch_delete'] = QCheckBox("监控文件删除")
            layout.addRow("", self.fields['watch_delete'])
            
            self.fields['include_content'] = QCheckBox("包含文件内容预览")
            layout.addRow("", self.fields['include_content'])
            
            # 添加格式说明
            self._add_format_hint(layout, "文件监控", 
                "自动监控文件变化\n"
                "无需外部输入，自动生成通知")
        
        elif self.source_type == "clipboard":
            self.fields['poll_interval'] = QSpinBox()
            self.fields['poll_interval'].setRange(1, 10)
            self.fields['poll_interval'].setValue(1)
            layout.addRow("检查间隔(秒):", self.fields['poll_interval'])
            
            self.fields['min_length'] = QSpinBox()
            self.fields['min_length'].setRange(1, 1000)
            self.fields['min_length'].setValue(1)
            layout.addRow("最小长度:", self.fields['min_length'])
            
            self.fields['max_length'] = QSpinBox()
            self.fields['max_length'].setRange(100, 10000)
            self.fields['max_length'].setValue(1000)
            layout.addRow("最大长度:", self.fields['max_length'])
            
            self.fields['ignore_duplicates'] = QCheckBox("忽略重复内容")
            self.fields['ignore_duplicates'].setChecked(True)
            layout.addRow("", self.fields['ignore_duplicates'])
            
            # 添加格式说明
            self._add_format_hint(layout, "剪贴板", 
                "自动监控剪贴板内容\n"
                "无需外部输入，自动捕获复制的文本")
        
        elif self.source_type == "webhook":
            self.fields['port'] = QSpinBox()
            self.fields['port'].setRange(1024, 65535)
            self.fields['port'].setValue(8080)
            layout.addRow("端口*:", self.fields['port'])
            
            self.fields['path'] = QLineEdit()
            self.fields['path'].setPlaceholderText("/webhook")
            self.fields['path'].setText("/webhook")
            layout.addRow("路径:", self.fields['path'])
            
            # 添加JSON模板
            self._add_json_template(layout, "Webhook")
        
        elif self.source_type == "api":
            self.fields['url'] = QLineEdit()
            self.fields['url'].setPlaceholderText("https://api.example.com/messages")
            layout.addRow("API URL*:", self.fields['url'])
            
            self.fields['method'] = QComboBox()
            self.fields['method'].addItems(["GET", "POST"])
            layout.addRow("方法:", self.fields['method'])
            
            self.fields['poll_interval'] = QSpinBox()
            self.fields['poll_interval'].setRange(10, 3600)
            self.fields['poll_interval'].setValue(60)
            layout.addRow("轮询间隔(秒):", self.fields['poll_interval'])
            
            # 添加JSON模板
            self._add_json_template(layout, "API")
        
        elif self.source_type == "imap":
            self.fields['server'] = QLineEdit()
            self.fields['server'].setPlaceholderText("imap.gmail.com")
            layout.addRow("服务器*:", self.fields['server'])
            
            self.fields['port'] = QSpinBox()
            self.fields['port'].setRange(1, 65535)
            self.fields['port'].setValue(993)
            layout.addRow("端口:", self.fields['port'])
            
            self.fields['username'] = QLineEdit()
            layout.addRow("用户名*:", self.fields['username'])
            
            self.fields['password'] = QLineEdit()
            self.fields['password'].setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("密码*:", self.fields['password'])
            
            self.fields['folder'] = QLineEdit()
            self.fields['folder'].setText("INBOX")
            layout.addRow("文件夹:", self.fields['folder'])
            
            self.fields['poll_interval'] = QSpinBox()
            self.fields['poll_interval'].setRange(30, 3600)
            self.fields['poll_interval'].setValue(60)
            layout.addRow("检查间隔(秒):", self.fields['poll_interval'])
            
            # 添加格式说明
            self._add_format_hint(layout, "IMAP", 
                "自动解析邮件内容\n"
                "无需特殊格式，自动提取主题和正文")
    
    def _add_json_template(self, layout, source_type):
        """添加JSON模板和一键复制功能"""
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel(f"📋 {source_type} 消息格式（仅支持JSON）")
        title_label.setStyleSheet("color: #4A9EFF; font-weight: bold; margin-top: 15px; font-size: 12px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        title_widget = QWidget()
        title_widget.setLayout(title_layout)
        layout.addRow("", title_widget)
        
        # JSON模板
        if source_type == "API":
            json_template = '''{
  "messages": [
    {
      "title": "消息标题",
      "content": "消息内容",
      "source": "来源名称"
    }
  ]
}

或单条消息：
{
  "title": "消息标题",
  "content": "消息内容",
  "source": "来源名称"
}'''
        else:
            json_template = '''{
  "title": "消息标题",
  "content": "消息内容",
  "source": "来源名称"
}'''
        
        # 模板显示区域
        template_text = QTextEdit()
        template_text.setPlainText(json_template)
        template_text.setReadOnly(True)
        template_text.setMaximumHeight(150)
        template_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E2329;
                color: #E5C07B;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #3A4149;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.5;
            }
        """)
        layout.addRow("", template_text)
        
        # 说明文字
        hint_text = QLabel("注：source 字段可选，用于自定义弹窗左上角显示的来源名称")
        hint_text.setStyleSheet("""
            QLabel {
                color: #B8BFC6;
                font-size: 10px;
                padding: 5px 10px;
                background-color: #2A3139;
                border-radius: 3px;
                border-left: 3px solid #E5C07B;
            }
        """)
        hint_text.setWordWrap(True)
        layout.addRow("", hint_text)
        
        # 复制按钮
        copy_btn = QPushButton("📋 一键复制JSON模板")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5AAFFF;
            }
            QPushButton:pressed {
                background-color: #3A8FEF;
            }
        """)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(json_template, copy_btn))
        layout.addRow("", copy_btn)
    
    def _copy_to_clipboard(self, text, button):
        """复制文本到剪贴板并显示反馈"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            # 临时改变按钮文字显示反馈
            original_text = button.text()
            button.setText("✓ 已复制到剪贴板")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #98C379;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
            
            # 1秒后恢复
            QTimer.singleShot(1000, lambda: self._restore_button(button, original_text))
            
        except Exception as e:
            button.setText("✗ 复制失败")
            QTimer.singleShot(1000, lambda: self._restore_button(button, "📋 一键复制JSON模板"))
    
    def _restore_button(self, button, original_text):
        """恢复按钮原始状态"""
        button.setText(original_text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5AAFFF;
            }
            QPushButton:pressed {
                background-color: #3A8FEF;
            }
        """)
    
    def _browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.fields['path'].setText(folder)
    
    def _get_default_mqtt_broker(self):
        """获取默认MQTT Broker地址
        
        如果本地MQTT服务正在运行，返回本机内网IP
        否则返回空字符串
        """
        try:
            # 尝试从主窗口获取本地MQTT管理器
            from PyQt6.QtWidgets import QApplication
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'local_mqtt_manager'):
                    main_window = widget
                    break
            
            if main_window and hasattr(main_window, 'local_mqtt_manager'):
                mqtt_manager = main_window.local_mqtt_manager
                # 检查MQTT服务是否正在运行
                if mqtt_manager and mqtt_manager.is_running():
                    # 获取本机内网IP
                    from utils.network_utils import get_local_ip
                    local_ip = get_local_ip()
                    if local_ip and local_ip != "127.0.0.1":
                        return local_ip
            
            # 如果本地MQTT服务没有运行，返回空字符串
            return ""
        except Exception as e:
            # 出错时返回空字符串
            return ""
    
    def _load_config(self):
        """加载配置到字段"""
        for key, widget in self.fields.items():
            if key in self.source_config:
                value = self.source_config[key]
                if isinstance(widget, QCheckBox):
                    widget.setChecked(value)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
    
    def get_config(self):
        """获取配置"""
        config = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                config[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                text = widget.text().strip()
                # 处理file_patterns
                if key == 'file_patterns' and text:
                    config[key] = [p.strip() for p in text.split(',')]
                else:
                    config[key] = text
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
        
        return config
