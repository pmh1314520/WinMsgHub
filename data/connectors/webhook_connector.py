"""
WinMsgHub - Webhook消息源连接器（仅支持POST）
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import json
import time
import uuid
import threading
from typing import Callable, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from data.connectors.base import MessageConnector
from data.models import Message
from utils.logger import get_logger

logger = get_logger(__name__)


class WebhookConnector(MessageConnector):
    """Webhook消息源连接器 - 仅支持POST方法"""
    
    def __init__(self):
        self._callback: Optional[Callable[[Message], None]] = None
        self._connected = False
        self._config: Optional[dict] = None
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        logger.info("Webhook连接器已初始化")
    
    def connect(self, config: dict) -> bool:
        try:
            self._config = config
            port = config.get('port', 8080)
            host = config.get('host', '0.0.0.0')
            
            connector = self
            
            class WebhookHandler(BaseHTTPRequestHandler):
                def do_POST(self):
                    """只处理POST请求 - 支持嵌套JSON格式"""
                    try:
                        # 检查Content-Length
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length == 0:
                            self.send_error(400, "Empty request body")
                            return
                        
                        # 限制请求大小（防止内存溢出）
                        max_size = 10 * 1024 * 1024  # 10MB
                        if content_length > max_size:
                            self.send_error(413, f"Request too large (max {max_size} bytes)")
                            return
                        
                        # 读取请求体
                        post_data = self.rfile.read(content_length)
                        
                        # 安全解码
                        try:
                            payload = post_data.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                payload = post_data.decode('gbk')
                            except:
                                self.send_error(400, "Invalid encoding")
                                return
                        
                        # 解析JSON
                        try:
                            data = json.loads(payload)
                        except json.JSONDecodeError as e:
                            self.send_error(400, f"Invalid JSON: {e}")
                            return
                        
                        # 检查是否是嵌套格式（msg字段包含JSON字符串）
                        if 'msg' in data and isinstance(data['msg'], str):
                            try:
                                # 尝试解析msg字段中的JSON字符串
                                nested_data = json.loads(data['msg'])
                                data = nested_data
                                logger.debug("Webhook检测到嵌套格式，已解析")
                            except json.JSONDecodeError:
                                # 如果msg字段不是JSON，就把它当作content
                                if 'title' not in data and 'content' not in data:
                                    data = {
                                        'title': '新消息',
                                        'content': data['msg']
                                    }
                        
                        # 验证必需字段
                        if 'title' not in data or 'content' not in data:
                            self.send_error(400, "Missing required fields: title or content")
                            return
                        
                        # 获取source（可选字段）
                        source_name = config.get('name', 'Webhook')
                        final_source = data.get('source', source_name)
                        
                        # 创建消息对象
                        message = Message(
                            id=data.get('id', str(uuid.uuid4())),
                            source=final_source,
                            title=str(data['title']),
                            content=str(data['content']),
                            timestamp=data.get('timestamp', time.time()),
                            metadata=data.get('metadata', {})
                        )
                        
                        logger.info(f"Webhook消息已解析: title={message.title}, source={message.source}")
                        
                        # 调用回调
                        if connector._callback:
                            try:
                                connector._callback(message)
                            except Exception as e:
                                logger.error(f"Webhook回调失败: {e}", exc_info=True)
                        
                        # 返回成功响应
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'ok'}).encode())
                        
                    except Exception as e:
                        logger.error(f"Webhook处理错误: {e}", exc_info=True)
                        try:
                            self.send_error(500, str(e))
                        except:
                            pass
                
                def log_message(self, format, *args):
                    """重定向日志到logger"""
                    logger.debug(f"Webhook: {format % args}")
            
            self._server = HTTPServer((host, port), WebhookHandler)
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True
            )
            self._server_thread.start()
            self._connected = True
            logger.info(f"Webhook服务器已启动: {host}:{port} (仅支持POST)")
            return True
            
        except Exception as e:
            logger.error(f"Webhook启动失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """停止Webhook服务器"""
        try:
            if self._server:
                logger.info("正在停止Webhook服务器...")
                self._server.shutdown()
                self._server.server_close()
                
                # 等待服务器线程结束
                if self._server_thread and self._server_thread.is_alive():
                    logger.info("等待Webhook服务器线程结束...")
                    self._server_thread.join(timeout=5)
                    if self._server_thread.is_alive():
                        logger.warning("Webhook服务器线程未能在5秒内停止")
                    else:
                        logger.info("Webhook服务器线程已完全停止")
                
                self._server = None
                self._server_thread = None
            
            self._connected = False
            logger.info("Webhook服务器已停止")
        except Exception as e:
            logger.error(f"停止Webhook服务器失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        self._callback = callback
    
    def is_connected(self) -> bool:
        return self._connected
