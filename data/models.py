"""
WinMsgHub (WinMsgHub) - 消息数据模型
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import json
import time


def normalize_timestamp(value: Any, default: float = None) -> float:
    """将任意来源的时间戳归一化为Unix秒级时间戳

    外部消息源（如SmsForwarder）可能发送毫秒/微秒级时间戳或字符串，
    如果不归一化，datetime.fromtimestamp会抛出异常导致弹窗无法显示。

    Args:
        value: 原始时间戳（秒/毫秒/微秒，int/float/str均可）
        default: 无法解析时使用的默认值，None表示当前时间

    Returns:
        Unix秒级时间戳（float）
    """
    if default is None:
        default = time.time()

    try:
        ts = float(value)
    except (TypeError, ValueError):
        return default

    if ts <= 0:
        return default

    # 依次处理微秒(>=1e15)、毫秒(>=1e12)级时间戳
    while ts >= 1e12:
        ts /= 1000.0

    return ts


@dataclass
class Message:
    """
    消息数据结构
    
    Attributes:
        id: 消息唯一标识符
        source: 消息来源（MQTT、API、Webhook、IMAP等）
        title: 消息标题
        content: 消息内容
        timestamp: 消息时间戳（Unix时间戳，秒）
        metadata: 消息元数据（额外信息）
    """
    id: str
    source: str
    title: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """归一化字段，保证所有消息源创建的消息都是合法的"""
        # 时间戳统一为秒级，防止毫秒级时间戳导致fromtimestamp崩溃
        self.timestamp = normalize_timestamp(self.timestamp)
        # metadata必须是字典
        if not isinstance(self.metadata, dict):
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将消息对象转换为字典
        
        Returns:
            包含所有消息字段的字典
        """
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'content': self.content,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        从字典创建消息对象
        
        Args:
            data: 包含消息字段的字典
            
        Returns:
            Message对象
        """
        return cls(
            id=data['id'],
            source=data['source'],
            title=data['title'],
            content=data['content'],
            timestamp=data['timestamp'],
            metadata=data.get('metadata', {})
        )
    
    def metadata_to_json(self) -> str:
        """
        将metadata转换为JSON字符串
        
        Returns:
            JSON格式的metadata字符串
        """
        return json.dumps(self.metadata, ensure_ascii=False)
    
    @staticmethod
    def metadata_from_json(json_str: str) -> Dict[str, Any]:
        """
        从JSON字符串解析metadata
        
        Args:
            json_str: JSON格式的字符串
            
        Returns:
            解析后的字典
        """
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}
