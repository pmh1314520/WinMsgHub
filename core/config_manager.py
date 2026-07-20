"""
配置管理器模块

作者：青云制作_彭明航
版权所有 (c) 2024
许可：要求二次开发必须开源并标明原作者，允许商用
"""

import json
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器
    
    负责加载、保存、获取和设置应用程序配置。
    配置以JSON格式存储在本地文件中。
    
    验证需求：9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(self, config_dir: Path):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置
        
        如果配置文件不存在或损坏，使用默认配置。
        
        Returns:
            配置字典
        """
        if not self.config_file.exists():
            logger.info("配置文件不存在，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # 检查文件是否为空
                if not content:
                    logger.warning("配置文件为空，使用默认配置")
                    return self._get_default_config()
                
                config = json.loads(content)
            logger.info(f"成功加载配置文件: {self.config_file}")
            return self._validate_config(config)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON解析失败: {e}")
            # 备份损坏的配置文件
            self._backup_corrupted_config()
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def reload_config(self):
        """重新加载配置文件（公共方法，用于热重载）"""
        self.config = self._load_config()
        logger.info("配置已重新加载")
    
    def _backup_corrupted_config(self):
        """备份损坏的配置文件"""
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix('.json.backup')
            try:
                import shutil
                shutil.copy2(self.config_file, backup_file)
                logger.info(f"已备份损坏的配置文件到: {backup_file}")
            except Exception as e:
                logger.error(f"备份配置文件失败: {e}")
    
    def _get_default_config(self) -> dict:
        """获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "version": "2.0.0",
            "message_sources": {
                "mqtt": [],
                "api": [],
                "webhook": [],
                "imap": [],
                "websocket": [],
                "rss": [],
                "file_monitor": [],
                "clipboard": []
            },
            "popup": {
                "width": 400,
                "height": 120,
                "opacity": 0.98,
                "background_color": "#2A3139",
                "background_image": None,
                "border_radius": 12,
                "animation_type": "slide",
                "animation_duration": 400,
                "animation_config": {
                    "slide_direction": "right_to_left",
                    "fade_start_opacity": 0.0,
                    "scale_start_size": 0.5,
                    "scale_center": "center",
                    "bounce_direction": "top_to_bottom",
                    "bounce_strength": 1.0,
                    "elastic_direction": "right_to_left",
                    "elastic_strength": 1.0
                },
                "display_duration": 5000,
                "position": "top_right",
                "sound_file": "resources/sounds/default.mp3",
                "sound_volume": 50,
                "auto_copy": False,
                "copy_rules": [],
                "max_popups": 5,
                "title_text_overflow": "ellipsis",
                "content_text_overflow": "wrap",
                "custom_font_file": None
            },
            "theme": {
                "mode": "system"
            },
            "filters": {
                "enabled": True,
                "rules": []
            },
            "system": {
                "auto_start": False,
                "minimize_to_tray": True,
                "start_minimized": False
            },
            "history": {
                "retention_days": 30
            }
        }
    
    def _validate_config(self, config: dict) -> dict:
        """验证配置数据的完整性和有效性
        
        如果配置无效，使用默认值修正。
        
        Args:
            config: 待验证的配置字典
            
        Returns:
            验证后的配置字典
        """
        default_config = self._get_default_config()
        validated_config = self._merge_with_defaults(config, default_config)
        
        # 验证特定字段的值范围
        try:
            # 验证弹窗尺寸
            if validated_config.get("popup", {}).get("width", 0) <= 0:
                logger.warning("弹窗宽度无效，使用默认值")
                validated_config["popup"]["width"] = default_config["popup"]["width"]
            
            if validated_config.get("popup", {}).get("height", 0) <= 0:
                logger.warning("弹窗高度无效，使用默认值")
                validated_config["popup"]["height"] = default_config["popup"]["height"]
            
            # 验证透明度范围 (0.0 - 1.0)
            opacity = validated_config.get("popup", {}).get("opacity", 1.0)
            if not (0.0 <= opacity <= 1.0):
                logger.warning(f"透明度值 {opacity} 超出范围，使用默认值")
                validated_config["popup"]["opacity"] = default_config["popup"]["opacity"]
            
            # 验证动画时长
            if validated_config.get("popup", {}).get("animation_duration", 0) < 0:
                logger.warning("动画时长无效，使用默认值")
                validated_config["popup"]["animation_duration"] = default_config["popup"]["animation_duration"]
            
            # 验证显示时长
            if validated_config.get("popup", {}).get("display_duration", 0) < 0:
                logger.warning("显示时长无效，使用默认值")
                validated_config["popup"]["display_duration"] = default_config["popup"]["display_duration"]
            
            # 验证端口号 - 兼容旧版字典格式与新版列表格式
            # 注意：默认配置中 message_sources 的各项是列表，
            # 不能从默认配置取端口默认值（此前这里会抛异常导致整个用户配置被重置）
            default_ports = {"mqtt": 8883, "webhook": 8080, "imap": 993}
            for source_type, default_port in default_ports.items():
                source_config = validated_config.get("message_sources", {}).get(source_type)
                if isinstance(source_config, dict) and "port" in source_config:
                    port = source_config.get("port", 0)
                    if not (isinstance(port, int) and 1 <= port <= 65535):
                        logger.warning(f"{source_type}端口号 {port} 无效，使用默认值 {default_port}")
                        source_config["port"] = default_port
                elif isinstance(source_config, list):
                    for item in source_config:
                        if isinstance(item, dict) and "port" in item:
                            port = item.get("port", 0)
                            if not (isinstance(port, int) and 1 <= port <= 65535):
                                logger.warning(f"{source_type}端口号 {port} 无效，使用默认值 {default_port}")
                                item["port"] = default_port
            
            # 验证历史保留天数
            retention_days = validated_config.get("history", {}).get("retention_days", 0)
            if retention_days < 0:
                logger.warning(f"历史保留天数 {retention_days} 无效，使用默认值")
                validated_config["history"]["retention_days"] = default_config["history"]["retention_days"]
            
        except Exception as e:
            import traceback
            logger.error(f"配置验证过程中出错: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return default_config
        
        return validated_config
    
    def _merge_with_defaults(self, config: dict, default: dict) -> dict:
        """将配置与默认配置合并，填充缺失的键
        
        Args:
            config: 用户配置
            default: 默认配置
            
        Returns:
            合并后的配置
        """
        result = default.copy()
        
        for key, value in config.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_with_defaults(value, result[key])
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def save_config(self):
        """保存配置到文件
        
        配置以JSON格式保存，使用UTF-8编码。
        采用"先写临时文件再原子替换"的方式，避免写入中途
        崩溃/断电导致配置文件损坏或清空。
        """
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # 先在主线程/调用线程序列化为字符串快照，
            # 避免json.dump边遍历边被其他线程修改导致的异常
            content = json.dumps(self.config, indent=2, ensure_ascii=False)
            
            # 先写临时文件，成功后原子替换正式文件
            import os
            temp_file = self.config_file.with_suffix('.json.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            
            os.replace(temp_file, self.config_file)
            
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        支持使用点号分隔的键路径，例如 "popup.width"
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值，当键不存在时返回
            
        Returns:
            配置值，如果不存在则返回默认值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项
        
        支持使用点号分隔的键路径，例如 "popup.width"
        设置后会自动保存配置。
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        
        Raises:
            TypeError: 当路径中间节点不是字典时（如试图往列表里按键名写入），
                       抛出明确异常而不是隐式破坏已有配置结构
        """
        keys = key.split('.')
        config = self.config
        
        # 导航到目标位置
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                raise TypeError(
                    f"无法设置配置项 '{key}'：路径 '{'.'.join(keys[:i + 1])}' "
                    f"处的值是 {type(config[k]).__name__} 而不是字典"
                )
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存配置
        self.save_config()
        
        logger.debug(f"配置项 '{key}' 已设置为: {value}")
    
    def get_all(self) -> dict:
        """获取完整的配置字典
        
        Returns:
            完整的配置字典
        """
        return self.config.copy()
    
    def reset_to_defaults(self):
        """重置配置为默认值"""
        self.config = self._get_default_config()
        self.save_config()
        logger.info("配置已重置为默认值")
