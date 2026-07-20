"""
WinMsgHub - 系统托盘图标
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from utils.logger import get_logger


logger = get_logger(__name__)


class TrayIcon(QObject):
    """
    系统托盘图标
    
    验证需求：
    - 6.1: 在系统托盘显示图标
    - 6.2: 点击托盘图标显示菜单
    - 6.4: 提供快捷菜单
    - 6.5: 新消息提示
    """
    
    # 信号
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    show_page_requested = pyqtSignal(str)  # 新增：显示指定页面
    test_popup_requested = pyqtSignal()    # 新增：测试弹窗
    
    def __init__(self, parent=None):
        """初始化托盘图标"""
        super().__init__(parent)
        
        # 统计信息（用于菜单显示）- 必须在_create_menu之前初始化
        self.message_count = 0
        self.active_sources = 0
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(parent)
        
        # 设置图标（使用默认图标，实际应用中应该使用自定义图标）
        self._set_default_icon()
        
        # 创建菜单
        self._create_menu()
        
        # 连接信号
        self.tray_icon.activated.connect(self._on_activated)
        self.active_sources = 0
        
        logger.info("系统托盘图标已初始化")
    
    def _set_default_icon(self):
        """设置默认图标"""
        # 尝试加载自定义图标
        from utils.resource_path import get_resource_path
        icon_path = get_resource_path("resources/icons/WinMsgHub_ICON.ico")
        
        try:
            icon = QIcon(icon_path)
            logger.info(f"已加载自定义图标: {icon_path}")
        except Exception as e:
            # 如果找不到图标文件，创建一个简单的默认图标
            logger.warning(f"加载图标失败: {e}，使用默认图标")
            from PyQt6.QtGui import QPixmap, QPainter, QColor
            
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(0, 0, 0, 0))
            
            painter = QPainter(pixmap)
            painter.setBrush(QColor(76, 175, 80))  # 绿色
            painter.drawEllipse(8, 8, 48, 48)
            painter.end()
            
            icon = QIcon(pixmap)
        
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("WinMsgHub")
    
    def _build_title_text(self) -> str:
        """构建统计信息标题文本"""
        if self.active_sources > 0:
            return f"WinMsgHub - {self.active_sources}个消息源 | {self.message_count}条消息"
        return f"WinMsgHub - 无活动消息源 | {self.message_count}条消息"
    
    def _create_menu(self):
        """创建托盘菜单（需求6.4）"""
        menu = QMenu()
        
        # 标题（显示统计信息）—— 保存引用，统计更新时只改文本不重建菜单
        self._title_action = QAction(self._build_title_text(), menu)
        title_action = self._title_action
        title_action.setEnabled(False)  # 不可点击，仅显示信息
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)
        menu.addAction(title_action)
        
        menu.addSeparator()
        
        # 显示主窗口
        from ui.svg_icons import SvgIcon
        show_action = QAction(SvgIcon.get_icon("dashboard", "#4A9EFF", 16), "显示主窗口", menu)
        show_action.triggered.connect(self.show_window_requested.emit)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        # 快速操作
        test_popup_action = QAction(SvgIcon.get_icon("bell", "#98C379", 16), "测试弹窗", menu)
        test_popup_action.triggered.connect(self.test_popup_requested.emit)
        menu.addAction(test_popup_action)
        
        refresh_action = QAction(SvgIcon.get_icon("refresh", "#61AFEF", 16), "刷新统计", menu)
        refresh_action.triggered.connect(self.show_window_requested.emit)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # 页面快捷方式
        history_action = QAction(SvgIcon.get_icon("history", "#E5C07B", 16), "消息历史", menu)
        history_action.triggered.connect(lambda: self.show_page_requested.emit("history"))
        menu.addAction(history_action)
        
        sources_action = QAction(SvgIcon.get_icon("plug", "#C678DD", 16), "消息源配置", menu)
        sources_action.triggered.connect(lambda: self.show_page_requested.emit("sources"))
        menu.addAction(sources_action)
        
        popup_action = QAction("  弹窗设置", menu)
        popup_action.setIcon(SvgIcon.get_icon("bell", "#ABB2BF", 16))
        popup_action.triggered.connect(lambda: self.show_page_requested.emit("popup"))
        menu.addAction(popup_action)
        
        menu.addSeparator()
        
        # 关于
        about_action = QAction(SvgIcon.get_icon("info", "#56B6C2", 16), "关于 WinMsgHub", menu)
        about_action.triggered.connect(lambda: self.show_page_requested.emit("about"))
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # 退出程序
        quit_action = QAction(SvgIcon.get_icon("close", "#E06C75", 16), "退出", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        
        # 必须保留Python引用，否则QMenu可能被垃圾回收导致托盘菜单失效
        self._menu = menu
        self.tray_icon.setContextMenu(menu)
    
    def _on_activated(self, reason):
        """托盘图标激活事件（需求6.2）"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标，显示主窗口
            self.show_window_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击托盘图标，显示主窗口
            self.show_window_requested.emit()
    
    def show(self):
        """显示托盘图标（需求6.1）"""
        self.tray_icon.show()
        logger.info("托盘图标已显示")
    
    def hide(self):
        """隐藏托盘图标"""
        self.tray_icon.hide()
        logger.info("托盘图标已隐藏")
    
    def show_message(self, title: str, message: str, duration: int = 3000, play_sound: bool = False):
        """显示托盘消息（需求6.5）
        
        Args:
            title: 消息标题
            message: 消息内容
            duration: 显示时长（毫秒）
            play_sound: 是否播放系统声音（默认False，静音）
        
        注意：Windows通知会使用应用程序的托盘图标
        """
        # 直接使用Information类型，Windows会自动使用托盘图标
        # 如果不需要声音，我们接受可能会有声音的代价，因为显示正确的图标更重要
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            duration
        )
        
        logger.info(f"托盘消息已显示: {title}")
    
    def set_icon_badge(self, count: int):
        """设置图标徽章（新消息数量提示，需求6.5）"""
        self.message_count = count
        
        # 在Windows上，可以通过修改图标来显示徽章
        # 这里简化实现，实际应用中可以绘制带数字的图标
        if count > 0:
            self.tray_icon.setToolTip(f"WinMsgHub - {count} 条新消息")
        else:
            self.tray_icon.setToolTip("WinMsgHub")
    
    def update_stats(self, message_count: int, active_sources: int):
        """更新统计信息"""
        self.message_count = message_count
        self.active_sources = active_sources
        
        # 更新工具提示
        if active_sources > 0:
            tooltip = f"WinMsgHub\n{active_sources}个消息源已连接 | 共{message_count}条消息"
        else:
            tooltip = f"WinMsgHub\n无活动消息源 | 共{message_count}条消息"
        
        self.tray_icon.setToolTip(tooltip)
        
        # 只更新标题文本，不重建整个菜单
        # （每条消息都重建菜单会导致菜单打开时被强制关闭，且泄漏旧菜单对象）
        if hasattr(self, '_title_action') and self._title_action:
            self._title_action.setText(self._build_title_text())
