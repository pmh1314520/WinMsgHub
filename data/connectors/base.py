"""
WinMsgHub (WinMsgHub) - 消息源连接器基类
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from data.models import Message


class MessageConnector(ABC):
    """
    消息源连接器抽象基类
    
    所有消息源连接器（MQTT、API、Webhook、IMAP）都必须实现此接口。
    该基类定义了统一的连接管理和消息订阅接口。
    
    验证需求：1.1 - 支持多种消息源类型的连接管理
    """
    
    @abstractmethod
    def connect(self, config: dict) -> bool:
        """
        建立与消息源的连接
        
        Args:
            config: 连接配置字典，具体内容由子类定义
                   例如MQTT可能包含：broker、port、username、password、topic、use_tls等
        
        Returns:
            bool: 连接成功返回True，失败返回False
            
        Raises:
            可能抛出连接相关的异常，由子类具体实现决定
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        断开与消息源的连接
        
        该方法应该清理所有连接资源，包括关闭网络连接、停止监听线程等。
        调用此方法后，连接器应该处于完全断开状态。
        """
        pass
    
    @abstractmethod
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """
        订阅消息，通过回调函数接收新消息
        
        当消息源接收到新消息时，应该调用此回调函数传递Message对象。
        回调函数在消息处理器中定义，负责后续的过滤、存储和显示逻辑。
        
        Args:
            callback: 消息接收回调函数，接收一个Message对象作为参数
                     回调函数签名：def on_message(message: Message) -> None
        
        Note:
            - 回调函数应该在单独的线程中调用，避免阻塞连接器的接收循环
            - 如果回调函数抛出异常，连接器应该捕获并记录，但不应该中断消息接收
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 如果当前已连接到消息源返回True，否则返回False
        """
        pass
