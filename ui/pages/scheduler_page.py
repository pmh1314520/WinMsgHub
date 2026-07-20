"""
WinMsgHub - 定时弹窗页面
作者：青云制作_彭明航
"""

import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QTimeEdit, QGroupBox, QGridLayout, QTextEdit, QFileDialog,
    QFrame
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont
from core.scheduler_manager import ScheduledTask
from ui.svg_icons import SvgIcon


class SchedulerPage(QWidget):
    """定时弹窗页面"""
    
    def __init__(self, config_manager, scheduler_manager):
        super().__init__()
        self.config_manager = config_manager
        self.scheduler_manager = scheduler_manager
        
        # 缓存任务列表，避免频繁重建表格
        self._cached_tasks = []
        
        self._setup_ui()
        self._load_tasks()
        
        # 监听scheduler_manager的任务变化（如果有信号的话）
        # 否则只在用户操作时刷新，不使用定时器轮询
        # 定时器只用于更新番茄钟状态，不刷新任务列表
        
        # 如果番茄钟状态是从上次会话恢复的运行中状态，
        # 需要启动状态刷新定时器，否则界面永远显示"未运行"
        try:
            if self.scheduler_manager.pomodoro_state.get("is_running", False):
                self.pomodoro_update_timer.start(2000)
                self._update_pomodoro_status()
        except Exception:
            pass
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # 标题和说明
        title = QLabel("定时弹窗")
        title.setProperty("heading", "h2")
        layout.addWidget(title)
        
        desc = QLabel("设置定时提醒，让WinMsgHub在指定时间自动弹出提醒")
        desc.setStyleSheet("color: #6C757D; font-size: 13px;")
        layout.addWidget(desc)
        
        # 番茄钟控制区域
        pomodoro_card = self._create_pomodoro_card()
        layout.addWidget(pomodoro_card)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("  添加定时任务")
        add_btn.setIcon(SvgIcon.get_icon("add", "#FFFFFF", 14))
        add_btn.setProperty("primary", "true")
        add_btn.clicked.connect(self._add_task)
        button_layout.addWidget(add_btn)
        
        # 快速添加按钮
        quick_drink_btn = QPushButton("  快速添加：喝水提醒")
        quick_drink_btn.setIcon(SvgIcon.get_icon("water", "#61AFEF", 14))
        quick_drink_btn.setProperty("secondary", "true")
        quick_drink_btn.clicked.connect(lambda: self._add_quick_task("drink"))
        button_layout.addWidget(quick_drink_btn)
        
        quick_rest_btn = QPushButton("  快速添加：休息提醒")
        quick_rest_btn.setIcon(SvgIcon.get_icon("rest", "#98C379", 14))
        quick_rest_btn.setProperty("secondary", "true")
        quick_rest_btn.clicked.connect(lambda: self._add_quick_task("rest"))
        button_layout.addWidget(quick_rest_btn)
        
        quick_eye_btn = QPushButton("  快速添加：护眼提醒")
        quick_eye_btn.setIcon(SvgIcon.get_icon("eye", "#E5C07B", 14))
        quick_eye_btn.setProperty("secondary", "true")
        quick_eye_btn.clicked.connect(lambda: self._add_quick_task("eye"))
        button_layout.addWidget(quick_eye_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 任务列表
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "启用", "任务名称", "类型", "触发条件", "弹窗标题", "运行次数", "操作"
        ])
        
        # 设置列宽 - 允许用户拖拽调整
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 启用列固定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # 任务名称可拖拽
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # 类型可拖拽
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # 触发条件可拖拽
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 弹窗标题自动拉伸
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 运行次数固定
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 操作列固定宽度
        
        # 设置初始列宽
        self.task_table.setColumnWidth(1, 150)  # 任务名称
        self.task_table.setColumnWidth(2, 100)  # 类型
        self.task_table.setColumnWidth(3, 200)  # 触发条件
        self.task_table.setColumnWidth(6, 180)  # 操作列固定180px
        
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.task_table)
    
    def _create_pomodoro_card(self) -> QFrame:
        """创建番茄钟控制卡片"""
        card = QFrame()
        card.setProperty("card", "true")
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(SvgIcon.get_pixmap("timer", "#E06C75", 20))
        title_layout.addWidget(icon_label)
        
        title = QLabel("番茄钟")
        title.setProperty("heading", "h3")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 说明
        desc = QLabel("番茄工作法：专注工作25分钟，休息5分钟，4个番茄钟后长休息15分钟")
        desc.setStyleSheet("color: #6C757D; font-size: 12px;")
        layout.addWidget(desc)
        
        # 配置区域
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("工作时长:"))
        self.pomodoro_work_spin = QSpinBox()
        self.pomodoro_work_spin.setRange(1, 60)
        self.pomodoro_work_spin.setValue(25)
        self.pomodoro_work_spin.setSuffix(" 分钟")
        config_layout.addWidget(self.pomodoro_work_spin)
        
        config_layout.addWidget(QLabel("短休息:"))
        self.pomodoro_short_break_spin = QSpinBox()
        self.pomodoro_short_break_spin.setRange(1, 30)
        self.pomodoro_short_break_spin.setValue(5)
        self.pomodoro_short_break_spin.setSuffix(" 分钟")
        config_layout.addWidget(self.pomodoro_short_break_spin)
        
        config_layout.addWidget(QLabel("长休息:"))
        self.pomodoro_long_break_spin = QSpinBox()
        self.pomodoro_long_break_spin.setRange(1, 60)
        self.pomodoro_long_break_spin.setValue(15)
        self.pomodoro_long_break_spin.setSuffix(" 分钟")
        config_layout.addWidget(self.pomodoro_long_break_spin)
        
        config_layout.addWidget(QLabel("长休息前的番茄数:"))
        self.pomodoro_sessions_spin = QSpinBox()
        self.pomodoro_sessions_spin.setRange(2, 10)
        self.pomodoro_sessions_spin.setValue(4)
        config_layout.addWidget(self.pomodoro_sessions_spin)
        
        config_layout.addStretch()
        layout.addLayout(config_layout)
        
        # 状态和控制按钮
        control_layout = QHBoxLayout()
        
        self.pomodoro_status_label = QLabel("未运行")
        self.pomodoro_status_label.setStyleSheet("color: #6C757D; font-size: 13px;")
        control_layout.addWidget(self.pomodoro_status_label)
        
        control_layout.addStretch()
        
        # 单个开关按钮
        self.pomodoro_toggle_btn = QPushButton("  开始番茄钟")
        self.pomodoro_toggle_btn.setIcon(SvgIcon.get_icon("play", "#FFFFFF", 14))
        self.pomodoro_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #98C379;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #88B369;
            }
        """)
        self.pomodoro_toggle_btn.clicked.connect(self._toggle_pomodoro)
        control_layout.addWidget(self.pomodoro_toggle_btn)
        
        layout.addLayout(control_layout)
        
        # 番茄钟更新定时器（只在番茄钟运行时启动）
        from PyQt6.QtCore import QTimer
        self.pomodoro_update_timer = QTimer()
        self.pomodoro_update_timer.timeout.connect(self._update_pomodoro_status)
        # 不自动启动，只在番茄钟开始时启动
        
        return card
    
    def _update_pomodoro_status(self):
        """更新番茄钟状态显示"""
        status = self.scheduler_manager.get_pomodoro_status()
        
        if status["is_running"]:
            remaining = status["time_remaining"]
            minutes = remaining // 60
            seconds = remaining % 60
            
            if status["is_break"]:
                state_text = "休息中"
            else:
                state_text = f"工作中 (第 {status['current_session']}/{status['total_sessions']} 个番茄钟)"
            
            self.pomodoro_status_label.setText(
                f"{state_text} - 剩余时间: {minutes:02d}:{seconds:02d}"
            )
            
            # 只在状态改变时更新按钮样式（避免频繁setStyleSheet导致卡顿）
            if not hasattr(self, '_pomodoro_btn_state') or self._pomodoro_btn_state != 'stop':
                self._pomodoro_btn_state = 'stop'
                self.pomodoro_toggle_btn.setText("  停止番茄钟")
                self.pomodoro_toggle_btn.setIcon(SvgIcon.get_icon("stop", "#FFFFFF", 14))
                self.pomodoro_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #E06C75;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #D05C65;
                    }
                """)
        else:
            self.pomodoro_status_label.setText("未运行")
            
            # 只在状态改变时更新按钮样式
            if not hasattr(self, '_pomodoro_btn_state') or self._pomodoro_btn_state != 'start':
                self._pomodoro_btn_state = 'start'
                self.pomodoro_toggle_btn.setText("  开始番茄钟")
                self.pomodoro_toggle_btn.setIcon(SvgIcon.get_icon("play", "#FFFFFF", 14))
                self.pomodoro_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #98C379;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #88B369;
                    }
                """)
    
    def _toggle_pomodoro(self):
        """切换番茄钟状态（开始/停止）"""
        status = self.scheduler_manager.get_pomodoro_status()
        
        if status["is_running"]:
            # 当前正在运行，停止它
            self._stop_pomodoro()
        else:
            # 当前未运行，启动它
            self._start_pomodoro()
    
    def _start_pomodoro(self):
        """启动番茄钟"""
        work_duration = self.pomodoro_work_spin.value()
        short_break = self.pomodoro_short_break_spin.value()
        long_break = self.pomodoro_long_break_spin.value()
        sessions = self.pomodoro_sessions_spin.value()
        
        self.scheduler_manager.start_pomodoro(
            work_duration, short_break, long_break, sessions
        )
        
        # 启动定时器更新UI（改为2秒更新一次，减少UI刷新频率）
        self.pomodoro_update_timer.start(2000)
        self._update_pomodoro_status()
    
    def _stop_pomodoro(self):
        """停止番茄钟"""
        self.scheduler_manager.stop_pomodoro()
        
        # 停止定时器
        self.pomodoro_update_timer.stop()
        self._update_pomodoro_status()
    
    def _load_tasks(self):
        """加载任务列表"""
        # 获取所有任务
        tasks = self.scheduler_manager.get_all_tasks()
        
        # 用字典快照做变化检测。
        # 注意：不能缓存任务对象引用——任务被原地修改时（如run_count自增），
        # 缓存和现值是同一个对象，比较永远相等，表格就不会刷新
        snapshot = [task.to_dict() for task in tasks]
        if getattr(self, '_cached_tasks', None) == snapshot:
            return  # 任务没变化，不刷新
        
        # 更新缓存
        self._cached_tasks = snapshot
        
        # 暂停更新避免频繁重绘
        self.task_table.setUpdatesEnabled(False)
        
        try:
            self.task_table.setRowCount(0)
            for task in tasks:
                self._add_task_to_table(task)
        finally:
            self.task_table.setUpdatesEnabled(True)
    
    def _refresh_tasks(self):
        """刷新任务列表（仅在任务变化时）"""
        self._load_tasks()
    
    def _add_task_to_table(self, task: ScheduledTask):
        """添加任务到表格"""
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)
        
        # 启用状态
        enabled_check = QCheckBox()
        enabled_check.setChecked(task.enabled)
        enabled_check.stateChanged.connect(
            lambda state, tid=task.id: self._toggle_task(tid, state == Qt.CheckState.Checked.value)
        )
        enabled_widget = QWidget()
        enabled_layout = QHBoxLayout()
        enabled_layout.addWidget(enabled_check)
        enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enabled_layout.setContentsMargins(0, 0, 0, 0)
        enabled_widget.setLayout(enabled_layout)
        self.task_table.setCellWidget(row, 0, enabled_widget)
        
        # 任务名称
        self.task_table.setItem(row, 1, QTableWidgetItem(task.name))
        
        # 类型
        type_map = {
            "interval": "间隔",
            "daily": "每天",
            "weekly": "每周",
            "pomodoro": "番茄钟"
        }
        self.task_table.setItem(row, 2, QTableWidgetItem(type_map.get(task.type, task.type)))
        
        # 触发条件
        if task.type == "interval":
            minutes = task.interval // 60
            seconds = task.interval % 60
            if minutes > 0:
                condition = f"每 {minutes} 分钟"
            else:
                condition = f"每 {seconds} 秒"
        elif task.type == "daily":
            condition = f"每天 {task.time_of_day}"
        elif task.type == "weekly":
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            days = ", ".join([weekday_names[d] for d in sorted(task.days_of_week)])
            condition = f"{days} {task.time_of_day}"
        else:
            condition = "-"
        
        self.task_table.setItem(row, 3, QTableWidgetItem(condition))
        
        # 弹窗标题
        self.task_table.setItem(row, 4, QTableWidgetItem(task.title))
        
        # 运行次数
        self.task_table.setItem(row, 5, QTableWidgetItem(str(task.run_count)))
        
        # 操作按钮
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(5, 2, 5, 2)
        action_layout.setSpacing(5)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setProperty("secondary", "true")
        edit_btn.clicked.connect(lambda: self._edit_task(task.id))
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setProperty("danger", "true")
        delete_btn.clicked.connect(lambda: self._delete_task(task.id))
        action_layout.addWidget(delete_btn)
        
        action_widget.setLayout(action_layout)
        self.task_table.setCellWidget(row, 6, action_widget)
    
    def _add_task(self):
        """添加任务"""
        dialog = TaskEditDialog(self, None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task = dialog.get_task()
            self.scheduler_manager.add_task(task)
            self._load_tasks()
    
    def _add_quick_task(self, task_type: str):
        """快速添加预设任务"""
        quick_tasks = {
            "drink": {
                "name": "喝水提醒",
                "title": "该喝水啦",
                "content": "已经过了一段时间了，记得喝水哦！保持身体水分充足很重要~",
                "interval": 30 * 60  # 30分钟
            },
            "rest": {
                "name": "休息提醒",
                "title": "该休息啦",
                "content": "工作一段时间了，站起来活动活动筋骨吧！伸个懒腰，放松一下~",
                "interval": 45 * 60  # 45分钟
            },
            "eye": {
                "name": "护眼提醒",
                "title": "保护眼睛",
                "content": "长时间盯着屏幕对眼睛不好哦！看看远处，让眼睛休息一下吧~",
                "interval": 20 * 60  # 20分钟
            }
        }
        
        if task_type in quick_tasks:
            preset = quick_tasks[task_type]
            task = ScheduledTask(
                task_id=str(uuid.uuid4()),
                name=preset["name"],
                title=preset["title"],
                content=preset["content"],
                task_type="interval",
                interval=preset["interval"],
                enabled=True
            )
            self.scheduler_manager.add_task(task)
            self._load_tasks()
            QMessageBox.information(self, "成功", f"已添加 {preset['name']} 任务")
    
    def _edit_task(self, task_id: str):
        """编辑任务"""
        task = self.scheduler_manager.get_task(task_id)
        if task:
            dialog = TaskEditDialog(self, task)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_task = dialog.get_task()
                self.scheduler_manager.update_task(task_id, updated_task)
                self._load_tasks()
    
    def _delete_task(self, task_id: str):
        """删除任务"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个定时任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler_manager.delete_task(task_id)
            self._load_tasks()
    
    def _toggle_task(self, task_id: str, enabled: bool):
        """切换任务启用状态"""
        task = self.scheduler_manager.get_task(task_id)
        if task:
            task.enabled = enabled
            self.scheduler_manager.update_task(task_id, task)


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, parent, task: ScheduledTask = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("编辑任务" if task else "添加任务")
        self.setMinimumWidth(600)
        self._setup_ui()
        
        if task:
            self._load_task_data()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout()
        basic_group.setLayout(basic_layout)
        
        basic_layout.addWidget(QLabel("任务名称:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：喝水提醒")
        basic_layout.addWidget(self.name_input, 0, 1)
        
        basic_layout.addWidget(QLabel("弹窗标题:"), 1, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("例如：该喝水啦")
        basic_layout.addWidget(self.title_input, 1, 1)
        
        basic_layout.addWidget(QLabel("弹窗内容:"), 2, 0)
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("例如：已经过了一段时间了，记得喝水哦！")
        self.content_input.setMaximumHeight(80)
        basic_layout.addWidget(self.content_input, 2, 1)
        
        layout.addWidget(basic_group)
        
        # 触发设置
        trigger_group = QGroupBox("触发设置")
        trigger_layout = QGridLayout()
        trigger_group.setLayout(trigger_layout)
        
        trigger_layout.addWidget(QLabel("任务类型:"), 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["间隔触发", "每天定时", "每周定时"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        trigger_layout.addWidget(self.type_combo, 0, 1)
        
        # 间隔设置
        self.interval_widget = QWidget()
        interval_layout = QHBoxLayout()
        interval_layout.setContentsMargins(0, 0, 0, 0)
        self.interval_widget.setLayout(interval_layout)
        
        interval_layout.addWidget(QLabel("间隔:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(30)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_unit_combo = QComboBox()
        self.interval_unit_combo.addItems(["分钟", "小时"])
        interval_layout.addWidget(self.interval_unit_combo)
        interval_layout.addStretch()
        
        trigger_layout.addWidget(QLabel(""), 1, 0)
        trigger_layout.addWidget(self.interval_widget, 1, 1)
        
        # 时间设置
        self.time_widget = QWidget()
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_widget.setLayout(time_layout)
        
        time_layout.addWidget(QLabel("时间:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        
        trigger_layout.addWidget(self.time_widget, 1, 1)
        self.time_widget.hide()
        
        # 星期选择
        self.weekday_widget = QWidget()
        weekday_layout = QHBoxLayout()
        weekday_layout.setContentsMargins(0, 0, 0, 0)
        self.weekday_widget.setLayout(weekday_layout)
        
        weekday_layout.addWidget(QLabel("星期:"))
        self.weekday_checks = []
        for day in ["一", "二", "三", "四", "五", "六", "日"]:
            check = QCheckBox(day)
            self.weekday_checks.append(check)
            weekday_layout.addWidget(check)
        weekday_layout.addStretch()
        
        trigger_layout.addWidget(self.weekday_widget, 2, 1)
        self.weekday_widget.hide()
        
        layout.addWidget(trigger_group)
        
        # 音效设置
        sound_group = QGroupBox("音效设置（可选）")
        sound_layout = QHBoxLayout()
        sound_group.setLayout(sound_layout)
        
        sound_layout.addWidget(QLabel("音效文件:"))
        self.sound_input = QLineEdit()
        self.sound_input.setPlaceholderText("留空使用默认弹窗音效")
        sound_layout.addWidget(self.sound_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_sound)
        sound_layout.addWidget(browse_btn)
        
        layout.addWidget(sound_group)
        
        # 按钮
        from PyQt6.QtWidgets import QDialogButtonBox
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _on_type_changed(self, index):
        """任务类型改变"""
        if index == 0:  # 间隔触发
            self.interval_widget.show()
            self.time_widget.hide()
            self.weekday_widget.hide()
        elif index == 1:  # 每天定时
            self.interval_widget.hide()
            self.time_widget.show()
            self.weekday_widget.hide()
        elif index == 2:  # 每周定时
            self.interval_widget.hide()
            self.time_widget.show()
            self.weekday_widget.show()
    
    def _browse_sound(self):
        """浏览音效文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音效文件", "",
            "音频文件 (*.wav *.mp3 *.ogg);;所有文件 (*.*)"
        )
        if file_path:
            self.sound_input.setText(file_path)
    
    def _load_task_data(self):
        """加载任务数据"""
        if not self.task:
            return
        
        self.name_input.setText(self.task.name)
        self.title_input.setText(self.task.title)
        self.content_input.setPlainText(self.task.content)
        
        # 类型
        type_map = {"interval": 0, "daily": 1, "weekly": 2}
        self.type_combo.setCurrentIndex(type_map.get(self.task.type, 0))
        
        # 间隔
        if self.task.type == "interval":
            if self.task.interval >= 3600:
                self.interval_spin.setValue(self.task.interval // 3600)
                self.interval_unit_combo.setCurrentIndex(1)
            else:
                self.interval_spin.setValue(self.task.interval // 60)
                self.interval_unit_combo.setCurrentIndex(0)
        
        # 时间
        if self.task.time_of_day:
            try:
                from datetime import datetime
                time_obj = datetime.strptime(self.task.time_of_day, "%H:%M").time()
                self.time_edit.setTime(QTime(time_obj.hour, time_obj.minute))
            except:
                pass
        
        # 星期
        for i, check in enumerate(self.weekday_checks):
            check.setChecked(i in self.task.days_of_week)
        
        # 音效
        self.sound_input.setText(self.task.sound_file)
    
    def get_task(self) -> ScheduledTask:
        """获取任务数据"""
        task_id = self.task.id if self.task else str(uuid.uuid4())
        name = self.name_input.text().strip()
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        type_index = self.type_combo.currentIndex()
        type_map = {0: "interval", 1: "daily", 2: "weekly"}
        task_type = type_map[type_index]
        
        # 间隔
        interval = 0
        if task_type == "interval":
            value = self.interval_spin.value()
            if self.interval_unit_combo.currentIndex() == 0:  # 分钟
                interval = value * 60
            else:  # 小时
                interval = value * 3600
        
        # 时间
        time_of_day = ""
        if task_type in ["daily", "weekly"]:
            time_of_day = self.time_edit.time().toString("HH:mm")
        
        # 星期
        days_of_week = []
        if task_type == "weekly":
            days_of_week = [i for i, check in enumerate(self.weekday_checks) if check.isChecked()]
        
        sound_file = self.sound_input.text().strip()
        
        # 编辑已有任务时保留其启用状态，新任务默认启用
        # （此前编辑任务会把禁用中的任务强制重新启用）
        enabled = self.task.enabled if self.task else True
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            title=title,
            content=content,
            task_type=task_type,
            interval=interval,
            time_of_day=time_of_day,
            enabled=enabled,
            sound_file=sound_file,
            days_of_week=days_of_week
        )
        
        # 保留原有的运行统计
        if self.task:
            task.last_run = self.task.last_run
            task.run_count = self.task.run_count
        
        return task
