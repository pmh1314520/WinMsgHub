"""
WinMsgHub - 本地MQTT服务管理器（使用amqtt）
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

import asyncio
import logging
from typing import Optional
import threading

logger = logging.getLogger(__name__)


class LocalMQTTManager:
    """本地MQTT服务管理器 - 使用hbmqtt实现"""
    
    def __init__(self, config_manager):
        """初始化管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.broker = None
        self.broker_thread = None
        self.loop = None
        self._is_running = False
        self._port = 1883
        self._ws_port = 8083
        
        logger.info("本地MQTT管理器已初始化（使用amqtt）")
    
    def _run_broker(self, port: int, ws_port: int):
        """在独立线程中运行Broker
        
        Args:
            port: MQTT TCP端口
            ws_port: WebSocket端口
        """
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 运行Broker
            self.loop.run_until_complete(self._start_broker(port, ws_port))
        except Exception as e:
            logger.error(f"Broker线程异常: {e}", exc_info=True)
            self._is_running = False
    
    async def _start_broker(self, port: int, ws_port: int):
        """启动MQTT Broker
        
        Args:
            port: MQTT TCP端口
            ws_port: WebSocket端口
        """
        try:
            from amqtt.broker import Broker
            
            # Broker配置（最简配置，允许匿名访问）
            config = {
                'listeners': {
                    'default': {
                        'type': 'tcp',
                        'bind': f'0.0.0.0:{port}',
                    },
                    'ws': {
                        'type': 'ws',
                        'bind': f'0.0.0.0:{ws_port}',
                    }
                },
            }
            
            # 创建并启动Broker
            self.broker = Broker(config)
            await self.broker.start()
            
            self._is_running = True
            logger.info(f"MQTT Broker已启动 - TCP端口: {port}, WebSocket端口: {ws_port}")
            
            # 保持运行
            while self._is_running:
                await asyncio.sleep(1)
            
            # 停止Broker
            try:
                await self.broker.shutdown()
                logger.info("MQTT Broker已停止")
            except asyncio.CancelledError:
                logger.info("MQTT Broker关闭时任务被取消（正常）")
            except Exception as e:
                logger.warning(f"MQTT Broker关闭时出现异常: {e}")
            
        except asyncio.CancelledError:
            logger.info("MQTT Broker任务被取消")
            self._is_running = False
        except Exception as e:
            logger.error(f"启动Broker失败: {e}", exc_info=True)
            self._is_running = False
            raise
    
    def start_service(self, port: int = 1883, ws_port: int = 8083) -> tuple:
        """启动MQTT服务
        
        Args:
            port: MQTT TCP端口，默认1883
            ws_port: WebSocket端口，默认8083
            
        Returns:
            tuple: (成功标志, 消息)
        """
        if self.is_running():
            logger.warning("MQTT服务已在运行")
            return True, "服务已在运行"
        
        try:
            logger.info(f"正在启动MQTT服务... TCP端口={port}, WS端口={ws_port}")
            
            self._port = port
            self._ws_port = ws_port
            
            # 在独立线程中启动Broker
            self.broker_thread = threading.Thread(
                target=self._run_broker,
                args=(port, ws_port),
                daemon=True,
                name="MQTT-Broker-Thread"
            )
            self.broker_thread.start()
            
            # 等待服务启动（最多5秒）
            import time
            for i in range(50):
                time.sleep(0.1)
                if self._is_running:
                    logger.info("MQTT服务启动成功")
                    # 保存启动状态到配置
                    self.config_manager.set("local_mqtt.auto_start", True)
                    self.config_manager.set("local_mqtt.port", port)
                    self.config_manager.set("local_mqtt.ws_port", ws_port)
                    return True, "服务启动成功"
            
            logger.error("MQTT服务启动超时")
            return False, "服务启动超时"
            
        except Exception as e:
            logger.error(f"启动MQTT服务失败: {e}", exc_info=True)
            return False, f"启动失败: {str(e)}"
    
    def stop_service(self) -> tuple:
        """停止MQTT服务
        
        Returns:
            tuple: (成功标志, 消息)
        """
        if not self.is_running():
            logger.warning("MQTT服务未运行")
            return True, "服务未运行"
        
        try:
            logger.info("正在停止MQTT服务...")
            
            # 设置停止标志
            self._is_running = False
            
            # 等待线程结束（最多5秒）
            if self.broker_thread and self.broker_thread.is_alive():
                self.broker_thread.join(timeout=5)
                
                if self.broker_thread.is_alive():
                    logger.warning("MQTT服务线程未能正常结束")
                    return False, "服务停止超时"
            
            self.broker = None
            self.broker_thread = None
            self.loop = None
            
            logger.info("MQTT服务已停止")
            
            # 保存停止状态到配置（用户手动停止）
            self.config_manager.set("local_mqtt.auto_start", False)
            
            return True, "服务已停止"
            
        except Exception as e:
            logger.error(f"停止MQTT服务失败: {e}", exc_info=True)
            return False, f"停止失败: {str(e)}"
    
    def is_running(self) -> bool:
        """检查服务是否运行
        
        Returns:
            bool: 服务运行中返回True
        """
        return self._is_running and self.broker_thread is not None and self.broker_thread.is_alive()
    
    def get_service_info(self) -> dict:
        """获取服务信息
        
        Returns:
            dict: 服务信息字典
        """
        return {
            'is_running': self.is_running(),
            'type': 'amqtt MQTT Broker',
            'tcp_port': self._port,
            'ws_port': self._ws_port,
            'available': True,  # amqtt是纯Python库，总是可用
        }
    
    def get_status(self) -> dict:
        """获取服务状态（兼容旧接口）
        
        Returns:
            dict: 服务状态字典
        """
        return self.get_service_info()
