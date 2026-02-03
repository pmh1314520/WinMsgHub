"""
WinMsgHub - 文件监控连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import logging
import time
import uuid
import os
from typing import Callable, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from data.connectors.base import MessageConnector
from data.models import Message

logger = logging.getLogger(__name__)


class FileMonitorHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, callback: Callable[[Message], None], config: dict):
        self.callback = callback
        self.config = config
        self.source_name = f"FileMonitor-{config.get('name', 'default')}"
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        if not event.is_directory and self.config.get('watch_create', True):
            self._send_message('文件创建', event.src_path, '新文件已创建')
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if not event.is_directory and self.config.get('watch_modify', True):
            self._send_message('文件修改', event.src_path, '文件内容已更改')
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件"""
        if not event.is_directory and self.config.get('watch_delete', True):
            self._send_message('文件删除', event.src_path, '文件已被删除')
    
    def on_moved(self, event: FileSystemEvent):
        """文件移动事件"""
        if not event.is_directory and self.config.get('watch_move', True):
            content = f'从 {event.src_path} 移动到 {event.dest_path}'
            self._send_message('文件移动', event.dest_path, content)
    
    def _send_message(self, event_type: str, file_path: str, content: str):
        """发送消息"""
        try:
            # 检查文件扩展名过滤
            patterns = self.config.get('file_patterns', [])
            if patterns:
                if not any(Path(file_path).match(pattern) for pattern in patterns):
                    return
            
            # 读取文件内容（如果配置了）
            if self.config.get('include_content', False):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read(1000)  # 只读取前1000字符
                        if len(file_content) == 1000:
                            file_content += '...'
                        content += f'\n\n内容预览:\n{file_content}'
                except Exception as e:
                    logger.debug(f"无法读取文件内容: {e}")
            
            # 获取用户配置的名称
            source_name = self.config.get('name', '默认')
            
            msg = Message(
                id=str(uuid.uuid4()),
                source=source_name,  # 顶部标签显示用户配置的名称
                title=f'文件监控: {event_type}',  # 标题显示中文+事件类型
                content=f'{Path(file_path).name}\n{content}',  # 内容显示文件名和详情
                timestamp=time.time(),
                metadata={
                    'event_type': event_type,
                    'file_path': file_path,
                    'file_name': Path(file_path).name,
                    'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
            )
            
            self.callback(msg)
            
        except Exception as e:
            logger.error(f"发送文件监控消息失败: {e}")


class FileMonitorConnector(MessageConnector):
    """文件监控连接器
    
    监控本地文件夹变化（如日志文件）。
    """
    
    def __init__(self):
        self.callback: Optional[Callable[[Message], None]] = None
        self.config: dict = {}
        self._connected = False
        self.observer: Optional[Observer] = None
    
    def connect(self, config: dict) -> bool:
        """建立文件监控
        
        Args:
            config: 配置字典，包含：
                - path: 要监控的文件夹路径
                - recursive: 是否递归监控子文件夹
                - file_patterns: 文件匹配模式列表（如 ['*.log', '*.txt']）
                - watch_create: 是否监控文件创建
                - watch_modify: 是否监控文件修改
                - watch_delete: 是否监控文件删除
                - watch_move: 是否监控文件移动
                - include_content: 是否包含文件内容预览
        """
        try:
            self.config = config
            path = config.get('path', '')
            recursive = config.get('recursive', False)
            
            if not path:
                logger.error("文件监控路径未配置")
                return False
            
            if not os.path.exists(path):
                logger.error(f"文件监控路径不存在: {path}")
                return False
            
            # 创建观察者
            self.observer = Observer()
            event_handler = FileMonitorHandler(self._on_message, config)
            self.observer.schedule(event_handler, path, recursive=recursive)
            self.observer.start()
            
            self._connected = True
            logger.info(f"文件监控已启动: {path} (递归: {recursive})")
            return True
            
        except Exception as e:
            logger.error(f"文件监控启动失败: {e}")
            return False
    
    def _on_message(self, message: Message):
        """消息回调"""
        if self.callback:
            self.callback(message)
    
    def disconnect(self) -> None:
        """停止文件监控"""
        try:
            if self.observer:
                logger.info("正在停止文件监控Observer...")
                self.observer.stop()
                # 等待observer线程完全停止
                self.observer.join(timeout=5)
                
                # 检查是否还在运行
                if self.observer.is_alive():
                    logger.warning("文件监控Observer线程未能在5秒内停止")
                else:
                    logger.info("文件监控Observer已完全停止")
                
                self.observer = None
            
            self._connected = False
            logger.info("文件监控已停止")
        except Exception as e:
            logger.error(f"停止文件监控失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息"""
        self.callback = callback
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
