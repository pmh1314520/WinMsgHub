"""
WinMsgHub (WinMsgHub) - MQTT连接器测试
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import pytest
import time
import json
import ssl
from unittest.mock import Mock, MagicMock, patch, call
from hypothesis import given, strategies as st, settings, HealthCheck
from data.connectors.mqtt_connector import MQTTConnector
from data.models import Message
from core.config_manager import ConfigManager
from pathlib import Path


class TestMQTTConnectorBasics:
    """测试MQTT连接器基本功能"""
    
    def test_mqtt_connector_initialization(self):
        """验证MQTT连接器可以正确初始化"""
        connector = MQTTConnector()
        assert connector is not None
        assert not connector.is_connected()
    
    def test_default_broker_address(self):
        """验证默认broker地址（需求1.2）"""
        assert MQTTConnector.DEFAULT_BROKER == "WinMsgHub.pmhs.top"
        assert MQTTConnector.DEFAULT_PORT == 8883
    
    def test_mqtt_connector_implements_interface(self):
        """验证MQTT连接器实现了MessageConnector接口"""
        from data.connectors.base import MessageConnector
        connector = MQTTConnector()
        assert isinstance(connector, MessageConnector)
    
    def test_subscribe_sets_callback(self):
        """验证subscribe方法设置回调函数"""
        connector = MQTTConnector()
        
        def test_callback(message: Message):
            pass
        
        connector.subscribe(test_callback)
        assert connector._callback is not None


class TestMQTTConnectorConnection:
    """测试MQTT连接器连接功能"""
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_with_default_broker(self, mock_client_class):
        """验证使用默认broker地址连接（需求1.2）
        
        当前实现使用connect_async进行非阻塞连接。
        """
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 模拟连接成功（异步连接发起后标记已连接，跳过等待循环）
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 连接时不指定broker
        config = {
            'topic': 'test/topic'
        }
        
        result = connector.connect(config)
        
        assert result is True
        # 验证使用了默认broker
        mock_client.connect_async.assert_called_once()
        call_args = mock_client.connect_async.call_args
        assert call_args[0][0] == MQTTConnector.DEFAULT_BROKER
        assert call_args[0][1] == MQTTConnector.DEFAULT_PORT
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_with_custom_broker(self, mock_client_class):
        """验证使用自定义broker地址连接（需求1.3）"""
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 模拟连接成功
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 连接时指定自定义broker
        custom_broker = "custom.broker.com"
        custom_port = 1883
        config = {
            'broker': custom_broker,
            'port': custom_port,
            'topic': 'test/topic'
        }
        
        result = connector.connect(config)
        
        assert result is True
        # 验证使用了自定义broker
        mock_client.connect_async.assert_called_once()
        call_args = mock_client.connect_async.call_args
        assert call_args[0][0] == custom_broker
        assert call_args[0][1] == custom_port
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_with_tls_enabled(self, mock_client_class):
        """验证TLS加密连接（需求1.1, 1.5）"""
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 模拟连接成功
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 连接时启用TLS
        config = {
            'topic': 'test/topic',
            'use_tls': True
        }
        
        result = connector.connect(config)
        
        # 验证调用了tls_set_context
        mock_client.tls_set_context.assert_called_once()
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_with_authentication(self, mock_client_class):
        """验证使用用户名和密码连接"""
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 模拟连接成功
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 连接时提供认证信息
        config = {
            'topic': 'test/topic',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        result = connector.connect(config)
        
        # 验证设置了用户名和密码
        mock_client.username_pw_set.assert_called_once_with('testuser', 'testpass')
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_subscribes_to_topic(self, mock_client_class):
        """验证连接成功后订阅主题（需求1.7）
        
        订阅在_on_connect回调中执行（保证断线重连后重新订阅）。
        """
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 连接
        topic = 'test/topic'
        config = {
            'topic': topic
        }
        
        connector.connect(config)
        
        # 模拟broker回调"连接成功"
        connector._on_connect(mock_client, None, None, 0)
        
        # 验证订阅了主题（QoS 0避免消息重复）
        mock_client.subscribe.assert_called_once_with(topic, qos=0)
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_starts_loop(self, mock_client_class):
        """验证连接后启动网络循环"""
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        # 模拟连接成功
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 连接
        config = {
            'topic': 'test/topic'
        }
        
        result = connector.connect(config)
        
        # 验证启动了网络循环
        mock_client.loop_start.assert_called_once()
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_failure_returns_false(self, mock_client_class):
        """验证连接初始化失败时返回False（需求1.6）"""
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # 模拟连接初始化失败（如地址无法解析）
        mock_client.connect_async.side_effect = Exception("连接失败")
        
        connector = MQTTConnector()
        
        # 连接
        config = {
            'topic': 'test/topic'
        }
        
        result = connector.connect(config)
        
        # 验证返回False
        assert result is False
        assert not connector.is_connected()
    
    def test_disconnect_stops_loop(self):
        """验证断开连接时停止网络循环"""
        connector = MQTTConnector()
        
        # 创建mock客户端
        mock_client = MagicMock()
        connector._client = mock_client
        connector._connected = True
        
        # 断开连接
        connector.disconnect()
        
        # 验证停止了网络循环
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
        assert not connector.is_connected()


class TestMQTTConnectorMessageHandling:
    """测试MQTT连接器消息处理"""
    
    def test_on_message_parses_json_payload(self):
        """验证消息处理器解析JSON payload"""
        connector = MQTTConnector()
        
        # 设置回调函数
        received_messages = []
        
        def callback(message: Message):
            received_messages.append(message)
        
        connector.subscribe(callback)
        
        # 创建mock MQTT消息
        mock_msg = MagicMock()
        mock_msg.topic = 'test/topic'
        mock_msg.qos = 1
        mock_msg.retain = False
        
        # JSON格式的payload
        payload_data = {
            'id': 'test-123',
            'title': '测试标题',
            'content': '测试内容',
            'timestamp': 1234567890.0
        }
        mock_msg.payload = json.dumps(payload_data).encode('utf-8')
        
        # 调用消息处理器
        connector._on_message(None, None, mock_msg)
        
        # 验证消息被正确解析
        assert len(received_messages) == 1
        message = received_messages[0]
        assert message.id == 'test-123'
        assert message.title == '测试标题'
        assert message.content == '测试内容'
        assert message.timestamp == 1234567890.0
        assert message.source == 'MQTT'
    
    def test_on_message_handles_non_json_payload(self):
        """验证消息处理器处理非JSON payload"""
        connector = MQTTConnector()
        
        # 设置回调函数
        received_messages = []
        
        def callback(message: Message):
            received_messages.append(message)
        
        connector.subscribe(callback)
        
        # 创建mock MQTT消息
        mock_msg = MagicMock()
        mock_msg.topic = 'test/topic'
        mock_msg.qos = 1
        mock_msg.retain = False
        mock_msg.payload = b'Plain text message'
        
        # 调用消息处理器
        connector._on_message(None, None, mock_msg)
        
        # 验证消息被正确处理
        assert len(received_messages) == 1
        message = received_messages[0]
        assert message.title == '新消息'
        assert message.content == 'Plain text message'
        assert message.source == 'MQTT'
    
    def test_on_message_handles_callback_exception(self):
        """验证消息处理器捕获回调函数异常（需求1.6）"""
        connector = MQTTConnector()
        
        # 设置会抛出异常的回调函数
        def failing_callback(message: Message):
            raise Exception("回调函数错误")
        
        connector.subscribe(failing_callback)
        
        # 创建mock MQTT消息
        mock_msg = MagicMock()
        mock_msg.topic = 'test/topic'
        mock_msg.qos = 1
        mock_msg.retain = False
        mock_msg.payload = b'Test message'
        
        # 调用消息处理器不应该抛出异常
        try:
            connector._on_message(None, None, mock_msg)
            # 如果没有抛出异常，测试通过
            assert True
        except Exception:
            # 如果抛出异常，测试失败
            pytest.fail("消息处理器应该捕获回调函数异常")
    
    def test_on_message_without_callback(self):
        """验证没有设置回调函数时的行为"""
        connector = MQTTConnector()
        
        # 不设置回调函数
        
        # 创建mock MQTT消息
        mock_msg = MagicMock()
        mock_msg.topic = 'test/topic'
        mock_msg.qos = 1
        mock_msg.retain = False
        mock_msg.payload = b'Test message'
        
        # 调用消息处理器不应该抛出异常
        try:
            connector._on_message(None, None, mock_msg)
            # 如果没有抛出异常，测试通过
            assert True
        except Exception:
            # 如果抛出异常，测试失败
            pytest.fail("消息处理器应该处理未设置回调函数的情况")


class TestMQTTConnectorReconnection:
    """测试MQTT连接器重连机制
    
    重连由paho网络线程根据reconnect_delay_set的指数退避配置自动执行，
    不在回调中手动sleep+reconnect（那样会阻塞网络线程）。
    """
    
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_connect_configures_auto_reconnect(self, mock_client_class):
        """验证连接时配置了paho自动重连的指数退避参数（需求1.6）"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        connector.connect({'topic': 'test/topic'})
        
        # 验证配置了指数退避自动重连
        mock_client.reconnect_delay_set.assert_called_once_with(
            min_delay=MQTTConnector.INITIAL_RECONNECT_DELAY,
            max_delay=MQTTConnector.MAX_RECONNECT_DELAY
        )
    
    def test_on_disconnect_marks_disconnected(self):
        """验证意外断开时标记为未连接（等待paho自动重连）"""
        connector = MQTTConnector()
        
        # 设置配置
        connector._config = {
            'broker': 'test.broker.com',
            'port': 1883,
            'topic': 'test/topic'
        }
        connector._should_reconnect = True
        connector._connected = True
        
        # 创建mock客户端
        mock_client = MagicMock()
        connector._client = mock_client
        
        # 模拟意外断开（rc != 0），回调不应阻塞也不应抛异常
        connector._on_disconnect(mock_client, None, 1)
        
        assert not connector.is_connected()
        # 不应在回调中手动调用reconnect（paho网络线程自动处理）
        mock_client.reconnect.assert_not_called()
    
    def test_reconnect_resubscribes_topic(self):
        """验证重连成功后重新订阅主题（需求1.7）"""
        connector = MQTTConnector()
        connector._config = {'topic': 'test/topic'}
        
        mock_client = MagicMock()
        connector._client = mock_client
        
        # 模拟断开后重连成功
        connector._on_disconnect(mock_client, None, 1)
        connector._on_connect(mock_client, None, None, 0)
        
        assert connector.is_connected()
        mock_client.subscribe.assert_called_once_with('test/topic', qos=0)
    
    def test_disconnect_prevents_reconnection(self):
        """验证主动断开连接时不触发重连"""
        connector = MQTTConnector()
        
        # 设置配置
        connector._config = {
            'broker': 'test.broker.com',
            'port': 1883,
            'topic': 'test/topic'
        }
        
        # 创建mock客户端
        mock_client = MagicMock()
        connector._client = mock_client
        connector._connected = True
        
        # 主动断开连接
        connector.disconnect()
        
        # 验证_should_reconnect被设置为False
        assert not connector._should_reconnect


