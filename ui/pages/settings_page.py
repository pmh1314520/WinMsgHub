"""
WinMsgHub - 系统设置页面
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QCheckBox, QPushButton, QMessageBox,
    QScrollArea, QGroupBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
import sys
import os
from pathlib import Path
from ui.icon_label import IconLabel
from ui.svg_icons import SvgIcon


class SettingsPage(QWidget):
    """系统设置页面 - 配置系统相关选项"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._auto_save)
        
        self._setup_ui()
        self._load_settings()
        self._connect_signals()
    
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
        title = IconLabel("settings", "系统设置")
        title.setProperty("heading", "h2")
        layout.addWidget(title)
        
        # 启动设置
        startup_card = self._create_startup_settings()
        layout.addWidget(startup_card)
        
        # 窗口设置
        window_card = self._create_window_settings()
        layout.addWidget(window_card)
        
        # 历史记录设置
        history_card = self._create_history_settings()
        layout.addWidget(history_card)
        
        # 系统监控设置
        monitor_card = self._create_monitor_settings()
        layout.addWidget(monitor_card)
        
        # 移除"应用设置"按钮，改为实时自动保存
        # 添加恢复默认按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("  恢复默认")
        reset_btn.setIcon(SvgIcon.get_icon("refresh", "#FFFFFF", 16))
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #C99A3E;
                color: white;
                font-weight: 500;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #DBAC50;
            }
            QPushButton:pressed {
                background-color: #B7882C;
            }
        """)
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
    
    def _create_startup_settings(self) -> QFrame:
        """创建启动设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("rocket", "启动设置")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("配置应用程序的启动行为")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        # 开机自启动
        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setToolTip("在Windows启动时自动运行WinMsgHub")
        layout.addWidget(self.auto_start_check)
        
        # 启动时最小化
        self.start_minimized_check = QCheckBox("启动时最小化到托盘")
        self.start_minimized_check.setToolTip("启动后直接最小化到系统托盘")
        layout.addWidget(self.start_minimized_check)
        
        # 自启动说明
        help_label = QLabel(
            "提示：开机自启动功能会在Windows注册表中添加启动项。\n"
            "勾选后会立即生效，无需手动保存。"
        )
        help_label.setStyleSheet("color: #6C757D; font-size: 12px; padding: 10px;")
        layout.addWidget(help_label)
        help_label.setStyleSheet("""
            QLabel {
                background-color: #1E3A5F;
                color: #ABB2BF;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #4A9EFF;
                font-size: 11px;
            }
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        return card
    
    def _create_window_settings(self) -> QFrame:
        """创建窗口设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("computer", "窗口设置")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("配置主窗口的行为")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        # 最小化到托盘
        self.minimize_to_tray_check = QCheckBox("关闭窗口时最小化到托盘")
        self.minimize_to_tray_check.setToolTip("点击关闭按钮时不退出程序，而是最小化到系统托盘")
        layout.addWidget(self.minimize_to_tray_check)
        
        # 显示托盘通知
        self.show_tray_notification_check = QCheckBox("显示托盘最小化通知")
        self.show_tray_notification_check.setToolTip("最小化到托盘时显示通知提示")
        layout.addWidget(self.show_tray_notification_check)
        
        return card
    
    def _create_history_settings(self) -> QFrame:
        """创建历史记录设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("history", "历史记录设置")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("配置消息历史记录的保留策略")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        # 保留天数
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("历史记录保留天数:"))
        
        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(0, 365)
        self.retention_days_spin.setValue(30)
        self.retention_days_spin.setSuffix(" 天")
        self.retention_days_spin.setToolTip("超过此天数的消息将被自动清理，设置为0表示永久保留")
        self.retention_days_spin.setSpecialValueText("永久保留")
        retention_layout.addWidget(self.retention_days_spin)
        
        retention_layout.addStretch()
        layout.addLayout(retention_layout)
        
        help_label = QLabel(
            "提示：设置为0表示永久保留所有消息。\n"
            "系统会每小时自动检查并清理过期消息。\n"
            "建议根据实际需求设置合理的保留天数，避免数据库过大。"
        )
        help_label.setStyleSheet("color: #6C757D; font-size: 12px; padding: 10px;")
        layout.addWidget(help_label)
        help_label.setStyleSheet("""
            QLabel {
                background-color: #1E3A5F;
                color: #ABB2BF;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #4A9EFF;
                font-size: 11px;
            }
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        return card
    
    def _create_monitor_settings(self) -> QFrame:
        """创建系统监控设置卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title = IconLabel("monitor", "系统监控设置")
        title.setProperty("heading", "h3")
        layout.addWidget(title)
        
        info = QLabel("配置整点提示、CPU和内存监控功能")
        info.setProperty("secondary", "true")
        layout.addWidget(info)
        
        # 整点提示
        self.hourly_alert_check = QCheckBox("启用整点提示")
        self.hourly_alert_check.setToolTip("每到整点（如1:00、2:00）时弹窗提示，提醒休息")
        layout.addWidget(self.hourly_alert_check)
        
        # CPU监控
        cpu_layout = QVBoxLayout()
        cpu_layout.setSpacing(10)
        
        self.cpu_alert_check = QCheckBox("启用CPU使用率监控")
        self.cpu_alert_check.setToolTip("当CPU使用率超过阈值时弹窗提示")
        cpu_layout.addWidget(self.cpu_alert_check)
        
        cpu_threshold_layout = QHBoxLayout()
        cpu_threshold_layout.addSpacing(30)
        cpu_threshold_layout.addWidget(QLabel("CPU告警阈值:"))
        
        self.cpu_threshold_spin = QSpinBox()
        self.cpu_threshold_spin.setRange(10, 100)
        self.cpu_threshold_spin.setValue(80)
        self.cpu_threshold_spin.setSuffix(" %")
        self.cpu_threshold_spin.setToolTip("CPU使用率超过此值时触发告警")
        cpu_threshold_layout.addWidget(self.cpu_threshold_spin)
        
        cpu_threshold_layout.addStretch()
        cpu_layout.addLayout(cpu_threshold_layout)
        
        layout.addLayout(cpu_layout)
        
        # 内存监控
        memory_layout = QVBoxLayout()
        memory_layout.setSpacing(10)
        
        self.memory_alert_check = QCheckBox("启用内存使用率监控")
        self.memory_alert_check.setToolTip("当内存使用率超过阈值时弹窗提示")
        memory_layout.addWidget(self.memory_alert_check)
        
        memory_threshold_layout = QHBoxLayout()
        memory_threshold_layout.addSpacing(30)
        memory_threshold_layout.addWidget(QLabel("内存告警阈值:"))
        
        self.memory_threshold_spin = QSpinBox()
        self.memory_threshold_spin.setRange(10, 100)
        self.memory_threshold_spin.setValue(80)
        self.memory_threshold_spin.setSuffix(" %")
        self.memory_threshold_spin.setToolTip("内存使用率超过此值时触发告警")
        memory_threshold_layout.addWidget(self.memory_threshold_spin)
        
        memory_threshold_layout.addStretch()
        memory_layout.addLayout(memory_threshold_layout)
        
        layout.addLayout(memory_layout)
        
        help_label = QLabel(
            "提示：\n"
            "• 整点提示可以帮助您定时休息，保护眼睛\n"
            "• CPU/内存监控会在资源使用过高时提醒您\n"
            "• 告警触发后5分钟内不会重复提示，避免频繁打扰"
        )
        help_label.setStyleSheet("""
            QLabel {
                background-color: #1E3A5F;
                color: #ABB2BF;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #4A9EFF;
                font-size: 11px;
            }
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        return card
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 启动设置
            self.auto_start_check.setChecked(
                self.config_manager.get("system.auto_start", False)
            )
            self.start_minimized_check.setChecked(
                self.config_manager.get("system.start_minimized", False)
            )
            
            # 窗口设置
            self.minimize_to_tray_check.setChecked(
                self.config_manager.get("system.minimize_to_tray", True)
            )
            self.show_tray_notification_check.setChecked(
                self.config_manager.get("system.show_tray_notification", True)
            )
            
            # 历史记录设置
            self.retention_days_spin.setValue(
                self.config_manager.get("history.retention_days", 30)
            )
            
            # 系统监控设置
            self.hourly_alert_check.setChecked(
                self.config_manager.get("system_monitor.hourly_alert_enabled", False)
            )
            self.cpu_alert_check.setChecked(
                self.config_manager.get("system_monitor.cpu_alert_enabled", False)
            )
            self.cpu_threshold_spin.setValue(
                self.config_manager.get("system_monitor.cpu_threshold", 80)
            )
            self.memory_alert_check.setChecked(
                self.config_manager.get("system_monitor.memory_alert_enabled", False)
            )
            self.memory_threshold_spin.setValue(
                self.config_manager.get("system_monitor.memory_threshold", 80)
            )
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {e}")
    
    def _connect_signals(self):
        """连接信号"""
        self.auto_start_check.stateChanged.connect(self._on_auto_start_changed)
        self.start_minimized_check.stateChanged.connect(self._trigger_auto_save)
        self.minimize_to_tray_check.stateChanged.connect(self._trigger_auto_save)
        self.show_tray_notification_check.stateChanged.connect(self._trigger_auto_save)
        self.retention_days_spin.valueChanged.connect(self._trigger_auto_save)
        
        # 系统监控设置
        self.hourly_alert_check.stateChanged.connect(self._trigger_auto_save)
        self.cpu_alert_check.stateChanged.connect(self._trigger_auto_save)
        self.cpu_threshold_spin.valueChanged.connect(self._trigger_auto_save)
        self.memory_alert_check.stateChanged.connect(self._trigger_auto_save)
        self.memory_threshold_spin.valueChanged.connect(self._trigger_auto_save)
    
    def _on_auto_start_changed(self):
        """开机自启动状态改变"""
        # 立即应用开机自启动设置
        try:
            if self.auto_start_check.isChecked():
                self._enable_auto_start()
            else:
                self._disable_auto_start()
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
        
        # 触发自动保存
        self._trigger_auto_save()
    
    def _trigger_auto_save(self):
        """触发自动保存（防抖延迟3秒）"""
        self.auto_save_timer.stop()
        self.auto_save_timer.start(3000)  # 改为3秒，避免频繁保存
    
    def _auto_save(self):
        """自动保存设置"""
        try:
            self._save_settings()
        except Exception as e:
            print(f"自动保存设置失败: {e}")
    
    def force_save(self):
        """强制立即保存配置（用于页面切换或程序退出时）"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        # 停止定时器
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
            logger.debug("[系统设置] 已停止防抖定时器")
        
        # 立即保存
        try:
            self._save_settings()
            # 强制保存到文件
            self.config_manager.save_config()
            logger.info("[系统设置] 配置已强制保存到文件")
        except Exception as e:
            logger.error(f"[系统设置] 强制保存设置失败: {e}", exc_info=True)
    
    def _save_settings(self):
        """保存设置"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        logger.info("[系统设置] 配置已修改，准备自动保存...")
        print("[系统设置] 配置已修改，准备自动保存...")
        
        # 启动设置
        self.config_manager.set("system.auto_start", self.auto_start_check.isChecked())
        self.config_manager.set("system.start_minimized", self.start_minimized_check.isChecked())
        
        # 窗口设置
        self.config_manager.set("system.minimize_to_tray", self.minimize_to_tray_check.isChecked())
        self.config_manager.set("system.show_tray_notification", self.show_tray_notification_check.isChecked())
        
        # 历史记录设置
        self.config_manager.set("history.retention_days", self.retention_days_spin.value())
        
        # 系统监控设置
        self.config_manager.set("system_monitor.hourly_alert_enabled", self.hourly_alert_check.isChecked())
        self.config_manager.set("system_monitor.cpu_alert_enabled", self.cpu_alert_check.isChecked())
        self.config_manager.set("system_monitor.cpu_threshold", self.cpu_threshold_spin.value())
        self.config_manager.set("system_monitor.memory_alert_enabled", self.memory_alert_check.isChecked())
        self.config_manager.set("system_monitor.memory_threshold", self.memory_threshold_spin.value())
        
        logger.info("[系统设置] 配置已更新到内存，等待写入文件...")
    
    def _apply_settings(self):
        """应用设置"""
        try:
            self._save_settings()
            
            # 处理开机自启动
            if self.auto_start_check.isChecked():
                self._enable_auto_start()
            else:
                self._disable_auto_start()
            
            QMessageBox.information(
                self,
                "成功",
                "设置已保存并立即生效！"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用设置失败: {e}")
    
    def _enable_auto_start(self):
        """启用开机自启动"""
        try:
            if sys.platform == "win32":
                import winreg
                
                # 获取可执行文件路径
                if getattr(sys, 'frozen', False):
                    # 打包后的exe
                    exe_path = sys.executable
                else:
                    # 开发环境
                    exe_path = os.path.abspath(sys.argv[0])
                
                # 添加到注册表
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                
                winreg.SetValueEx(key, "WinMsgHub", 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
                
                print(f"已添加开机自启动: {exe_path}")
            else:
                QMessageBox.warning(
                    self,
                    "不支持",
                    "当前系统不支持开机自启动功能"
                )
        except Exception as e:
            QMessageBox.warning(self, "警告", f"设置开机自启动失败: {e}")
    
    def _disable_auto_start(self):
        """禁用开机自启动"""
        try:
            if sys.platform == "win32":
                import winreg
                
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                
                try:
                    winreg.DeleteValue(key, "WinMsgHub")
                    print("已移除开机自启动")
                except FileNotFoundError:
                    # 注册表项不存在，忽略
                    pass
                
                winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"移除开机自启动失败: {e}")
    
    def _reset_to_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 恢复系统设置默认值
                self.auto_start_check.setChecked(False)
                self.start_minimized_check.setChecked(False)
                self.minimize_to_tray_check.setChecked(True)
                self.show_tray_notification_check.setChecked(True)
                
                # 恢复历史记录设置默认值
                self.retention_days_spin.setValue(30)
                
                # 恢复系统监控设置默认值
                self.hourly_alert_check.setChecked(False)
                self.cpu_alert_check.setChecked(False)
                self.cpu_threshold_spin.setValue(80)
                self.memory_alert_check.setChecked(False)
                self.memory_threshold_spin.setValue(80)
                
                # 保存设置
                self._save_settings()
                
                # 禁用开机自启动
                self._disable_auto_start()
                
                QMessageBox.information(self, "成功", "已恢复所有设置为默认值")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"恢复默认设置失败: {e}")
