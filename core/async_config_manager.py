"""
WinMsgHub - 异步配置管理器
作者：青云制作_彭明航

提供异步配置保存功能，避免频繁IO阻塞UI
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pathlib import Path
from typing import Any
import json
import logging

logger = logging.getLogger(__name__)


class AsyncConfigManager(QObject):
    """异步配置管理器
    
    特性：
    1. 配置修改立即生效（内存）
    2. 保存操作防抖（延迟写入磁盘）
    3. 批量修改合并保存
    """
    
    # 信号
    config_saved = pyqtSignal()  # 配置已保存
    config_error = pyqtSignal(str)  # 保存出错
    
    def __init__(self, config_manager):
        """初始化
        
        Args:
            config_manager: 原始ConfigManager实例
        """
        super().__init__()
        self.config_manager = config_manager
        
        # 防抖定时器
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._do_save)
        
        # 保存延迟（毫秒）- 500ms，避免过于频繁
        self.save_delay = 500
        
        # 待保存标志
        self._pending_save = False
    
    @property
    def config_file(self):
        """获取配置文件路径"""
        return self.config_manager.config_file
    
    @property
    def config_dir(self):
        """获取配置目录路径"""
        return self.config_manager.config_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置（同步，从内存读取）"""
        return self.config_manager.get(key, default)
    
    def set(self, key: str, value: Any, immediate: bool = False):
        """设置配置
        
        Args:
            key: 配置键
            value: 配置值
            immediate: 是否立即保存（默认False，使用防抖）
        """
        # 立即更新内存
        keys = key.split('.')
        config = self.config_manager.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                raise TypeError(
                    f"无法设置配置项 '{key}'：路径 '{'.'.join(keys[:i + 1])}' "
                    f"处的值是 {type(config[k]).__name__} 而不是字典"
                )
            config = config[k]
        
        config[keys[-1]] = value
        
        # 标记待保存
        self._pending_save = True
        
        if immediate:
            # 立即保存
            self._do_save()
        else:
            # 延迟保存（防抖）
            self.save_timer.stop()
            self.save_timer.start(self.save_delay)
    
    def _do_save(self):
        """执行保存（异步）
        
        在主线程完成JSON序列化（生成不可变快照），
        仅将磁盘写入放到后台线程，避免后台线程遍历配置字典时
        主线程并发修改导致的序列化异常或写入脏数据。
        """
        if not self._pending_save:
            return
        
        # 使用后台线程保存，避免阻塞UI
        from utils.async_worker import AsyncTaskManager
        
        if not hasattr(self, '_save_task_manager'):
            self._save_task_manager = AsyncTaskManager()
        
        # 主线程序列化快照（配置体量小，序列化开销可忽略）
        import json
        try:
            snapshot = json.dumps(self.config_manager.config, indent=2, ensure_ascii=False)
        except Exception as e:
            error_msg = f"序列化配置失败: {e}"
            logger.error(error_msg)
            self.config_error.emit(error_msg)
            return
        
        # 序列化完成即认为本批修改已被捕获；
        # 之后的新修改会重新置位 _pending_save 并重启防抖定时器
        self._pending_save = False
        
        config_file = self.config_manager.config_file
        config_dir = self.config_manager.config_dir
        
        def save_task():
            """后台保存任务（原子写入）"""
            try:
                import os
                config_dir.mkdir(parents=True, exist_ok=True)
                temp_file = config_file.with_suffix('.json.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(snapshot)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_file, config_file)
                return True
            except Exception as e:
                return str(e)
        
        def on_complete(result):
            """保存完成回调"""
            if result is True:
                self.config_saved.emit()
                logger.info("配置已自动保存到文件")
            else:
                # 保存失败，重新标记待保存，等待下次机会（或退出时force_save）
                self._pending_save = True
                error_msg = f"保存配置失败: {result}"
                logger.error(error_msg)
                self.config_error.emit(error_msg)
        
        # 异步执行保存
        self._save_task_manager.run_task(
            "save_config",
            save_task,
            on_finished=on_complete
        )
    
    def force_save(self):
        """强制立即保存（同步）
        
        用于程序退出时确保配置被保存
        注意：不检查_pending_save标志，直接保存
        """
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"[AsyncConfig] force_save 被调用")
        
        try:
            # 停止定时器
            self.save_timer.stop()
            logger.debug("[AsyncConfig] 已停止防抖定时器")
            
            # 同步保存（不检查_pending_save，直接保存）
            logger.info(f"[AsyncConfig] 开始同步保存配置到: {self.config_file}")
            self.config_manager.save_config()
            self._pending_save = False
            self.config_saved.emit()
            logger.info("[AsyncConfig] 配置已强制保存成功")
        except Exception as e:
            error_msg = f"强制保存配置失败: {e}"
            logger.error(f"[AsyncConfig] {error_msg}", exc_info=True)
            self.config_error.emit(error_msg)
    
    def save_config(self):
        """保存配置（兼容旧接口）"""
        self.force_save()
    
    @property
    def config(self):
        """获取配置对象（兼容旧接口）"""
        return self.config_manager.config
    
    @config.setter
    def config(self, value):
        """设置配置对象（兼容旧接口）"""
        self.config_manager.config = value
        self._pending_save = True
    
    def get_all(self) -> dict:
        """获取完整配置"""
        return self.config_manager.get_all()
    
    def reload_config(self):
        """重新加载配置"""
        self.config_manager.reload_config()
