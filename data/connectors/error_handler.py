"""
WinMsgHub - 连接器错误处理装饰器
作者：青云制作_彭明航

提供统一的错误处理和防御机制，确保连接器不会因为异常而崩溃
"""

import functools
import traceback
from typing import Callable, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def safe_message_handler(func: Callable) -> Callable:
    """
    安全的消息处理装饰器
    
    捕获所有异常，记录日志，但不中断程序运行
    适用于消息回调函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"消息处理失败 [{func.__name__}]: {str(e)}",
                exc_info=True
            )
            # 返回None而不是抛出异常
            return None
    return wrapper


def safe_connector_operation(default_return=False):
    """
    安全的连接器操作装饰器
    
    捕获所有异常，记录日志，返回默认值
    适用于connect, disconnect等操作
    
    Args:
        default_return: 发生异常时的默认返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"连接器操作失败 [{func.__name__}]: {str(e)}",
                    exc_info=True
                )
                return default_return
        return wrapper
    return decorator


def validate_message_data(data: dict, source_name: str = "Unknown") -> dict:
    """
    验证和清理消息数据
    
    确保消息数据包含必需的字段，并进行类型转换
    
    Args:
        data: 原始消息数据字典
        source_name: 消息源名称
    
    Returns:
        清理后的消息数据字典
    """
    try:
        # 获取title和content
        title = str(data.get('title', '新消息'))
        content = str(data.get('content', ''))
        
        # 如果content为空，尝试使用title作为content
        if not content and title:
            content = title
        
        # 如果都为空，使用默认消息
        if not content:
            content = '(无内容)'
        
        # 确保基本字段存在
        cleaned_data = {
            'id': str(data.get('id', '')),
            'source': str(data.get('source', source_name)),
            'title': title if title else '新消息',
            'content': content,
            'timestamp': float(data.get('timestamp', 0)),
            'metadata': dict(data.get('metadata', {}))
        }
        
        # 验证字段长度
        if len(cleaned_data['title']) > 500:
            cleaned_data['title'] = cleaned_data['title'][:500] + '...'
            logger.warning(f"消息标题过长，已截断: {source_name}")
        
        if len(cleaned_data['content']) > 10000:
            cleaned_data['content'] = cleaned_data['content'][:10000] + '...'
            logger.warning(f"消息内容过长，已截断: {source_name}")
        
        return cleaned_data
        
    except Exception as e:
        logger.error(f"消息数据验证失败: {e}")
        # 返回最小有效数据
        return {
            'id': '',
            'source': source_name,
            'title': '数据格式错误',
            'content': '收到的消息格式不正确',
            'timestamp': 0,
            'metadata': {}
        }


