"""
WinMsgHub - 剪贴板监控连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import logging
import time
import uuid
import threading
from typing import Callable, Optional
import pyperclip
from PyQt6.QtCore import QObject, pyqtSignal
from data.connectors.base import MessageConnector
from data.models import Message

logger = logging.getLogger(__name__)


class ClipboardSignalEmitter(QObject):
    """用于跨线程发送信号的辅助类"""
    message_received = pyqtSignal(object)


class ClipboardConnector(MessageConnector):
    """剪贴板监控连接器
    
    监控剪贴板内容变化。
    """
    
    # 类变量：用于标记是否应该忽略下一次剪贴板变化（由智能复制触发）
    _ignore_next_change = False
    _ignore_lock = threading.Lock()
    
    @classmethod
    def mark_ignore_next_change(cls):
        """标记忽略下一次剪贴板变化（由智能复制调用）"""
        with cls._ignore_lock:
            cls._ignore_next_change = True
    
    def __init__(self):
        self.callback: Optional[Callable[[Message], None]] = None
        self.config: dict = {}
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_content = ""
        # 最近出现过的内容（用于ignore_duplicates去重）
        self._recent_contents: dict = {}
        self._max_recent_contents = 20
        # 创建信号发射器（在主线程中）
        self._signal_emitter = ClipboardSignalEmitter()
    
    def connect(self, config: dict) -> bool:
        """建立剪贴板监控
        
        Args:
            config: 配置字典，包含：
                - poll_interval: 轮询间隔（秒），默认1秒
                - min_length: 最小内容长度，默认1
                - max_length: 最大内容长度（超过则截断），默认1000
                - ignore_duplicates: 是否忽略重复内容，默认True
        """
        try:
            self.config = config
            self._last_content = ""
            self._connected = True
            self._stop_event.clear()
            
            # 启动监控线程
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            
            logger.info("剪贴板监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"剪贴板监控启动失败: {e}")
            return False
    
    def _monitor_loop(self):
        """监控循环"""
        poll_interval = self.config.get('poll_interval', 1)
        min_length = self.config.get('min_length', 1)
        max_length = self.config.get('max_length', 1000)
        ignore_duplicates = self.config.get('ignore_duplicates', True)
        
        # 首次获取剪贴板内容
        try:
            self._last_content = pyperclip.paste()
        except Exception as e:
            logger.warning(f"无法访问剪贴板: {e}")
            self._last_content = ""
        
        while not self._stop_event.is_set():
            try:
                # 获取当前剪贴板内容（添加超时保护）
                current_content = ""
                try:
                    current_content = pyperclip.paste()
                except Exception as e:
                    logger.debug(f"读取剪贴板失败: {e}")
                    # 继续下一次循环
                    self._stop_event.wait(poll_interval)
                    continue
                
                # 检查是否有变化
                if current_content and current_content != self._last_content:
                    # 检查是否应该忽略这次变化（由智能复制触发）
                    with self.__class__._ignore_lock:
                        if self.__class__._ignore_next_change:
                            logger.debug("忽略由智能复制触发的剪贴板变化")
                            self.__class__._ignore_next_change = False
                            self._last_content = current_content
                            self._stop_event.wait(poll_interval)
                            continue
                    
                    # ignore_duplicates: 最近出现过的相同内容不重复提醒
                    is_recent_duplicate = (
                        ignore_duplicates and current_content in self._recent_contents
                    )
                    
                    # 检查长度
                    if len(current_content) >= min_length and not is_recent_duplicate:
                        self._send_message(current_content, max_length)
                    elif is_recent_duplicate:
                        logger.debug("剪贴板内容与最近记录重复，已跳过提醒")
                    
                    # 记录到最近内容缓存（dict保持插入顺序）
                    self._recent_contents[current_content] = True
                    if len(self._recent_contents) > self._max_recent_contents:
                        oldest_key = next(iter(self._recent_contents))
                        del self._recent_contents[oldest_key]
                    
                    self._last_content = current_content
                    
            except Exception as e:
                logger.error(f"剪贴板监控错误: {e}")
            
            # 等待下一次检查
            self._stop_event.wait(poll_interval)
    
    def _send_message(self, content: str, max_length: int):
        """发送消息 - 使用信号跨线程通信"""
        try:
            # 截断过长的内容
            truncated = False
            if len(content) > max_length:
                content = content[:max_length]
                truncated = True
            
            # 获取用户配置的名称
            source_name = self.config.get('name', '默认')
            
            msg = Message(
                id=str(uuid.uuid4()),
                source=source_name,  # 顶部标签显示用户配置的名称
                title='剪贴板',  # 标题显示中文
                content=content + ('\n\n[内容已截断]' if truncated else ''),  # 内容就是剪贴板内容
                timestamp=time.time(),
                metadata={
                    'length': len(content),
                    'truncated': truncated,
                    'connector_type': 'clipboard'
                }
            )
            
            # 使用信号发送消息到主线程
            self._signal_emitter.message_received.emit(msg)
            
        except Exception as e:
            logger.error(f"发送剪贴板消息失败: {e}")
    
    def disconnect(self) -> None:
        """停止剪贴板监控"""
        try:
            logger.info("正在停止剪贴板监控...")
            self._stop_event.set()
            
            if self._thread and self._thread.is_alive():
                logger.info("等待剪贴板监控线程结束...")
                self._thread.join(timeout=5)
                if self._thread.is_alive():
                    logger.warning("剪贴板监控线程未能在5秒内停止")
                else:
                    logger.info("剪贴板监控线程已完全停止")
            
            self._connected = False
            logger.info("剪贴板监控已停止")
        except Exception as e:
            logger.error(f"停止剪贴板监控失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息 - 连接信号到回调"""
        # 先断开旧连接，防止subscribe被多次调用时消息重复分发
        if self.callback is not None:
            try:
                self._signal_emitter.message_received.disconnect()
            except TypeError:
                pass
        
        self.callback = callback
        # 将信号连接到回调函数，确保在主线程中执行
        self._signal_emitter.message_received.connect(callback)
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
