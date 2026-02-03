"""
WinMsgHub - 关于页面
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTextBrowser, QScrollArea, QGridLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap
from pathlib import Path
from ui.svg_icons import SvgIcon
from utils.update_checker import UpdateChecker


class UpdateCheckThread(QThread):
    """更新检查线程"""
    update_checked = pyqtSignal(object)  # 检查完成信号，传递更新信息或None
    
    def run(self):
        """执行更新检查"""
        update_info = UpdateChecker.check_update()
        self.update_checked.emit(update_info)


class AboutPage(QWidget):
    """关于页面 - 显示应用信息"""
    
    def __init__(self):
        super().__init__()
        self._check_thread = None
        self._setup_ui()
    
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
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        content.setLayout(layout)
        
        # Logo和标题区域 - 使用渐变背景的大卡片
        header_card = self._create_header_card()
        layout.addWidget(header_card)
        
        # 作者信息卡片
        author_card = self._create_author_card()
        layout.addWidget(author_card)
        
        # 功能特性卡片
        features_card = self._create_features_card()
        layout.addWidget(features_card)
        
        # 开源协议卡片
        license_card = self._create_license_card()
        layout.addWidget(license_card)
        
        # 底部链接按钮
        links_card = self._create_links_card()
        layout.addWidget(links_card)
        
        layout.addStretch()
    
    def _create_header_card(self) -> QFrame:
        """创建头部卡片 - 简洁大方"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)  # 从15减小到8，让间距更紧凑
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.setLayout(layout)
        
        # Logo图标 - 更小更精致
        from PyQt6.QtGui import QPixmap
        from pathlib import Path
        
        logo = QLabel()
        icon_path = Path(__file__).parent.parent.parent / "resources" / "icons" / "WinMsgHub_ICON.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    80, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo.setPixmap(scaled_pixmap)
            else:
                # 使用 SVG 图标作为后备
                logo.setPixmap(SvgIcon.get_pixmap("phone", "#4A9EFF", 60))
        else:
            # 使用 SVG 图标作为后备
            logo.setPixmap(SvgIcon.get_pixmap("phone", "#4A9EFF", 60))
        
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        # 应用名称 - 简洁
        app_name = QLabel("WinMsgHub")
        app_name.setStyleSheet("""
            font-size: 32px;
            font-weight: 600;
            color: #FFFFFF;
            letter-spacing: 1px;
        """)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_name)
        
        # 版本号 - 简单标签
        version_layout = QHBoxLayout()
        version_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_layout.setSpacing(10)
        
        version = QLabel(f"v{UpdateChecker.get_current_version()}")
        version.setStyleSheet("""
            font-size: 14px;
            color: #4A9EFF;
            font-weight: 500;
        """)
        version_layout.addWidget(version)
        
        # 检查更新按钮
        self.check_update_btn = QPushButton("检查更新")
        self.check_update_btn.setStyleSheet("""
            QPushButton {
                background: rgba(74, 158, 255, 0.15);
                color: #4A9EFF;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 12px;
                border: 1px solid rgba(74, 158, 255, 0.3);
                border-radius: 12px;
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
        
        layout.addLayout(version_layout)
        
        # 标语 - 简洁
        slogan = QLabel("现代化的 Windows 消息聚合中心")
        slogan.setStyleSheet("""
            font-size: 14px;
            color: #ABB2BF;
            margin-top: 5px;
        """)
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(slogan)
        
        return card
    
    def _create_author_card(self) -> QFrame:
        """创建作者信息卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("author", "#4A9EFF", 24))
        title_layout.addWidget(icon_label)
        
        title = QLabel("作者信息")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 作者信息容器 - 使用更醒目的样式
        author_container = QFrame()
        author_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 158, 255, 0.12),
                    stop:1 rgba(74, 158, 255, 0.06));
                border-left: 4px solid #4A9EFF;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        author_layout = QVBoxLayout()
        author_layout.setSpacing(15)
        author_container.setLayout(author_layout)
        
        # 作者名称
        author_name = QLabel("开发者：青云制作_彭明航")
        author_name.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #FFFFFF;
        """)
        author_layout.addWidget(author_name)
        
        # 版权信息
        copyright_text = QLabel("© 2026 青云制作_彭明航 版权所有")
        copyright_text.setStyleSheet("""
            font-size: 14px;
            color: #4A9EFF;
            font-weight: 500;
        """)
        author_layout.addWidget(copyright_text)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            background-color: rgba(74, 158, 255, 0.3);
            max-height: 1px;
            margin: 5px 0;
        """)
        author_layout.addWidget(separator)
        
        # 项目描述
        description = QLabel(
            "WinMsgHub 是我开源的第二款软件项目，开发它的初衷就是为了解决生活中每次接收"
            "验证码都得掏出手机，再解锁手机才能看到验证码的繁琐操作，让验证码直接"
            "出现在电脑上。若这款工具能提升您的电脑使用体验，希望您能在 GitHub 上为"
            "这款工具点一个小小的 Star ⭐，🦀🦀啦！"
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            font-size: 14px;
            color: #ABB2BF;
            line-height: 1.8;
        """)
        author_layout.addWidget(description)
        
        layout.addWidget(author_container)
        
        return card
    
    def _create_features_card(self) -> QFrame:
        """创建功能特性卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        card.setLayout(layout)
        
        title = QLabel("✨ 核心特性")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 特性列表 - 使用网格布局
        features = [
            ("network", "多消息源支持", "MQTT、API、Webhook、IMAP\nWebSocket、RSS、文件监控、剪贴板"),
            ("ui", "现代化界面", "深色主题、流畅动画\n响应式设计"),
            ("popup", "智能弹窗系统", "9种位置、5种动画\n自定义样式、音效提醒"),
            ("filter", "强大过滤引擎", "关键词过滤、正则匹配\n优先级控制、黑白名单"),
            ("chart", "历史记录管理", "搜索、筛选、导出\n自动清理、数据统计"),
            ("settings", "灵活配置系统", "实时保存、热重载\n导入导出、备份恢复"),
            ("security", "安全加密连接", "TLS/SSL 支持\n密码加密存储"),
            ("performance", "高性能架构", "PyQt6 框架\n多线程处理、异步IO"),
            ("schedule", "定时任务功能", "定时弹窗、番茄钟\n间隔提醒、周期任务"),
            ("tray", "系统托盘集成", "后台运行、快速访问\n实时统计、一键操作"),
        ]
        
        # 创建网格容器
        grid_container = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_container.setLayout(grid_layout)
        
        # 2列布局
        for i, (icon, feature_title, feature_desc) in enumerate(features):
            row = i // 2
            col = i % 2
            feature_item = self._create_feature_item(icon, feature_title, feature_desc)
            grid_layout.addWidget(feature_item, row, col)
        
        layout.addWidget(grid_container)
        
        return card
    
    def _create_feature_item(self, icon: str, title: str, description: str) -> QFrame:
        """创建特性项 - 卡片样式"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2A3139,
                    stop:1 #242930);
                border: 1px solid #3A4149;
                border-radius: 12px;
                padding: 20px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2F3641,
                    stop:1 #282C34);
                border: 1px solid #4A9EFF;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        item.setLayout(layout)
        
        # 图标 - 使用 SVG
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap(icon, "#4A9EFF", 36))
        icon_label.setStyleSheet("min-width: 50px; max-width: 50px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 文字容器
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #FFFFFF;
        """)
        text_layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #ABB2BF;
            line-height: 1.5;
        """)
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return item
    
    def _create_license_card(self) -> QFrame:
        """创建开源协议卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        card.setLayout(layout)
        
        title = QLabel("📜 开源协议")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        # 协议名称标签
        license_name_container = QFrame()
        license_name_container.setStyleSheet("""
            QFrame {
                background: rgba(74, 158, 255, 0.1);
                border: 1px solid rgba(74, 158, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        license_name_layout = QHBoxLayout()
        license_name_layout.setContentsMargins(0, 0, 0, 0)
        license_name_container.setLayout(license_name_layout)
        
        license_name = QLabel("自定义开源许可协议 (Custom Open Source License)")
        license_name.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #4A9EFF;
        """)
        license_name_layout.addWidget(license_name)
        layout.addWidget(license_name_container)
        
        # 协议内容
        license_text = QTextBrowser()
        license_text.setMaximumHeight(320)
        license_text.setOpenExternalLinks(True)
        license_text.setStyleSheet("""
            QTextBrowser {
                background-color: #282C34;
                border: 1px solid #3A4149;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        license_text.setHtml("""
        <div style="font-family: 'Microsoft YaHei UI', sans-serif; line-height: 1.9; color: #FFFFFF;">
            <p style="font-size: 14px; color: #FFFFFF; font-weight: 600; margin-bottom: 15px;">
                版权所有 © 2026 青云制作_彭明航
            </p>
            
            <p style="font-size: 14px; color: #98C379; font-weight: 600; margin-top: 18px; margin-bottom: 10px;">
                允许的使用方式
            </p>
            <ul style="margin: 0; padding-left: 25px; color: #ABB2BF; font-size: 13px;">
                <li style="margin: 6px 0;">个人使用和学习</li>
                <li style="margin: 6px 0;">商业使用</li>
                <li style="margin: 6px 0;">二次开发和修改</li>
                <li style="margin: 6px 0;">分发和传播</li>
            </ul>
            
            <p style="font-size: 14px; color: #E5C07B; font-weight: 600; margin-top: 18px; margin-bottom: 10px;">
                使用条件（必须遵守）
            </p>
            <ul style="margin: 0; padding-left: 25px; color: #ABB2BF; font-size: 13px;">
                <li style="margin: 6px 0;">二次开发必须开源</li>
                <li style="margin: 6px 0;">必须标明原作者：青云制作_彭明航</li>
                <li style="margin: 6px 0;">衍生作品必须使用相同协议</li>
                <li style="margin: 6px 0;">保留版权声明</li>
            </ul>
            
            <p style="font-size: 14px; color: #E06C75; font-weight: 600; margin-top: 18px; margin-bottom: 10px;">
                禁止的行为
            </p>
            <ul style="margin: 0; padding-left: 25px; color: #ABB2BF; font-size: 13px;">
                <li style="margin: 6px 0;">闭源发布衍生作品</li>
                <li style="margin: 6px 0;">移除或篡改原作者信息</li>
                <li style="margin: 6px 0;">用于非法用途</li>
            </ul>
            
            <p style="font-size: 14px; color: #61AFEF; font-weight: 600; margin-top: 18px; margin-bottom: 10px;">
                免责声明
            </p>
            <p style="color: #ABB2BF; font-size: 12px; line-height: 1.7;">
                本软件按"原样"提供，不提供任何明示或暗示的保证。
                作者不对使用本软件造成的任何损失承担责任。
                使用本软件即表示您同意承担所有相关风险。
            </p>
            
            <p style="font-size: 13px; color: #4A9EFF; margin-top: 18px; text-align: center; font-weight: 500;">
                完整协议内容请查看项目根目录的 <b>LICENSE</b> 文件
            </p>
        </div>
        """)
        layout.addWidget(license_text)
        
        return card
    
    def _create_links_card(self) -> QFrame:
        """创建链接按钮卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("links", "#4A9EFF", 24))
        title_layout.addWidget(icon_label)
        
        title = QLabel("相关链接")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 按钮容器
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # GitHub按钮
        github_btn = QPushButton("  GitHub 仓库")
        github_btn.setIcon(SvgIcon.get_icon("github", "#FFFFFF", 16))
        github_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A9EFF,
                    stop:1 #357ABD);
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5AAAFF,
                    stop:1 #458ACD);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3A8EEF,
                    stop:1 #256AAD);
            }
        """)
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(lambda: self._open_url("https://github.com/pmh1314520/WinMsgHub"))
        buttons_layout.addWidget(github_btn)
        
        # 文档按钮
        docs_btn = QPushButton("  个人导航站")
        docs_btn.setIcon(SvgIcon.get_icon("docs", "#FFFFFF", 16))
        docs_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #98C379,
                    stop:1 #78A359);
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A8D389,
                    stop:1 #88B369);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #88B369,
                    stop:1 #689349);
            }
        """)
        docs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        docs_btn.clicked.connect(lambda: self._open_url("https://www.pmhs.top"))
        buttons_layout.addWidget(docs_btn)
        
        # 反馈按钮
        feedback_btn = QPushButton("  问题反馈")
        feedback_btn.setIcon(SvgIcon.get_icon("feedback", "#FFFFFF", 16))
        feedback_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E5C07B,
                    stop:1 #C5A05B);
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #F5D08B,
                    stop:1 #D5B06B);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #D5B06B,
                    stop:1 #B5904B);
            }
        """)
        feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        feedback_btn.clicked.connect(lambda: self._open_url("https://github.com/pmh1314520/WinMsgHub/issues"))
        buttons_layout.addWidget(feedback_btn)
        
        layout.addLayout(buttons_layout)
        
        return card
    
    def _open_url(self, url: str):
        """打开URL"""
        QDesktopServices.openUrl(QUrl(url))
    
    def _check_for_updates(self):
        """检查更新"""
        # 禁用按钮，防止重复点击
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("检查中...")
        
        # 创建并启动检查线程
        self._check_thread = UpdateCheckThread()
        self._check_thread.update_checked.connect(self._on_update_checked)
        self._check_thread.start()
    
    def _on_update_checked(self, update_info):
        """更新检查完成"""
        # 恢复按钮状态
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("检查更新")
        
        if update_info is None:
            # 没有更新或检查失败
            msg = QMessageBox(self)
            msg.setWindowTitle("检查更新")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("当前已是最新版本！")
            msg.setInformativeText(f"当前版本：v{UpdateChecker.get_current_version()}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # 设置样式
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
            self._show_update_dialog(update_info)
    
    def _show_update_dialog(self, update_info: dict):
        """显示更新对话框"""
        msg = QMessageBox(self)
        msg.setWindowTitle("发现新版本")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"发现新版本 v{update_info['latest_version']}！")
        
        # 构建详细信息
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
        
        # 设置按钮文本
        yes_btn = msg.button(QMessageBox.StandardButton.Yes)
        yes_btn.setText("前往下载")
        no_btn = msg.button(QMessageBox.StandardButton.No)
        no_btn.setText("稍后再说")
        
        # 设置样式
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
            QPushButton:pressed {
                background-color: #3A8EEF;
            }
        """)
        
        # 显示对话框并处理结果
        result = msg.exec()
        if result == QMessageBox.StandardButton.Yes:
            # 打开下载页面
            download_url = update_info.get('download_url', UpdateChecker.get_releases_url())
            self._open_url(download_url)
