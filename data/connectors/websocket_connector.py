"""
WinMsgHub - WebSocket消息源连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import json
import logging
import time
import uuid
from typing import Callable, Optional
import threading
try:
    from websocket import WebSocketApp
except ImportError:
    import websocket
    WebSocketApp = websocket.WebSocketApp
from data.connectors.base import MessageConnector
from data.models import Message

logger = logging.getLogger(__name__)


class WebSocketConnector(MessageConnector):
    """WebSocket消息源连接器
    
    支持实时双向通信，比API轮询更高效。
    """
    
    def __init__(self):
        self.ws: Optional[websocket.WebSocketApp] = None
        self.callback: Optional[Callable[[Message], None]] = None
        self.config: dict = {}
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._should_reconnect = True
    
    def connect(self, config: dict) -> bool:
        """建立WebSocket连接
        
        Args:
            config: 配置字典，包含：
                - url: WebSocket服务器URL (ws:// 或 wss://)
                - headers: 可选的HTTP头部字典
                - ping_interval: 心跳间隔（秒）
                - ping_timeout: 心跳超时（秒）
                - reconnect: 是否自动重连
        """
        try:
            self.config = config
            url = config.get('url', '')
            headers = config.get('headers', {})
            ping_interval = config.get('ping_interval', 30)
            ping_timeout = config.get('ping_timeout', 10)
            self._should_reconnect = config.get('reconnect', True)
            
            if not url:
                logger.error("WebSocket URL未配置")
                return False
            
            # 创建WebSocket应用
            self.ws = WebSocketApp(
                url,
                header=headers,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 在单独的线程中运行
            self._thread = threading.Thread(
                target=self._run_forever,
                args=(ping_interval, ping_timeout),
                daemon=True
            )
            self._thread.start()
            
            # 等待连接建立
            timeout = 5
            start_time = time.time()
            while not self._connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self._connected:
                logger.info(f"WebSocket已连接: {url}")
                return True
            else:
                logger.error("WebSocket连接超时")
                return False
                
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False
    
    def _run_forever(self, ping_interval: int, ping_timeout: int):
        """在循环中运行WebSocket，支持自动重连"""
        while self._should_reconnect:
            try:
                self.ws.run_forever(
                    ping_interval=ping_interval,
                    ping_timeout=ping_timeout
                )
            except Exception as e:
                logger.error(f"WebSocket运行错误: {e}")
            
            if self._should_reconnect:
                logger.info("WebSocket断开，5秒后重连...")
                time.sleep(5)
    
    def _on_open(self, ws):
        """WebSocket连接打开回调"""
        self._connected = True
        logger.info("WebSocket连接已建立")
    
    def _on_message(self, ws, message):
        """WebSocket消息接收回调"""
        try:
            if self.callback:
                # 获取用户配置的名称
                source_name = self.config.get('name', '默认')
                
                # 尝试解析JSON消息
                try:
                    data = json.loads(message)
                    # 支持自定义source（第3参数）
                    final_source = data.get('source', source_name)
                    
                    msg = Message(
                        id=data.get('id', str(uuid.uuid4())),
                        source=final_source,  # 优先使用解析出来的source
                        title=data.get('title', 'WebSocket'),  # 标题默认显示中文
                        content=data.get('content', message),
                        timestamp=data.get('timestamp', time.time()),
                        metadata=data.get('metadata', {})
                    )
                except json.JSONDecodeError:
                    # 如果不是JSON，作为纯文本处理
                    msg = Message(
                        id=str(uuid.uuid4()),
                        source=source_name,  # 顶部标签显示用户配置的名称
                        title='WebSocket',  # 标题显示中文
                        content=message,
                        timestamp=time.time(),
                        metadata={}
                    )
                
                self.callback(msg)
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket错误回调"""
        logger.error(f"WebSocket错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭回调"""
        self._connected = False
        logger.info(f"WebSocket连接已关闭: {close_status_code} - {close_msg}")
    
    def disconnect(self) -> None:
        """断开WebSocket连接"""
        try:
            self._should_reconnect = False
            if self.ws:
                self.ws.close()
            
            # 等待线程结束
            if self._thread and self._thread.is_alive():
                logger.info("等待WebSocket线程结束...")
                self._thread.join(timeout=5)
                if self._thread.is_alive():
                    logger.warning("WebSocket线程未能在5秒内停止")
            
            self._connected = False
            logger.info("WebSocket已断开")
        except Exception as e:
            logger.error(f"断开WebSocket失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息"""
        self.callback = callback
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def send(self, message: str) -> bool:
        """发送消息到WebSocket服务器
        
        Args:
            message: 要发送的消息
            
        Returns:
            发送成功返回True
        """
        try:
            if self.ws and self._connected:
                self.ws.send(message)
                return True
            else:
                logger.error("WebSocket未连接")
                return False
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            return False
