"""
WinMsgHub (WinMsgHub) - MQTT消息源连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import json
import time
import uuid
import ssl
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from data.connectors.base import MessageConnector
from data.models import Message
from utils.logger import get_logger


logger = get_logger(__name__)


class MQTTConnector(MessageConnector):
    """
    MQTT消息源连接器
    
    实现基于MQTT协议的消息接收功能，支持TLS加密连接、自动重连等特性。
    
    验证需求：
    - 1.1: 使用加密连接到指定的Broker地址
    - 1.2: 使用默认地址 WinMsgHub.pmhs.top/mqtt
    - 1.3: 允许用户输入并保存自定义Broker地址
    - 1.5: 使用最安全的加密算法进行数据传输
    - 1.6: 记录错误信息并通知用户
    - 1.7: 持续监听新消息
    """
    
    # 默认MQTT Broker地址（需求1.2）
    DEFAULT_BROKER = "WinMsgHub.pmhs.top"
    DEFAULT_PORT = 8883  # MQTT over TLS的标准端口
    
    # 重连配置
    MAX_RECONNECT_DELAY = 60  # 最大重连延迟（秒）
    INITIAL_RECONNECT_DELAY = 1  # 初始重连延迟（秒）
    
    def __init__(self):
        """初始化MQTT连接器"""
        self._client: Optional[mqtt.Client] = None
        self._callback: Optional[Callable[[Message], None]] = None
        self._connected = False
        self._config: Optional[dict] = None
        self._reconnect_delay = self.INITIAL_RECONNECT_DELAY
        self._should_reconnect = True
        
        logger.info("MQTT连接器已初始化")
    
    def connect(self, config: dict) -> bool:
        """
        连接到MQTT Broker
        
        Args:
            config: 连接配置字典，包含以下字段：
                - broker (str, 可选): Broker地址，默认使用DEFAULT_BROKER
                - port (int, 可选): 端口号，默认8883
                - username (str, 可选): 用户名
                - password (str, 可选): 密码
                - topic (str): 订阅的主题
                - use_tls (bool, 可选): 是否使用TLS，默认True
                - client_id (str, 可选): 客户端ID，默认自动生成
        
        Returns:
            bool: 连接成功返回True，失败返回False
            
        验证需求：1.1, 1.2, 1.3, 1.5
        """
        try:
            self._config = config
            self._should_reconnect = True
            
            # 获取配置参数（需求1.2：使用默认broker地址）
            broker = config.get('broker', self.DEFAULT_BROKER)
            port = config.get('port', self.DEFAULT_PORT)
            username = config.get('username')
            password = config.get('password')
            topic = config.get('topic', 'WinMsgHub/notifications')
            use_tls = config.get('use_tls', True)
            client_id = config.get('client_id', f'WinMsgHub-{uuid.uuid4().hex[:8]}')
            
            # 检测是否为本地连接
            is_local = broker in ['localhost', '127.0.0.1'] or broker.startswith('192.168.')
            if is_local and use_tls:
                logger.warning(f"检测到本地Broker地址 ({broker})，建议关闭TLS加密以提高兼容性")
            
            logger.info(f"正在连接到MQTT Broker: {broker}:{port}, 主题: {topic}")
            
            # 创建MQTT客户端
            self._client = mqtt.Client(client_id=client_id)
            
            # 设置用户名和密码（如果提供）
            if username and password:
                self._client.username_pw_set(username, password)
                logger.debug("已设置MQTT认证信息")
            
            # 配置TLS加密连接（需求1.1, 1.5：使用加密连接和最安全的加密算法）
            if use_tls:
                tls_context = ssl.create_default_context()
                # 使用最安全的TLS版本
                tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
                # 验证服务器证书
                tls_context.check_hostname = True
                tls_context.verify_mode = ssl.CERT_REQUIRED
                
                self._client.tls_set_context(tls_context)
                logger.info("已启用TLS加密连接")
            else:
                # 本地连接不使用TLS
                logger.info("使用非加密连接（适用于本地Broker）")
            
            # 设置回调函数
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            # 使用connect_async进行非阻塞连接，避免UI卡死
            try:
                self._client.connect_async(broker, port, keepalive=60)
            except Exception as conn_err:
                logger.error(f"MQTT连接初始化失败: {conn_err}")
                return False
            
            # 启动网络循环（在后台线程中运行）
            self._client.loop_start()
            
            # 等待连接建立（最多等待3秒，避免长时间阻塞）
            timeout = 3
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self._connected:
                # 订阅主题（需求1.7：持续监听新消息）
                self._client.subscribe(topic)
                logger.info(f"已订阅主题: {topic}")
                return True
            else:
                logger.warning(f"MQTT连接超时（{timeout}秒），将在后台继续尝试连接")
                # 即使超时也返回True，让连接在后台继续尝试
                # 这样不会阻塞UI
                return True
                
        except Exception as e:
            # 需求1.6：记录错误信息
            logger.error(f"MQTT连接失败: {str(e)}", exc_info=True)
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """
        断开MQTT连接
        
        清理所有连接资源，停止网络循环。
        """
        self._should_reconnect = False
        
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
                logger.info("MQTT连接已断开")
            except Exception as e:
                logger.error(f"断开MQTT连接时出错: {str(e)}")
            finally:
                self._client = None
                self._connected = False
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """
        订阅消息，通过回调函数接收新消息
        
        Args:
            callback: 消息接收回调函数，接收一个Message对象作为参数
        """
        self._callback = callback
        logger.debug("已设置消息回调函数")
    
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 如果当前已连接到MQTT Broker返回True，否则返回False
        """
        return self._connected
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        MQTT连接成功回调
        
        Args:
            client: MQTT客户端实例
            userdata: 用户数据
            flags: 连接标志
            rc: 连接结果码
        """
        if rc == 0:
            self._connected = True
            self._reconnect_delay = self.INITIAL_RECONNECT_DELAY  # 重置重连延迟
            logger.info("MQTT连接成功")
            
            # 连接成功后立即订阅主题（修复：确保每次连接成功都会订阅）
            if self._config:
                topic = self._config.get('topic', 'WinMsgHub/notifications')
                try:
                    self._client.subscribe(topic)
                    logger.info(f"已订阅主题: {topic}")
                except Exception as e:
                    logger.error(f"订阅主题失败: {e}")
        else:
            self._connected = False
            error_messages = {
                1: "协议版本不正确",
                2: "客户端ID无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            error_msg = error_messages.get(rc, f"未知错误 (代码: {rc})")
            logger.error(f"MQTT连接失败: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        MQTT断开连接回调
        
        实现自动重连机制（需求1.6：错误处理和重连机制）
        
        Args:
            client: MQTT客户端实例
            userdata: 用户数据
            rc: 断开连接结果码
        """
        self._connected = False
        
        if rc != 0:
            logger.warning(f"MQTT连接意外断开 (代码: {rc})")
            
            # 实现指数退避重连机制
            if self._should_reconnect and self._config:
                logger.info(f"将在 {self._reconnect_delay} 秒后尝试重连...")
                time.sleep(self._reconnect_delay)
                
                # 增加重连延迟（指数退避）
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self.MAX_RECONNECT_DELAY
                )
                
                # 尝试重连
                try:
                    broker = self._config.get('broker', self.DEFAULT_BROKER)
                    port = self._config.get('port', self.DEFAULT_PORT)
                    client.reconnect()
                    logger.info(f"正在重连到 {broker}:{port}...")
                except Exception as e:
                    logger.error(f"重连失败: {str(e)}")
        else:
            logger.info("MQTT连接正常断开")
    
    def _on_message(self, client, userdata, msg):
        """
        MQTT消息接收回调
        
        解析接收到的MQTT消息并转换为Message对象，然后调用用户回调函数。
        使用防御性编程，确保任何格式的消息都不会导致崩溃。
        
        Args:
            client: MQTT客户端实例
            userdata: 用户数据
            msg: MQTT消息对象
        """
        try:
            # 导入错误处理工具
            from data.connectors.error_handler import (
                safe_json_parse, 
                validate_message_data, 
                safe_callback_invoke
            )
            
            print("\n" + "="*80)
            print("🔔 收到MQTT消息")
            print("="*80)
            
            # 安全解码payload
            try:
                payload = msg.payload.decode('utf-8')
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                try:
                    payload = msg.payload.decode('gbk')
                except:
                    payload = str(msg.payload)
                    logger.warning("消息解码失败，使用原始字节表示")
            
            print(f"📥 原始payload: {payload}")
            print(f"📍 主题: {msg.topic}")
            print(f"🔢 QoS: {msg.qos}")
            
            logger.debug(f"收到MQTT消息: {payload[:200]}...")  # 只记录前200字符
            
            # 安全解析JSON
            data = safe_json_parse(payload, default={
                'title': '新消息',
                'content': payload
            })
            
            print(f"\n📋 解析后的数据:")
            print(f"  - title: {data.get('title')}")
            print(f"  - content: {data.get('content')}")
            print(f"  - 其他字段: {list(data.keys())}")
            
            logger.debug(f"解析后的数据: title={data.get('title')}, content={data.get('content')[:50] if data.get('content') else 'None'}...")
            
            # 验证和清理消息数据
            source_name = self._config.get('name', 'MQTT')
            cleaned_data = validate_message_data(data, source_name)
            
            print(f"\n✅ 清理后的数据:")
            print(f"  - id: {cleaned_data.get('id')}")
            print(f"  - source: {cleaned_data.get('source')}")
            print(f"  - title: {cleaned_data.get('title')}")
            print(f"  - content: {cleaned_data.get('content')}")
            print(f"  - timestamp: {cleaned_data.get('timestamp')}")
            
            logger.debug(f"清理后的数据: title={cleaned_data.get('title')}, content={cleaned_data.get('content')[:50] if cleaned_data.get('content') else 'None'}...")
            
            # 创建Message对象
            # 如果解析出来的数据中有自定义source，优先使用它（支持3参数格式）
            final_source = data.get('source', source_name)
            
            message = Message(
                id=cleaned_data.get('id') or str(uuid.uuid4()),
                source=final_source,  # 优先使用解析出来的source
                title=cleaned_data.get('title', 'MQTT'),
                content=cleaned_data.get('content', payload),
                timestamp=cleaned_data.get('timestamp') or time.time(),
                metadata={
                    'topic': msg.topic,
                    'qos': msg.qos,
                    'retain': msg.retain,
                    **cleaned_data.get('metadata', {})
                }
            )
            
            print(f"\n📦 创建的Message对象:")
            print(f"  - id: {message.id}")
            print(f"  - source: {message.source}")
            print(f"  - title: {message.title}")
            print(f"  - content: {message.content}")
            print(f"  - content长度: {len(message.content)}")
            print(f"  - timestamp: {message.timestamp}")
            print("="*80 + "\n")
            
            logger.info(f"创建消息对象: id={message.id}, title={message.title}, content_len={len(message.content)}")
            
            # 安全调用回调函数
            safe_callback_invoke(self._callback, message, f"MQTT-{source_name}")
                
        except Exception as e:
            # 最后的防线：捕获所有异常
            print(f"\n❌ 处理MQTT消息时出错: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"处理MQTT消息时出现严重错误: {str(e)}", exc_info=True)
