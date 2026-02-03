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
    智能过滤VPN、虚拟网卡等非真实局域网IP
    
    Returns:
        str: 本机局域网IP地址，如果获取失败返回 "127.0.0.1"
    """
    try:
        import psutil
        
        # 获取所有网络接口
        interfaces = psutil.net_if_addrs()
        
        # 优先级列表：优先选择真实的局域网IP
        # 1. 192.168.x.x (最常见的家庭/办公网络)
        # 2. 10.x.x.x (企业网络)
        # 3. 172.16-31.x.x (企业网络)
        # 排除：127.x.x.x (本地回环), 169.254.x.x (APIPA), VPN/虚拟网卡
        
        candidates = []
        
        for interface_name, addresses in interfaces.items():
            # 跳过明显的虚拟网卡和VPN
            interface_lower = interface_name.lower()
            if any(keyword in interface_lower for keyword in [
                'vmware', 'virtualbox', 'vbox', 'virtual', 
                'vpn', 'tap', 'tun', 'meta', 'loopback'
            ]):
                continue
            
            for addr in addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    ip = addr.address
                    
                    # 跳过本地回环和APIPA
                    if ip.startswith('127.') or ip.startswith('169.254.'):
                        continue
                    
                    # 优先级评分
                    priority = 0
                    if ip.startswith('192.168.'):
                        priority = 100  # 最高优先级
                    elif ip.startswith('10.'):
                        priority = 90
                    elif ip.startswith('172.'):
                        # 检查是否在 172.16-31 范围内
                        second_octet = int(ip.split('.')[1])
                        if 16 <= second_octet <= 31:
                            priority = 80
                    else:
                        priority = 50  # 其他IP（可能是公网IP或特殊IP）
                    
                    candidates.append((priority, ip, interface_name))
        
        # 按优先级排序，选择最高优先级的IP
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            selected_ip = candidates[0][1]
            selected_interface = candidates[0][2]
            logger.info(f"获取到本机局域网IP: {selected_ip} (网卡: {selected_interface})")
            return selected_ip
        
        # 如果没有找到合适的IP，使用旧方法作为后备
        logger.warning("未找到合适的局域网IP，尝试使用socket方法")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"使用socket方法获取到IP: {local_ip}")
        return local_ip
        
    except Exception as e:
        logger.warning(f"获取本机IP失败: {e}，使用默认值 127.0.0.1")
        return "127.0.0.1"
