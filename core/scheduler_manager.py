"""
WinMsgHub - 定时任务管理器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from data.models import Message
from utils.logger import get_logger


logger = get_logger(__name__)


class ScheduledTask:
    """定时任务"""
    
    def __init__(self, task_id: str, name: str, title: str, content: str,
                 task_type: str, interval: int = 0, time_of_day: str = "",
                 enabled: bool = True, sound_file: str = "", days_of_week: List[int] = None):
        """
        初始化定时任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            title: 弹窗标题
            content: 弹窗内容
            task_type: 任务类型 (interval/daily/weekly/pomodoro)
            interval: 间隔时间（秒）
            time_of_day: 每天的时间 (HH:MM格式)
            enabled: 是否启用
            sound_file: 音效文件路径
            days_of_week: 星期几执行（0=周一，6=周日）
        """
        self.id = task_id
        self.name = name
        self.title = title
        self.content = content
        self.type = task_type
        self.interval = interval
        self.time_of_day = time_of_day
        self.enabled = enabled
        self.sound_file = sound_file
        self.days_of_week = days_of_week or []
        self.last_run = 0.0
        self.run_count = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "content": self.content,
            "type": self.type,
            "interval": self.interval,
            "time_of_day": self.time_of_day,
            "enabled": self.enabled,
            "sound_file": self.sound_file,
            "days_of_week": self.days_of_week,
            "last_run": self.last_run,
            "run_count": self.run_count
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'ScheduledTask':
        """从字典创建"""
        task = ScheduledTask(
            task_id=data.get("id", ""),
            name=data.get("name", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            task_type=data.get("type", "interval"),
            interval=data.get("interval", 0),
            time_of_day=data.get("time_of_day", ""),
            enabled=data.get("enabled", True),
            sound_file=data.get("sound_file", ""),
            days_of_week=data.get("days_of_week", [])
        )
        task.last_run = data.get("last_run", 0.0)
        task.run_count = data.get("run_count", 0)
        return task


class SchedulerManager(QObject):
    """定时任务管理器"""
    
    task_triggered = pyqtSignal(ScheduledTask)  # 任务触发信号
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.tasks: List[ScheduledTask] = []
        
        # 记录启动时间，用于防止启动时立即触发每日/每周任务
        self.startup_time = time.time()
        
        # 检查定时器 - 每秒检查一次
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_tasks)
        self.check_timer.start(5000)  # 改为5秒检查一次，降低频率
        
        # 番茄钟状态（从配置加载）
        self._load_pomodoro_state()
        
        self._load_tasks()
        logger.info("定时任务管理器已初始化")
    
    def _load_pomodoro_state(self):
        """从配置加载番茄钟状态"""
        saved_state = self.config_manager.get("pomodoro", {})
        
        self.pomodoro_state = {
            "is_running": saved_state.get("is_running", False),
            "is_break": saved_state.get("is_break", False),
            "start_time": saved_state.get("start_time", 0),
            "work_duration": saved_state.get("work_duration", 25 * 60),
            "short_break": saved_state.get("short_break", 5 * 60),
            "long_break": saved_state.get("long_break", 15 * 60),
            "sessions_until_long_break": saved_state.get("sessions_until_long_break", 4),
            "current_session": saved_state.get("current_session", 0)
        }
        
        # 如果上次关闭时番茄钟在运行，恢复运行状态
        if self.pomodoro_state["is_running"]:
            logger.info("恢复番茄钟运行状态")
    
    def _save_pomodoro_state(self):
        """保存番茄钟状态到配置"""
        self.config_manager.set("pomodoro", self.pomodoro_state)
    
    def _load_tasks(self):
        """从配置加载任务"""
        tasks_data = self.config_manager.get("scheduled_tasks", [])
        self.tasks = [ScheduledTask.from_dict(data) for data in tasks_data]
        
        # 重置所有间隔任务的last_run为当前时间
        # 这样软件启动时从当前时刻开始重新计时，避免累积触发
        current_time = time.time()
        for task in self.tasks:
            if task.type == "interval":
                task.last_run = current_time
                logger.debug(f"重置任务 {task.name} 的计时器")
        
        logger.info(f"已加载 {len(self.tasks)} 个定时任务")
    
    def _save_tasks(self):
        """保存任务到配置（异步）"""
        tasks_data = [task.to_dict() for task in self.tasks]
        
        # 使用异步配置管理器保存，避免阻塞UI
        if hasattr(self.config_manager, 'set_async'):
            # 如果有异步方法，使用异步保存
            self.config_manager.set_async("scheduled_tasks", tasks_data)
        else:
            # 否则使用普通保存（但会触发防抖延迟保存）
            self.config_manager.set("scheduled_tasks", tasks_data)
        
        logger.debug("定时任务已保存")
    
    def add_task(self, task: ScheduledTask):
        """添加任务"""
        # 设置last_run为当前时间，避免立即触发
        task.last_run = time.time()
        self.tasks.append(task)
        self._save_tasks()
        logger.info(f"添加定时任务: {task.name}")
    
    def update_task(self, task_id: str, updated_task: ScheduledTask):
        """更新任务"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks[i] = updated_task
                self._save_tasks()
                logger.info(f"更新定时任务: {updated_task.name}")
                return True
        return False
    
    def delete_task(self, task_id: str):
        """删除任务"""
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self._save_tasks()
        logger.info(f"删除定时任务: {task_id}")
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        return self.tasks.copy()
    
    def _check_tasks(self):
        """检查并触发任务"""
        # 如果没有启用的任务，直接返回
        if not any(task.enabled for task in self.tasks):
            return
        
        current_time = time.time()
        now = datetime.now()
        
        for task in self.tasks:
            if not task.enabled:
                continue
            
            should_trigger = False
            
            if task.type == "interval":
                # 间隔触发 - 只有当距离上次运行超过间隔时间才触发
                if task.last_run > 0 and (current_time - task.last_run) >= task.interval:
                    should_trigger = True
            
            elif task.type == "daily":
                # 每天定时触发
                if task.time_of_day:
                    try:
                        target_time = datetime.strptime(task.time_of_day, "%H:%M").time()
                        current_date = now.date()
                        last_run_date = datetime.fromtimestamp(task.last_run).date() if task.last_run > 0 else None
                        
                        # 如果今天还没运行过，且当前时间已过目标时间
                        if last_run_date != current_date and now.time() >= target_time:
                            # 额外检查：如果是刚启动（5分钟内），且目标时间已经过去很久（超过1小时）
                            # 则不触发，避免启动时弹出昨天应该触发的任务
                            time_since_startup = current_time - self.startup_time
                            if time_since_startup < 300:  # 启动后5分钟内
                                # 计算当前时间与目标时间的差距
                                target_datetime = datetime.combine(current_date, target_time)
                                time_diff = (now - target_datetime).total_seconds()
                                if time_diff > 3600:  # 目标时间已过去超过1小时
                                    logger.debug(f"跳过任务 {task.name}：启动时目标时间已过去 {time_diff/3600:.1f} 小时")
                                    continue
                            should_trigger = True
                    except ValueError:
                        logger.error(f"无效的时间格式: {task.time_of_day}")
            
            elif task.type == "weekly":
                # 每周定时触发
                if task.time_of_day and task.days_of_week:
                    try:
                        current_weekday = now.weekday()  # 0=周一，6=周日
                        if current_weekday in task.days_of_week:
                            target_time = datetime.strptime(task.time_of_day, "%H:%M").time()
                            current_date = now.date()
                            last_run_date = datetime.fromtimestamp(task.last_run).date() if task.last_run > 0 else None
                            
                            # 如果今天还没运行过，且当前时间已过目标时间
                            if last_run_date != current_date and now.time() >= target_time:
                                # 额外检查：如果是刚启动（5分钟内），且目标时间已经过去很久（超过1小时）
                                # 则不触发，避免启动时弹出昨天应该触发的任务
                                time_since_startup = current_time - self.startup_time
                                if time_since_startup < 300:  # 启动后5分钟内
                                    # 计算当前时间与目标时间的差距
                                    target_datetime = datetime.combine(current_date, target_time)
                                    time_diff = (now - target_datetime).total_seconds()
                                    if time_diff > 3600:  # 目标时间已过去超过1小时
                                        logger.debug(f"跳过任务 {task.name}：启动时目标时间已过去 {time_diff/3600:.1f} 小时")
                                        continue
                                should_trigger = True
                    except ValueError:
                        logger.error(f"无效的时间格式: {task.time_of_day}")
            
            elif task.type == "pomodoro":
                # 番茄钟由单独的方法处理
                pass
            
            if should_trigger:
                self._trigger_task(task)
    
    def _trigger_task(self, task: ScheduledTask):
        """触发任务"""
        task.last_run = time.time()
        task.run_count += 1
        self._save_tasks()
        
        logger.info(f"触发定时任务: {task.name} (第{task.run_count}次)")
        self.task_triggered.emit(task)
    
    # 番茄钟功能
    def start_pomodoro(self, work_duration: int = 25, short_break: int = 5, 
                      long_break: int = 15, sessions: int = 4):
        """启动番茄钟"""
        self.pomodoro_state = {
            "is_running": True,
            "is_break": False,
            "start_time": time.time(),
            "work_duration": work_duration * 60,
            "short_break": short_break * 60,
            "long_break": long_break * 60,
            "sessions_until_long_break": sessions,
            "current_session": 1
        }
        self._save_pomodoro_state()  # 保存状态
        logger.info(f"番茄钟已启动: {work_duration}分钟工作 / {short_break}分钟休息")
    
    def stop_pomodoro(self):
        """停止番茄钟"""
        self.pomodoro_state["is_running"] = False
        self._save_pomodoro_state()  # 保存状态
        logger.info("番茄钟已停止")
    
    def stop_all(self):
        """停止所有定时任务和番茄钟"""
        try:
            # 停止番茄钟
            if self.pomodoro_state.get("is_running", False):
                self.stop_pomodoro()
            
            # 停止检查定时器
            if hasattr(self, 'check_timer'):
                self.check_timer.stop()
            
            # 保存所有任务状态
            self._save_tasks()
            
            logger.info("所有定时任务已停止")
        except Exception as e:
            logger.error(f"停止定时任务失败: {e}")
    
    def get_pomodoro_status(self) -> Dict:
        """获取番茄钟状态"""
        if not self.pomodoro_state["is_running"]:
            return {
                "is_running": False,
                "time_remaining": 0,
                "is_break": False,
                "current_session": 0
            }
        
        elapsed = time.time() - self.pomodoro_state["start_time"]
        
        if self.pomodoro_state["is_break"]:
            # 休息时间
            if self.pomodoro_state["current_session"] % self.pomodoro_state["sessions_until_long_break"] == 0:
                duration = self.pomodoro_state["long_break"]
            else:
                duration = self.pomodoro_state["short_break"]
        else:
            # 工作时间
            duration = self.pomodoro_state["work_duration"]
        
        time_remaining = max(0, duration - elapsed)
        
        # 检查是否需要切换状态
        if time_remaining == 0:
            self._switch_pomodoro_state()
            return self.get_pomodoro_status()
        
        return {
            "is_running": True,
            "time_remaining": int(time_remaining),
            "is_break": self.pomodoro_state["is_break"],
            "current_session": self.pomodoro_state["current_session"],
            "total_sessions": self.pomodoro_state["sessions_until_long_break"]
        }
    
    def _switch_pomodoro_state(self):
        """切换番茄钟状态（工作/休息）"""
        if self.pomodoro_state["is_break"]:
            # 从休息切换到工作
            self.pomodoro_state["is_break"] = False
            self.pomodoro_state["current_session"] += 1
            self.pomodoro_state["start_time"] = time.time()
            
            # 触发工作开始提醒
            task = ScheduledTask(
                task_id="pomodoro_work",
                name="番茄钟 - 工作时间",
                title="🍅 开始工作",
                content=f"第 {self.pomodoro_state['current_session']} 个番茄钟，专注工作 {self.pomodoro_state['work_duration']//60} 分钟！",
                task_type="pomodoro",
                enabled=True
            )
            self.task_triggered.emit(task)
        else:
            # 从工作切换到休息
            self.pomodoro_state["is_break"] = True
            self.pomodoro_state["start_time"] = time.time()
            
            # 判断是长休息还是短休息
            if self.pomodoro_state["current_session"] % self.pomodoro_state["sessions_until_long_break"] == 0:
                break_duration = self.pomodoro_state["long_break"] // 60
                break_type = "长"
            else:
                break_duration = self.pomodoro_state["short_break"] // 60
                break_type = "短"
            
            # 触发休息提醒
            task = ScheduledTask(
                task_id="pomodoro_break",
                name=f"番茄钟 - {break_type}休息",
                title="☕ 休息时间",
                content=f"完成了一个番茄钟！休息 {break_duration} 分钟，放松一下吧~",
                task_type="pomodoro",
                enabled=True
            )
            self.task_triggered.emit(task)
