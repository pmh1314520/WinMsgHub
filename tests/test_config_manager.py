"""
WinMsgHub (WinMsgHub) - 配置管理器测试
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import pytest
import json
from pathlib import Path
from core.config_manager import ConfigManager


class TestConfigManager:
    """测试ConfigManager类"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """创建临时配置目录"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """创建ConfigManager实例"""
        return ConfigManager(temp_config_dir)
    
    def test_config_manager_initialization(self, config_manager):
        """测试配置管理器初始化"""
        assert config_manager is not None
        assert config_manager.config is not None
        assert isinstance(config_manager.config, dict)
    
    def test_default_config_structure(self, config_manager):
        """测试默认配置结构"""
        config = config_manager.config
        
        # 验证顶层键存在
        assert "version" in config
        assert "message_sources" in config
        assert "popup" in config
        assert "theme" in config
        assert "filters" in config
        assert "startup" in config
        assert "history" in config
    
    def test_get_simple_key(self, config_manager):
        """测试获取简单配置项"""
        version = config_manager.get("version")
        assert version == "1.0.0"
    
    def test_get_nested_key(self, config_manager):
        """测试获取嵌套配置项"""
        broker = config_manager.get("message_sources.mqtt.broker")
        assert broker == "WinMsgHub.pmhs.top/mqtt"
        
        width = config_manager.get("popup.width")
        assert width == 350
    
    def test_get_nonexistent_key_returns_default(self, config_manager):
        """测试获取不存在的键返回默认值"""
        value = config_manager.get("nonexistent.key", "default_value")
        assert value == "default_value"
    
    def test_get_nonexistent_key_returns_none(self, config_manager):
        """测试获取不存在的键返回None"""
        value = config_manager.get("nonexistent.key")
        assert value is None
    
    def test_set_simple_key(self, config_manager):
        """测试设置简单配置项"""
        config_manager.set("version", "2.0.0")
        assert config_manager.get("version") == "2.0.0"
    
    def test_set_nested_key(self, config_manager):
        """测试设置嵌套配置项"""
        config_manager.set("popup.width", 400)
        assert config_manager.get("popup.width") == 400
        
        config_manager.set("message_sources.mqtt.port", 1883)
        assert config_manager.get("message_sources.mqtt.port") == 1883
    
    def test_set_creates_nested_structure(self, config_manager):
        """测试设置配置项会创建嵌套结构"""
        config_manager.set("new.nested.key", "value")
        assert config_manager.get("new.nested.key") == "value"
    
    def test_save_and_load_config(self, temp_config_dir):
        """测试保存和加载配置"""
        # 创建配置管理器并设置值
        config1 = ConfigManager(temp_config_dir)
        config1.set("popup.width", 500)
        config1.set("theme.mode", "dark")
        
        # 创建新的配置管理器实例（模拟重启）
        config2 = ConfigManager(temp_config_dir)
        
        # 验证配置已持久化
        assert config2.get("popup.width") == 500
        assert config2.get("theme.mode") == "dark"
    
    def test_config_file_is_valid_json(self, config_manager):
        """测试配置文件是有效的JSON格式"""
        config_manager.save_config()
        
        # 读取配置文件并验证JSON格式
        with open(config_manager.config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            parsed = json.loads(content)
        
        assert isinstance(parsed, dict)
        assert "version" in parsed
    
    def test_corrupted_config_file_uses_defaults(self, temp_config_dir):
        """测试损坏的配置文件使用默认配置"""
        # 创建损坏的配置文件
        config_file = temp_config_dir / "config.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json content }")
        
        # 创建配置管理器
        config_manager = ConfigManager(temp_config_dir)
        
        # 应该使用默认配置
        assert config_manager.get("version") == "1.0.0"
        assert config_manager.get("popup.width") == 350
        
        # 验证备份文件已创建
        backup_file = config_file.with_suffix('.json.backup')
        assert backup_file.exists()
    
    def test_missing_config_file_creates_default(self, temp_config_dir):
        """测试缺失的配置文件创建默认配置"""
        config_manager = ConfigManager(temp_config_dir)
        
        # 应该使用默认配置
        assert config_manager.get("version") == "1.0.0"
        assert config_manager.get("message_sources.mqtt.broker") == "WinMsgHub.pmhs.top/mqtt"
    
    def test_validate_popup_width_negative(self, config_manager):
        """测试验证弹窗宽度为负数时使用默认值"""
        config_manager.config["popup"]["width"] = -100
        validated = config_manager._validate_config(config_manager.config)
        assert validated["popup"]["width"] == 350  # 默认值
    
    def test_validate_popup_height_zero(self, config_manager):
        """测试验证弹窗高度为0时使用默认值"""
        config_manager.config["popup"]["height"] = 0
        validated = config_manager._validate_config(config_manager.config)
        assert validated["popup"]["height"] == 100  # 默认值
    
    def test_validate_opacity_out_of_range(self, config_manager):
        """测试验证透明度超出范围时使用默认值"""
        # 测试大于1.0
        config_manager.config["popup"]["opacity"] = 1.5
        validated = config_manager._validate_config(config_manager.config)
        assert validated["popup"]["opacity"] == 0.95  # 默认值
        
        # 测试小于0.0
        config_manager.config["popup"]["opacity"] = -0.5
        validated = config_manager._validate_config(config_manager.config)
        assert validated["popup"]["opacity"] == 0.95  # 默认值
    
    def test_validate_port_out_of_range(self, config_manager):
        """测试验证端口号超出范围时使用默认值"""
        # 测试MQTT端口
        config_manager.config["message_sources"]["mqtt"]["port"] = 70000
        validated = config_manager._validate_config(config_manager.config)
        assert validated["message_sources"]["mqtt"]["port"] == 8883  # 默认值
        
        # 测试端口为0
        config_manager.config["message_sources"]["mqtt"]["port"] = 0
        validated = config_manager._validate_config(config_manager.config)
        assert validated["message_sources"]["mqtt"]["port"] == 8883  # 默认值
    
    def test_validate_negative_retention_days(self, config_manager):
        """测试验证负数保留天数时使用默认值"""
        config_manager.config["history"]["retention_days"] = -10
        validated = config_manager._validate_config(config_manager.config)
        assert validated["history"]["retention_days"] == 30  # 默认值
    
    def test_get_all_returns_copy(self, config_manager):
        """测试get_all返回配置的副本"""
        config_copy = config_manager.get_all()
        
        # 修改副本不应影响原配置
        config_copy["version"] = "999.0.0"
        assert config_manager.get("version") == "1.0.0"
    
    def test_reset_to_defaults(self, config_manager):
        """测试重置配置为默认值"""
        # 修改一些配置
        config_manager.set("popup.width", 500)
        config_manager.set("theme.mode", "dark")
        
        # 重置
        config_manager.reset_to_defaults()
        
        # 验证已恢复默认值
        assert config_manager.get("popup.width") == 350
        assert config_manager.get("theme.mode") == "system"
    
    def test_merge_with_defaults_fills_missing_keys(self, config_manager):
        """测试合并配置会填充缺失的键"""
        partial_config = {
            "version": "1.0.0",
            "popup": {
                "width": 400
            }
        }
        
        default_config = config_manager._get_default_config()
        merged = config_manager._merge_with_defaults(partial_config, default_config)
        
        # 验证缺失的键已填充
        assert "message_sources" in merged
        assert "theme" in merged
        assert merged["popup"]["width"] == 400  # 保留用户值
        assert "height" in merged["popup"]  # 填充默认值



# ============================================================================
# 基于属性的测试 (Property-Based Tests)
# ============================================================================

from hypothesis import given, strategies as st, settings, assume


class TestConfigManagerProperties:
    """
    基于属性的测试 - 配置管理
    
    Feature: WinMsgHub-desktop-app
    """
    
    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        key=st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'), 
                whitelist_characters='._'
            )
        ),
        value=st.one_of(
            st.text(max_size=200),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
            st.booleans()
        )
    )
    def test_property_config_persistence_roundtrip(self, key, value):
        """
        属性 12：配置持久化往返
        
        **Validates: Requirements 9.1, 9.2**
        
        对于任何配置键值对，通过ConfigManager设置并保存后，
        重新加载配置文件，应该能够获取到相同的值。
        
        这个属性验证了配置持久化的完整性：
        - 所有类型的值都能正确保存
        - 重新加载后能获取相同的值
        - 配置在应用重启后保持一致
        """
        import tempfile
        
        # 过滤掉可能导致问题的键名
        assume('.' in key or key.isalnum())  # 确保键名有效
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config_test"
            
            # 创建配置管理器并设置值
            config1 = ConfigManager(config_dir)
            config1.set(key, value)
            
            # 创建新的配置管理器实例（模拟重启）
            config2 = ConfigManager(config_dir)
            
            # 验证往返一致性
            retrieved_value = config2.get(key)
            assert retrieved_value == value, \
                f"配置值应该保持一致: 期望 {value}, 实际 {retrieved_value}"
    
    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        config_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000, max_value=1000),
                st.floats(allow_nan=False, allow_infinity=False, min_value=-1e3, max_value=1e3),
                st.booleans(),
                st.none()
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_property_config_json_format_validity(self, config_data):
        """
        属性 13：配置JSON格式有效性
        
        **Validates: Requirements 9.4**
        
        对于任何配置对象，保存到文件后，该文件内容应该是有效的JSON格式
        且能够被json.loads()成功解析。
        
        这个属性验证了配置文件的格式正确性：
        - 保存的文件是有效的JSON
        - 文件可以被标准JSON解析器解析
        - 不会产生格式错误
        """
        import tempfile
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config_json_test"
            config_manager = ConfigManager(config_dir)
            
            # 设置配置数据
            for key, value in config_data.items():
                config_manager.set(key, value)
            
            # 验证配置文件是有效的JSON
            with open(config_manager.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 应该能够成功解析JSON
            try:
                parsed = json.loads(content)
                assert isinstance(parsed, dict), "解析后的配置应该是字典类型"
            except json.JSONDecodeError as e:
                pytest.fail(f"配置文件不是有效的JSON格式: {e}")
    
    @pytest.mark.property
    @settings(max_examples=100)
    @given(
        width=st.integers(min_value=-1000, max_value=0),
        height=st.integers(min_value=-1000, max_value=0),
        opacity=st.one_of(
            st.floats(min_value=-10.0, max_value=-0.01, allow_nan=False, allow_infinity=False),
            st.floats(min_value=1.01, max_value=10.0, allow_nan=False, allow_infinity=False)
        ),
        port=st.one_of(
            st.integers(min_value=-1000, max_value=0),
            st.integers(min_value=65536, max_value=100000)
        ),
        retention_days=st.integers(min_value=-1000, max_value=-1)
    )
    def test_property_config_validation_rejects_invalid_data(
        self, width, height, opacity, port, retention_days
    ):
        """
        属性 14：配置验证拒绝无效数据
        
        **Validates: Requirements 9.5**
        
        对于任何包含无效值的配置（如负数的宽度、超出范围的透明度），
        配置验证应该拒绝该配置或将其修正为有效值。
        
        这个属性验证了配置验证的健壮性：
        - 无效的数值会被检测
        - 无效值会被修正为默认值
        - 系统不会使用无效配置
        """
        import tempfile
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config_validation_test"
            config_manager = ConfigManager(config_dir)
            
            # 创建包含无效值的配置
            invalid_config = {
                "version": "1.0.0",
                "popup": {
                    "width": width,
                    "height": height,
                    "opacity": opacity,
                    "animation_duration": 300,
                    "display_duration": 5000
                },
                "message_sources": {
                    "mqtt": {
                        "port": port
                    }
                },
                "history": {
                    "retention_days": retention_days
                }
            }
            
            # 验证配置
            validated = config_manager._validate_config(invalid_config)
            
            # 验证无效值已被修正
            assert validated["popup"]["width"] > 0, "宽度应该被修正为正数"
            assert validated["popup"]["height"] > 0, "高度应该被修正为正数"
            assert 0.0 <= validated["popup"]["opacity"] <= 1.0, "透明度应该在0-1范围内"
            assert 1 <= validated["message_sources"]["mqtt"]["port"] <= 65535, "端口号应该在有效范围内"
            assert validated["history"]["retention_days"] >= 0, "保留天数应该是非负数"
