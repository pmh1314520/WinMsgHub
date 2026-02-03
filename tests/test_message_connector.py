"""
WinMsgHub (WinMsgHub) - 消息源连接器基类测试
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import pytest
from abc import ABC
from data.connectors.base import MessageConnector
from data.models import Message


class TestMessageConnectorInterface:
    """测试MessageConnector抽象基类接口定义"""
    
    def test_message_connector_is_abstract(self):
        """验证MessageConnector是抽象基类"""
        assert issubclass(MessageConnector, ABC)
        
        # 尝试直接实例化应该失败
        with pytest.raises(TypeError):
            MessageConnector()
    
    def test_message_connector_has_required_methods(self):
        """验证MessageConnector定义了所有必需的抽象方法"""
        required_methods = ['connect', 'disconnect', 'subscribe', 'is_connected']
        
        for method_name in required_methods:
            assert hasattr(MessageConnector, method_name), \
                f"MessageConnector应该定义{method_name}方法"
            
            method = getattr(MessageConnector, method_name)
            assert callable(method), f"{method_name}应该是可调用的方法"
    
    def test_concrete_implementation_must_implement_all_methods(self):
        """验证具体实现必须实现所有抽象方法"""
        
        # 创建一个不完整的实现（缺少某些方法）
        class IncompleteConnector(MessageConnector):
            def connect(self, config: dict) -> bool:
                return True
            
            def disconnect(self) -> None:
                pass
            
            # 故意不实现subscribe和is_connected
        
        # 尝试实例化不完整的实现应该失败
        with pytest.raises(TypeError):
            IncompleteConnector()
    
    def test_complete_implementation_can_be_instantiated(self):
        """验证完整实现所有方法的子类可以被实例化"""
        
        class CompleteConnector(MessageConnector):
            def __init__(self):
                self._connected = False
                self._callback = None
            
            def connect(self, config: dict) -> bool:
                self._connected = True
                return True
            
            def disconnect(self) -> None:
                self._connected = False
            
            def subscribe(self, callback) -> None:
                self._callback = callback
            
            def is_connected(self) -> bool:
                return self._connected
        
        # 应该能够成功实例化
        connector = CompleteConnector()
        assert connector is not None
        assert isinstance(connector, MessageConnector)
        
        # 验证基本功能
        assert not connector.is_connected()
        assert connector.connect({})
        assert connector.is_connected()
        connector.disconnect()
        assert not connector.is_connected()
    
    def test_subscribe_accepts_callback(self):
        """验证subscribe方法接受回调函数"""
        
        class TestConnector(MessageConnector):
            def __init__(self):
                self._callback = None
            
            def connect(self, config: dict) -> bool:
                return True
            
            def disconnect(self) -> None:
                pass
            
            def subscribe(self, callback) -> None:
                self._callback = callback
            
            def is_connected(self) -> bool:
                return True
        
        connector = TestConnector()
        
        # 定义一个回调函数
        received_messages = []
        
        def on_message(message: Message):
            received_messages.append(message)
        
        # 订阅回调
        connector.subscribe(on_message)
        assert connector._callback is not None
        
        # 模拟接收消息
        test_message = Message(
            id="test-1",
            source="test",
            title="测试标题",
            content="测试内容",
            timestamp=1234567890.0,
            metadata={}
        )
        
        connector._callback(test_message)
        assert len(received_messages) == 1
        assert received_messages[0].id == "test-1"


class TestMessageConnectorDocumentation:
    """测试MessageConnector的文档和注释"""
    
    def test_class_has_docstring(self):
        """验证类有文档字符串"""
        assert MessageConnector.__doc__ is not None
        assert len(MessageConnector.__doc__.strip()) > 0
    
    def test_methods_have_docstrings(self):
        """验证所有方法都有文档字符串"""
        methods = ['connect', 'disconnect', 'subscribe', 'is_connected']
        
        for method_name in methods:
            method = getattr(MessageConnector, method_name)
            assert method.__doc__ is not None, \
                f"{method_name}方法应该有文档字符串"
            assert len(method.__doc__.strip()) > 0, \
                f"{method_name}方法的文档字符串不应为空"
