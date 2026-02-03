"""
WinMsgHub - 异步数据库访问层
作者：青云制作_彭明航

提供异步数据库操作，避免阻塞UI线程
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional
from data.models import Message
from data.database import Database
from utils.async_worker import AsyncTaskManager
import logging

logger = logging.getLogger(__name__)


class AsyncDatabase(QObject):
    """异步数据库访问类
    
    所有耗时的数据库操作都在后台线程执行
    """
    
    # 信号定义
    messages_loaded = pyqtSignal(list)  # 消息加载完成
    message_saved = pyqtSignal(bool)  # 消息保存完成
    message_deleted = pyqtSignal(bool)  # 消息删除完成
    messages_cleared = pyqtSignal(bool)  # 消息清空完成
    search_completed = pyqtSignal(list)  # 搜索完成
    count_updated = pyqtSignal(int)  # 消息数量更新
    operation_error = pyqtSignal(str)  # 操作出错
    
    def __init__(self, database: Database):
        """初始化
        
        Args:
            database: Database实例
        """
        super().__init__()
        self.database = database
        self.task_manager = AsyncTaskManager()
    
    def get_messages_async(self, limit: int = 100, offset: int = 0):
        """异步获取消息列表"""
        def task():
            return self.database.get_messages(limit, offset)
        
        self.task_manager.run_task(
            "get_messages",
            task,
            on_finished=self.messages_loaded.emit,
            on_error=self.operation_error.emit
        )
    
    def get_all_messages_async(self):
        """异步获取所有消息"""
        def task():
            return self.database.get_all_messages()
        
        self.task_manager.run_task(
            "get_all_messages",
            task,
            on_finished=self.messages_loaded.emit,
            on_error=self.operation_error.emit
        )
    
    def save_message_async(self, message: Message):
        """异步保存消息"""
        def task():
            return self.database.save_message(message)
        
        self.task_manager.run_task(
            f"save_message_{message.id}",
            task,
            on_finished=self.message_saved.emit,
            on_error=self.operation_error.emit
        )
    
    def delete_message_async(self, message_id: str):
        """异步删除消息"""
        def task():
            return self.database.delete_message(message_id)
        
        self.task_manager.run_task(
            f"delete_message_{message_id}",
            task,
            on_finished=self.message_deleted.emit,
            on_error=self.operation_error.emit
        )
    
    def clear_all_messages_async(self):
        """异步清空所有消息"""
        def task():
            return self.database.clear_all_messages()
        
        self.task_manager.run_task(
            "clear_all_messages",
            task,
            on_finished=self.messages_cleared.emit,
            on_error=self.operation_error.emit
        )
    
    def search_messages_async(self, keyword: str, source: Optional[str] = None):
        """异步搜索消息"""
        def task():
            return self.database.search_messages(keyword, source)
        
        self.task_manager.run_task(
            "search_messages",
            task,
            on_finished=self.search_completed.emit,
            on_error=self.operation_error.emit
        )
    
    def get_message_count_async(self):
        """异步获取消息数量"""
        def task():
            return self.database.get_message_count()
        
        self.task_manager.run_task(
            "get_message_count",
            task,
            on_finished=self.count_updated.emit,
            on_error=self.operation_error.emit
        )
    
    def delete_old_messages_async(self, days: int):
        """异步删除旧消息"""
        def task():
            return self.database.delete_old_messages(days)
        
        def on_finished(count):
            logger.info(f"已删除 {count} 条旧消息")
            self.count_updated.emit(self.database.get_message_count())
        
        self.task_manager.run_task(
            "delete_old_messages",
            task,
            on_finished=on_finished,
            on_error=self.operation_error.emit
        )
    
    # 同步方法（用于必须立即返回结果的场景）
    def save_message_sync(self, message: Message) -> bool:
        """同步保存消息（用于消息处理器）"""
        return self.database.save_message(message)
    
    def get_message_by_id_sync(self, message_id: str) -> Optional[Message]:
        """同步获取消息"""
        return self.database.get_message_by_id(message_id)
    
    def cancel_all_tasks(self):
        """取消所有异步任务"""
        self.task_manager.cancel_all()
