"""
WinMsgHub (WinMsgHub) - API消息源连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import json
import time
import uuid
import threading
from typing import Callable, Optional, List
import requests
from data.connectors.base import MessageConnector
from data.models import Message
from utils.logger import get_logger


logger = get_logger(__name__)


class APIConnector(MessageConnector):
    """
    API消息源连接器
    
    通过HTTP轮询方式从API端点获取消息。
    
    验证需求：
    - 1.4: 支持API消息源类型
    - 1.5: 使用HTTPS加密连接
    """
    
    def __init__(self):
        """初始化API连接器"""
        self._callback: Optional[Callable[[Message], None]] = None
        self._connected = False
        self._config: Optional[dict] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()
        
        # 消息去重：记录最近处理过的消息指纹，
        # 避免API每次轮询返回相同内容时重复弹窗
        self._seen_fingerprints: dict = {}
        self._max_fingerprint_cache = 500
        
        logger.info("API连接器已初始化")
    
    @staticmethod
    def _get_endpoints(config: dict) -> List[str]:
        """从配置中提取端点列表
        
        同时兼容两种配置格式：
        - endpoints: ["https://...", ...]（列表格式）
        - url: "https://..."（界面配置对话框保存的单URL格式）
        """
        endpoints = config.get('endpoints') or []
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        
        single_url = (config.get('url') or '').strip()
        if single_url and single_url not in endpoints:
            endpoints = list(endpoints) + [single_url]
        
        return [e for e in endpoints if isinstance(e, str) and e.strip()]
    
    def connect(self, config: dict) -> bool:
        """
        连接到API端点
        
        Args:
            config: 连接配置字典，包含以下字段：
                - endpoints (list) 或 url (str): API端点
                - method (str, 可选): 请求方法 GET/POST，默认GET
                - poll_interval (int, 可选): 轮询间隔（秒），默认60
                - headers (dict, 可选): HTTP请求头
                - timeout (int, 可选): 请求超时（秒），默认30
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        try:
            self._config = config
            endpoints = self._get_endpoints(config)
            
            if not endpoints:
                logger.error("未配置API端点（请填写url或endpoints）")
                return False
            
            # 验证端点URL
            for endpoint in endpoints:
                if not endpoint.startswith('https://'):
                    logger.warning(f"API端点未使用HTTPS: {endpoint}")
            
            self._connected = True
            self._stop_polling.clear()
            
            # 启动轮询线程
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()
            
            logger.info(f"API连接器已启动，监听 {len(endpoints)} 个端点")
            return True
            
        except Exception as e:
            logger.error(f"API连接失败: {str(e)}", exc_info=True)
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """断开API连接"""
        try:
            logger.info("正在停止API连接器...")
            self._stop_polling.set()
            
            if self._poll_thread and self._poll_thread.is_alive():
                logger.info("等待API轮询线程结束...")
                self._poll_thread.join(timeout=5)
                if self._poll_thread.is_alive():
                    logger.warning("API轮询线程未能在5秒内停止")
                else:
                    logger.info("API轮询线程已完全停止")
            
            self._connected = False
            logger.info("API连接器已断开")
        except Exception as e:
            logger.error(f"断开API连接失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息"""
        self._callback = callback
        logger.debug("已设置消息回调函数")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def _poll_loop(self):
        """轮询循环"""
        poll_interval = self._config.get('poll_interval', 60)
        
        while not self._stop_polling.is_set():
            try:
                self._poll_endpoints()
            except Exception as e:
                logger.error(f"轮询出错: {str(e)}", exc_info=True)
            
            # 等待下一次轮询
            self._stop_polling.wait(poll_interval)
    
    def _poll_endpoints(self):
        """轮询所有端点"""
        endpoints = self._get_endpoints(self._config)
        headers = self._config.get('headers', {})
        timeout = self._config.get('timeout', 30)
        method = str(self._config.get('method', 'GET')).upper()
        
        for endpoint in endpoints:
            # 每个端点处理前都检查停止标志，保证断开时快速退出
            if self._stop_polling.is_set():
                return
            
            try:
                if method == 'POST':
                    response = requests.post(endpoint, headers=headers, timeout=timeout)
                else:
                    response = requests.get(endpoint, headers=headers, timeout=timeout)
                response.raise_for_status()
                
                # 解析响应
                data = response.json()
                messages = self._parse_response(data, endpoint)
                
                # 调用回调函数（跳过重复消息）
                if self._callback:
                    for message in messages:
                        if self._is_duplicate(message):
                            logger.debug(f"API消息与上次轮询重复，已跳过: {message.title}")
                            continue
                        try:
                            self._callback(message)
                        except Exception as e:
                            logger.error(f"消息回调函数执行失败: {str(e)}", exc_info=True)
                            
            except Exception as e:
                logger.error(f"轮询端点 {endpoint} 失败: {str(e)}")
    
    def _is_duplicate(self, message: Message) -> bool:
        """检查消息是否与最近轮询到的消息重复
        
        API轮询大概率反复返回相同内容，用内容指纹去重，
        否则每个轮询周期都会为同一条消息弹窗。
        """
        import hashlib
        fingerprint = hashlib.md5(
            f"{message.source}|{message.title}|{message.content}".encode('utf-8', errors='ignore')
        ).hexdigest()
        
        if fingerprint in self._seen_fingerprints:
            return True
        
        self._seen_fingerprints[fingerprint] = True
        # 限制缓存大小（dict保持插入顺序，删除最旧的一半）
        if len(self._seen_fingerprints) > self._max_fingerprint_cache:
            keys = list(self._seen_fingerprints.keys())
            self._seen_fingerprints = {k: True for k in keys[-self._max_fingerprint_cache // 2:]}
        
        return False
    
    def _parse_response(self, data: dict, endpoint: str) -> List[Message]:
        """解析API响应 - 支持嵌套JSON格式"""
        messages = []
        
        try:
            # 支持三种格式：
            # 1. 单个消息：{"title": "标题", "content": "内容", "source": "来源"}
            # 2. 消息数组：{"messages": [{...}, {...}]}
            # 3. 嵌套格式：{"msg": "{\"title\": \"标题\", ...}"}
            
            source_name = self._config.get('name', 'API')
            
            if isinstance(data, dict):
                # 检查是否是嵌套格式
                if 'msg' in data and isinstance(data['msg'], str):
                    try:
                        nested_data = json.loads(data['msg'])
                        # 只有解析结果是字典才采用，避免字符串/数组破坏后续处理
                        if isinstance(nested_data, dict):
                            data = nested_data
                            logger.debug("API检测到嵌套格式，已解析")
                        else:
                            data = {'title': '新消息', 'content': str(nested_data)}
                    except json.JSONDecodeError:
                        if 'title' not in data and 'content' not in data:
                            data = {
                                'title': '新消息',
                                'content': data['msg']
                            }
                
                if 'messages' in data and isinstance(data['messages'], list):
                    # 格式2：消息数组
                    for item in data['messages']:
                        if not isinstance(item, dict):
                            continue
                        
                        # 检查嵌套格式
                        if 'msg' in item and isinstance(item['msg'], str):
                            try:
                                nested_item = json.loads(item['msg'])
                                if isinstance(nested_item, dict):
                                    item = nested_item
                            except json.JSONDecodeError:
                                pass
                        
                        # 验证必需字段
                        if 'title' not in item or 'content' not in item:
                            logger.warning("API消息缺少必需字段，跳过")
                            continue
                        
                        final_source = item.get('source', source_name)
                        message = Message(
                            id=item.get('id', str(uuid.uuid4())),
                            source=final_source,
                            title=str(item['title']),
                            content=str(item['content']),
                            timestamp=item.get('timestamp', time.time()),
                            metadata={'endpoint': endpoint, **item.get('metadata', {})}
                        )
                        messages.append(message)
                        
                elif 'title' in data and 'content' in data:
                    # 格式1：单个消息
                    final_source = data.get('source', source_name)
                    message = Message(
                        id=data.get('id', str(uuid.uuid4())),
                        source=final_source,
                        title=str(data['title']),
                        content=str(data['content']),
                        timestamp=data.get('timestamp', time.time()),
                        metadata={'endpoint': endpoint}
                    )
                    messages.append(message)
                else:
                    logger.error("API响应格式不正确，缺少必需字段")
            
            if messages:
                logger.info(f"API解析了 {len(messages)} 条消息")
            
        except Exception as e:
            logger.error(f"解析API响应失败: {e}", exc_info=True)
        
        return messages
