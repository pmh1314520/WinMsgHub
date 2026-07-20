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
        
        # 消息去重：记录最近处理的消息hash（最多保留100条）
        self._recent_message_hashes = []
        self._max_hash_cache = 100
        
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
            
            # 创建MQTT客户端（兼容paho-mqtt 1.x和2.x：
            # 2.x要求显式指定回调API版本，否则构造函数直接报错）
            try:
                self._client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION1,
                    client_id=client_id
                )
            except AttributeError:
                # paho-mqtt 1.x 没有 CallbackAPIVersion
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
            
            # 配置paho内置的指数退避自动重连（在网络线程中自动执行，
            # 无需在回调里手动sleep+reconnect阻塞网络循环）
            self._client.reconnect_delay_set(
                min_delay=self.INITIAL_RECONNECT_DELAY,
                max_delay=self.MAX_RECONNECT_DELAY
            )
            
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
                # 主题订阅已在_on_connect回调中完成，这里不需要重复订阅
                logger.info(f"MQTT连接成功，主题订阅将在_on_connect回调中完成")
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
                # 先清除所有回调函数，防止在断开过程中触发回调
                self._client.on_connect = None
                self._client.on_disconnect = None
                self._client.on_message = None
                
                # 停止网络循环
                self._client.loop_stop()
                
                # 断开连接
                self._client.disconnect()
                
                logger.info("MQTT连接已断开")
            except Exception as e:
                logger.error(f"断开MQTT连接时出错: {str(e)}")
            finally:
                self._client = None
                self._connected = False
                self._callback = None
    
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
                    # 使用QoS 0，避免消息重复
                    result = self._client.subscribe(topic, qos=0)
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
        
        注意：此回调运行在paho的网络线程中，绝不能在这里sleep或
        手动调用reconnect()——paho的loop_start线程会依据
        reconnect_delay_set的配置自动进行指数退避重连。
        
        Args:
            client: MQTT客户端实例
            userdata: 用户数据
            rc: 断开连接结果码
        """
        self._connected = False
        
        if rc != 0:
            if self._should_reconnect and self._config:
                broker = self._config.get('broker', self.DEFAULT_BROKER)
                port = self._config.get('port', self.DEFAULT_PORT)
                logger.warning(
                    f"MQTT连接意外断开 (代码: {rc})，"
                    f"将自动重连到 {broker}:{port}（指数退避，最大间隔{self.MAX_RECONNECT_DELAY}秒）"
                )
            else:
                logger.warning(f"MQTT连接意外断开 (代码: {rc})")
        else:
            logger.info("MQTT连接正常断开")
    
    def _on_message(self, client, userdata, msg):
        """
        MQTT消息接收回调
        
        支持两种JSON格式：
        1. 标准格式：{"title": "标题", "content": "内容", "source": "来源"}
        2. 嵌套格式：{"msg": "{\"title\": \"标题\", \"content\": \"内容\", \"source\": \"来源\"}"}
        其中source字段可选
        
        Args:
            client: MQTT客户端实例
            userdata: 用户数据
            msg: MQTT消息对象
        """
        try:
            # 消息去重：计算消息hash（只使用topic和payload，不使用timestamp）
            import hashlib
            message_hash = hashlib.md5(f"{msg.topic}:{msg.payload.decode('utf-8', errors='ignore')}".encode()).hexdigest()
            
            # 检查是否是重复消息
            if message_hash in self._recent_message_hashes:
                logger.debug(f"检测到重复MQTT消息，已跳过 (hash: {message_hash})")
                return
            
            # 添加到缓存
            self._recent_message_hashes.append(message_hash)
            # 限制缓存大小
            if len(self._recent_message_hashes) > self._max_hash_cache:
                self._recent_message_hashes.pop(0)
            
            # 安全解码payload
            try:
                payload = msg.payload.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    payload = msg.payload.decode('gbk')
                except (UnicodeDecodeError, LookupError):
                    logger.error("MQTT消息解码失败（非UTF-8/GBK编码），跳过此消息")
                    return
            
            logger.info(f"收到MQTT消息 - 主题: {msg.topic}, 长度: {len(payload)}")
            logger.debug(f"MQTT原始payload: {payload[:500]}")
            
            # 解析payload（宽容解析：JSON优先，纯文本兜底）
            data = self._parse_payload(payload)
            if data is None:
                return
            
            # 获取source（可选字段）
            source_name = (self._config or {}).get('name', 'MQTT')
            final_source = data.get('source') or source_name
            
            # 创建Message对象（timestamp由Message自动归一化为秒级）
            message = Message(
                id=str(data.get('id') or uuid.uuid4()),
                source=str(final_source),
                title=str(data['title']),
                content=str(data['content']),
                timestamp=data.get('timestamp', time.time()),
                metadata={
                    'topic': msg.topic,
                    'qos': msg.qos,
                    'retain': msg.retain
                }
            )
            
            logger.info(f"MQTT消息已解析: title={message.title}, source={message.source}")
            
            # 调用回调函数
            if self._callback:
                try:
                    self._callback(message)
                except Exception as e:
                    logger.error(f"MQTT消息回调失败: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"处理MQTT消息时出错: {e}", exc_info=True)
    
    def _parse_payload(self, payload: str) -> Optional[dict]:
        """解析MQTT payload为消息字典
        
        支持的格式（按优先级）：
        1. 标准JSON：{"title": "...", "content": "...", "source": "..."}
        2. 嵌套JSON：{"msg": "{\"title\": ...}"} （SmsForwarder等转发工具格式）
        3. msg字段为纯文本：{"msg": "文本"}
        4. 非字典JSON（字符串/数组/数字）：整体作为内容
        5. 纯文本：整体作为内容
        
        Returns:
            至少包含title和content键的字典；无法解析时返回None
        """
        payload = payload.strip()
        if not payload:
            logger.warning("MQTT消息为空，已跳过")
            return None
        
        data = None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # 非JSON：作为纯文本消息处理
            logger.debug("MQTT消息不是JSON格式，作为纯文本处理")
        
        if data is None or not isinstance(data, (dict,)):
            # 纯文本或非字典JSON（如"hello"、[1,2]）
            content = payload if data is None else str(data)
            return {'title': '新消息', 'content': content}
        
        # 检查是否是嵌套格式（msg字段包含JSON字符串）
        if 'msg' in data and isinstance(data['msg'], str):
            try:
                nested_data = json.loads(data['msg'])
                if isinstance(nested_data, dict):
                    # 合并外层与内层数据，内层优先
                    merged = {**data, **nested_data}
                    merged.pop('msg', None)
                    data = merged
                    logger.debug("MQTT检测到嵌套JSON格式，已解析msg字段")
                else:
                    data = {'title': '新消息', 'content': str(nested_data)}
            except json.JSONDecodeError:
                # msg字段不是JSON，把它当作content
                if 'title' not in data and 'content' not in data:
                    data = {'title': '新消息', 'content': data['msg']}
        
        # 补全缺失字段（至少要有title或content之一）
        has_title = 'title' in data and data['title'] is not None
        has_content = 'content' in data and data['content'] is not None
        
        if not has_title and not has_content:
            logger.error(f"MQTT消息缺少title和content字段，已跳过。当前字段: {list(data.keys())}")
            return None
        
        if not has_title:
            data['title'] = '新消息'
        if not has_content:
            data['content'] = str(data['title'])
        
        return data
