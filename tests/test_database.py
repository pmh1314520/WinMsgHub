"""
WinMsgHub (WinMsgHub) - 数据库单元测试
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import pytest
import time
from pathlib import Path
from data.models import Message
from data.database import Database


class TestMessage:
    """测试Message数据模型"""
    
    def test_message_creation(self):
        """测试消息对象创建"""
        msg = Message(
            id="test-1",
            source="MQTT",
            title="测试标题",
            content="测试内容",
            timestamp=time.time(),
            metadata={"key": "value"}
        )
        
        assert msg.id == "test-1"
        assert msg.source == "MQTT"
        assert msg.title == "测试标题"
        assert msg.content == "测试内容"
        assert msg.metadata == {"key": "value"}
    
    def test_message_to_dict(self):
        """测试消息转换为字典"""
        msg = Message(
            id="test-1",
            source="MQTT",
            title="测试标题",
            content="测试内容",
            timestamp=1234567890.0,
            metadata={"key": "value"}
        )
        
        data = msg.to_dict()
        assert data['id'] == "test-1"
        assert data['source'] == "MQTT"
        assert data['title'] == "测试标题"
        assert data['content'] == "测试内容"
        assert data['timestamp'] == 1234567890.0
        assert data['metadata'] == {"key": "value"}
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        data = {
            'id': "test-1",
            'source': "MQTT",
            'title': "测试标题",
            'content': "测试内容",
            'timestamp': 1234567890.0,
            'metadata': {"key": "value"}
        }
        
        msg = Message.from_dict(data)
        assert msg.id == "test-1"
        assert msg.source == "MQTT"
        assert msg.title == "测试标题"
        assert msg.content == "测试内容"
        assert msg.timestamp == 1234567890.0
        assert msg.metadata == {"key": "value"}
    
    def test_message_metadata_json(self):
        """测试metadata的JSON序列化"""
        msg = Message(
            id="test-1",
            source="MQTT",
            title="测试",
            content="内容",
            timestamp=time.time(),
            metadata={"key": "value", "number": 123}
        )
        
        json_str = msg.metadata_to_json()
        assert isinstance(json_str, str)
        
        parsed = Message.metadata_from_json(json_str)
        assert parsed == {"key": "value", "number": 123}
    
    def test_message_empty_metadata(self):
        """测试空metadata的处理"""
        msg = Message(
            id="test-1",
            source="MQTT",
            title="测试",
            content="内容",
            timestamp=time.time()
        )
        
        assert msg.metadata == {}
        json_str = msg.metadata_to_json()
        assert json_str == "{}"


class TestDatabase:
    """测试Database类"""
    
    @pytest.fixture
    def db(self):
        """创建内存数据库用于测试"""
        return Database(":memory:")
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return Message(
            id="test-msg-1",
            source="MQTT",
            title="测试消息",
            content="这是一条测试消息",
            timestamp=time.time(),
            metadata={"priority": "high"}
        )
    
    def test_database_initialization(self, db):
        """测试数据库初始化"""
        assert db is not None
        # 验证表已创建
        count = db.get_message_count()
        assert count == 0
    
    def test_save_message(self, db, sample_message):
        """测试保存消息"""
        result = db.save_message(sample_message)
        assert result is True
        
        # 验证消息已保存
        count = db.get_message_count()
        assert count == 1
    
    def test_get_message_by_id(self, db, sample_message):
        """测试根据ID获取消息"""
        db.save_message(sample_message)
        
        retrieved = db.get_message_by_id(sample_message.id)
        assert retrieved is not None
        assert retrieved.id == sample_message.id
        assert retrieved.source == sample_message.source
        assert retrieved.title == sample_message.title
        assert retrieved.content == sample_message.content
        assert abs(retrieved.timestamp - sample_message.timestamp) < 0.001
        assert retrieved.metadata == sample_message.metadata
    
    def test_get_message_by_id_not_found(self, db):
        """测试获取不存在的消息"""
        retrieved = db.get_message_by_id("non-existent-id")
        assert retrieved is None
    
    def test_get_messages(self, db):
        """测试获取消息列表"""
        # 保存多条消息
        for i in range(5):
            msg = Message(
                id=f"msg-{i}",
                source="MQTT",
                title=f"消息 {i}",
                content=f"内容 {i}",
                timestamp=time.time() + i,
                metadata={}
            )
            db.save_message(msg)
        
        messages = db.get_messages(limit=10)
        assert len(messages) == 5
        
        # 验证按时间倒序排列（最新的在前）
        for i in range(len(messages) - 1):
            assert messages[i].timestamp >= messages[i + 1].timestamp
    
    def test_get_messages_with_limit(self, db):
        """测试带限制的消息列表查询"""
        # 保存10条消息
        for i in range(10):
            msg = Message(
                id=f"msg-{i}",
                source="MQTT",
                title=f"消息 {i}",
                content=f"内容 {i}",
                timestamp=time.time() + i,
                metadata={}
            )
            db.save_message(msg)
        
        messages = db.get_messages(limit=5)
        assert len(messages) == 5
    
    def test_get_messages_with_offset(self, db):
        """测试带偏移的消息列表查询（分页）"""
        # 保存10条消息
        for i in range(10):
            msg = Message(
                id=f"msg-{i}",
                source="MQTT",
                title=f"消息 {i}",
                content=f"内容 {i}",
                timestamp=time.time() + i,
                metadata={}
            )
            db.save_message(msg)
        
        # 获取第一页
        page1 = db.get_messages(limit=5, offset=0)
        assert len(page1) == 5
        
        # 获取第二页
        page2 = db.get_messages(limit=5, offset=5)
        assert len(page2) == 5
        
        # 验证两页不重复
        page1_ids = {msg.id for msg in page1}
        page2_ids = {msg.id for msg in page2}
        assert len(page1_ids & page2_ids) == 0
    
    def test_search_messages_by_title(self, db):
        """测试按标题搜索消息"""
        messages = [
            Message("1", "MQTT", "重要通知", "内容1", time.time(), {}),
            Message("2", "MQTT", "普通消息", "内容2", time.time(), {}),
            Message("3", "MQTT", "重要提醒", "内容3", time.time(), {}),
        ]
        
        for msg in messages:
            db.save_message(msg)
        
        results = db.search_messages("重要")
        assert len(results) == 2
        assert all("重要" in msg.title for msg in results)
    
    def test_search_messages_by_content(self, db):
        """测试按内容搜索消息"""
        messages = [
            Message("1", "MQTT", "标题1", "这是紧急内容", time.time(), {}),
            Message("2", "MQTT", "标题2", "普通内容", time.time(), {}),
            Message("3", "MQTT", "标题3", "紧急通知内容", time.time(), {}),
        ]
        
        for msg in messages:
            db.save_message(msg)
        
        results = db.search_messages("紧急")
        assert len(results) == 2
        assert all("紧急" in msg.content for msg in results)
    
    def test_search_messages_by_source(self, db):
        """测试按消息源搜索"""
        messages = [
            Message("1", "MQTT", "消息1", "内容1", time.time(), {}),
            Message("2", "API", "消息2", "内容2", time.time(), {}),
            Message("3", "MQTT", "消息3", "内容3", time.time(), {}),
        ]
        
        for msg in messages:
            db.save_message(msg)
        
        results = db.search_messages("消息", source="MQTT")
        assert len(results) == 2
        assert all(msg.source == "MQTT" for msg in results)
    
    def test_search_messages_no_results(self, db, sample_message):
        """测试搜索无结果的情况"""
        db.save_message(sample_message)
        
        results = db.search_messages("不存在的关键词")
        assert len(results) == 0
    
    def test_delete_old_messages(self, db):
        """测试删除旧消息"""
        now = time.time()
        
        # 创建不同时间的消息
        messages = [
            Message("1", "MQTT", "旧消息1", "内容", now - 40 * 86400, {}),  # 40天前
            Message("2", "MQTT", "旧消息2", "内容", now - 35 * 86400, {}),  # 35天前
            Message("3", "MQTT", "新消息1", "内容", now - 20 * 86400, {}),  # 20天前
            Message("4", "MQTT", "新消息2", "内容", now - 10 * 86400, {}),  # 10天前
            Message("5", "MQTT", "新消息3", "内容", now, {}),              # 现在
        ]
        
        for msg in messages:
            db.save_message(msg)
        
        # 删除30天前的消息
        deleted_count = db.delete_old_messages(30)
        assert deleted_count == 2
        
        # 验证剩余消息
        remaining = db.get_messages(limit=100)
        assert len(remaining) == 3
        assert all(msg.timestamp > now - 30 * 86400 for msg in remaining)
    
    def test_clear_all_messages(self, db):
        """测试清空所有消息"""
        # 保存多条消息
        for i in range(5):
            msg = Message(
                id=f"msg-{i}",
                source="MQTT",
                title=f"消息 {i}",
                content=f"内容 {i}",
                timestamp=time.time(),
                metadata={}
            )
            db.save_message(msg)
        
        assert db.get_message_count() == 5
        
        result = db.clear_all_messages()
        assert result is True
        assert db.get_message_count() == 0
    
    def test_get_message_count(self, db):
        """测试获取消息数量"""
        assert db.get_message_count() == 0
        
        # 保存3条消息
        for i in range(3):
            msg = Message(
                id=f"msg-{i}",
                source="MQTT",
                title=f"消息 {i}",
                content=f"内容 {i}",
                timestamp=time.time(),
                metadata={}
            )
            db.save_message(msg)
        
        assert db.get_message_count() == 3
    
    def test_save_message_with_same_id_replaces(self, db):
        """测试保存相同ID的消息会替换原消息"""
        msg1 = Message(
            id="same-id",
            source="MQTT",
            title="原标题",
            content="原内容",
            timestamp=time.time(),
            metadata={}
        )
        db.save_message(msg1)
        
        msg2 = Message(
            id="same-id",
            source="API",
            title="新标题",
            content="新内容",
            timestamp=time.time(),
            metadata={"updated": True}
        )
        db.save_message(msg2)
        
        # 应该只有一条消息
        assert db.get_message_count() == 1
        
        # 获取消息，应该是新的内容
        retrieved = db.get_message_by_id("same-id")
        assert retrieved.title == "新标题"
        assert retrieved.content == "新内容"
        assert retrieved.source == "API"


# ============================================================================
# 基于属性的测试 (Property-Based Tests)
# ============================================================================

from hypothesis import given, strategies as st, settings


class TestMessageStorageProperties:
    """
    基于属性的测试 - 消息存储
    
    Feature: WinMsgHub-desktop-app
    """
    
    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        message_id=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=50),
        title=st.text(min_size=1, max_size=200),
        content=st.text(min_size=1, max_size=1000),
        timestamp=st.floats(min_value=0, max_value=2e9, allow_nan=False, allow_infinity=False),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            max_size=10
        )
    )
    def test_property_message_storage_roundtrip(
        self, message_id, source, title, content, timestamp, metadata
    ):
        """
        属性 4：消息存储往返
        
        **Validates: Requirements 2.3, 10.1**
        
        对于任何消息，保存到数据库后通过ID查询，应该得到内容相同的消息对象。
        
        这个属性验证了消息存储的完整性和一致性：
        - 所有消息字段都能正确保存
        - 查询返回的消息与原始消息内容相同
        - 支持各种类型的metadata值
        """
        # 创建原始消息
        original_message = Message(
            id=message_id,
            source=source,
            title=title,
            content=content,
            timestamp=timestamp,
            metadata=metadata
        )
        
        # 使用内存数据库进行测试
        db = Database(":memory:")
        
        # 保存消息到数据库
        save_result = db.save_message(original_message)
        assert save_result is True, "消息保存应该成功"
        
        # 通过ID查询消息
        retrieved_message = db.get_message_by_id(message_id)
        
        # 验证往返一致性
        assert retrieved_message is not None, "应该能够查询到保存的消息"
        assert retrieved_message.id == original_message.id, "消息ID应该相同"
        assert retrieved_message.source == original_message.source, "消息来源应该相同"
        assert retrieved_message.title == original_message.title, "消息标题应该相同"
        assert retrieved_message.content == original_message.content, "消息内容应该相同"
        
        # 时间戳可能有微小的浮点误差，使用容差比较
        assert abs(retrieved_message.timestamp - original_message.timestamp) < 0.001, \
            "消息时间戳应该相同（允许微小浮点误差）"
        
        # 验证metadata完整性
        assert retrieved_message.metadata == original_message.metadata, \
            "消息元数据应该相同"
