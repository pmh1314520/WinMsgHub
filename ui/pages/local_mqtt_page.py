"""
WinMsgHub - 本地MQTT服务管理页面
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QGroupBox, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from utils.network_utils import get_local_ip
from utils.resource_path import get_resource_url
from ui.svg_icons import SvgIcon
from ui.icon_label import IconLabel
from utils.logger import get_logger

logger = get_logger(__name__)


class LocalMQTTPage(QWidget):
    """本地MQTT服务管理页面"""
    
    def __init__(self, local_mqtt_manager):
        super().__init__()
        self.mqtt_manager = local_mqtt_manager
        self.config_manager = local_mqtt_manager.config_manager  # 添加 config_manager 引用
        
        # 缓存上一次的状态，避免不必要的UI更新
        self._last_status = None
        
        # 异步任务管理器
        from utils.async_worker import AsyncTaskManager
        self._task_manager = AsyncTaskManager()
        
        self._setup_ui()
        
        # 启动定时器更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_async)
        self.status_timer.start(2000)  # 每2秒检查一次
        
        # 立即执行一次异步更新
        self._update_status_async()
    
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
        title = QLabel("本地MQTT服务")
        title.setProperty("heading", "h2")
        layout.addWidget(title)
        
        # 重要提示卡片
        tip_card = self._create_tip_card()
        layout.addWidget(tip_card)
        
        # 服务状态卡片
        status_card = self._create_status_card()
        layout.addWidget(status_card)
        
        # 控制按钮卡片
        control_card = self._create_control_card()
        layout.addWidget(control_card)
        
        # 使用说明卡片
        guide_card = self._create_guide_card()
        layout.addWidget(guide_card)
        
        layout.addStretch()
    
    def _create_tip_card(self) -> QFrame:
        """创建重要提示卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E5C07B, stop:1 #E06C75);
                border-radius: 8px;
                padding: 2px;
            }
        """)
        
        # 内部容器
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #2A3139;
                border-radius: 6px;
            }
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card.setLayout(card_layout)
        card_layout.addWidget(container)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        container.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("lightbulb", "#E5C07B", 24))
        title_layout.addWidget(icon_label)
        
        title = QLabel("重要提示")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #E5C07B;
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 提示内容
        tip_text = QLabel(
            "若使用本地MQTT服务，<b>强烈建议</b>您将电脑的内网IP配置为<b>静态IP</b>。\n"
            "否则每次路由器重启或DHCP租约到期后，内网IP地址可能会变化，导致其它设备端连接失败。"
        )
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet("""
            font-size: 13px;
            color: #B8BFC6;
            line-height: 1.6;
            padding: 10px;
            background-color: rgba(229, 192, 123, 0.1);
            border-radius: 4px;
        """)
        layout.addWidget(tip_text)
        
        # 配置指南按钮
        guide_btn = QPushButton("  查看静态IP配置教程")
        guide_btn.setIcon(SvgIcon.get_icon("book", "#61AFEF", 14))
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #61AFEF;
                border: 1px solid #61AFEF;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(97, 175, 239, 0.1);
            }
        """)
        guide_btn.clicked.connect(self._show_static_ip_guide)
        layout.addWidget(guide_btn)
        
        return card
    
    def _show_static_ip_guide(self):
        """显示静态IP配置教程"""
        from PyQt6.QtWidgets import QMessageBox
        
        guide = """
<h3 style="color: #61AFEF;">Windows 配置静态IP教程</h3>

<p><b>方法一：通过设置界面（推荐）</b></p>
<ol>
<li>按 <b>Win + I</b> 打开设置</li>
<li>进入 <b>网络和Internet</b></li>
<li>点击 <b>属性</b>（当前连接的网络）</li>
<li>找到 <b>IP设置</b>，点击 <b>编辑</b></li>
<li>选择 <b>手动</b>，打开 <b>IPv4</b></li>
<li>填写以下信息：
<ul>
<li><b>IP地址</b>: 当前显示的IP（如 192.168.1.100）</li>
<li><b>子网掩码</b>: 通常是 255.255.255.0</li>
<li><b>网关</b>: 路由器IP（通常是 192.168.1.1）</li>
<li><b>首选DNS</b>: 可填 8.8.8.8 或路由器IP</li>
</ul>
</li>
<li>点击 <b>保存</b></li>
</ol>

<p><b>方法二：通过控制面板</b></p>
<ol>
<li>打开 <b>控制面板</b> → <b>网络和共享中心</b></li>
<li>点击当前连接的网络</li>
<li>点击 <b>属性</b></li>
<li>双击 <b>Internet协议版本4 (TCP/IPv4)</b></li>
<li>选择 <b>使用下面的IP地址</b></li>
<li>填写IP、子网掩码、网关、DNS</li>
<li>点击 <b>确定</b></li>
</ol>

<p style="color: #E5C07B;"><b>注意事项：</b></p>
<ul>
<li>选择的IP地址应在路由器DHCP范围之外，避免冲突</li>
<li>建议选择较大的IP号（如 192.168.1.200）</li>
<li>配置完成后，建议重启网络适配器或重启电脑</li>
</ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("静态IP配置教程")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(guide)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def _create_status_card(self) -> QFrame:
        """创建服务状态卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("chart", "#61AFEF", 20))
        title_layout.addWidget(icon_label)
        
        title = QLabel("服务状态")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 状态信息
        self.status_label = IconLabel("circle_red", "服务未运行", "#E06C75", 16)
        self.status_label.setStyleSheet("""
            QWidget {
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                background-color: #3A4149;
                border-radius: 8px;
                border-left: 4px solid #E06C75;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 服务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # 服务地址
        ip_layout = QHBoxLayout()
        ip_icon = QLabel()
        ip_icon.setPixmap(SvgIcon.get_pixmap("location", "#61AFEF", 14))
        ip_layout.addWidget(ip_icon)
        self.ip_label = QLabel(f"服务地址: {get_local_ip()}:1883")
        self.ip_label.setStyleSheet("font-size: 13px; color: #B8BFC6;")
        ip_layout.addWidget(self.ip_label)
        ip_layout.addStretch()
        info_layout.addLayout(ip_layout)
        
        # MQTT端口
        port_layout = QHBoxLayout()
        port_icon = QLabel()
        port_icon.setPixmap(SvgIcon.get_pixmap("plug", "#98C379", 14))
        port_layout.addWidget(port_icon)
        self.port_label = QLabel("MQTT端口: 1883 (TCP)")
        self.port_label.setStyleSheet("font-size: 13px; color: #B8BFC6;")
        port_layout.addWidget(self.port_label)
        port_layout.addStretch()
        info_layout.addLayout(port_layout)
        
        # WebSocket
        ws_layout = QHBoxLayout()
        ws_icon = QLabel()
        ws_icon.setPixmap(SvgIcon.get_pixmap("globe", "#E5C07B", 14))
        ws_layout.addWidget(ws_icon)
        self.ws_label = QLabel("WebSocket: 8083/mqtt")
        self.ws_label.setStyleSheet("font-size: 13px; color: #B8BFC6;")
        ws_layout.addWidget(self.ws_label)
        ws_layout.addStretch()
        info_layout.addLayout(ws_layout)
        
        layout.addLayout(info_layout)
        
        return card
    
    def _create_control_card(self) -> QFrame:
        """创建控制按钮卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("gamepad", "#61AFEF", 20))
        title_layout.addWidget(icon_label)
        
        title = QLabel("服务控制")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 启动按钮
        self.start_btn = QPushButton("  启动服务")
        self.start_btn.setIcon(SvgIcon.get_icon("play", "#FFFFFF", 16))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #98C379;
                color: white;
                font-weight: 500;
                font-size: 14px;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #88B369;
            }
            QPushButton:pressed {
                background-color: #78A359;
            }
            QPushButton:disabled {
                background-color: #4A5159;
                color: #6C757D;
            }
        """)
        self.start_btn.clicked.connect(self._start_service)
        button_layout.addWidget(self.start_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("  停止服务")
        self.stop_btn.setIcon(SvgIcon.get_icon("stop", "#FFFFFF", 16))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #E06C75;
                color: white;
                font-weight: 500;
                font-size: 14px;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D05C65;
            }
            QPushButton:pressed {
                background-color: #C04C55;
            }
            QPushButton:disabled {
                background-color: #4A5159;
                color: #6C757D;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_service)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        # 重启按钮
        self.restart_btn = QPushButton("  重启服务")
        self.restart_btn.setIcon(SvgIcon.get_icon("refresh", "#FFFFFF", 16))
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #61AFEF;
                color: white;
                font-weight: 500;
                font-size: 14px;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #519FDF;
            }
            QPushButton:pressed {
                background-color: #418FCF;
            }
            QPushButton:disabled {
                background-color: #4A5159;
                color: #6C757D;
            }
        """)
        self.restart_btn.clicked.connect(self._restart_service)
        self.restart_btn.setEnabled(False)
        button_layout.addWidget(self.restart_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 自动启动复选框
        auto_start_layout = QHBoxLayout()
        auto_start_layout.setContentsMargins(0, 10, 0, 0)
        
        self.auto_start_check = QCheckBox("下次启动软件时自动启动MQTT服务")
        self.auto_start_check.setStyleSheet("""
            QCheckBox {
                color: #ABB2BF;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #4A5159;
                background-color: #282C34;
            }
            QCheckBox::indicator:hover {
                border-color: #61AFEF;
            }
            QCheckBox::indicator:checked {
                background-color: #61AFEF;
                border-color: #61AFEF;
                image: url(%s);
            }
        """ % get_resource_url('resources/icons/checkbox_checked.svg'))
        
        # 从配置加载状态
        auto_start = self.config_manager.get("local_mqtt.auto_start", False)
        self.auto_start_check.setChecked(auto_start)
        
        # 连接信号
        self.auto_start_check.stateChanged.connect(self._on_auto_start_changed)
        
        auto_start_layout.addWidget(self.auto_start_check)
        auto_start_layout.addStretch()
        layout.addLayout(auto_start_layout)
        
        return card
    
    def _create_guide_card(self) -> QFrame:
        """创建使用说明卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("book", "#61AFEF", 20))
        title_layout.addWidget(icon_label)
        
        title = QLabel("使用说明")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 说明文本
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setMaximumHeight(400)
        
        local_ip = get_local_ip()
        
        guide_content = f"""
<div style="font-size: 13px; line-height: 1.8;">
<h3 style="color: #61AFEF; margin-top: 0;">重要提示</h3>
<p style="color: #E5C07B;">该服务只能让<b>与您电脑同局域网</b>的设备之间传输消息。</p>
<p style="color: #E5C07B;">启动服务后，本地MQTT服务将自动运行在后台并开放1883端口等待消息</p>
<p style="color: #E5C07B;"><b>强烈建议您将电脑IP设置为静态IP</b>，避免IP变化导致手机端连接失败。</p>

<h3 style="color: #E06C75; margin-top: 20px;">⚠️ 广域网MQTT消息传输（重要警告）</h3>
<div style="background-color: rgba(224, 108, 117, 0.15); border-left: 4px solid #E06C75; padding: 15px; border-radius: 4px; margin: 10px 0;">
<p style="color: #E06C75; font-weight: bold; margin-top: 0;">如果您需要实现广域网（跨网络）的MQTT消息传输：</p>
<p style="color: #B8BFC6;">
您可以将<b>手机端（SmsForwarder）</b>和<b>WinMsgHub消息源配置</b>中的Broker地址都改为：<br>
<span style="color: #98C379; font-weight: bold; font-size: 14px;">broker.emqx.io</span><br>
端口保持：<span style="color: #98C379; font-weight: bold;">1883</span>
</p>

<p style="color: #E06C75; font-weight: bold; font-size: 14px; margin-top: 15px;">⚠️ 隐私风险警告：</p>
<ul style="color: #E06C75; margin: 5px 0; padding-left: 20px;">
<li><b>broker.emqx.io 是一个公共的MQTT消息转发服务！</b></li>
<li><b>任何人都可以连接并订阅您的主题，存在隐私泄露风险！</b></li>
<li><b>请勿通过公共Broker传输敏感信息、隐私数据、密码等重要内容！</b></li>
<li><b>对于重要的隐私消息，务必使用本地MQTT局域网通信！</b></li>
</ul>

<p style="color: #E5C07B; font-weight: bold; margin-top: 15px;">📢 免责声明：</p>
<p style="color: #B8BFC6;">
使用公共MQTT服务（如 broker.emqx.io）导致的任何隐私泄露、数据丢失、安全风险等问题，<b style="color: #E06C75;">均与本软件开发者无关</b>，用户需自行承担所有风险和责任。
</p>

<p style="color: #98C379; font-weight: bold; margin-top: 15px;">✅ 推荐做法：</p>
<ul style="color: #B8BFC6; margin: 5px 0; padding-left: 20px;">
<li>日常使用：优先使用<b>本地MQTT服务</b>（局域网通信，安全可靠）</li>
<li>临时需求：仅在必要时使用公共Broker，且避免传输敏感信息</li>
<li>自建服务：有条件的用户可自建MQTT服务器并配置公网访问</li>
</ul>
</div>

<h3 style="color: #61AFEF;">Android手机配置（SmsForwarder）</h3>
<ol style="color: #B8BFC6;">
<li>下载并安装 <b>SmsForwarder</b>：
<br><a href="https://github.com/pppscn/SmsForwarder/releases" style="color: #61AFEF;">https://github.com/pppscn/SmsForwarder/releases</a>
<br>下载最新版本的APK文件并安装</li>

<li>打开SmsForwarder，进入<b>"发送通道"</b>分页</li>

<li>点击右上角的<b>"+"</b>按钮</li>

<li>选择<b>"Socket"</b>类型</li>

<li>填写以下配置：
<ul style="margin-top: 8px;">
<li><b>服务端IP</b>: <span style="color: #98C379; font-weight: bold;">{local_ip}</span></li>
<li><b>端口</b>: <span style="color: #98C379; font-weight: bold;">1883</span></li>
<li><b>输入消息主题</b>: <span style="color: #98C379; font-weight: bold;">/WMH</span></li>
<li><b>输出消息主题</b>: <span style="color: #98C379; font-weight: bold;">/WMH</span></li>
</ul>
</li>

<li>其他选项保持默认，点击<b>"保存"</b></li>
</ol>

<h3 style="color: #61AFEF;">在WinMsgHub中配置MQTT消息源</h3>
<ol style="color: #B8BFC6;">
<li>进入<b>"消息源配置"</b>页面</li>
<li>选择<b>"MQTT"</b>标签页</li>
<li>点击<b>"添加MQTT消息源"</b>按钮</li>
<li>配置已自动填入默认值：
<ul style="margin-top: 8px;">
<li><b>Broker</b>: {local_ip}</li>
<li><b>端口</b>: 1883</li>
<li><b>主题</b>: /WMH</li>
<li><b>TLS加密</b>: 不勾选（本地服务不需要）</li>
</ul>
</li>
<li>点击<b>"OK"</b>按钮即可</li>
</ol>

<h3 style="color: #61AFEF;">其他MQTT客户端</h3>
<p style="color: #B8BFC6;">
任何支持MQTT协议的客户端都可以连接到本地服务器：<br>
• <b>服务器地址</b>: {local_ip}<br>
• <b>端口</b>: 1883<br>
• <b>主题</b>: /WMH<br>
• <b>协议</b>: MQTT 3.1.1<br>
• <b>认证</b>: 无需用户名密码
</p>

<h3 style="color: #61AFEF;">常见问题</h3>
<p style="color: #B8BFC6;">
<b>Q: 为什么手机连接不上？</b><br>
A: 请确保手机和电脑在同一个WiFi网络下。
</p>
<p style="color: #B8BFC6;">
<b>Q: 服务启动失败怎么办？</b><br>
A: 检查1883端口是否被占用，或等待几秒后重新点击“启动服务”按钮重试。
</p>
</div>
        """
        
        guide_text.setHtml(guide_content)
        guide_text.setStyleSheet("""
            QTextEdit {
                background-color: #2A3139;
                border: 1px solid #3A4149;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        layout.addWidget(guide_text)
        
        return card
    
    def _update_status_async(self):
        """异步更新服务状态显示（完全不阻塞UI）"""
        def check_status_task():
            """后台任务：检查服务状态"""
            try:
                status = self.mqtt_manager.get_status()
                return status["is_running"]
            except Exception as e:
                logger.error(f"检查MQTT服务状态失败: {e}")
                return None
        
        def on_status_checked(is_running):
            """状态检查完成回调"""
            if is_running is None:
                return
            
            # 如果状态没有改变，直接返回，避免不必要的UI更新
            if self._last_status == is_running:
                return
            
            self._last_status = is_running
            
            if is_running:
                # 更新为运行中状态
                self.status_label.icon_label.setPixmap(SvgIcon.get_pixmap("circle_green", "#98C379", 16))
                self.status_label.text_label.setText("服务运行中")
                self.status_label.setStyleSheet("""
                    QWidget {
                        font-size: 16px;
                        font-weight: bold;
                        padding: 15px;
                        background-color: #3A4149;
                        border-radius: 8px;
                        border-left: 4px solid #98C379;
                    }
                """)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.restart_btn.setEnabled(True)
            else:
                # 更新为未运行状态
                self.status_label.icon_label.setPixmap(SvgIcon.get_pixmap("circle_red", "#E06C75", 16))
                self.status_label.text_label.setText("服务未运行")
                self.status_label.setStyleSheet("""
                    QWidget {
                        font-size: 16px;
                        font-weight: bold;
                        padding: 15px;
                        background-color: #3A4149;
                        border-radius: 8px;
                        border-left: 4px solid #E06C75;
                    }
                """)
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.restart_btn.setEnabled(False)
        
        # 异步执行状态检查
        self._task_manager.run_task(
            "check_mqtt_status",
            check_status_task,
            on_finished=on_status_checked
        )
    
    def _update_status(self):
        """更新服务状态显示（只在状态改变时更新UI）- 已废弃，使用_update_status_async"""
        # 保留此方法以防有其他地方调用
        self._update_status_async()
    
    def _start_service(self):
        """启动服务"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 异步启动服务，避免阻塞UI
        def start_task():
            """后台启动任务"""
            try:
                return self.mqtt_manager.start_service()
            except Exception as e:
                logger.error(f"启动MQTT服务失败: {e}")
                return False, f"异常: {str(e)}"
        
        def on_started(result):
            """启动完成回调"""
            success, message = result
            
            if success:
                QMessageBox.information(
                    self, 
                    "启动成功", 
                    f"本地MQTT服务已启动！\n\n{message}"
                )
                # 立即更新状态
                self._update_status_async()
            else:
                # 显示详细的错误信息和解决方案
                error_msg = QMessageBox(self)
                error_msg.setIcon(QMessageBox.Icon.Critical)
                error_msg.setWindowTitle("启动失败")
                error_msg.setText(f"启动本地MQTT服务失败！\n\n错误: {message}")
                
                detailed_text = """
========================================
可能的原因和解决方法
========================================

【方法1】添加到Windows Defender白名单（推荐）
-----------------------------------------
1. 右键以管理员身份运行：添加到白名单.bat
2. 或手动添加：
   - 打开 Windows 安全中心
   - 病毒和威胁防护 → 管理设置
   - 排除项 → 添加或删除排除项
   - 添加文件夹：选择 WinMsgHub 文件夹

【方法2】解除文件锁定
-----------------------------------------
1. 右键 localMQTTServer\\nanomq.exe
2. 选择"属性"
3. 在底部找到"安全"部分
4. 勾选"解除锁定"
5. 点击"确定"

【方法3】检查Windows安全中心隔离区
-----------------------------------------
1. 打开 Windows 安全中心
2. 病毒和威胁防护
3. 保护历史记录
4. 查找 nanomq.exe
5. 如果被隔离，点击"还原"

【方法4】以管理员身份运行WinMsgHub
-----------------------------------------
1. 完全关闭 WinMsgHub
2. 右键 WinMsgHub 快捷方式
3. 选择"以管理员身份运行"
4. 重新尝试启动MQTT服务

【方法5】使用诊断工具
-----------------------------------------
1. 进入 localMQTTServer 文件夹
2. 右键以管理员身份运行：check_and_fix.bat
3. 查看诊断结果和建议

【方法6】临时关闭实时保护（不推荐）
-----------------------------------------
1. 打开 Windows 安全中心
2. 病毒和威胁防护 → 管理设置
3. 临时关闭"实时保护"
4. 启动MQTT服务
5. 重新开启"实时保护"
6. 将WinMsgHub添加到白名单

========================================
详细说明文档
========================================
localMQTTServer\\README_启动失败解决方法.txt
                """
                
                error_msg.setDetailedText(detailed_text)
                error_msg.setStandardButtons(
                    QMessageBox.StandardButton.Ok | 
                    QMessageBox.StandardButton.Help
                )
                
                result = error_msg.exec()
                
                if result == QMessageBox.StandardButton.Help:
                    # 打开帮助文档
                    import os
                    help_file = self.mqtt_manager.mqtt_dir / "README_启动失败解决方法.txt"
                    if help_file.exists():
                        os.startfile(str(help_file))
                    
                    # 同时打开诊断工具
                    check_tool = self.mqtt_manager.mqtt_dir / "check_and_fix.bat"
                    if check_tool.exists():
                        try:
                            import ctypes
                            # 以管理员权限运行诊断工具
                            ctypes.windll.shell32.ShellExecuteW(
                                None,
                                "runas",
                                str(check_tool),
                                "",
                                str(self.mqtt_manager.mqtt_dir),
                                1  # SW_SHOWNORMAL
                            )
                        except:
                            os.startfile(str(check_tool))
        
        # 异步执行启动
        if not hasattr(self, '_start_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._start_task_manager = AsyncTaskManager()
        
        self._start_task_manager.run_task(
            "start_mqtt_service",
            start_task,
            on_finished=on_started
        )
    
    def _stop_service(self):
        """停止服务"""
        from PyQt6.QtWidgets import QMessageBox
        
        if self.mqtt_manager.stop_service():
            QMessageBox.information(self, "成功", "本地MQTT服务已停止！")
        else:
            QMessageBox.warning(self, "警告", "停止本地MQTT服务时出现问题，请查看日志。")
    
    def _restart_service(self):
        """重启服务"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 异步重启服务，避免阻塞UI
        def restart_task():
            """后台重启任务"""
            try:
                return self.mqtt_manager.restart_service()
            except Exception as e:
                logger.error(f"重启MQTT服务失败: {e}")
                return False, f"异常: {str(e)}"
        
        def on_restarted(result):
            """重启完成回调"""
            success, message = result
            
            if success:
                QMessageBox.information(self, "成功", f"本地MQTT服务已重启！\n\n{message}")
                # 立即更新状态
                self._update_status_async()
            else:
                QMessageBox.critical(self, "错误", f"重启本地MQTT服务失败！\n\n错误: {message}")
        
        # 异步执行重启
        if not hasattr(self, '_restart_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._restart_task_manager = AsyncTaskManager()
        
        self._restart_task_manager.run_task(
            "restart_mqtt_service",
            restart_task,
            on_finished=on_restarted
        )
    
    def _on_auto_start_changed(self, state):
        """自动启动状态改变"""
        from PyQt6.QtCore import Qt
        auto_start = (state == Qt.CheckState.Checked.value)
        self.config_manager.set("local_mqtt.auto_start", auto_start)
        logger.info(f"本地MQTT服务自动启动已{'启用' if auto_start else '禁用'}")
    
    def force_save(self):
        """强制立即保存配置（用于页面切换或程序退出时）"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            # local_mqtt_page的配置是立即保存的，但为了保险，再强制保存一次
            self.config_manager.save_config()
            logger.info("[本地MQTT] 配置已强制保存到文件")
        except Exception as e:
            logger.error(f"[本地MQTT] 强制保存失败: {e}", exc_info=True)

