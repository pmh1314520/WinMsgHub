"""
WinMsgHub (WinMsgHub) - 消息处理器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from typing import Dict
from PyQt6.QtCore import QObject, pyqtSignal
from data.connectors.base import MessageConnector
from data.models import Message
from data.database import Database
from core.filter_engine import FilterEngine
from utils.logger import get_logger


logger = get_logger(__name__)


class MessageProcessor(QObject):
    """
    消息处理核心
    
    负责接收来自各个消息源的消息，应用过滤规则，保存到数据库，并触发弹窗显示。
    
    验证需求：
    - 2.2: 解析消息内容
    - 2.3: 保存消息到历史记录
    - 2.5: 处理解析失败的情况
    """
    
    # 定义信号，用于在主线程中显示弹窗
    message_received = pyqtSignal(Message)
    
    def __init__(self, filter_engine: FilterEngine, database: Database, popup_manager=None):
        """
        初始化消息处理器
        
        Args:
            filter_engine: 消息过滤引擎
            database: 数据库访问对象
            popup_manager: 弹窗管理器（可选）
        """
        super().__init__()  # 调用QObject的初始化
        self.filter_engine = filter_engine
        self.database = database
        self.popup_manager = popup_manager
        self.connectors: Dict[str, MessageConnector] = {}
        
        # 连接信号到槽函数（在主线程中执行）
        if self.popup_manager:
            # 先断开可能存在的旧连接，避免重复连接
            try:
                self.message_received.disconnect()
            except:
                pass  # 如果没有连接，会抛出异常，忽略即可
            
            # 连接信号
            self.message_received.connect(self._show_popup_in_main_thread)
        
        logger.info("消息处理器已初始化")
    
    def register_connector(self, name: str, connector: MessageConnector):
        """
        注册消息源连接器
        
        Args:
            name: 连接器名称
            connector: 连接器实例
        """
        connector.subscribe(self._on_message_received)
        self.connectors[name] = connector
        logger.info(f"已注册消息源连接器: {name}")
    
    def _on_message_received(self, message: Message):
        """
        消息接收回调
        
        Args:
            message: 接收到的消息
        """
        try:
            logger.info(f"收到消息: id={message.id}, 来源={message.source}, 标题={message.title}")
            
            # 1. 验证消息完整性（需求2.2）
            if not self._validate_message(message):
                logger.warning(f"消息验证失败: {message.id}")
                return
            
            # 2. 应用过滤规则（需求2.4）
            should_show, should_save = self.filter_engine.should_process(message)
            
            if not should_show:
                logger.info(f"消息被过滤规则拦截: {message.id}"
                            f"（{'仍保存' if should_save else '不保存'}到历史记录）")
                
                # 检查是否仍然保存到历史记录
                if should_save:
                    self.database.save_message(message)
                return
            
            # 3. 保存到数据库（需求2.3）
            try:
                self.database.save_message(message)
                logger.debug(f"消息已保存: {message.id}")
            except Exception as e:
                logger.error(f"保存消息失败: {e}", exc_info=True)
                # 继续处理，即使保存失败
            
            # 4. 触发弹窗显示（使用信号发送到主线程）
            if self.popup_manager:
                try:
                    # 发送信号，让主线程处理弹窗显示
                    self.message_received.emit(message)
                except Exception as e:
                    logger.error(f"发送消息信号失败: {e}", exc_info=True)
            else:
                logger.warning("没有弹窗管理器，消息不会弹窗显示")
            
        except Exception as e:
            # 需求2.5：处理解析失败
            logger.error(f"处理消息时出错: {e}", exc_info=True)
    
    def _validate_message(self, message: Message) -> bool:
        """
        验证消息完整性
        
        Args:
            message: 要验证的消息
            
        Returns:
            bool: 如果消息有效返回True，否则返回False
        """
        # 检查必需字段
        if not message.id:
            logger.error("消息缺少ID")
            return False
        
        if not message.source:
            logger.error("消息缺少来源")
            return False
        
        if not message.title:
            logger.error("消息缺少标题")
            return False
        
        # content可以为空，但不能是None
        if message.content is None:
            logger.error("消息内容为None")
            return False
        
        if message.timestamp <= 0:
            logger.error("消息时间戳无效")
            return False
        
        return True
    
    def get_connector(self, name: str) -> MessageConnector:
        """获取已注册的连接器"""
        return self.connectors.get(name)
    
    def get_all_connectors(self) -> Dict[str, MessageConnector]:
        """获取所有已注册的连接器"""
        return self.connectors.copy()
    
    def _show_popup_in_main_thread(self, message: Message):
        """
        在主线程中显示弹窗（槽函数）
        
        Args:
            message: 要显示的消息
        """
        try:
            self.popup_manager.show_notification(message)
            logger.debug(f"弹窗已显示: {message.id}")
        except Exception as e:
            logger.error(f"显示弹窗失败: {e}", exc_info=True)
