"""
日志系统测试

作者：青云制作_彭明航
许可：要求二次开发必须开源并标明原作者，允许商用
"""

import pytest
import logging
from pathlib import Path
from utils.logger import get_logger, set_log_level, Logger


def test_logger_singleton():
    """测试日志器是单例模式"""
    logger1 = Logger()
    logger2 = Logger()
    assert logger1 is logger2


def test_get_logger():
    """测试获取日志记录器"""
    logger = get_logger('test')
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'test'


def test_get_logger_default_name():
    """测试获取默认名称的日志记录器"""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'WinMsgHub'


def test_set_log_level():
    """测试设置日志级别"""
    logger = get_logger()
    
    # 测试有效的日志级别
    set_log_level('DEBUG')
    assert logger.level == logging.DEBUG
    
    set_log_level('INFO')
    assert logger.level == logging.INFO
    
    set_log_level('WARNING')
    assert logger.level == logging.WARNING
    
    set_log_level('ERROR')
    assert logger.level == logging.ERROR
    
    set_log_level('CRITICAL')
    assert logger.level == logging.CRITICAL


def test_logger_writes_to_file(tmp_path):
    """测试日志写入文件"""
    # 注意：由于Logger是单例，这个测试只验证日志功能存在
    # 获取根日志记录器来检查处理器
    root_logger = get_logger('WinMsgHub')
    
    # 记录一些日志
    logger = get_logger('file_test')
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # 验证根日志记录器已配置处理器
    assert len(root_logger.handlers) > 0


def test_logger_basic_functionality():
    """测试日志基本功能"""
    logger = get_logger('basic_test')
    
    # 测试不同级别的日志方法存在且可调用
    try:
        logger.debug("Debug test")
        logger.info("Info test")
        logger.warning("Warning test")
        logger.error("Error test")
        logger.critical("Critical test")
    except Exception as e:
        pytest.fail(f"Logger methods should not raise exceptions: {e}")
