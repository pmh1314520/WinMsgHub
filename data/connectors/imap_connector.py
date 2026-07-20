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
        self._processed_uids = set()  # 记录已处理的邮件UID，避免重复弹窗
        self._uid_cache_file = None  # UID缓存文件路径
        self._last_check_time = 0  # 最后一次检查的时间戳
        self._is_first_check = True  # 首次检查标志，首次检查时只标记不弹窗
        
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
            
            # 设置UID缓存文件路径（基于用户名，避免不同账号混淆）
            import sys
            import os
            from pathlib import Path
            if sys.platform == 'win32':
                cache_dir = Path(os.environ.get('APPDATA', '.')) / 'WinMsgHub' / 'cache'
            else:
                cache_dir = Path.home() / '.WinMsgHub' / 'cache'
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用用户名和服务器作为文件名，避免冲突
            safe_username = username.replace('@', '_').replace('.', '_')
            self._uid_cache_file = cache_dir / f'imap_uids_{safe_username}_{server}.txt'
            
            # 加载已处理的UID
            self._load_processed_uids()
            
            # 如果有缓存，说明不是首次启动
            if len(self._processed_uids) > 0:
                self._is_first_check = False
                logger.info(f"📂 检测到UID缓存，跳过首次检查标记")
            
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
            
            # 保存UID缓存
            self._save_processed_uids()
            
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
    
    def _load_processed_uids(self):
        """从缓存文件加载已处理的UID"""
        try:
            if self._uid_cache_file and self._uid_cache_file.exists():
                with open(self._uid_cache_file, 'r', encoding='utf-8') as f:
                    lines = f.read().strip().split('\n')
                
                # 第一行是最后检查时间戳
                if lines and lines[0].startswith('LAST_CHECK:'):
                    try:
                        self._last_check_time = float(lines[0].split(':', 1)[1])
                        lines = lines[1:]
                    except:
                        pass
                
                # 其余行是UID
                self._processed_uids = set(uid.strip() for uid in lines if uid.strip())
                logger.info(f"📂 从缓存加载了 {len(self._processed_uids)} 个已处理的UID")
            else:
                logger.info(f"📂 没有找到UID缓存文件")
        except Exception as e:
            logger.error(f"加载UID缓存失败: {e}", exc_info=True)
    
    def _save_processed_uids(self):
        """保存已处理的UID和最后检查时间到缓存文件"""
        try:
            if self._uid_cache_file:
                import time
                with open(self._uid_cache_file, 'w', encoding='utf-8') as f:
                    # 第一行保存最后检查时间
                    f.write(f'LAST_CHECK:{time.time()}\n')
                    # 其余行保存UID
                    f.write('\n'.join(sorted(self._processed_uids)))
                logger.debug(f"💾 已保存 {len(self._processed_uids)} 个UID到缓存")
        except Exception as e:
            logger.error(f"保存UID缓存失败: {e}", exc_info=True)
    
    def _idle_loop(self):
        """IDLE监听循环"""
        # 从配置读取轮询间隔，默认 60 秒
        poll_interval = self._config.get('poll_interval', 60)
        logger.info(f"⏰ IMAP 轮询间隔: {poll_interval} 秒")
        
        while not self._stop_idle.is_set():
            try:
                # 检查新邮件
                self._check_new_messages()
                
                # 等待配置的时间再检查
                logger.debug(f"⏳ 等待 {poll_interval} 秒后再次检查...")
                self._stop_idle.wait(poll_interval)
                
            except Exception as e:
                logger.error(f"IDLE循环出错: {str(e)}", exc_info=True)
                # 出错后等待 60 秒再重试
                self._stop_idle.wait(60)
    
    def _check_new_messages(self):
        """检查新邮件 - 只弹出最近收到的新邮件（24小时内）"""
        try:
            # 检查连接是否有效
            if not self._imap:
                logger.warning("⚠️ IMAP 连接对象为空，跳过检查")
                return
            
            # 尝试发送 NOOP 命令保持连接活跃
            try:
                self._imap.noop()
            except Exception as e:
                logger.warning(f"⚠️ IMAP 连接可能已断开: {e}，尝试重新连接...")
                if not self._reconnect():
                    logger.error("❌ 重新连接失败，跳过本次检查")
                    return
            
            logger.debug(f"🔍 开始检查邮件...")
            
            # 🔥 关键修改：使用IMAP搜索最近1天的未读邮件（用于获取候选邮件）
            import datetime
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            search_date = yesterday.strftime("%d-%b-%Y")  # 格式：03-Feb-2026
            
            # 搜索昨天以来的未读邮件（包括今天）
            status, messages = self._imap.search(None, f'(UNSEEN SINCE {search_date})')
            
            if status != 'OK':
                logger.warning(f"搜索未读邮件失败，状态: {status}")
                return
            
            message_nums = messages[0].split()
            
            if not message_nums:
                logger.debug(f"📭 最近1天没有未读邮件")
                return
            
            logger.info(f"📬 发现 {len(message_nums)} 封最近1天的未读邮件")
            
            # 🔥 首次检查：只标记所有邮件为已处理，不弹窗
            if self._is_first_check:
                logger.info(f"⚠️ 首次检查，将所有未读邮件标记为已处理（不弹窗）")
                import re
                for num in message_nums:
                    try:
                        status, uid_data = self._imap.fetch(num, '(UID)')
                        if status == 'OK':
                            uid_str = uid_data[0].decode('utf-8', errors='ignore')
                            # 用正则精确提取UID（第一个数字是序列号，不是UID）
                            uid_match = re.search(r'UID (\d+)', uid_str)
                            if uid_match:
                                self._processed_uids.add(uid_match.group(1))
                    except Exception as e:
                        logger.error(f"标记邮件UID失败: {e}")
                
                logger.info(f"✅ 已标记 {len(message_nums)} 封邮件为已处理")
                self._is_first_check = False
                self._save_processed_uids()
                return
            
            # 计算30分钟前的时间戳
            import time
            thirty_minutes_ago = time.time() - (30 * 60)  # 30分钟 = 1800秒
            
            new_email_count = 0
            
            for num in message_nums:
                try:
                    # 检查连接是否有效
                    if not self._imap:
                        logger.warning("⚠️ IMAP 连接已断开，停止处理邮件")
                        break
                    
                    # 获取邮件的唯一标识符 (UID) 和日期
                    status, uid_data = self._imap.fetch(num, '(UID INTERNALDATE)')
                    if status != 'OK':
                        logger.warning(f"获取邮件 UID 失败，状态: {status}")
                        continue
                    
                    # 解析 UID 和日期
                    # 响应格式类似：b'1 (UID 4827 INTERNALDATE "03-Feb-2026 10:23:45 +0800")'
                    uid_str = uid_data[0].decode('utf-8', errors='ignore')
                    email_date = None
                    
                    # 解析UID：必须用正则精确提取"UID <数字>"，
                    # 不能取第一个数字（那是会随邮箱变化的序列号，会导致去重失效）
                    import re
                    uid_match = re.search(r'UID (\d+)', uid_str)
                    uid = uid_match.group(1) if uid_match else None
                    
                    # 解析日期
                    try:
                        from email.utils import parsedate_to_datetime
                        date_match = re.search(r'INTERNALDATE "([^"]+)"', uid_str)
                        if date_match:
                            date_str = date_match.group(1)
                            email_date = parsedate_to_datetime(date_str)
                            email_timestamp = email_date.timestamp()
                            
                            # 🔥 关键过滤：只处理30分钟内的邮件
                            if email_timestamp < thirty_minutes_ago:
                                logger.debug(f"邮件 UID {uid} 超过30分钟，跳过（日期: {email_date}）")
                                # 标记为已处理，避免下次再检查
                                if uid:
                                    self._processed_uids.add(uid)
                                continue
                    except Exception as e:
                        logger.warning(f"解析邮件日期失败: {e}，将处理该邮件")
                    
                    if not uid:
                        logger.warning(f"无法解析邮件 UID: {uid_str}")
                        continue
                    
                    # 检查是否已经处理过这封邮件
                    if uid in self._processed_uids:
                        logger.debug(f"邮件 UID {uid} 已处理过，跳过")
                        continue
                    
                    # 这是一封新邮件！
                    new_email_count += 1
                    logger.info(f"🆕 发现新邮件 UID: {uid}，日期: {email_date}")
                    
                    # 检查连接（获取邮件内容前）
                    if not self._imap:
                        logger.warning("⚠️ IMAP 连接已断开，停止处理邮件")
                        break
                    
                    # 获取邮件内容
                    # 使用BODY.PEEK[]而不是RFC822，避免将用户邮箱中的邮件标记为已读
                    status, data = self._imap.fetch(num, '(BODY.PEEK[])')
                    
                    if status == 'OK':
                        email_body = self._extract_email_body(data)
                        if email_body is None:
                            logger.warning(f"无法提取邮件内容 (UID: {uid})")
                            continue
                        
                        email_message = email.message_from_bytes(email_body)
                        
                        # 解析邮件（附带真实收件时间）
                        message = self._parse_email(email_message, email_date)
                        
                        # 记录已处理的 UID
                        self._processed_uids.add(uid)
                        logger.info(f"✉️ 新邮件: {message.title} (UID: {uid})")
                        
                        # 调用回调
                        if self._callback:
                            try:
                                self._callback(message)
                            except Exception as e:
                                logger.error(f"消息回调函数执行失败: {str(e)}", exc_info=True)
                                
                    else:
                        logger.warning(f"获取邮件内容失败，状态: {status}")
                        
                except Exception as e:
                    logger.error(f"处理邮件失败: {str(e)}", exc_info=True)
            
            if new_email_count > 0:
                logger.info(f"📨 本次检查发现 {new_email_count} 封新邮件")
                # 保存UID缓存
                self._save_processed_uids()
            
            # 定期清理已处理的 UID 集合，避免内存无限增长
            # UID在同一邮箱内单调递增，按数值排序保留最新的500个
            if len(self._processed_uids) > 1000:
                logger.info(f"🧹 清理旧的 UID 记录，当前数量: {len(self._processed_uids)}")
                sorted_uids = sorted(
                    self._processed_uids,
                    key=lambda u: int(u) if u.isdigit() else 0
                )
                self._processed_uids = set(sorted_uids[-500:])
                logger.info(f"✅ 清理完成，剩余 UID 数量: {len(self._processed_uids)}")
                    
        except Exception as e:
            logger.error(f"检查新邮件失败: {str(e)}", exc_info=True)
    
    def _reconnect(self) -> bool:
        """重新连接到 IMAP 服务器"""
        try:
            logger.info("🔄 尝试重新连接 IMAP 服务器...")
            
            # 关闭旧连接
            if self._imap:
                try:
                    self._imap.close()
                    self._imap.logout()
                except:
                    pass
                self._imap = None
            
            # 重新连接
            server = self._config.get('server')
            port = self._config.get('port', 993)
            username = self._config.get('username')
            password = self._config.get('password')
            folder = self._config.get('folder', 'INBOX')
            
            self._imap = imaplib.IMAP4_SSL(server, port)
            self._imap.login(username, password)
            self._imap.select(folder)
            
            logger.info("✅ IMAP 重新连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ IMAP 重新连接失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _extract_email_body(fetch_data) -> Optional[bytes]:
        """从IMAP fetch响应中提取邮件原文字节
        
        fetch响应是列表，其中真正的邮件内容是(元信息, 字节)元组。
        """
        try:
            for item in fetch_data:
                if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                    return bytes(item[1])
            return None
        except Exception:
            return None
    
    def _parse_email(self, email_message, email_date=None) -> Message:
        """解析邮件
        
        Args:
            email_message: email.message.Message对象
            email_date: 邮件的真实收件时间（datetime，可选）
        """
        from email.header import decode_header
        
        # 解码邮件标题
        subject_raw = email_message.get('Subject', '无主题')
        subject = ''
        try:
            decoded_parts = decode_header(subject_raw)
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    if encoding:
                        try:
                            subject += content.decode(encoding, errors='ignore')
                        except (LookupError, UnicodeDecodeError):
                            # 如果编码不支持，尝试常见编码
                            for fallback_encoding in ['utf-8', 'gb2312', 'gbk', 'latin1']:
                                try:
                                    subject += content.decode(fallback_encoding, errors='ignore')
                                    break
                                except:
                                    continue
                            else:
                                # 所有编码都失败，使用原始字节
                                subject += content.decode('utf-8', errors='replace')
                    else:
                        subject += content.decode('utf-8', errors='ignore')
                else:
                    subject += str(content)
        except Exception as e:
            logger.warning(f"解码邮件标题失败: {e}，使用原始标题")
            # 确保返回字符串
            subject = str(subject_raw) if subject_raw else '无主题'
        
        # 确保subject是字符串
        if not isinstance(subject, str):
            subject = str(subject)
        
        # 如果解码后为空，使用默认值
        if not subject or subject.strip() == '':
            subject = '无主题'
        
        # 解码发件人
        from_raw = email_message.get('From', '未知发件人')
        from_addr = ''
        try:
            decoded_parts = decode_header(from_raw)
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    if encoding:
                        try:
                            from_addr += content.decode(encoding, errors='ignore')
                        except (LookupError, UnicodeDecodeError):
                            # 如果编码不支持，尝试常见编码
                            for fallback_encoding in ['utf-8', 'gb2312', 'gbk', 'latin1']:
                                try:
                                    from_addr += content.decode(fallback_encoding, errors='ignore')
                                    break
                                except:
                                    continue
                            else:
                                from_addr += content.decode('utf-8', errors='replace')
                    else:
                        from_addr += content.decode('utf-8', errors='ignore')
                else:
                    from_addr += str(content)
        except Exception as e:
            logger.warning(f"解码发件人失败: {e}，使用原始发件人")
            from_addr = str(from_raw) if from_raw else '未知发件人'
        
        # 确保from_addr是字符串
        if not isinstance(from_addr, str):
            from_addr = str(from_addr)
        
        if not from_addr or from_addr.strip() == '':
            from_addr = '未知发件人'
        
        # 获取邮件正文
        content = ''
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        content = payload.decode(charset, errors='ignore')
                        break
                    except Exception as e:
                        logger.warning(f"解码邮件正文失败: {e}")
        else:
            try:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='ignore')
            except Exception as e:
                logger.warning(f"解码邮件正文失败: {e}")
        
        # 使用用户配置的名称作为来源（与其他连接器保持一致）
        source_name = (self._config or {}).get('name', 'IMAP')
        
        # 优先使用邮件的真实收件时间
        timestamp = time.time()
        if email_date is not None:
            try:
                timestamp = email_date.timestamp()
            except Exception:
                pass
        
        return Message(
            id=str(uuid.uuid4()),
            source=source_name,
            title=subject if subject else '无主题',
            content=content if content else '(无内容)',
            timestamp=timestamp,
            metadata={'from': from_addr}
        )
