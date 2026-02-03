"""
WinMsgHub - 网络工具函数
作者:青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import socket
from utils.logger import get_logger

logger = get_logger(__name__)


def get_local_ip() -> str:
    """
    获取本机局域网IP地址
    
    Returns:
        str: 本机局域网IP地址，如果获取失败返回 "127.0.0.1"
    """
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个外部地址（不需要真的连接，只是为了获取本地IP）
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"获取到本机局域网IP: {local_ip}")
        return local_ip
    except Exception as e:
        logger.warning(f"获取本机IP失败: {e}，使用默认值 127.0.0.1")
        return "127.0.0.1"
