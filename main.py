"""
WinMsgHub (WinMsgHub) - 应用程序主入口
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import sys
from pathlib import Path

# 版本标记 - 用于确认代码是否正确加载
APP_VERSION = "2026-02-03-v3-realtime-save"
print(f"[启动] WinMsgHub 版本: {APP_VERSION}")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 导入核心模块
from core.async_config_manager import AsyncConfigManager
from core.filter_engine import FilterEngine
from core.message_processor import MessageProcessor
from core.popup_manager import PopupManager
from core.connector_manager import ConnectorManager
from data.database import Database

# 导入UI模块 - 添加调试信息
print(f"[启动] 正在导入 ModernMainWindow...")
from ui.modern_main_window import ModernMainWindow
print(f"[启动] ModernMainWindow 导入完成，文件路径: {ModernMainWindow.__module__}")

from ui.tray_icon import TrayIcon
from ui.modern_theme import ModernTheme
from utils.logger import get_logger


logger = get_logger(__name__)


class WinMsgHubApplication:
    """WinMsgHub应用程序主类"""
    
    def __init__(self):
        """初始化应用程序"""
        logger.info("=" * 60)
        logger.info("WinMsgHub 启动中...")
        logger.info("=" * 60)
        
        # 退出标志
        self._is_quitting = False
        
        # 创建Qt应用
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("WinMsgHub")
        self.app.setOrganizationName("青云制作")
        self.app.setApplicationDisplayName("WinMsgHub")
        
        # 设置应用程序版本
        self.app.setApplicationVersion("1.1.4")
        
        # 设置应用图标（必须在设置AppUserModelID之前）
        from PyQt6.QtGui import QIcon
        from utils.resource_path import get_resource_path
        icon_path = get_resource_path("resources/icons/WinMsgHub_ICON.ico")
        try:
            self.app.setWindowIcon(QIcon(icon_path))
            logger.info(f"已设置应用图标: {icon_path}")
        except Exception as e:
            logger.warning(f"设置图标失败: {e}")
        
        # 在Windows上设置应用程序用户模型ID
        # 这会让Windows通知显示正确的应用名称和图标
        try:
            import ctypes
            # 使用更简洁的ID
            myappid = 'WinMsgHub.Desktop'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            logger.info(f"已设置Windows应用程序用户模型ID: {myappid}")
        except Exception as e:
            logger.warning(f"设置Windows应用程序用户模型ID失败: {e}")
        
        # 初始化配置
        self._init_config()
        
        # 初始化数据库
        self._init_database()
        
        # 初始化主题
        self._init_theme()
        
        # 初始化过滤引擎
        self._init_filter_engine()
        
        # 初始化弹窗管理器
        self._init_popup_manager()
        
        # 初始化定时任务管理器
        self._init_scheduler_manager()
        
        # 初始化系统监控管理器
        self._init_system_monitor()
        
        # 初始化本地MQTT服务管理器
        self._init_local_mqtt_manager()
        
        # 初始化消息处理器
        self._init_message_processor()
        
        # 初始化消息源连接器
        self._init_connectors()
        
        # 初始化UI
        self._init_ui()
        
        logger.info("WinMsgHub 初始化完成")
    
    def _init_config(self):
        """初始化配置管理器"""
        # 配置目录
        if sys.platform == 'win32':
            import os
            config_dir = Path(os.environ.get('APPDATA', '.')) / 'WinMsgHub'
        else:
            config_dir = Path.home() / '.WinMsgHub'
        
        # 先创建同步配置管理器
        from core.config_manager import ConfigManager
        sync_config_manager = ConfigManager(config_dir)
        
        # 再包装为异步配置管理器，避免同步IO阻塞UI
        self.config_manager = AsyncConfigManager(sync_config_manager)
        logger.info(f"配置目录: {config_dir}")
    
    def _init_database(self):
        """初始化数据库"""
        # 数据库文件
        if sys.platform == 'win32':
            import os
            db_dir = Path(os.environ.get('APPDATA', '.')) / 'WinMsgHub'
        else:
            db_dir = Path.home() / '.WinMsgHub'
        
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / 'WinMsgHub.db'
        
        self.database = Database(db_path)
        logger.info(f"数据库: {db_path}")
    
    def _init_theme(self):
        """初始化主题管理器"""
        # 应用现代化主题
        self.app.setStyleSheet(ModernTheme.get_stylesheet())
        logger.info("已应用现代化主题")
    
    def _init_filter_engine(self):
        """初始化过滤引擎"""
        from core.filter_engine import FilterRule, FilterCondition
        
        # 从配置加载过滤规则
        config = self.config_manager.get_all()
        filters_config = config.get('filters', {})
        filter_rules = filters_config.get('rules', [])
        
        rules = []
        for rule_data in filter_rules:
            if not rule_data.get('enabled', True):
                continue
            
            # 转换规则类型
            rule_type = rule_data.get('type', 'contains')
            condition_map = {
                'contains': FilterCondition.CONTAINS,
                'not_contains': FilterCondition.NOT_CONTAINS,
                'source': FilterCondition.EQUALS,
                'regex': FilterCondition.REGEX
            }
            condition = condition_map.get(rule_type, FilterCondition.CONTAINS)
            
            # 确定要检查的字段
            field = rule_data.get('field', 'content')
            if field == 'both':
                # 如果是"标题和内容"，需要创建两条规则
                rules.append(FilterRule(
                    enabled=True,
                    field='title',
                    condition=condition,
                    value=rule_data.get('keyword', ''),
                    action='block' if rule_data.get('action_block', True) else 'allow'
                ))
                rules.append(FilterRule(
                    enabled=True,
                    field='content',
                    condition=condition,
                    value=rule_data.get('keyword', ''),
                    action='block' if rule_data.get('action_block', True) else 'allow'
                ))
            else:
                rules.append(FilterRule(
                    enabled=True,
                    field=field,
                    condition=condition,
                    value=rule_data.get('keyword', ''),
                    action='block' if rule_data.get('action_block', True) else 'allow'
                ))
        
        self.filter_engine = FilterEngine(rules)
        logger.info(f"过滤引擎已初始化，加载了 {len(rules)} 条规则")
    
    def _init_popup_manager(self):
        """初始化弹窗管理器"""
        self.popup_manager = PopupManager(self.config_manager)
    
    def _init_scheduler_manager(self):
        """初始化定时任务管理器"""
        from core.scheduler_manager import SchedulerManager
        self.scheduler_manager = SchedulerManager(self.config_manager)
        
        # 连接定时任务触发信号到弹窗管理器
        self.scheduler_manager.task_triggered.connect(self._on_scheduled_task_triggered)
        logger.info("定时任务管理器已初始化")
    
    def _init_system_monitor(self):
        """初始化系统监控管理器"""
        from core.system_monitor import SystemMonitor
        self.system_monitor = SystemMonitor(self.config_manager)
        
        # 连接监控信号
        self.system_monitor.hourly_alert.connect(self._on_hourly_alert)
        self.system_monitor.cpu_alert.connect(self._on_cpu_alert)
        self.system_monitor.memory_alert.connect(self._on_memory_alert)
        logger.info("系统监控管理器已初始化")
    
    def _init_local_mqtt_manager(self):
        """初始化本地MQTT服务管理器"""
        from core.local_mqtt_manager import LocalMQTTManager
        self.local_mqtt_manager = LocalMQTTManager(self.config_manager)
        logger.info("本地MQTT服务管理器已初始化")
        
        # 检查是否需要自动启动服务
        auto_start = self.config_manager.get("local_mqtt.auto_start", False)
        if auto_start:
            port = self.config_manager.get("local_mqtt.port", 1883)
            ws_port = self.config_manager.get("local_mqtt.ws_port", 8083)
            logger.info(f"检测到上次服务已启动，正在自动启动本地MQTT服务...")
            
            # 使用QTimer延迟启动，避免阻塞初始化
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._auto_start_mqtt(port, ws_port))
    
    def _auto_start_mqtt(self, port: int, ws_port: int):
        """自动启动MQTT服务（延迟执行）"""
        try:
            success, message = self.local_mqtt_manager.start_service(port, ws_port)
            if success:
                logger.info(f"本地MQTT服务自动启动成功")
            else:
                logger.warning(f"本地MQTT服务自动启动失败: {message}")
        except Exception as e:
            logger.error(f"自动启动本地MQTT服务失败: {e}")
    
    def _on_scheduled_task_triggered(self, task):
        """处理定时任务触发"""
        from data.models import Message
        import time
        
        # 创建消息对象
        message = Message(
            id=f"scheduled_{task.id}_{int(time.time())}",
            source=task.name,
            title=task.title,
            content=task.content,
            timestamp=time.time(),
            metadata={"task_type": task.type, "task_id": task.id}
        )
        
        # 保存到数据库
        self.database.save_message(message)
        
        # 显示弹窗（使用任务自定义音效或默认音效）
        if task.sound_file:
            # 临时修改弹窗配置使用自定义音效
            original_sound = self.config_manager.get("popup.sound_file")
            self.config_manager.set("popup.sound_file", task.sound_file)
            self.popup_manager.show_notification(message)
            # 恢复原音效配置
            if original_sound:
                self.config_manager.set("popup.sound_file", original_sound)
            else:
                self.config_manager.set("popup.sound_file", "")
        else:
            self.popup_manager.show_notification(message)
        
        logger.info(f"定时任务触发: {task.name}")
    
    def _on_hourly_alert(self, hour):
        """处理整点提示"""
        from data.models import Message
        import time
        
        # 创建整点提示消息
        message = Message(
            id=f"hourly_{hour}_{int(time.time())}",
            source="整点提示",
            title=f"整点提示 - {hour}:00",
            content=f"现在是{hour}点整，累了就休息一会儿！",
            timestamp=time.time(),
            metadata={"type": "hourly_alert", "hour": hour}
        )
        
        # 保存到数据库
        self.database.save_message(message)
        
        # 显示弹窗
        self.popup_manager.show_notification(message)
        logger.info(f"整点提示: {hour}:00")
    
    def _on_cpu_alert(self, cpu_percent):
        """处理CPU过高提示"""
        from data.models import Message
        import time
        
        # 创建CPU告警消息
        message = Message(
            id=f"cpu_alert_{int(time.time())}",
            source="系统监控",
            title="CPU使用率过高",
            content=f"当前CPU使用率: {cpu_percent:.1f}%\n建议关闭一些不必要的程序。",
            timestamp=time.time(),
            metadata={"type": "cpu_alert", "cpu_percent": cpu_percent}
        )
        
        # 保存到数据库
        self.database.save_message(message)
        
        # 显示弹窗
        self.popup_manager.show_notification(message)
        logger.warning(f"CPU告警: {cpu_percent:.1f}%")
    
    def _on_memory_alert(self, memory_percent):
        """处理内存过高提示"""
        from data.models import Message
        import time
        
        # 创建内存告警消息
        message = Message(
            id=f"memory_alert_{int(time.time())}",
            source="系统监控",
            title="内存使用率过高",
            content=f"当前内存使用率: {memory_percent:.1f}%\n建议关闭一些不必要的程序或重启电脑。",
            timestamp=time.time(),
            metadata={"type": "memory_alert", "memory_percent": memory_percent}
        )
        
        # 保存到数据库
        self.database.save_message(message)
        
        # 显示弹窗
        self.popup_manager.show_notification(message)
        logger.warning(f"内存告警: {memory_percent:.1f}%")
    
    def _init_message_processor(self):
        """初始化消息处理器"""
        self.message_processor = MessageProcessor(
            self.filter_engine,
            self.database,
            self.popup_manager
        )
    
    def _init_connectors(self):
        """初始化消息源连接器"""
        # 使用ConnectorManager统一管理所有连接器（支持多实例）
        self.connector_manager = ConnectorManager(self.message_processor)
        
        # 从配置加载所有连接器
        config = self.config_manager.get_all()
        self.connector_manager.load_connectors(config)
        
        # 显示连接器状态
        counts = self.connector_manager.get_connector_count()
        logger.info("=" * 60)
        logger.info("消息源连接器加载完成：")
        for connector_type, count in counts.items():
            if count > 0:
                logger.info(f"  {connector_type}: {count} 个实例")
        logger.info("=" * 60)
    
    def reload_connectors(self):
        """重新加载连接器（热重载）- 异步执行"""
        logger.info("正在重新加载消息源连接器...")
        
        # 显示加载提示（可选）
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        def reload_task():
            """后台重载任务"""
            try:
                # 不要重新加载配置！配置已经在调用方更新了
                # 直接使用当前内存中的配置
                config = self.config_manager.get_all()
                
                logger.info(f"[ReloadConnectors] 使用当前配置重新加载连接器")
                
                # 使用ConnectorManager重新加载所有连接器
                self.connector_manager.reload_connectors(config)
                
                logger.info("消息源连接器重新加载完成")
                return True
            except Exception as e:
                logger.error(f"重新加载连接器失败: {e}", exc_info=True)
                return False
        
        def on_complete(success):
            """重载完成回调"""
            QApplication.restoreOverrideCursor()
            if success:
                logger.info("连接器热重载成功")
            else:
                logger.error("连接器热重载失败")
        
        # 使用异步任务管理器
        if not hasattr(self, '_reload_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._reload_task_manager = AsyncTaskManager()
        
        self._reload_task_manager.run_task(
            "reload_connectors",
            reload_task,
            on_finished=on_complete
        )
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主窗口（传入所需的依赖）
        self.main_window = ModernMainWindow(
            self.config_manager,
            self.database,
            self.message_processor,
            self.popup_manager,
            self.scheduler_manager,
            self.local_mqtt_manager  # 传入本地MQTT管理器
        )
        
        # 创建托盘图标
        self.tray_icon = TrayIcon()
        self.tray_icon.show()
        
        # 连接信号
        self.tray_icon.show_window_requested.connect(self._show_main_window)
        self.tray_icon.quit_requested.connect(self._quit_application)
        self.tray_icon.show_page_requested.connect(self._show_page)
        self.tray_icon.test_popup_requested.connect(self._test_popup)
        self.main_window.closing.connect(self._on_main_window_closing)
        self.main_window.reload_connectors_requested.connect(self.reload_connectors)
        
        # 监听数据库变化信号（事件驱动，真正的实时更新）
        self.database.data_changed.connect(self._update_tray_stats)
        
        # 初始更新
        self._update_tray_stats()
        
        # 启动历史记录清理定时器
        self._init_history_cleanup()
        
        # 检查是否启动时最小化
        start_minimized = self.config_manager.get("system.start_minimized", False)
        if start_minimized:
            logger.info("启动时最小化到托盘")
            self.main_window.hide()
            # 检查是否显示托盘通知
            show_notification = self.config_manager.get("system.show_tray_notification", True)
            if show_notification:
                self.tray_icon.show_message(
                    "WinMsgHub",
                    "应用程序已在后台启动",
                    2000,
                    play_sound=False  # 静音
                )
        else:
            # 显示主窗口
            self.main_window.show()
    
    def _init_history_cleanup(self):
        """初始化历史记录清理定时器"""
        self.history_cleanup_timer = QTimer()
        self.history_cleanup_timer.timeout.connect(self._cleanup_old_messages)
        # 每小时检查一次
        self.history_cleanup_timer.start(3600000)
        # 启动时立即执行一次
        QTimer.singleShot(5000, self._cleanup_old_messages)
    
    def _cleanup_old_messages(self):
        """清理过期的历史消息（异步）"""
        def cleanup_task():
            """后台清理任务"""
            try:
                retention_days = self.config_manager.get("history.retention_days", 30)
                if retention_days <= 0:
                    # 0表示永久保留
                    return 0
                
                import time
                cutoff_time = time.time() - (retention_days * 24 * 3600)
                
                # 获取所有消息
                all_messages = self.database.get_all_messages()
                deleted_count = 0
                
                for msg in all_messages:
                    if msg.timestamp < cutoff_time:
                        self.database.delete_message(msg.id)
                        deleted_count += 1
                
                return deleted_count
            except Exception as e:
                logger.error(f"清理历史消息失败: {e}")
                return 0
        
        def on_complete(deleted_count):
            """清理完成回调"""
            if deleted_count > 0:
                retention_days = self.config_manager.get("history.retention_days", 30)
                logger.info(f"已清理 {deleted_count} 条过期消息（保留期限：{retention_days}天）")
        
        # 使用异步任务管理器
        if not hasattr(self, '_cleanup_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._cleanup_task_manager = AsyncTaskManager()
        
        self._cleanup_task_manager.run_task(
            "cleanup_messages",
            cleanup_task,
            on_finished=on_complete
        )
    
    def _show_page(self, page_id: str):
        """显示指定页面"""
        self._show_main_window()
        # 切换到指定页面
        self.main_window._switch_page(page_id)
    
    def _test_popup(self):
        """测试弹窗"""
        self._show_main_window()
        # 可以在这里触发测试弹窗
        from data.models import Message
        from ui.notification_popup import NotificationPopup, PopupStyle, PopupPosition
        import time
        
        message = Message(
            id="tray_test",
            source="托盘测试",
            title="托盘菜单测试",
            content="这是从托盘菜单触发的测试弹窗",
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
    
    def _update_tray_stats(self):
        """更新托盘统计信息（异步）"""
        def update_task():
            """后台任务"""
            try:
                # 获取消息总数
                total_messages = len(self.database.get_all_messages())
                
                # 获取活动连接器数量
                connectors = self.message_processor.get_all_connectors()
                active_connectors = sum(1 for c in connectors.values() if c.is_connected())
                
                return {
                    'total_messages': total_messages,
                    'active_connectors': active_connectors
                }
            except Exception as e:
                logger.error(f"获取托盘统计失败: {e}")
                return None
        
        def on_complete(result):
            """更新托盘图标"""
            if result:
                try:
                    self.tray_icon.update_stats(result['total_messages'], result['active_connectors'])
                except Exception as e:
                    logger.error(f"更新托盘统计失败: {e}")
        
        # 使用异步任务管理器
        if not hasattr(self, '_tray_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._tray_task_manager = AsyncTaskManager()
        
        self._tray_task_manager.run_task(
            "update_tray",
            update_task,
            on_finished=on_complete
        )
    
    def _show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.activateWindow()
        logger.debug("主窗口已显示")
    
    def _on_main_window_closing(self):
        """主窗口关闭时（最小化到托盘）"""
        # 只有在窗口关闭时才显示提示，托盘退出时不显示
        if not self._is_quitting:
            # 检查是否显示托盘通知
            show_notification = self.config_manager.get("system.show_tray_notification", True)
            if show_notification:
                self.tray_icon.show_message(
                    "WinMsgHub",
                    "应用程序已最小化到系统托盘",
                    2000,
                    play_sound=False  # 静音
                )
    
    def _quit_application(self):
        """退出应用程序"""
        logger.info("正在退出应用程序...")
        
        # 标记正在退出，避免显示"最小化到托盘"提示
        self._is_quitting = True
        
        # ⚠️ 关键：强制保存所有页面的配置
        if hasattr(self, 'main_window'):
            try:
                # 遍历所有页面，调用force_save方法（如果有）
                for i in range(self.main_window.pages.count()):
                    page_widget = self.main_window.pages.widget(i)
                    if page_widget and hasattr(page_widget, 'force_save'):
                        try:
                            page_widget.force_save()
                            logger.debug(f"已保存页面 {i} 的配置")
                        except Exception as e:
                            logger.error(f"保存页面 {i} 配置失败: {e}")
            except Exception as e:
                logger.error(f"保存页面配置失败: {e}")
        
        # ⚠️ 关键：强制保存所有待保存的配置
        if hasattr(self, 'config_manager'):
            try:
                logger.info("正在保存配置...")
                self.config_manager.force_save()
                logger.info("配置已保存")
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
        
        # 停止系统监控
        if hasattr(self, 'system_monitor'):
            try:
                self.system_monitor.stop()
                logger.info("系统监控已停止")
            except Exception as e:
                logger.error(f"停止系统监控失败: {e}")
        
        # 停止定时任务管理器
        if hasattr(self, 'scheduler_manager'):
            try:
                self.scheduler_manager.stop_all()
                logger.info("定时任务已停止")
            except Exception as e:
                logger.error(f"停止定时任务失败: {e}")
        
        # 停止本地MQTT服务
        if hasattr(self, 'local_mqtt_manager'):
            try:
                if self.local_mqtt_manager.is_running():
                    logger.info("正在停止本地MQTT服务...")
                    self.local_mqtt_manager.stop_service()
            except Exception as e:
                logger.error(f"停止本地MQTT服务失败: {e}")
        
        # 关闭所有弹窗
        if hasattr(self, 'popup_manager'):
            self.popup_manager.close_all()
        
        # 断开所有连接器
        if hasattr(self, 'connector_manager'):
            try:
                self.connector_manager.disconnect_all()
                logger.info("所有连接器已断开")
            except Exception as e:
                logger.error(f"断开连接器失败: {e}")
        
        # 清理所有异步任务管理器
        for attr_name in dir(self):
            if attr_name.endswith('_task_manager'):
                try:
                    task_manager = getattr(self, attr_name)
                    if hasattr(task_manager, 'cleanup'):
                        task_manager.cleanup()
                        logger.info(f"已清理任务管理器: {attr_name}")
                except Exception as e:
                    logger.error(f"清理任务管理器 {attr_name} 失败: {e}")
        
        # 退出应用
        self.app.quit()
    
    def run(self):
        """运行应用程序"""
        logger.info("WinMsgHub 正在运行...")
        
        # 启动Qt事件循环
        return self.app.exec()


def main():
    """主函数"""
    # 单实例检测
    from utils.single_instance import SingleInstance
    
    single_instance = SingleInstance("WinMsgHub")
    
    if not single_instance.check():
        # 已有实例在运行，显示提示并退出
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "WinMsgHub 已在运行",
            "WinMsgHub 已经在运行中！\n\n"
            "请检查系统托盘，或者关闭已有实例后再启动。",
            QMessageBox.StandardButton.Ok
        )
        sys.exit(0)
    
    try:
        app = WinMsgHubApplication()
        result = app.run()
        
        # 释放单实例锁
        single_instance.release()
        
        sys.exit(result)
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        single_instance.release()
        sys.exit(1)


if __name__ == '__main__':
    main()
