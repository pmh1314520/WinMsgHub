"""
WinMsgHub (WinMsgHub) - 消息过滤引擎
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple
from data.models import Message
from utils.logger import get_logger


logger = get_logger(__name__)


class FilterAction(Enum):
    """过滤动作"""
    ALLOW = "allow"  # 允许显示
    BLOCK = "block"  # 阻止显示
    BLOCK_BUT_SAVE = "block_but_save"  # 阻止显示但保存到历史


class FilterCondition(Enum):
    """过滤条件类型"""
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EQUALS = "equals"
    REGEX = "regex"


@dataclass
class FilterRule:
    """过滤规则
    
    Attributes:
        enabled: 是否启用此规则
        field: 要过滤的字段（"title", "content", "source"）
        condition: 过滤条件类型
        value: 过滤值
        action: 动作（"allow"允许, "block"阻止, "block_but_save"阻止但保存）
        save_to_history: 是否保存到历史记录（当action为block时有效）
    """
    enabled: bool
    field: str
    condition: FilterCondition
    value: str
    action: str
    save_to_history: bool = False  # 新增字段


class FilterEngine:
    """
    消息过滤引擎
    
    根据配置的过滤规则决定是否处理消息。
    
    验证需求：2.4 - 仅处理符合过滤条件的消息
    """
    
    def __init__(self, rules: List[FilterRule]):
        """
        初始化过滤引擎
        
        Args:
            rules: 过滤规则列表
        """
        self.rules = rules
        logger.info(f"过滤引擎已初始化，共 {len(rules)} 条规则")
    
    def should_process(self, message: Message) -> Tuple[bool, bool]:
        """
        判断消息是否应该被处理
        
        Args:
            message: 要判断的消息
            
        Returns:
            Tuple[bool, bool]: (是否显示弹窗, 是否保存到历史记录)
        """
        # 如果没有规则，默认允许所有消息
        if not self.rules:
            return (True, True)
        
        # 检查每条规则
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if self._match_rule(message, rule):
                # 如果匹配到规则
                if rule.action == "allow":
                    logger.debug(f"消息 {message.id} 匹配允许规则")
                    return (True, True)
                elif rule.action == "block":
                    logger.debug(f"消息 {message.id} 匹配阻止规则")
                    # 检查是否仍然保存到历史记录
                    save_to_history = rule.save_to_history
                    return (False, save_to_history)
        
        # 默认允许（如果没有匹配到任何规则）
        return (True, True)
    
    def _match_rule(self, message: Message, rule: FilterRule) -> bool:
        """
        判断消息是否匹配规则
        
        Args:
            message: 消息对象
            rule: 过滤规则
            
        Returns:
            bool: 如果匹配返回True，否则返回False
        """
        # 获取要检查的字段值
        field_value = getattr(message, rule.field, "")
        
        # 根据条件类型进行匹配
        if rule.condition == FilterCondition.CONTAINS:
            return rule.value in field_value
        elif rule.condition == FilterCondition.NOT_CONTAINS:
            return rule.value not in field_value
        elif rule.condition == FilterCondition.EQUALS:
            return rule.value == field_value
        elif rule.condition == FilterCondition.REGEX:
            try:
                return bool(re.search(rule.value, field_value))
            except re.error as e:
                logger.error(f"正则表达式错误: {e}")
                return False
        
        return False
    
    def add_rule(self, rule: FilterRule):
        """添加过滤规则"""
        self.rules.append(rule)
        logger.info(f"已添加过滤规则: {rule.field} {rule.condition.value} {rule.value}")
    
    def remove_rule(self, index: int):
        """删除过滤规则"""
        if 0 <= index < len(self.rules):
            removed = self.rules.pop(index)
            logger.info(f"已删除过滤规则: {removed.field} {removed.condition.value} {removed.value}")
    
    def clear_rules(self):
        """清空所有规则"""
        self.rules.clear()
        logger.info("已清空所有过滤规则")
    
    def get_rules(self) -> List[FilterRule]:
        """获取所有规则"""
        return self.rules.copy()
