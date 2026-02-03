"""
WinMsgHub - 音效管理器（单例模式）
作者：青云制作_彭明航
"""

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class SoundManager:
    """
    音效管理器 - 单例模式
    确保同一时间只播放一个音效
    """
    _instance = None
    _player = None
    _audio_output = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化音频播放器"""
        try:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            logger.debug("音效管理器初始化完成")
        except Exception as e:
            logger.error(f"音效管理器初始化失败: {e}")
    
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
            sound_path = Path(sound_file)
            if not sound_path.exists():
                logger.warning(f"音效文件不存在: {sound_file}")
                return
            
            # 如果正在播放，先停止
            if self._player and self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self._player.stop()
                logger.debug("停止当前音效")
            
            # 播放新音效
            self._player.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._player.play()
            logger.debug(f"播放音效: {sound_file}")
            
        except Exception as e:
            logger.error(f"播放音效失败: {e}")
    
    def stop(self):
        """停止当前播放的音效"""
        try:
            if self._player:
                self._player.stop()
                logger.debug("音效已停止")
        except Exception as e:
            logger.error(f"停止音效失败: {e}")
    
    def is_playing(self) -> bool:
        """检查是否正在播放音效"""
        try:
            if self._player:
                return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        except:
            pass
        return False
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
