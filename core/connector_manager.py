"""
WinMsgHub - 连接器管理器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from typing import Dict, List
from data.connectors import (
    MQTTConnector,
    APIConnector,
    WebhookConnector,
    IMAPConnector,
    WebSocketConnector,
    RSSConnector,
    FileMonitorConnector,
    ClipboardConnector
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ConnectorManager:
    """连接器管理器
    
    负责管理多个消息源连接器实例，支持每种类型添加多个实例。
    """
    
    # 连接器类型映射
    CONNECTOR_TYPES = {
        'mqtt': MQTTConnector,
        'api': APIConnector,
        'webhook': WebhookConnector,
        'imap': IMAPConnector,
        'websocket': WebSocketConnector,
        'rss': RSSConnector,
        'file_monitor': FileMonitorConnector,
        'clipboard': ClipboardConnector
    }
    
    def __init__(self, message_processor):
        """初始化连接器管理器
        
        Args:
            message_processor: 消息处理器实例
        """
        self.message_processor = message_processor
        self.connectors: Dict[str, List] = {}
        
        # 初始化每种类型的连接器列表
        for connector_type in self.CONNECTOR_TYPES.keys():
            self.connectors[connector_type] = []
        
        logger.info("连接器管理器已初始化")
    
    def load_connectors(self, config: dict):
        """从配置加载所有连接器
        
        Args:
            config: 配置字典，包含message_sources配置
        """
        message_sources = config.get('message_sources', {})
        
        logger.info("=" * 60)
        logger.info("开始加载消息源连接器")
        logger.info("=" * 60)
        
        for connector_type, sources in message_sources.items():
            if connector_type not in self.CONNECTOR_TYPES:
                logger.warning(f"未知的连接器类型: {connector_type}")
                continue
            
            logger.info(f"处理连接器类型: {connector_type}")
            logger.info(f"  配置类型: {type(sources)}")
            logger.info(f"  配置内容: {sources}")
            
            # 如果sources是列表，则为多实例配置
            if isinstance(sources, list):
                logger.info(f"  检测到列表格式，共 {len(sources)} 个配置")
                for idx, source_config in enumerate(sources):
                    enabled = source_config.get('enabled', False)
                    name = source_config.get('name', f'{connector_type}_{idx}')
                    logger.info(f"    [{idx}] {name} - enabled={enabled}")
                    if enabled:
                        self._create_connector(connector_type, source_config, idx)
                    else:
                        logger.info(f"    [{idx}] {name} 未启用，跳过")
            # 兼容旧的单实例配置
            elif isinstance(sources, dict) and sources.get('enabled', False):
                logger.info(f"  检测到字典格式（旧格式）")
                self._create_connector(connector_type, sources, 0)
            else:
                logger.info(f"  跳过（空配置或未启用）")
        
        logger.info("=" * 60)
        logger.info("消息源连接器加载完成")
        logger.info("=" * 60)
    
    def _create_connector(self, connector_type: str, config: dict, index: int):
        """创建并启动连接器
        
        Args:
            connector_type: 连接器类型
            config: 连接器配置
            index: 连接器索引
        """
        try:
            # 获取连接器类
            connector_class = self.CONNECTOR_TYPES[connector_type]
            
            # 创建连接器实例
            connector = connector_class()
            
            # 生成唯一名称
            name = config.get('name', f'{connector_type}_{index}')
            unique_name = f'{connector_type}_{name}'
            
            # 注册到消息处理器
            self.message_processor.register_connector(unique_name, connector)
            
            # 连接
            if connector.connect(config):
                self.connectors[connector_type].append({
                    'name': unique_name,
                    'connector': connector,
                    'config': config
                })
                logger.info(f"✅ 连接器已启动: {unique_name}")
            else:
                logger.error(f"❌ 连接器启动失败: {unique_name}")
                
        except Exception as e:
            logger.error(f"❌ 创建连接器失败 ({connector_type}): {e}", exc_info=True)
    
    def disconnect_all(self):
        """断开所有连接器"""
        for connector_type, connector_list in self.connectors.items():
            for connector_info in connector_list:
                try:
                    connector_info['connector'].disconnect()
                    logger.info(f"已断开连接器: {connector_info['name']}")
                except Exception as e:
                    logger.error(f"断开连接器失败 ({connector_info['name']}): {e}")
        
        # 清空连接器列表
        for connector_type in self.connectors.keys():
            self.connectors[connector_type] = []
    
    def reload_connectors(self, config: dict):
        """重新加载所有连接器
        
        Args:
            config: 新的配置字典
        """
        logger.info("正在重新加载所有连接器...")
        
        # 断开所有现有连接器
        self.disconnect_all()
        
        # 清空消息处理器的连接器
        self.message_processor.connectors.clear()
        
        # 重新加载
        self.load_connectors(config)
        
        logger.info("连接器重新加载完成")
    
    def get_connector_status(self) -> Dict[str, List[Dict]]:
        """获取所有连接器的状态
        
        Returns:
            连接器状态字典
        """
        status = {}
        
        for connector_type, connector_list in self.connectors.items():
            status[connector_type] = []
            for connector_info in connector_list:
                status[connector_type].append({
                    'name': connector_info['name'],
                    'connected': connector_info['connector'].is_connected(),
                    'config': connector_info['config']
                })
        
        return status
    
    def get_connector_count(self) -> Dict[str, int]:
        """获取每种类型的连接器数量
        
        Returns:
            连接器数量字典
        """
        return {
            connector_type: len(connector_list)
            for connector_type, connector_list in self.connectors.items()
        }