def safe_json_parse(payload: str, default: dict = None) -> dict:
    """
    安全的JSON解析，支持多种格式
    
    支持的格式：
    1. JSON格式：{"title":"标题", "content":"内容"}
    2. 空格分隔（2参数）：标题 内容
    3. 空格分隔（3参数）：标题 内容 来源名称
    4. 纯文本：内容
    5. SmsForwarder格式：{"msg": "标题 内容"}
    
    Args:
        payload: 消息字符串
        default: 解析失败时的默认值
    
    Returns:
        解析后的字典，或默认值
    """
    import json
    
    if default is None:
        default = {}
    
    # 去除首尾空白
    payload = payload.strip()
    
    if not payload:
        return {'title': '空消息', 'content': '(无内容)'}
    
    # 1. 尝试解析JSON格式
    if payload.startswith('{') or payload.startswith('['):
        try:
            data = json.loads(payload)
            
            # 确保返回的是字典
            if not isinstance(data, dict):
                logger.warning(f"JSON解析结果不是字典类型: {type(data)}")
                return {'content': str(data)}
            
            # 检查是否有嵌套的msg字段（SmsForwarder格式）
            if 'msg' in data and isinstance(data['msg'], str):
                msg_content = data['msg'].strip()
                print(f"🔄 检测到msg字段: {msg_content}")
                
                # 尝试解析msg字段中的JSON
                try:
                    nested_data = json.loads(msg_content)
                    if isinstance(nested_data, dict):
                        print(f"✅ msg字段是JSON，已解析")
                        # 合并外层和内层数据，内层优先
                        result = {**data, **nested_data}
                        # 删除原始的msg字段
                        if 'msg' in result:
                            del result['msg']
                        return result
                except:
                    # msg字段不是JSON，按空格分隔处理
                    print(f"📝 msg字段不是JSON，按空格分隔处理")
                    parts = msg_content.split(maxsplit=2)  # 最多分割2次，支持3个参数
                    
                    if len(parts) >= 2:
                        result = {
                            'title': parts[0],
                            'content': parts[1]
                        }
                        # 如果有第3个参数，作为source
                        if len(parts) == 3:
                            result['source'] = parts[2]
                            print(f"✅ 检测到3个参数: 标题={parts[0]}, 内容={parts[1]}, 来源={parts[2]}")
                        else:
                            print(f"✅ 检测到2个参数: 标题={parts[0]}, 内容={parts[1]}")
                        return result
                    else:
                        # 只有一个词，作为内容
                        return {'title': msg_content[:50], 'content': msg_content}
            
            return data
            
        except json.JSONDecodeError:
            # 不是有效的JSON，继续尝试其他格式
            pass
    
    # 2. 尝试空格分隔格式：标题 内容 [来源]
    parts = payload.split(maxsplit=2)  # 最多分割2次，支持3个参数
    
    if len(parts) >= 2:
        result = {
            'title': parts[0],
            'content': parts[1]
        }
        # 如果有第3个参数，作为source
        if len(parts) == 3:
            result['source'] = parts[2]
            print(f"📝 检测到空格分隔格式(3参数): 标题='{parts[0]}', 内容='{parts[1]}', 来源='{parts[2]}'")
        else:
            print(f"📝 检测到空格分隔格式(2参数): 标题='{parts[0]}', 内容='{parts[1]}'")
        return result
    
    # 3. 纯文本格式（没有空格或只有一个词）
    print(f"📝 检测到纯文本格式，使用内容作为标题和内容")
    return {
        'title': payload[:50] if len(payload) > 50 else payload,  # 标题最多50字符
        'content': payload
    }


def safe_callback_invoke(callback: Callable, message: Any, connector_name: str = "Unknown"):
    """
    安全地调用回调函数
    
    Args:
        callback: 回调函数
        message: 消息对象
        connector_name: 连接器名称
    """
    if callback is None:
        logger.warning(f"[{connector_name}] 回调函数未设置，消息被丢弃")
        return
    
    try:
        callback(message)
    except Exception as e:
        logger.error(
            f"[{connector_name}] 回调函数执行失败: {str(e)}",
            exc_info=True
        )


class ConnectionTimeout:
    """连接超时上下文管理器"""
    
    def __init__(self, timeout: float, operation: str = "操作"):
        """
        Args:
            timeout: 超时时间（秒）
            operation: 操作描述
        """
        self.timeout = timeout
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.time() - self.start_time
        
        if elapsed > self.timeout:
            logger.warning(
                f"{self.operation} 超时: {elapsed:.2f}秒 (限制: {self.timeout}秒)"
            )
        
        # 不抑制异常
        return False
    
    def check(self):
        """检查是否超时"""
        import time
        if time.time() - self.start_time > self.timeout:
            raise TimeoutError(f"{self.operation} 超时")


def rate_limit(max_calls: int, time_window: float):
    """
    速率限制装饰器
    
    Args:
        max_calls: 时间窗口内最大调用次数
        time_window: 时间窗口（秒）
    """
    import time
    from collections import deque
    
    def decorator(func: Callable) -> Callable:
        calls = deque()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # 移除过期的调用记录
            while calls and calls[0] < now - time_window:
                calls.popleft()
            
            # 检查是否超过限制
            if len(calls) >= max_calls:
                logger.warning(
                    f"速率限制: {func.__name__} 在 {time_window}秒内调用超过 {max_calls}次"
                )
                return None
            
            # 记录调用
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
