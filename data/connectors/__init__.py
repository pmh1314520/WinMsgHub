"""
消息源连接器模块

作者：青云制作_彭明航
许可：要求二次开发必须开源并标明原作者，允许商用
"""

from data.connectors.base import MessageConnector
from data.connectors.mqtt_connector import MQTTConnector
from data.connectors.api_connector import APIConnector
from data.connectors.webhook_connector import WebhookConnector
from data.connectors.imap_connector import IMAPConnector
from data.connectors.websocket_connector import WebSocketConnector
from data.connectors.rss_connector import RSSConnector
from data.connectors.file_monitor_connector import FileMonitorConnector
from data.connectors.clipboard_connector import ClipboardConnector

__all__ = [
    'MessageConnector',
    'MQTTConnector',
    'APIConnector',
    'WebhookConnector',
    'IMAPConnector',
    'WebSocketConnector',
    'RSSConnector',
    'FileMonitorConnector',
    'ClipboardConnector'
]
