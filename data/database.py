"""
WinMsgHub - 数据库访问层
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from PyQt6.QtCore import QObject, pyqtSignal

from data.models import Message

logger = logging.getLogger(__name__)


class Database(QObject):
    """
    SQLite数据库访问类
    
    负责消息的持久化存储、查询、搜索和清理
    支持事件驱动的实时更新
    """
    
    # 信号定义
    message_added = pyqtSignal(Message)  # 新消息添加
    message_deleted = pyqtSignal(str)  # 消息删除（消息ID）
    messages_cleared = pyqtSignal()  # 所有消息清空
    data_changed = pyqtSignal()  # 数据发生变化（通用信号）
    
    def __init__(self, db_path: Path | str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，可以是Path对象或字符串
                    使用":memory:"创建内存数据库（用于测试）
        """
        super().__init__()
        
        if isinstance(db_path, str):
            self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        else:
            self.db_path = db_path
        
        # 对于内存数据库，保持一个持久连接
        self._memory_conn = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
        
        # 确保数据库目录存在
        if self.db_path != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _init_database(self):
        """
        初始化数据库表结构
        
        创建messages表和相关索引
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建时间戳索引，用于按时间排序和查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON messages(timestamp DESC)
            """)
            
            # 创建消息源索引，用于按来源过滤
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source 
                ON messages(source)
            """)
            
            conn.commit()
            logger.debug("数据库表结构初始化成功")
        except sqlite3.Error as e:
            logger.error(f"初始化数据库表失败: {e}")
            raise
        finally:
            self._close_connection(conn)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Returns:
            SQLite数据库连接对象
        """
        if self.db_path == ":memory:":
            return self._memory_conn
        return sqlite3.connect(str(self.db_path))
    
    def _close_connection(self, conn: sqlite3.Connection):
        """
        关闭数据库连接（如果不是内存数据库）
        
        Args:
            conn: 数据库连接对象
        """
        if self.db_path != ":memory:":
            conn.close()
    
    def save_message(self, message: Message) -> bool:
        """
        保存消息到数据库
        
        Args:
            message: 要保存的消息对象
            
        Returns:
            保存成功返回True，失败返回False
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO messages 
                (id, source, title, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.source,
                message.title,
                message.content,
                message.timestamp,
                message.metadata_to_json()
            ))
            
            conn.commit()
            logger.debug(f"消息保存成功: {message.id}")
            
            # 发出信号通知数据变化
            self.message_added.emit(message)
            self.data_changed.emit()
            
            return True
        except sqlite3.Error as e:
            logger.error(f"保存消息失败: {e}")
            return False
        finally:
            self._close_connection(conn)
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        根据ID获取单条消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            找到返回Message对象，否则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, source, title, content, timestamp, metadata
                FROM messages
                WHERE id = ?
            """, (message_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_message(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"查询消息失败: {e}")
            return None
        finally:
            self._close_connection(conn)
    
    def get_messages(self, limit: int = 100, offset: int = 0) -> List[Message]:
        """
        获取消息列表（按时间倒序）
        
        Args:
            limit: 返回的最大消息数量，默认100
            offset: 偏移量，用于分页，默认0
            
        Returns:
            消息对象列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, source, title, content, timestamp, metadata
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(self._row_to_message(row))
            
            logger.debug(f"查询到 {len(messages)} 条消息")
            return messages
        except sqlite3.Error as e:
            logger.error(f"查询消息列表失败: {e}")
            return []
        finally:
            self._close_connection(conn)
    
    def search_messages(self, keyword: str, source: Optional[str] = None) -> List[Message]:
        """
        搜索消息
        
        在标题和内容中搜索关键词，可选按消息源过滤
        
        Args:
            keyword: 搜索关键词
            source: 可选的消息源过滤，None表示不过滤
            
        Returns:
            匹配的消息对象列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if source:
                # 按关键词和消息源搜索
                cursor.execute("""
                    SELECT id, source, title, content, timestamp, metadata
                    FROM messages
                    WHERE (title LIKE ? OR content LIKE ?) AND source = ?
                    ORDER BY timestamp DESC
                """, (f'%{keyword}%', f'%{keyword}%', source))
            else:
                # 仅按关键词搜索
                cursor.execute("""
                    SELECT id, source, title, content, timestamp, metadata
                    FROM messages
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY timestamp DESC
                """, (f'%{keyword}%', f'%{keyword}%'))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(self._row_to_message(row))
            
            logger.debug(f"搜索到 {len(messages)} 条匹配消息")
            return messages
        except sqlite3.Error as e:
            logger.error(f"搜索消息失败: {e}")
            return []
        finally:
            self._close_connection(conn)
    
    def delete_old_messages(self, days: int) -> int:
        """
        删除超过指定天数的旧消息
        
        Args:
            days: 保留天数，超过此天数的消息将被删除
            
        Returns:
            删除的消息数量
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff.timestamp()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM messages WHERE timestamp < ?", 
                (cutoff_timestamp,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"删除了 {deleted_count} 条超过 {days} 天的旧消息")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"删除旧消息失败: {e}")
            return 0
        finally:
            self._close_connection(conn)
    
    def clear_all_messages(self) -> bool:
        """
        清空所有消息
        
        Returns:
            清空成功返回True，失败返回False
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages")
            conn.commit()
            logger.info("已清空所有消息")
            
            # 发出信号通知数据变化
            self.messages_cleared.emit()
            self.data_changed.emit()
            
            return True
        except sqlite3.Error as e:
            logger.error(f"清空消息失败: {e}")
            return False
        finally:
            self._close_connection(conn)
    
    def get_message_count(self) -> int:
        """
        获取消息总数
        
        Returns:
            消息总数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"获取消息数量失败: {e}")
            return 0
        finally:
            self._close_connection(conn)
    
    def get_all_messages(self) -> List[Message]:
        """
        获取所有消息（按时间倒序）
        
        Returns:
            所有消息对象列表
        """
        return self.get_messages(limit=999999, offset=0)
    
    def delete_message(self, message_id: str) -> bool:
        """
        删除指定ID的消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            删除成功返回True，失败返回False
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            conn.commit()
            logger.debug(f"消息已删除: {message_id}")
            
            # 发出信号通知数据变化
            self.message_deleted.emit(message_id)
            self.data_changed.emit()
            
            return True
        except sqlite3.Error as e:
            logger.error(f"删除消息失败: {e}")
            return False
        finally:
            self._close_connection(conn)
    
    def _row_to_message(self, row: tuple) -> Message:
        """
        将数据库行转换为Message对象
        
        Args:
            row: 数据库查询结果行
            
        Returns:
            Message对象
        """
        return Message(
            id=row[0],
            source=row[1],
            title=row[2],
            content=row[3],
            timestamp=row[4],
            metadata=Message.metadata_from_json(row[5])
        )
