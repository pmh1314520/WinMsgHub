"""
WinMsgHub (WinMsgHub) - IMAP消息源连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import imaplib
import email
import time
import uuid
import threading
from typing import Callable, Optional
from data.connectors.base import MessageConnector
from data.models import Message
from utils.logger import get_logger


logger = get_logger(__name__)


class IMAPConnector(MessageConnector):
    """
    IMAP消息源连接器
    
    通过IMAP IDLE监听邮件服务器的新邮件。
    
    验证需求：
    - 1.4: 支持IMAP消息源类型
    - 1.5: 使用SSL/TLS连接
    """
    
    def __init__(self):
        """初始化IMAP连接器"""
        self._callback: Optional[Callable[[Message], None]] = None
        self._connected = False
        self._config: Optional[dict] = None
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._idle_thread: Optional[threading.Thread] = None
        self._stop_idle = threading.Event()
        
        logger.info("IMAP连接器已初始化")
    
    def connect(self, config: dict) -> bool:
        """
        连接到IMAP服务器
        
        Args:
            config: 连接配置字典，包含以下字段：
                - server (str): IMAP服务器地址
                - port (int, 可选): 端口号，默认993
                - username (str): 用户名
                - password (str): 密码
                - folder (str, 可选): 监听的文件夹，默认'INBOX'
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        try:
            self._config = config
            server = config.get('server')
            port = config.get('port', 993)
            username = config.get('username')
            password = config.get('password')
            folder = config.get('folder', 'INBOX')
            
            if not all([server, username, password]):
                logger.error("IMAP配置不完整")
                return False
            
            # 连接到IMAP服务器（使用SSL）
            self._imap = imaplib.IMAP4_SSL(server, port)
            self._imap.login(username, password)
            self._imap.select(folder)
            
            self._connected = True
            self._stop_idle.clear()
            
            # 启动IDLE监听线程
            self._idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
            self._idle_thread.start()
            
            logger.info(f"IMAP连接器已启动，监听 {server}:{port}/{folder}")
            return True
            
        except Exception as e:
            logger.error(f"IMAP连接失败: {str(e)}", exc_info=True)
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """断开IMAP连接"""
        try:
            logger.info("正在停止IMAP连接器...")
            self._stop_idle.set()
            
            if self._imap:
                try:
                    self._imap.close()
                    self._imap.logout()
                except:
                    pass
                self._imap = None
            
            if self._idle_thread and self._idle_thread.is_alive():
                logger.info("等待IMAP监听线程结束...")
                self._idle_thread.join(timeout=5)
                if self._idle_thread.is_alive():
                    logger.warning("IMAP监听线程未能在5秒内停止")
                else:
                    logger.info("IMAP监听线程已完全停止")
            
            self._connected = False
            logger.info("IMAP连接器已断开")
        except Exception as e:
            logger.error(f"断开IMAP连接失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息"""
        self._callback = callback
        logger.debug("已设置消息回调函数")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def _idle_loop(self):
        """IDLE监听循环"""
        while not self._stop_idle.is_set():
            try:
                # 检查新邮件
                self._check_new_messages()
                
                # 等待一段时间再检查
                self._stop_idle.wait(30)
                
            except Exception as e:
                logger.error(f"IDLE循环出错: {str(e)}", exc_info=True)
                self._stop_idle.wait(60)
    
    def _check_new_messages(self):
        """检查新邮件"""
        try:
            # 搜索未读邮件
            status, messages = self._imap.search(None, 'UNSEEN')
            
            if status == 'OK':
                for num in messages[0].split():
                    try:
                        # 获取邮件
                        status, data = self._imap.fetch(num, '(RFC822)')
                        
                        if status == 'OK':
                            email_body = data[0][1]
                            email_message = email.message_from_bytes(email_body)
                            
                            # 解析邮件
                            message = self._parse_email(email_message)
                            
                            # 调用回调
                            if self._callback:
                                try:
                                    self._callback(message)
                                except Exception as e:
                                    logger.error(f"消息回调函数执行失败: {str(e)}")
                                    
                    except Exception as e:
                        logger.error(f"处理邮件失败: {str(e)}")
                        
        except Exception as e:
            logger.error(f"检查新邮件失败: {str(e)}")
    
    def _parse_email(self, email_message) -> Message:
        """解析邮件"""
        subject = email_message.get('Subject', '无主题')
        from_addr = email_message.get('From', '未知发件人')
        
        # 获取邮件正文
        content = ''
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return Message(
            id=str(uuid.uuid4()),
            source='IMAP',
            title=subject,
            content=content,
            timestamp=time.time(),
            metadata={'from': from_addr}
        )
