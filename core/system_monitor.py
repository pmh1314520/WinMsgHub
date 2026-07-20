"""
WinMsgHub - 系统监控管理器
作者：青云制作_彭明航

提供整点提示、CPU监控、内存监控等功能
"""

import time
import psutil
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemMonitor(QObject):
    """系统监控管理器"""
    
    # 信号
    hourly_alert = pyqtSignal(int)  # 整点提示信号（小时）
    cpu_alert = pyqtSignal(float)  # CPU过高提示信号（使用率）
    memory_alert = pyqtSignal(float)  # 内存过高提示信号（使用率）
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
        # 上次提示时间（防止重复提示）
        self._last_hourly_alert = None
        self._last_cpu_alert_time = 0
        self._last_memory_alert_time = 0
        
        # 提示冷却时间（秒）
        self.alert_cooldown = 300  # 5分钟内不重复提示
        
        # 启动监控定时器
        self._start_monitors()
        
        logger.info("系统监控管理器已初始化")
    
    def _start_monitors(self):
        """启动所有监控定时器"""
        # 整点提示定时器（每分钟检查一次）
        self.hourly_timer = QTimer()
        self.hourly_timer.timeout.connect(self._check_hourly)
        self.hourly_timer.start(60000)  # 每60秒检查一次
        
        # CPU监控定时器（每10秒检查一次）
        self.cpu_timer = QTimer()
        self.cpu_timer.timeout.connect(self._check_cpu_async)
        self.cpu_timer.start(10000)  # 每10秒检查一次
        
        # 内存监控定时器（每10秒检查一次）
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self._check_memory_async)
        self.memory_timer.start(10000)  # 每10秒检查一次
        
        logger.info("系统监控定时器已启动")
    
    def _check_hourly(self):
        """检查是否到整点
        
        允许2分钟的触发窗口：QTimer的粗粒度定时器有约5%的时间偏差，
        只判断minute==0偶尔会错过整点检查，导致整点提示丢失。
        """
        # 检查功能是否启用
        if not self.config_manager.get("system_monitor.hourly_alert_enabled", False):
            return
        
        now = datetime.now()
        current_hour = now.hour
        
        # 整点后2分钟内均可触发（每小时仍只提示一次）
        if now.minute < 2:
            # 防止同一小时重复提示（用(日期,小时)做键，跨天同小时也能正确触发）
            alert_key = (now.date(), current_hour)
            if self._last_hourly_alert != alert_key:
                self._last_hourly_alert = alert_key
                self.hourly_alert.emit(current_hour)
                logger.info(f"触发整点提示: {current_hour}:00")
    
    def _check_cpu_async(self):
        """异步检查CPU使用率"""
        # 检查功能是否启用
        if not self.config_manager.get("system_monitor.cpu_alert_enabled", False):
            return
        
        # 使用异步任务管理器
        if not hasattr(self, '_cpu_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._cpu_task_manager = AsyncTaskManager()
        
        def check_task():
            """后台检查CPU"""
            try:
                # 获取CPU使用率（1秒采样）
                cpu_percent = psutil.cpu_percent(interval=1)
                return cpu_percent
            except Exception as e:
                logger.error(f"获取CPU使用率失败: {e}")
                return None
        
        def on_checked(cpu_percent):
            """检查完成回调"""
            if cpu_percent is None:
                return
            
            threshold = self.config_manager.get("system_monitor.cpu_threshold", 80)
            
            # 检查是否超过阈值
            if cpu_percent >= threshold:
                # 检查冷却时间
                current_time = time.time()
                if current_time - self._last_cpu_alert_time >= self.alert_cooldown:
                    self._last_cpu_alert_time = current_time
                    self.cpu_alert.emit(cpu_percent)
                    logger.warning(f"CPU使用率过高: {cpu_percent:.1f}%")
        
        # 异步执行检查
        self._cpu_task_manager.run_task(
            "check_cpu",
            check_task,
            on_finished=on_checked
        )
    
    def _check_memory_async(self):
        """异步检查内存使用率"""
        # 检查功能是否启用
        if not self.config_manager.get("system_monitor.memory_alert_enabled", False):
            return
        
        # 使用异步任务管理器
        if not hasattr(self, '_memory_task_manager'):
            from utils.async_worker import AsyncTaskManager
            self._memory_task_manager = AsyncTaskManager()
        
        def check_task():
            """后台检查内存"""
            try:
                # 获取内存使用率
                memory = psutil.virtual_memory()
                return memory.percent
            except Exception as e:
                logger.error(f"获取内存使用率失败: {e}")
                return None
        
        def on_checked(memory_percent):
            """检查完成回调"""
            if memory_percent is None:
                return
            
            threshold = self.config_manager.get("system_monitor.memory_threshold", 80)
            
            # 检查是否超过阈值
            if memory_percent >= threshold:
                # 检查冷却时间
                current_time = time.time()
                if current_time - self._last_memory_alert_time >= self.alert_cooldown:
                    self._last_memory_alert_time = current_time
                    self.memory_alert.emit(memory_percent)
                    logger.warning(f"内存使用率过高: {memory_percent:.1f}%")
        
        # 异步执行检查
        self._memory_task_manager.run_task(
            "check_memory",
            check_task,
            on_finished=on_checked
        )
    
    def stop(self):
        """停止所有监控"""
        if hasattr(self, 'hourly_timer'):
            self.hourly_timer.stop()
        if hasattr(self, 'cpu_timer'):
            self.cpu_timer.stop()
        if hasattr(self, 'memory_timer'):
            self.memory_timer.stop()
        
        # 清理异步任务管理器
        if hasattr(self, '_cpu_task_manager'):
            self._cpu_task_manager.cleanup()
        if hasattr(self, '_memory_task_manager'):
            self._memory_task_manager.cleanup()
        
        logger.info("系统监控已停止")
