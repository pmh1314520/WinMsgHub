"""
WinMsgHub - 过滤规则页面
作者：青云制作_彭明航
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QListWidget, QListWidgetItem, QPushButton,
    QDialog, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QTextEdit, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from ui.svg_icons import SvgIcon


class FilterRuleDialog(QDialog):
    """过滤规则编辑对话框"""
    
    def __init__(self, rule=None, parent=None):
        super().__init__(parent)
        self.rule = rule or {}
        self._setup_ui()
        if rule:
            self._load_rule()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("编辑过滤规则" if self.rule else "添加过滤规则")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 规则名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("规则名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 过滤测试消息")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 规则类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("规则类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["包含关键词", "不包含关键词", "来源匹配", "正则表达式"])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 匹配条件
        condition_group = QGroupBox("匹配条件")
        condition_layout = QVBoxLayout()
        condition_group.setLayout(condition_layout)
        
        # 关键词
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("关键词:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入关键词或正则表达式")
        keyword_layout.addWidget(self.keyword_input)
        condition_layout.addLayout(keyword_layout)
        
        # 匹配字段
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("匹配字段:"))
        self.field_combo = QComboBox()
        self.field_combo.addItems(["标题", "内容", "标题和内容", "来源"])
        field_layout.addWidget(self.field_combo)
        field_layout.addStretch()
        condition_layout.addLayout(field_layout)
        
        # 大小写敏感
        self.case_sensitive = QCheckBox("区分大小写")
        condition_layout.addWidget(self.case_sensitive)
        
        layout.addWidget(condition_group)
        
        # 动作
        action_group = QGroupBox("执行动作")
        action_layout = QVBoxLayout()
        action_group.setLayout(action_layout)
        
        self.action_block = QCheckBox("阻止显示（不显示弹窗）")
        self.action_block.setChecked(True)
        action_layout.addWidget(self.action_block)
        
        self.action_save = QCheckBox("仍然保存到历史记录")
        action_layout.addWidget(self.action_save)
        
        layout.addWidget(action_group)
        
        # 启用状态
        self.enabled_check = QCheckBox("启用此规则")
        self.enabled_check.setChecked(True)
        self.enabled_check.setStyleSheet("font-weight: 500;")
        layout.addWidget(self.enabled_check)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("secondary", "true")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _load_rule(self):
        """加载规则数据"""
        self.name_input.setText(self.rule.get("name", ""))
        
        rule_type = self.rule.get("type", "contains")
        type_map = {"contains": 0, "not_contains": 1, "source": 2, "regex": 3}
        self.type_combo.setCurrentIndex(type_map.get(rule_type, 0))
        
        self.keyword_input.setText(self.rule.get("keyword", ""))
        
        field = self.rule.get("field", "content")
        field_map = {"title": 0, "content": 1, "both": 2, "source": 3}
        self.field_combo.setCurrentIndex(field_map.get(field, 1))
        
        self.case_sensitive.setChecked(self.rule.get("case_sensitive", False))
        self.action_block.setChecked(self.rule.get("action_block", True))
        self.action_save.setChecked(self.rule.get("action_save", False))
        self.enabled_check.setChecked(self.rule.get("enabled", True))
    
    def get_rule(self) -> dict:
        """获取规则数据"""
        type_map = ["contains", "not_contains", "source", "regex"]
        field_map = ["title", "content", "both", "source"]
        
        return {
            "name": self.name_input.text(),
            "type": type_map[self.type_combo.currentIndex()],
            "keyword": self.keyword_input.text(),
            "field": field_map[self.field_combo.currentIndex()],
            "case_sensitive": self.case_sensitive.isChecked(),
            "action_block": self.action_block.isChecked(),
            "action_save": self.action_save.isChecked(),
            "enabled": self.enabled_check.isChecked()
        }


class FilterPage(QWidget):
    """过滤规则页面 - 管理消息过滤规则"""
    
    def __init__(self, config_manager, message_processor):
        super().__init__()
        self.config_manager = config_manager
        self.message_processor = message_processor
        self.rules = []
        self._setup_ui()
        self._load_rules()
    
    def _setup_ui(self):
        """设置UI"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content = QWidget()
        scroll.setWidget(content)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        content.setLayout(layout)
        
        # 页面标题
        title = QLabel("过滤规则")
        title.setProperty("heading", "h2")
        layout.addWidget(title)
        
        # 说明
        info_card = QFrame()
        info_card.setProperty("card", "true")
        info_layout = QVBoxLayout()
        info_card.setLayout(info_layout)
        
        info_label = QLabel("过滤规则可以帮助您自动处理特定的消息")
        info_label.setProperty("secondary", "true")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_card)
        
        # 规则列表
        list_card = self._create_list_card()
        layout.addWidget(list_card)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("  添加规则")
        add_btn.setIcon(SvgIcon.get_icon("plus", "#FFFFFF", 14))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #5FA04E;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #71B260;
            }
            QPushButton:pressed {
                background-color: #4D8E3C;
            }
        """)
        add_btn.clicked.connect(self._add_rule)
        button_layout.addWidget(add_btn)
        
        test_btn = QPushButton("  测试规则")
        test_btn.setIcon(SvgIcon.get_icon("test", "#FFFFFF", 14))
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B7FDB;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3D8FED;
            }
            QPushButton:pressed {
                background-color: #1A6FC9;
            }
        """)
        test_btn.clicked.connect(self._test_rules)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_list_card(self) -> QFrame:
        """创建规则列表卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题
        header_layout = QHBoxLayout()
        
        title = QLabel("规则列表")
        title.setProperty("heading", "h3")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.count_label = QLabel("共 0 条规则")
        self.count_label.setProperty("secondary", "true")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # 列表
        self.rule_list = QListWidget()
        self.rule_list.setMinimumHeight(300)
        layout.addWidget(self.rule_list)
        
        # 列表操作按钮
        list_button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("  编辑")
        edit_btn.setIcon(SvgIcon.get_icon("edit", "#FFFFFF", 14))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B7FDB;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3D8FED;
            }
            QPushButton:pressed {
                background-color: #1A6FC9;
            }
        """)
        edit_btn.clicked.connect(self._edit_rule)
        list_button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("  删除")
        delete_btn.setIcon(SvgIcon.get_icon("delete", "#FFFFFF", 14))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #C5444F;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D75661;
            }
            QPushButton:pressed {
                background-color: #B3323D;
            }
        """)
        delete_btn.clicked.connect(self._delete_rule)
        list_button_layout.addWidget(delete_btn)
        
        toggle_btn = QPushButton("  启用/禁用")
        toggle_btn.setIcon(SvgIcon.get_icon("refresh", "#FFFFFF", 14))
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #C99A3E;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #DBAC50;
            }
            QPushButton:pressed {
                background-color: #B7882C;
            }
        """)
        toggle_btn.clicked.connect(self._toggle_rule)
        list_button_layout.addWidget(toggle_btn)
        
        list_button_layout.addStretch()
        layout.addLayout(list_button_layout)
        
        return card
    
    def _load_rules(self):
        """加载规则"""
        try:
            filter_config = self.config_manager.get("filters", {})
            self.rules = filter_config.get("rules", [])
            self._update_list()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载规则失败: {e}")
    
    def _update_list(self):
        """更新列表显示"""
        self.rule_list.clear()
        self.count_label.setText(f"共 {len(self.rules)} 条规则")
        
        for i, rule in enumerate(self.rules):
            # 创建列表项
            item = QListWidgetItem()
            
            # 规则信息
            name = rule.get("name", "未命名规则")
            keyword = rule.get("keyword", "")
            enabled = rule.get("enabled", True)
            
            # 状态图标
            status_icon = "[启用]" if enabled else "[禁用]"
            
            # 类型图标
            type_icons = {
                "contains": "[包含]",
                "not_contains": "[排除]",
                "source": "[来源]",
                "regex": "[正则]"
            }
            type_icon = type_icons.get(rule.get("type", "contains"), "[包含]")
            
            # 设置文本
            item.setText(f"{status_icon} {type_icon} {name} - 关键词: {keyword}")
            
            # 设置样式
            if not enabled:
                item.setForeground(Qt.GlobalColor.gray)
            
            self.rule_list.addItem(item)
    
    def _add_rule(self):
        """添加规则"""
        dialog = FilterRuleDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule = dialog.get_rule()
            if not rule["name"] or not rule["keyword"]:
                QMessageBox.warning(self, "警告", "请填写规则名称和关键词")
                return
            
            self.rules.append(rule)
            self._update_list()
            self._auto_save_rules()  # 自动保存
            QMessageBox.information(self, "成功", "规则已添加并自动保存")
    
    def _edit_rule(self):
        """编辑规则"""
        current_row = self.rule_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一条规则")
            return
        
        rule = self.rules[current_row]
        dialog = FilterRuleDialog(rule=rule, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.rules[current_row] = dialog.get_rule()
            self._update_list()
            self._auto_save_rules()  # 自动保存
            QMessageBox.information(self, "成功", "规则已修改并自动保存")
    
    def _delete_rule(self):
        """删除规则"""
        current_row = self.rule_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一条规则")
            return
        
        rule = self.rules[current_row]
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除规则 '{rule.get('name', '未命名')}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.rules.pop(current_row)
            self._update_list()
            self._auto_save_rules()  # 自动保存
            QMessageBox.information(self, "成功", "规则已删除并自动保存")
    
    def _toggle_rule(self):
        """切换规则启用状态"""
        current_row = self.rule_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一条规则")
            return
        
        rule = self.rules[current_row]
        rule["enabled"] = not rule.get("enabled", True)
        self._update_list()
        
        status = "启用" if rule["enabled"] else "禁用"
        self._auto_save_rules()  # 自动保存
        QMessageBox.information(self, "成功", f"规则已{status}并自动保存")
    
    def _save_rules(self):
        """保存规则并实时重载过滤引擎"""
        try:
            self.config_manager.set("filters.rules", self.rules)
            
            # 实时重载过滤引擎
            self._reload_filter_engine()
            
            QMessageBox.information(self, "成功", "规则已保存并立即生效！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存规则失败: {e}")
    
    def _auto_save_rules(self):
        """自动保存规则（无提示）"""
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            
            logger.info("[过滤规则] 配置已修改，准备自动保存...")
            print("[过滤规则] 配置已修改，准备自动保存...")
            
            self.config_manager.set("filters.rules", self.rules)
            # 重新加载过滤引擎
            self._reload_filter_engine()
            
            logger.info("[过滤规则] 配置已更新到内存，等待写入文件...")
        except Exception as e:
            print(f"自动保存规则失败: {e}")
            logger.error(f"自动保存规则失败: {e}", exc_info=True)
    
    def force_save(self):
        """强制立即保存配置（用于页面切换或程序退出时）"""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            self.config_manager.set("filters.rules", self.rules)
            # 重新加载过滤引擎
            self._reload_filter_engine()
            # 强制保存到文件
            self.config_manager.save_config()
            logger.info("[过滤规则] 配置已强制保存到文件")
        except Exception as e:
            logger.error(f"[过滤规则] 强制保存规则失败: {e}", exc_info=True)
    
    def _reload_filter_engine(self):
        """重新加载过滤引擎
        
        使用与main.py一致的统一转换入口rules_from_config，
        并通过set_rules原子替换规则列表，避免消息线程遍历规则时
        出现"清空后逐条添加"的中间状态。
        """
        try:
            from core.filter_engine import rules_from_config
            from utils.logger import get_logger
            logger = get_logger(__name__)
            
            if hasattr(self.message_processor, 'filter_engine'):
                new_rules = rules_from_config(self.rules)
                self.message_processor.filter_engine.set_rules(new_rules)
                logger.info(f"过滤引擎已重新加载，共 {len(new_rules)} 条规则")
        except Exception as e:
            from utils.logger import get_logger
            get_logger(__name__).error(f"重载过滤引擎失败: {e}", exc_info=True)
    
    def _test_rules(self):
        """测试规则"""
        dialog = QDialog(self)
        dialog.setWindowTitle("测试过滤规则")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 说明
        info = QLabel("输入测试消息，查看哪些规则会匹配:")
        layout.addWidget(info)
        
        # 测试输入
        test_layout = QVBoxLayout()
        
        test_layout.addWidget(QLabel("消息标题:"))
        title_input = QLineEdit()
        title_input.setPlaceholderText("输入测试标题")
        test_layout.addWidget(title_input)
        
        test_layout.addWidget(QLabel("消息内容:"))
        content_input = QTextEdit()
        content_input.setPlaceholderText("输入测试内容")
        content_input.setMaximumHeight(100)
        test_layout.addWidget(content_input)
        
        test_layout.addWidget(QLabel("消息来源:"))
        source_input = QLineEdit()
        source_input.setPlaceholderText("输入测试来源")
        test_layout.addWidget(source_input)
        
        layout.addLayout(test_layout)
        
        # 测试按钮
        test_btn = QPushButton("执行测试")
        layout.addWidget(test_btn)
        
        # 结果显示
        result_label = QLabel("测试结果:")
        layout.addWidget(result_label)
        
        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setMaximumHeight(150)
        layout.addWidget(result_text)
        
        def run_test():
            """使用真实的过滤引擎逐条测试规则，保证测试结果与实际行为完全一致
            （支持包含/排除/来源/正则四种类型及大小写敏感设置）"""
            import time as _time
            from core.filter_engine import FilterEngine, rules_from_config
            from data.models import Message
            
            title = title_input.text()
            content = content_input.toPlainText()
            source = source_input.text()
            
            if not title and not content:
                result_text.setPlainText("请至少输入标题或内容")
                return
            
            test_message = Message(
                id="filter_test",
                source=source,
                title=title,
                content=content,
                timestamp=_time.time(),
                metadata={}
            )
            
            matched_rules = []
            blocked = False
            saved_to_history = True
            
            for rule_data in self.rules:
                if not rule_data.get("enabled", True):
                    continue
                
                # 每条规则单独构建引擎测试是否匹配
                engine_rules = rules_from_config([rule_data])
                if not engine_rules:
                    continue
                
                single_engine = FilterEngine(engine_rules)
                matched = any(
                    single_engine._match_rule(test_message, r) for r in engine_rules
                )
                if matched:
                    matched_rules.append(rule_data.get("name", "未命名"))
            
            # 用完整规则集判断最终处理结果
            full_engine = FilterEngine(rules_from_config(self.rules))
            should_show, should_save = full_engine.should_process(test_message)
            
            lines = []
            if matched_rules:
                lines.append(f"匹配到 {len(matched_rules)} 条规则:")
                lines.extend(f"• {name}" for name in matched_rules)
                lines.append("")
            else:
                lines.append("没有匹配到任何规则")
                lines.append("")
            
            lines.append(f"最终结果: {'显示弹窗' if should_show else '拦截弹窗'}"
                         f"，{'保存' if should_save else '不保存'}到历史记录")
            
            result_text.setPlainText("\n".join(lines))
        
        test_btn.clicked.connect(run_test)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
