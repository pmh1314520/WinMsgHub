"""
WinMsgHub - 音效管理器（单例模式）
作者：青云制作_彭明航
"""

from pathlib import Path
from utils.logger import get_logger
import logging

logger = logging.getLogger('WinMsgHub')


class SoundManager:
    """
    音效管理器 - 单例模式
    确保同一时间只播放一个音效
    使用 pygame 实现可靠的音量控制
    """
    _instance = None
    _pygame_initialized = False
    _volume = 0.5  # 默认音量50%
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化音频播放器"""
        try:
            import pygame
            if not self._pygame_initialized:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(self._volume)
                self._pygame_initialized = True
                logger.info(f"🎵 音效管理器初始化完成 (pygame), 默认音量: {self._volume * 100:.0f}%")
        except Exception as e:
            logger.error(f"音效管理器初始化失败: {e}")
    
    def set_volume(self, volume: float):
        """
        设置音量
        
        Args:
            volume: 音量值 (0.0 - 1.0)
        """
        try:
            import pygame
            # 限制音量范围
            volume = max(0.0, min(1.0, volume))
            self._volume = volume
            
            if self._pygame_initialized:
                pygame.mixer.music.set_volume(volume)
                logger.info(f"🔊 音量已设置: {volume * 100:.0f}% (值: {volume})")
        except Exception as e:
            logger.error(f"设置音量失败: {e}")
    
    def get_volume(self) -> float:
        """
        获取当前音量
        
        Returns:
            当前音量值 (0.0 - 1.0)
        """
        return self._volume
    
    def play(self, sound_file: str):
        """
        播放音效
        
        Args:
            sound_file: 音效文件路径
        
        Note:
            如果当前正在播放音效，会停止当前音效并播放新音效
        """
        if not sound_file:
            return
        
        try:
            import pygame
            sound_path = Path(sound_file)
            if not sound_path.exists():
                logger.warning(f"音效文件不存在: {sound_file}")
                return
            
            if not self._pygame_initialized:
                logger.error("pygame 未初始化")
                return
            
            # 如果正在播放，先停止
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                logger.debug("停止当前音效")
            
            # 设置音量
            pygame.mixer.music.set_volume(self._volume)
            logger.info(f"🔊 设置音量: {self._volume * 100:.0f}% (值: {self._volume})")
            
            # 加载并播放音效
            pygame.mixer.music.load(str(sound_path))
            pygame.mixer.music.play()
            logger.info(f"▶️  播放音效: {Path(sound_file).name}, 音量: {self._volume * 100:.0f}%")
            
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
    
    def stop(self):
        """停止当前播放的音效"""
        try:
            import pygame
            if self._pygame_initialized:
                pygame.mixer.music.stop()
                logger.debug("音效已停止")
        except Exception as e:
            logger.error(f"停止音效失败: {e}")
    
    def is_playing(self) -> bool:
        """检查是否正在播放音效"""
        try:
            import pygame
            if self._pygame_initialized:
                return pygame.mixer.music.get_busy()
        except:
            pass
        return False
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
