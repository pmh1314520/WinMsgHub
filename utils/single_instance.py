"""
WinMsgHub - 单实例检测
作者：青云制作_彭明航

确保应用程序只能运行一个实例
"""

import sys
import os
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class SingleInstance:
    """单实例检测器
    
    使用文件锁实现跨平台的单实例检测
    """
    
    def __init__(self, app_name: str = "WinMsgHub"):
        """初始化单实例检测器
        
        Args:
            app_name: 应用名称，用于生成唯一标识
        """
        self.app_name = app_name
        self.lock_file = None
        self.lock_fd = None
        self.is_running = False
        
        # 锁文件路径
        if sys.platform == 'win32':
            # Windows: 使用TEMP目录
            lock_dir = Path(os.environ.get('TEMP', tempfile.gettempdir()))
        else:
            # Linux/Mac: 使用/tmp
            lock_dir = Path('/tmp')
        
        self.lock_file_path = lock_dir / f"{app_name}.lock"
    
    def check(self) -> bool:
        """检查是否已有实例在运行
        
        Returns:
            True: 当前是唯一实例
            False: 已有其他实例在运行
        """
        try:
            if sys.platform == 'win32':
                # Windows: 使用文件独占打开
                import msvcrt
                
                try:
                    # 尝试以独占模式打开文件
                    self.lock_fd = os.open(
                        str(self.lock_file_path),
                        os.O_CREAT | os.O_EXCL | os.O_RDWR
                    )
                    
                    # 写入进程ID
                    os.write(self.lock_fd, str(os.getpid()).encode())
                    
                    self.is_running = True
                    print(f"[单实例] 检测通过，锁文件: {self.lock_file_path}")
                    return True
                    
                except FileExistsError:
                    # 文件已存在，检查进程是否还在运行
                    try:
                        # 读取锁文件中的PID
                        with open(self.lock_file_path, 'r') as f:
                            old_pid = int(f.read().strip())
                        
                        # 检查进程是否还在运行
                        import psutil
                        if psutil.pid_exists(old_pid):
                            print(f"[单实例] 检测到已有实例在运行 (PID: {old_pid})")
                            return False
                        else:
                            # 进程已不存在，清理旧锁文件
                            print(f"[单实例] 检测到僵尸锁文件 (PID: {old_pid} 已不存在)，正在清理...")
                            os.remove(self.lock_file_path)
                            # 重新尝试创建锁
                            return self.check()
                    except (ValueError, FileNotFoundError, ImportError):
                        # 如果无法读取PID或psutil未安装，假设有实例在运行
                        print(f"[单实例] 检测到已有实例在运行（无法验证进程状态）")
                        return False
            else:
                # Linux/Mac: 使用fcntl文件锁
                import fcntl
                
                self.lock_fd = open(self.lock_file_path, 'w')
                fcntl.lockf(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # 写入进程ID
                self.lock_fd.write(str(os.getpid()))
                self.lock_fd.flush()
                
                self.is_running = True
                print(f"[单实例] 检测通过，锁文件: {self.lock_file_path}")
                return True
                
        except (IOError, OSError) as e:
            print(f"[单实例] 检测到已有实例在运行")
            return False
    
    def release(self):
        """释放单实例锁"""
        if self.lock_fd is not None:
            try:
                if sys.platform == 'win32':
                    os.close(self.lock_fd)
                    # 删除锁文件
                    if self.lock_file_path.exists():
                        os.remove(self.lock_file_path)
                else:
                    import fcntl
                    fcntl.lockf(self.lock_fd, fcntl.LOCK_UN)
                    self.lock_fd.close()
                    # 删除锁文件
                    if self.lock_file_path.exists():
                        os.remove(self.lock_file_path)
                
                print("[单实例] 锁已释放")
            except Exception as e:
                print(f"[单实例] 释放锁失败: {e}")
            finally:
                self.lock_fd = None
                self.is_running = False
    
    def __del__(self):
        """析构函数，确保释放锁"""
        self.release()
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self.check():
            raise RuntimeError(f"{self.app_name} 已在运行")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()
        return False
