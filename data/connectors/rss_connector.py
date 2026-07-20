"""
WinMsgHub - RSS/Atom订阅连接器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import logging
import time
import uuid
import hashlib
from typing import Callable, Optional
import threading
import feedparser
from datetime import datetime
from data.connectors.base import MessageConnector
from data.models import Message

logger = logging.getLogger(__name__)


class RSSConnector(MessageConnector):
    """RSS/Atom订阅连接器
    
    监控博客、新闻等更新。
    """
    
    def __init__(self):
        self.callback: Optional[Callable[[Message], None]] = None
        self.config: dict = {}
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # 用dict作为"插入有序集合"，裁剪时可以准确删除最旧的条目
        self._seen_entries: dict = {}
    
    def connect(self, config: dict) -> bool:
        """建立RSS订阅连接
        
        Args:
            config: 配置字典，包含：
                - url: RSS/Atom订阅URL
                - poll_interval: 轮询间隔（秒），默认300（5分钟）
                - user_agent: 自定义User-Agent
        """
        try:
            self.config = config
            url = config.get('url', '')
            
            if not url:
                logger.error("RSS订阅URL未配置")
                return False
            
            # 测试订阅源是否可访问
            # 注意：bozo=1只表示解析过程中有非致命问题（如编码声明不规范），
            # 只要能解析出条目就应该接受，否则会误拒很多正常订阅源
            feed = self._fetch_feed(url)
            if not feed or (feed.bozo and not feed.entries):
                logger.error(f"无法访问RSS订阅源: {url}")
                return False
            
            # 初始化已见条目（避免首次运行时推送所有历史条目）
            self._initialize_seen_entries(feed)
            
            self._connected = True
            self._stop_event.clear()
            
            # 启动轮询线程
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            
            logger.info(f"RSS订阅已连接: {url}")
            return True
            
        except Exception as e:
            logger.error(f"RSS订阅连接失败: {e}")
            return False
    
    def _fetch_feed(self, url: str):
        """获取RSS订阅内容"""
        try:
            user_agent = self.config.get('user_agent', 'WinMsgHub RSS Reader/1.0')
            feed = feedparser.parse(url, agent=user_agent)
            return feed
        except Exception as e:
            logger.error(f"获取RSS订阅失败: {e}")
            return None
    
    def _initialize_seen_entries(self, feed):
        """初始化已见条目集合
        
        必须记录首次抓取到的所有条目，否则首次轮询时
        未记录的历史条目会被当作新内容，造成弹窗风暴。
        """
        try:
            for entry in feed.entries:
                entry_id = self._get_entry_id(entry)
                self._seen_entries[entry_id] = True
            logger.info(f"RSS初始化完成，已记录 {len(self._seen_entries)} 条历史条目")
        except Exception as e:
            logger.error(f"初始化已见条目失败: {e}")
    
    def _get_entry_id(self, entry) -> str:
        """获取条目唯一标识"""
        # 优先使用entry的id，否则使用link的hash
        if hasattr(entry, 'id'):
            return entry.id
        elif hasattr(entry, 'link'):
            return hashlib.md5(entry.link.encode()).hexdigest()
        else:
            return hashlib.md5(str(entry).encode()).hexdigest()
    
    def _poll_loop(self):
        """轮询循环"""
        poll_interval = self.config.get('poll_interval', 300)
        url = self.config.get('url', '')
        
        while not self._stop_event.is_set():
            try:
                feed = self._fetch_feed(url)
                # 只要能解析出条目就处理（bozo只是非致命解析警告）
                if feed and feed.entries:
                    self._process_feed(feed)
            except Exception as e:
                logger.error(f"RSS轮询错误: {e}")
            
            # 等待下一次轮询
            self._stop_event.wait(poll_interval)
    
    def _process_feed(self, feed):
        """处理订阅内容"""
        try:
            for entry in feed.entries:
                entry_id = self._get_entry_id(entry)
                
                # 跳过已见条目
                if entry_id in self._seen_entries:
                    continue
                
                # 标记为已见
                self._seen_entries[entry_id] = True
                
                # 限制已见集合大小（dict保持插入顺序，删除最旧的一半）
                if len(self._seen_entries) > 1000:
                    keys = list(self._seen_entries.keys())
                    self._seen_entries = {k: True for k in keys[-500:]}
                
                # 创建消息
                if self.callback:
                    title = entry.get('title', '无标题')
                    content = entry.get('summary', entry.get('description', ''))
                    link = entry.get('link', '')
                    
                    # 解析发布时间
                    # feedparser返回的struct_time是UTC时间，
                    # 必须用calendar.timegm转换；time.mktime会当成本地时间导致时区偏差
                    import calendar
                    timestamp = time.time()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        timestamp = calendar.timegm(entry.published_parsed)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        timestamp = calendar.timegm(entry.updated_parsed)
                    
                    # 获取用户配置的名称
                    source_name = self.config.get('name', '默认')
                    
                    msg = Message(
                        id=entry_id,
                        source=source_name,  # 顶部标签显示用户配置的名称
                        title=f"RSS: {title}",  # 标题显示中文+文章标题
                        content=content,
                        timestamp=timestamp,
                        metadata={
                            'link': link,
                            'author': entry.get('author', ''),
                            'feed_title': feed.feed.get('title', '')
                        }
                    )
                    
                    self.callback(msg)
                    
        except Exception as e:
            logger.error(f"处理RSS订阅内容失败: {e}")
    
    def disconnect(self) -> None:
        """断开RSS订阅"""
        try:
            logger.info("正在停止RSS订阅...")
            self._stop_event.set()
            
            if self._thread and self._thread.is_alive():
                logger.info("等待RSS订阅线程结束...")
                self._thread.join(timeout=5)
                if self._thread.is_alive():
                    logger.warning("RSS订阅线程未能在5秒内停止")
                else:
                    logger.info("RSS订阅线程已完全停止")
            
            self._connected = False
            logger.info("RSS订阅已断开")
        except Exception as e:
            logger.error(f"断开RSS订阅失败: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅消息"""
        self.callback = callback
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
