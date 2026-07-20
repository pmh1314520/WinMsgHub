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
        self._last_error = ""  # 最近一次启动失败的原因
        
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
            self._last_error = str(e)
        finally:
            # 关闭事件循环，避免资源泄漏（尤其是多次启动/停止服务时）
            try:
                if self.loop and not self.loop.is_closed():
                    self.loop.close()
            except Exception as e:
                logger.debug(f"关闭事件循环时出现异常: {e}")
    
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
            self._last_error = str(e)
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
            self._last_error = ""
            
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
                    # 保存端口到配置（auto_start是用户偏好，由界面复选框单独控制，
                    # 不应在这里强行改写）
                    self.config_manager.set("local_mqtt.port", port)
                    self.config_manager.set("local_mqtt.ws_port", ws_port)
                    return True, "服务启动成功"
                # 启动线程已报错，无需继续等待
                if self._last_error:
                    break
            
            if self._last_error:
                error_msg = self._last_error
                if "10048" in error_msg or "address already in use" in error_msg.lower():
                    error_msg = f"端口被占用（TCP {port} 或 WS {ws_port}），请更换端口或关闭占用程序。原始错误: {error_msg}"
                logger.error(f"MQTT服务启动失败: {error_msg}")
                return False, error_msg
            
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
            
            # 如果broker存在且loop存在，尝试优雅关闭
            if self.broker and self.loop:
                try:
                    # 在broker的事件循环中调度关闭任务
                    future = asyncio.run_coroutine_threadsafe(
                        self.broker.shutdown(),
                        self.loop
                    )
                    # 等待关闭完成（最多3秒）
                    future.result(timeout=3)
                    logger.info("Broker已优雅关闭")
                except Exception as e:
                    logger.warning(f"Broker关闭时出现异常: {e}")
            
            # 等待线程结束（最多8秒）
            if self.broker_thread and self.broker_thread.is_alive():
                logger.info("等待MQTT服务线程结束...")
                self.broker_thread.join(timeout=8)
                
                if self.broker_thread.is_alive():
                    logger.warning("MQTT服务线程未能在8秒内结束")
                    return False, "服务停止超时"
                else:
                    logger.info("MQTT服务线程已结束")
            
            self.broker = None
            self.broker_thread = None
            self.loop = None
            
            logger.info("MQTT服务已完全停止")
            
            # 注意：不在这里改写 local_mqtt.auto_start ——
            # 该配置是"下次启动软件时自动启动服务"的用户偏好，
            # 由界面上的复选框独立控制，与本次启停操作无关。
            
            return True, "服务已停止"
            
        except Exception as e:
            logger.error(f"停止MQTT服务失败: {e}", exc_info=True)
            return False, f"停止失败: {str(e)}"
    
    def restart_service(self) -> tuple:
        """重启MQTT服务
        
        Returns:
            tuple: (成功标志, 消息)
        """
        try:
            logger.info("正在重启MQTT服务...")
            
            # 保存当前端口配置
            port = self._port
            ws_port = self._ws_port
            
            # 停止服务
            logger.info("第1步：停止现有服务...")
            success, message = self.stop_service()
            if not success:
                return False, f"停止服务失败: {message}"
            
            # 等待足够长的时间确保端口完全释放
            logger.info("第2步：等待端口释放...")
            import time
            time.sleep(2)  # 增加到2秒
            
            # 启动服务
            logger.info("第3步：启动新服务...")
            success, message = self.start_service(port, ws_port)
            if not success:
                return False, f"启动服务失败: {message}"
            
            logger.info("MQTT服务重启成功")
            return True, "服务重启成功"
            
        except Exception as e:
            logger.error(f"重启MQTT服务失败: {e}", exc_info=True)
            return False, f"重启失败: {str(e)}"
    
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
