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
        self.ws: Optional[WebSocketApp] = None
        self.callback: Optional[Callable[[Message], None]] = None
        self.config: dict = {}
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._should_reconnect = True
        # 可中断的重连等待事件（disconnect时立即唤醒，避免线程卡在sleep中）
        self._stop_event = threading.Event()
    
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
            self._stop_event.clear()
            url = config.get('url', '')
            headers = config.get('headers', {})
            ping_interval = config.get('ping_interval', 30)
            ping_timeout = config.get('ping_timeout', 10)
            self._should_reconnect = config.get('reconnect', True)
            
            if not url:
                logger.error("WebSocket URL未配置")
                return False
            
            # websocket-client要求 ping_timeout < ping_interval，否则直接抛异常
            if ping_interval > 0 and ping_timeout >= ping_interval:
                ping_timeout = max(1, ping_interval - 1)
                logger.warning(
                    f"心跳超时必须小于心跳间隔，已自动调整为 {ping_timeout} 秒"
                )
            
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
            elif self._should_reconnect:
                # 启用了自动重连：后台线程会持续尝试，返回True让连接器被正常管理，
                # 否则重连线程会成为无法停止的"僵尸线程"
                logger.warning(f"WebSocket连接超时（{timeout}秒），将在后台继续尝试连接: {url}")
                return True
            else:
                # 未启用自动重连：彻底停止线程后返回失败
                logger.error("WebSocket连接超时")
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False
    
    def _run_forever(self, ping_interval: int, ping_timeout: int):
        """在循环中运行WebSocket，支持自动重连"""
        while self._should_reconnect and not self._stop_event.is_set():
            try:
                self.ws.run_forever(
                    ping_interval=ping_interval,
                    ping_timeout=ping_timeout
                )
            except Exception as e:
                logger.error(f"WebSocket运行错误: {e}")
            
            if self._should_reconnect and not self._stop_event.is_set():
                logger.info("WebSocket断开，5秒后重连...")
                # 使用Event等待，disconnect时可以立即中断
                self._stop_event.wait(5)
    
    def _on_open(self, ws):
        """WebSocket连接打开回调"""
        self._connected = True
        logger.info("WebSocket连接已建立")
    
    def _on_message(self, ws, message):
        """WebSocket消息接收回调
        
        支持两种JSON格式：
        1. 标准格式：{"title": "标题", "content": "内容", "source": "来源"}
        2. 嵌套格式：{"msg": "{\"title\": \"标题\", \"content\": \"内容\", \"source\": \"来源\"}"}
        其中source字段可选
        """
        try:
            if not self.callback:
                return
            
            # 解析JSON（非JSON文本作为纯文本消息处理）
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.debug("WebSocket消息不是JSON格式，作为纯文本处理")
                data = {'title': '新消息', 'content': str(message)}
            
            # 非字典JSON（字符串/数组/数字）：整体作为消息内容
            if not isinstance(data, dict):
                data = {'title': '新消息', 'content': str(data)}
            
            # 检查是否是嵌套格式（msg字段包含JSON字符串）
            if 'msg' in data and isinstance(data['msg'], str):
                try:
                    # 尝试解析msg字段中的JSON字符串
                    nested_data = json.loads(data['msg'])
                    if isinstance(nested_data, dict):
                        data = nested_data
                        logger.debug("WebSocket检测到嵌套格式，已解析")
                    else:
                        data = {'title': '新消息', 'content': str(nested_data)}
                except json.JSONDecodeError:
                    # 如果msg字段不是JSON，就把它当作content
                    if 'title' not in data and 'content' not in data:
                        data = {
                            'title': '新消息',
                            'content': data['msg']
                        }
            
            # 验证必需字段
            if 'title' not in data or 'content' not in data:
                logger.error("WebSocket消息缺少必需字段(title或content)，跳过")
                return
            
            # 获取source（可选字段）
            source_name = self.config.get('name', 'WebSocket')
            final_source = data.get('source', source_name)
            
            # 创建Message对象
            msg = Message(
                id=data.get('id', str(uuid.uuid4())),
                source=final_source,
                title=str(data['title']),
                content=str(data['content']),
                timestamp=data.get('timestamp', time.time()),
                metadata=data.get('metadata', {})
            )
            
            logger.info(f"WebSocket消息已解析: title={msg.title}, source={msg.source}")
            self.callback(msg)
            
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}", exc_info=True)
    
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
            self._stop_event.set()  # 唤醒可能在等待重连的线程
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