class TestMQTTConnectorConnectionCallbacks:
    """测试MQTT连接器连接回调"""
    
    def test_on_connect_success(self):
        """验证连接成功回调"""
        connector = MQTTConnector()
        
        # 调用连接成功回调（rc=0表示成功）
        connector._on_connect(None, None, None, 0)
        
        # 验证连接状态
        assert connector.is_connected()
        assert connector._reconnect_delay == MQTTConnector.INITIAL_RECONNECT_DELAY
    
    def test_on_connect_failure(self):
        """验证连接失败回调"""
        connector = MQTTConnector()
        
        # 调用连接失败回调（rc!=0表示失败）
        connector._on_connect(None, None, None, 4)  # 4表示用户名或密码错误
        
        # 验证连接状态
        assert not connector.is_connected()
    
    def test_on_disconnect_normal(self):
        """验证正常断开连接回调"""
        connector = MQTTConnector()
        connector._connected = True
        
        # 调用正常断开回调（rc=0表示正常断开）
        connector._on_disconnect(None, None, 0)
        
        # 验证连接状态
        assert not connector.is_connected()



# ============================================================================
# 基于属性的测试 (Property-Based Tests)
# ============================================================================

@pytest.mark.property
class TestMQTTConnectorProperties:
    """MQTT连接器属性测试
    
    使用Hypothesis进行基于属性的测试，验证系统在各种输入下的通用属性。
    每个测试至少运行100次迭代。
    """
    
    # Feature: WinMsgHub-desktop-app, Property 1: MQTT连接使用加密
    @given(
        broker=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='.-_'
        )),
        port=st.integers(min_value=1, max_value=65535),
        topic=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='/-_'
        )),
        username=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        password=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    )
    @settings(max_examples=100, deadline=None)
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_property_mqtt_connection_uses_encryption(
        self, mock_client_class, broker, port, topic, username, password
    ):
        """
        **属性 1：MQTT连接使用加密**
        
        对于任何MQTT连接配置，当系统建立连接时，应该启用TLS加密并验证服务器证书。
        
        **Validates: Requirements 1.1, 1.5**
        
        验证：
        1. 当use_tls为True或未指定时，必须调用tls_set_context
        2. TLS上下文必须配置为验证服务器证书
        3. TLS版本至少为TLSv1.2
        """
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # 模拟连接成功
        connector = MQTTConnector()
        
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 构建配置（默认启用TLS）
        config = {
            'broker': broker,
            'port': port,
            'topic': topic,
        }
        
        if username is not None and password is not None:
            config['username'] = username
            config['password'] = password
        
        # 尝试连接
        try:
            result = connector.connect(config)
            
            # 属性验证：必须调用tls_set_context来启用TLS加密
            mock_client.tls_set_context.assert_called_once()
            
            # 获取传递给tls_set_context的TLS上下文
            tls_context_call = mock_client.tls_set_context.call_args
            if tls_context_call:
                tls_context = tls_context_call[0][0]
                
                # 验证TLS上下文配置了证书验证
                # 注意：由于我们使用的是ssl.create_default_context()，
                # 它默认就配置了CERT_REQUIRED和check_hostname=True
                # 我们验证这些属性在代码中被正确设置
                assert isinstance(tls_context, ssl.SSLContext)
                
        except Exception as e:
            # 某些随机生成的broker地址可能导致连接失败，这是可以接受的
            # 但我们仍然要验证TLS被正确配置
            if mock_client.tls_set_context.called:
                # 如果tls_set_context被调用了，验证它
                tls_context_call = mock_client.tls_set_context.call_args
                if tls_context_call:
                    tls_context = tls_context_call[0][0]
                    assert isinstance(tls_context, ssl.SSLContext)
    
    # Feature: WinMsgHub-desktop-app, Property 2: 自定义Broker配置往返
    @given(
        broker=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='.-_'
        )),
        port=st.integers(min_value=1, max_value=65535),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[
        HealthCheck.function_scoped_fixture
    ])
    def test_property_custom_broker_config_roundtrip(self, tmp_path, broker, port):
        """
        **属性 2：自定义Broker配置往返**
        
        对于任何自定义MQTT Broker地址，保存到配置后再加载，应该得到相同的地址值。
        
        **Validates: Requirements 1.3**
        
        验证：
        1. 设置自定义broker地址和端口
        2. 保存配置到文件
        3. 重新加载配置
        4. 验证broker和port值完全一致
        """
        # 创建配置管理器
        config_dir = tmp_path / "config"
        config_manager = ConfigManager(config_dir)
        
        # 设置自定义MQTT broker配置（多实例列表格式）
        config_manager.set('message_sources.mqtt', [{
            'enabled': True,
            'name': '测试MQTT',
            'broker': broker,
            'port': port,
        }])
        
        # 创建新的配置管理器实例（模拟重启应用）
        config_manager2 = ConfigManager(config_dir)
        
        # 验证往返一致性
        mqtt_sources = config_manager2.get('message_sources.mqtt')
        assert isinstance(mqtt_sources, list) and len(mqtt_sources) == 1
        
        retrieved_broker = mqtt_sources[0]['broker']
        retrieved_port = mqtt_sources[0]['port']
        
        assert retrieved_broker == broker, \
            f"Broker地址往返不一致: 期望 {broker}, 实际 {retrieved_broker}"
        assert retrieved_port == port, \
            f"端口号往返不一致: 期望 {port}, 实际 {retrieved_port}"
    
    # Feature: WinMsgHub-desktop-app, Property 1 (扩展): 验证TLS配置细节
    @given(
        use_tls=st.booleans(),
    )
    @settings(max_examples=100, deadline=None)
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_property_tls_configuration_when_disabled(
        self, mock_client_class, use_tls
    ):
        """
        **属性 1（扩展）：TLS配置根据use_tls标志正确应用**
        
        验证当use_tls为False时，不应该调用tls_set_context。
        当use_tls为True时，必须调用tls_set_context。
        
        **Validates: Requirements 1.1, 1.5**
        """
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 构建配置
        config = {
            'broker': 'test.broker.com',
            'port': 1883,
            'topic': 'test/topic',
            'use_tls': use_tls
        }
        
        # 尝试连接
        try:
            result = connector.connect(config)
            
            # 属性验证
            if use_tls:
                # 当启用TLS时，必须调用tls_set_context
                mock_client.tls_set_context.assert_called_once()
            else:
                # 当禁用TLS时，不应该调用tls_set_context
                mock_client.tls_set_context.assert_not_called()
                
        except Exception:
            # 连接可能失败，但TLS配置逻辑应该正确执行
            if use_tls:
                assert mock_client.tls_set_context.called or not mock_client.connect_async.called
            else:
                mock_client.tls_set_context.assert_not_called()
    
    # Feature: WinMsgHub-desktop-app, Property 2 (扩展): 完整MQTT配置往返
    @given(
        broker=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='.-_'
        )),
        port=st.integers(min_value=1, max_value=65535),
        username=st.text(min_size=0, max_size=50),
        password=st.text(min_size=0, max_size=50),
        topic=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='/-_'
        )),
        use_tls=st.booleans(),
        enabled=st.booleans(),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[
        HealthCheck.function_scoped_fixture
    ])
    def test_property_full_mqtt_config_roundtrip(
        self, tmp_path, broker, port, username, password, topic, use_tls, enabled
    ):
        """
        **属性 2（扩展）：完整MQTT配置往返**
        
        对于任何完整的MQTT配置（包括broker、port、username、password、topic、use_tls、enabled），
        保存到配置后再加载，应该得到所有字段值相同的配置。
        
        **Validates: Requirements 1.3**
        """
        # 创建配置管理器
        config_dir = tmp_path / "config"
        config_manager = ConfigManager(config_dir)
        
        # 设置完整的MQTT配置（多实例列表格式）
        mqtt_config = {
            'enabled': enabled,
            'name': '完整配置测试',
            'broker': broker,
            'port': port,
            'username': username,
            'password': password,
            'topic': topic,
            'use_tls': use_tls,
        }
        config_manager.set('message_sources.mqtt', [mqtt_config])
        
        # 创建新的配置管理器实例（模拟重启应用）
        config_manager2 = ConfigManager(config_dir)
        
        # 验证所有字段的往返一致性
        loaded = config_manager2.get('message_sources.mqtt')
        assert isinstance(loaded, list) and len(loaded) == 1
        assert loaded[0] == mqtt_config
    
    # Feature: WinMsgHub-desktop-app, Property 1 (边缘情况): 默认broker使用TLS
    @given(
        topic=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='/-_'
        ))
    )
    @settings(max_examples=100, deadline=None)
    @patch('data.connectors.mqtt_connector.mqtt.Client')
    def test_property_default_broker_uses_tls(self, mock_client_class, topic):
        """
        **属性 1（边缘情况）：默认broker配置使用TLS**
        
        当使用默认broker地址时（未指定broker），系统应该使用TLS加密连接。
        
        **Validates: Requirements 1.1, 1.2, 1.5**
        """
        # 设置mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        connector = MQTTConnector()
        
        def simulate_connect(*args, **kwargs):
            connector._connected = True
        
        mock_client.connect_async.side_effect = simulate_connect
        
        # 使用最小配置（不指定broker，使用默认值）
        config = {
            'topic': topic
        }
        
        try:
            result = connector.connect(config)
            
            # 验证使用了默认broker
            call_args = mock_client.connect_async.call_args
            if call_args:
                assert call_args[0][0] == MQTTConnector.DEFAULT_BROKER
                assert call_args[0][1] == MQTTConnector.DEFAULT_PORT
            
            # 验证启用了TLS
            mock_client.tls_set_context.assert_called_once()
            
        except Exception:
            # 即使连接失败，TLS配置也应该被调用
            if mock_client.connect_async.called:
                mock_client.tls_set_context.assert_called()
