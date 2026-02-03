"""
WinMsgHub - 异步工作线程
作者：青云制作_彭明航

提供异步执行耗时操作的工具类，避免阻塞UI线程
"""

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import Callable, Any
import traceback


class AsyncWorker(QThread):
    """异步工作线程
    
    用于在后台线程执行耗时操作，完成后通过信号通知主线程
    """
    
    # 信号定义
    finished = pyqtSignal(object)  # 任务完成，携带结果
    error = pyqtSignal(str)  # 任务出错，携带错误信息
    progress = pyqtSignal(int)  # 进度更新（0-100）
    
    def __init__(self, func: Callable, *args, **kwargs):
        """初始化异步工作线程
        
        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """执行任务"""
        try:
            result = self.func(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.finished.emit(result)
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True


class AsyncTaskManager(QObject):
    """异步任务管理器
    
    管理多个异步任务，避免任务堆积
    """
    
    def __init__(self):
        super().__init__()
        self.workers = {}  # 任务ID -> Worker
    
    def run_task(self, task_id: str, func: Callable, 
                 on_finished: Callable = None,
                 on_error: Callable = None,
                 *args, **kwargs):
        """运行异步任务
        
        Args:
            task_id: 任务唯一标识
            func: 要执行的函数
            on_finished: 完成回调
            on_error: 错误回调
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        # 如果同ID任务正在运行，先取消
        if task_id in self.workers:
            old_worker = self.workers[task_id]
            if old_worker.isRunning():
                old_worker.cancel()
                old_worker.wait()
        
        # 创建新任务
        worker = AsyncWorker(func, *args, **kwargs)
        
        # 连接信号
        if on_finished:
            worker.finished.connect(on_finished)
        if on_error:
            worker.error.connect(on_error)
        
        # 任务完成后清理
        def cleanup():
            if task_id in self.workers:
                del self.workers[task_id]
        
        worker.finished.connect(cleanup)
        worker.error.connect(cleanup)
        
        # 保存并启动
        self.workers[task_id] = worker
        worker.start()
    
    def cancel_task(self, task_id: str):
        """取消指定任务"""
        if task_id in self.workers:
            worker = self.workers[task_id]
            worker.cancel()
            worker.wait()
            del self.workers[task_id]
    
    def cancel_all(self):
        """取消所有任务"""
        for worker in list(self.workers.values()):
            worker.cancel()
            worker.wait()
        self.workers.clear()
    
    def cleanup(self):
        """清理所有任务（程序退出时调用）"""
        for worker in list(self.workers.values()):
            if worker.isRunning():
                worker.cancel()
                # 给线程一点时间退出
                worker.wait(1000)  # 最多等待1秒
                if worker.isRunning():
                    # 如果还在运行，强制终止
                    worker.terminate()
        self.workers.clear()
