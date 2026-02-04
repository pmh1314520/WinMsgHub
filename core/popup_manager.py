"""
WinMsgHub (WinMsgHub) - 弹窗管理器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from typing import List
from data.models import Message
from ui.notification_popup import NotificationPopup, PopupStyle, PopupPosition
from core.config_manager import ConfigManager
from utils.logger import get_logger


logger = get_logger(__name__)


class PopupManager:
    """
    弹窗管理器
    
    验证需求：
    - 3.1: 显示通知弹窗
    - 3.4: 自动关闭定时器
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化弹窗管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config = config_manager
        self.active_popups: List[NotificationPopup] = []
        self.style = self._load_style()
        
        logger.info("弹窗管理器已初始化")
    
    def _load_style(self) -> PopupStyle:
        """从配置加载样式"""
        popup_config = self.config.get('popup', {})
        
        # 获取 max_popups 并记录日志
        max_popups_value = popup_config.get('max_popups', 5)
        logger.info(f"📖 _load_style: 从配置读取 max_popups = {max_popups_value}")
        
        # 转换position字符串为枚举
        position_str = popup_config.get('position', 'top_right')
        try:
            position = PopupPosition(position_str)
        except ValueError:
            position = PopupPosition.TOP_RIGHT
        
        # 加载动画配置
        animation_config = popup_config.get('animation_config', {})
        
        # 获取音量值并记录
        sound_volume_value = popup_config.get('sound_volume', 50)
        logger.info(f"📖 创建 PopupStyle，sound_volume 参数 = {sound_volume_value}")
        
        style = PopupStyle(
            width=popup_config.get('width', 400),
            height=popup_config.get('height', 120),
            opacity=popup_config.get('opacity', 0.98),
            background_color=popup_config.get('background_color', '#2A3139'),
            background_image=popup_config.get('background_image'),
            border_radius=popup_config.get('border_radius', 12),
            animation_type=popup_config.get('animation_type', 'slide'),
            animation_duration=popup_config.get('animation_duration', 400),
            animation_config=animation_config,
            display_duration=popup_config.get('display_duration', 5000),
            position=position,
            sound_file=popup_config.get('sound_file'),
            sound_volume=sound_volume_value,
            auto_copy=popup_config.get('auto_copy', False),
            copy_mode=popup_config.get('copy_mode', 'on_click'),
            copy_rules=popup_config.get('copy_rules', []),
            max_popups=max_popups_value,
            # 字体配置
            title_font_family=popup_config.get('title_font_family', 'Microsoft YaHei UI'),
            title_font_size=popup_config.get('title_font_size', 13),
            title_font_bold=popup_config.get('title_font_bold', True),
            title_color=popup_config.get('title_color', '#FFFFFF'),
            content_font_family=popup_config.get('content_font_family', 'Microsoft YaHei UI'),
            content_font_size=popup_config.get('content_font_size', 10),
            content_font_bold=popup_config.get('content_font_bold', False),
            content_color=popup_config.get('content_color', '#B8BFC6'),
            source_font_family=popup_config.get('source_font_family', 'Microsoft YaHei UI'),
            source_font_size=popup_config.get('source_font_size', 9),
            source_font_bold=popup_config.get('source_font_bold', False),
            source_color=popup_config.get('source_color', '#4A9EFF'),
            source_bg_color=popup_config.get('source_bg_color', 'rgba(74, 158, 255, 0.15)'),
            time_font_family=popup_config.get('time_font_family', 'Microsoft YaHei UI'),
            time_font_size=popup_config.get('time_font_size', 9),
            time_font_bold=popup_config.get('time_font_bold', False),
            time_color=popup_config.get('time_color', '#6C757D'),
            custom_font_file=popup_config.get('custom_font_file'),
            # 文本溢出处理
            title_text_overflow=popup_config.get('title_text_overflow', 'ellipsis'),
            content_text_overflow=popup_config.get('content_text_overflow', 'wrap'),
            # 最大行数
            title_max_lines=popup_config.get('title_max_lines', 2),
            content_max_lines=popup_config.get('content_max_lines', 5),
            # 文本对齐方式
            title_align=popup_config.get('title_align', 'left'),
            content_align=popup_config.get('content_align', 'left'),
            time_align=popup_config.get('time_align', 'left'),
            # 时间格式
            time_format=popup_config.get('time_format', '%H:%M:%S')
        )
        
        logger.info(f"📖 PopupStyle 创建完成，max_popups = {style.max_popups}")
        return style
    
    def show_notification(self, message: Message):
        """
        显示通知弹窗
        
        Args:
            message: 要显示的消息
        """
        try:
            # 强制重新加载配置，确保使用最新的配置
            if hasattr(self.config, 'reload_config'):
                self.config.reload_config()
                logger.debug("已重新加载配置")
            
            # 每次显示前重新加载样式，确保使用最新配置
            self.style = self._load_style()
            
            # 获取最大弹窗数量限制
            max_popups = self.style.max_popups
            logger.info(f"📊 准备显示弹窗: {message.id}, 当前数量: {len(self.active_popups)}, 最大限制: {max_popups}")
            
            # 在添加新弹窗之前，检查是否超过限制
            # 如果当前数量 >= 最大限制，需要先移除旧弹窗腾出空间
            while len(self.active_popups) >= max_popups:
                oldest_popup = self.active_popups[0]
                logger.info(f"🚫 PopupManager: 超过最大弹窗数量({max_popups})，移除最旧的弹窗: {oldest_popup.message.id}")
                self.active_popups.remove(oldest_popup)
            
            # 创建弹窗
            popup = NotificationPopup(message, self.style)
            
            # 给弹窗添加 PopupManager 的引用，让 PopupStackManager 可以访问
            popup._popup_manager_ref = self
            
            # 添加到活动弹窗列表（在 show() 之前）
            self.active_popups.append(popup)
            logger.info(f"➕ 弹窗已添加到列表: {message.id}, 当前数量: {len(self.active_popups)}")
            
            # 显示弹窗（PopupStackManager 会在内部处理数量限制）
            popup.show()
            
            # 设置自动关闭定时器（需求3.4）
            if self.style.display_duration > 0:
                popup.set_auto_close(self.style.display_duration)
            
            # 当弹窗关闭时从列表中移除
            popup.closed.connect(lambda: self._on_popup_closed(popup))
            
            logger.info(f"✅ 弹窗已显示: {message.id} (当前活动: {len(self.active_popups)})")
            
        except Exception as e:
            logger.error(f"显示弹窗失败: {e}", exc_info=True)
    
    def _on_popup_closed(self, popup: NotificationPopup):
        """弹窗关闭时的回调"""
        if popup in self.active_popups:
            self.active_popups.remove(popup)
            logger.debug(f"PopupManager: 弹窗已关闭并从列表移除: {popup.message.id}, 剩余: {len(self.active_popups)}")
        else:
            logger.debug(f"PopupManager: 弹窗已关闭（已不在列表中）: {popup.message.id}")
    
    def close_all(self):
        """关闭所有活动弹窗"""
        for popup in self.active_popups[:]:
            popup.close()
        self.active_popups.clear()
        logger.info("所有弹窗已关闭")
    
    def get_active_count(self) -> int:
        """获取活动弹窗数量"""
        return len(self.active_popups)
