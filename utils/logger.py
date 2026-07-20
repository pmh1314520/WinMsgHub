"""
日志系统模块

作者：青云制作_彭明航
许可：要求二次开发必须开源并标明原作者，允许商用
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import os


class Logger:
    """日志管理器"""
    
    _instance: Optional['Logger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志系统"""
        if self._initialized:
            return
        
        # 确定日志目录
        if os.name == 'nt':  # Windows
            log_dir = Path(os.environ.get('APPDATA', '.')) / 'WinMsgHub' / 'logs'
        else:
            log_dir = Path.home() / '.winmsghub' / 'logs'
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        log_file = log_dir / 'winmsghub.log'
        
        # 配置根日志记录器
        self.logger = logging.getLogger('WinMsgHub')
        self.logger.setLevel(logging.INFO)  # 改为INFO级别，减少日志量
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 使用QueueHandler实现异步日志写入，避免阻塞UI
            from logging.handlers import QueueHandler, QueueListener
            import queue
            
            # 创建日志队列
            log_queue = queue.Queue(-1)  # 无限大小
            
            # 创建队列处理器（主线程使用，不阻塞）
            queue_handler = QueueHandler(log_queue)
            self.logger.addHandler(queue_handler)
            
            # 创建实际的文件和控制台处理器（后台线程使用）
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)  # 文件也只记录INFO以上
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 保存处理器引用，set_level时需要同步调整处理器级别
            self._handlers = [file_handler, console_handler]
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 创建队列监听器（在后台线程中处理日志）
            self.queue_listener = QueueListener(
                log_queue,
                file_handler,
                console_handler,
                respect_handler_level=True
            )
            
            # 启动监听器
            self.queue_listener.start()
        
        self._initialized = True
        self.logger.info("日志系统初始化完成")
    
    def get_logger(self, name: str = 'WinMsgHub') -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        # 如果是子模块，使用WinMsgHub作为父logger
        if name != 'WinMsgHub' and not name.startswith('WinMsgHub.'):
            name = f'WinMsgHub.{name}'
        
        child_logger = logging.getLogger(name)
        # 确保子logger不会重复处理（propagate=True会传递给父logger）
        child_logger.propagate = True
        return child_logger
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            new_level = level_map[level.upper()]
            self.logger.setLevel(new_level)
            # 同步调整文件/控制台处理器级别，
            # 否则处理器停留在INFO，设置DEBUG后调试日志依然不会输出
            for handler in getattr(self, '_handlers', []):
                handler.setLevel(new_level)
            self.logger.info(f"日志级别设置为: {level.upper()}")
        else:
            self.logger.warning(f"无效的日志级别: {level}")


# 全局日志实例
_logger_instance = Logger()


def get_logger(name: str = 'WinMsgHub') -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return _logger_instance.get_logger(name)


def set_log_level(level: str):
    """
    设置日志级别的便捷函数
    
    Args:
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    _logger_instance.set_level(level)
