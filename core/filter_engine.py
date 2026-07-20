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
        case_sensitive: 是否区分大小写
    """
    enabled: bool
    field: str
    condition: FilterCondition
    value: str
    action: str
    save_to_history: bool = False  # 新增字段
    case_sensitive: bool = False  # 是否区分大小写


def rules_from_config(rule_dicts: list) -> List[FilterRule]:
    """将配置中的规则字典列表转换为FilterRule列表
    
    这是页面配置格式与过滤引擎之间的唯一转换入口，
    main.py 和 filter_page.py 都必须使用它，确保行为一致。
    
    Args:
        rule_dicts: 配置中的规则字典列表
        
    Returns:
        FilterRule列表（仅包含启用的规则）
    """
    condition_map = {
        'contains': FilterCondition.CONTAINS,
        'not_contains': FilterCondition.NOT_CONTAINS,
        'source': FilterCondition.EQUALS,
        'regex': FilterCondition.REGEX
    }
    
    rules: List[FilterRule] = []
    for rule_data in rule_dicts or []:
        if not rule_data.get('enabled', True):
            continue
        
        rule_type = rule_data.get('type', 'contains')
        condition = condition_map.get(rule_type, FilterCondition.CONTAINS)
        
        field = rule_data.get('field', 'content')
        # "来源匹配"类型的规则始终检查source字段
        if rule_type == 'source':
            field = 'source'
        
        keyword = rule_data.get('keyword', '')
        action = 'block' if rule_data.get('action_block', True) else 'allow'
        save_to_history = rule_data.get('action_save', False)
        case_sensitive = rule_data.get('case_sensitive', False)
        
        # "标题和内容"需要展开为两条规则
        fields = ['title', 'content'] if field == 'both' else [field]
        for f in fields:
            rules.append(FilterRule(
                enabled=True,
                field=f,
                condition=condition,
                value=keyword,
                action=action,
                save_to_history=save_to_history,
                case_sensitive=case_sensitive
            ))
    
    return rules


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
        if field_value is None:
            field_value = ""
        field_value = str(field_value)
        rule_value = rule.value or ""
        
        # 大小写不敏感时统一转为小写比较（正则使用IGNORECASE标志）
        if not rule.case_sensitive and rule.condition != FilterCondition.REGEX:
            field_value = field_value.lower()
            rule_value = rule_value.lower()
        
        # 根据条件类型进行匹配
        if rule.condition == FilterCondition.CONTAINS:
            return rule_value in field_value
        elif rule.condition == FilterCondition.NOT_CONTAINS:
            return rule_value not in field_value
        elif rule.condition == FilterCondition.EQUALS:
            return rule_value == field_value
        elif rule.condition == FilterCondition.REGEX:
            try:
                flags = 0 if rule.case_sensitive else re.IGNORECASE
                return bool(re.search(rule.value, field_value, flags))
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
    
    def set_rules(self, rules: List[FilterRule]):
        """原子替换所有规则
        
        直接整体替换列表引用，避免在消息线程遍历规则时
        出现"清空后逐条添加"导致的中间状态。
        """
        self.rules = list(rules)
        logger.info(f"过滤规则已更新，共 {len(self.rules)} 条")
    
    def get_rules(self) -> List[FilterRule]:
        """获取所有规则"""
        return self.rules.copy()
