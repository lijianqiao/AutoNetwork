"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: websocket_cli.py
@DateTime: 2025/07/30
@Docs: WebSocket CLI处理器 - 实现多用户并发CLI会话终端
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliException

from app.core.exceptions import BusinessException
from app.core.network.config import get_platform_for_vendor, network_config
from app.models.device import Device
from app.models.vendor import Vendor
from app.services.authentication import AuthenticationManager
from app.utils.logger import logger


class CLISession:
    """CLI会话对象 - 管理单个用户的设备CLI连接"""

    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        websocket: WebSocket,
        device: Device | None = None,
        device_config: dict[str, Any] | None = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.websocket = websocket
        self.device = device
        self.device_config = device_config  # 手动输入的设备配置
        self.scrapli_connection: AsyncScrapli | None = None
        self.is_connected = False
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.command_count = 0
        self.auth_manager = AuthenticationManager()
        self._connection_lock = asyncio.Lock()
        self._input_buffer = ""
        self._in_config_mode = False
        self._device_prompt = ""

    async def connect_to_device(self, dynamic_password: str | None = None) -> bool:
        """连接到设备"""
        async with self._connection_lock:
            try:
                if self.is_connected and self.scrapli_connection and self.scrapli_connection.isalive():
                    return True

                # 获取设备认证信息
                if self.device:
                    # 使用数据库中的设备
                    credentials = await self.auth_manager.get_device_credentials(self.device.id, dynamic_password)
                    vendor = await self.device.vendor
                    platform = self._get_scrapli_platform(vendor) if vendor else "generic"

                    # Scrapli连接配置
                    scrapli_config = {
                        "host": self.device.ip_address,
                        "auth_username": credentials.username,
                        "auth_password": credentials.password,
                        "port": credentials.ssh_port,
                        "platform": platform,
                        "transport": "asyncssh",
                        "auth_strict_key": False,
                        "timeout_socket": network_config.connection.CONNECT_TIMEOUT,
                        "timeout_transport": network_config.connection.CONNECT_TIMEOUT,
                        "timeout_ops": network_config.connection.COMMAND_TIMEOUT,
                        "transport_options": {
                            "known_hosts": None,
                            "server_host_key_algs": [],
                            "client_keys": [],
                        },
                    }

                elif self.device_config:
                    # 使用手动输入的设备配置
                    scrapli_config = {
                        "host": self.device_config["ip_address"],
                        "auth_username": self.device_config["username"],
                        "auth_password": self.device_config["password"],
                        "port": self.device_config.get("ssh_port", 22),
                        "platform": self.device_config.get("platform", "generic"),
                        "transport": "asyncssh",
                        "auth_strict_key": False,
                        "timeout_socket": network_config.connection.CONNECT_TIMEOUT,
                        "timeout_transport": network_config.connection.CONNECT_TIMEOUT,
                        "timeout_ops": network_config.connection.COMMAND_TIMEOUT,
                        "transport_options": {
                            "known_hosts": None,
                            "server_host_key_algs": [],
                            "client_keys": [],
                        },
                    }
                else:
                    raise BusinessException("缺少设备连接信息")

                # 创建Scrapli连接
                self.scrapli_connection = AsyncScrapli(**scrapli_config)
                await self.scrapli_connection.open()
                self.is_connected = True

                # 获取初始提示符
                try:
                    prompt_response = await self.scrapli_connection.get_prompt()
                    self._device_prompt = prompt_response.strip()
                except Exception:
                    self._device_prompt = "# "

                logger.info(f"CLI会话 {self.session_id} 成功连接到设备")
                return True

            except Exception as e:
                self.is_connected = False
                if self.scrapli_connection:
                    try:
                        await self.scrapli_connection.close()
                    except Exception:
                        pass
                    self.scrapli_connection = None

                logger.error(f"CLI会话 {self.session_id} 连接设备失败: {e}")
                raise BusinessException(f"连接设备失败: {e}") from e

    async def disconnect(self) -> None:
        """断开设备连接"""
        async with self._connection_lock:
            try:
                if self.scrapli_connection and self.scrapli_connection.isalive():
                    await self.scrapli_connection.close()
                self.is_connected = False
                self.scrapli_connection = None
                logger.info(f"CLI会话 {self.session_id} 已断开设备连接")
            except Exception as e:
                logger.error(f"CLI会话 {self.session_id} 断开连接时出错: {e}")

    async def send_input(self, user_input: str) -> str | None:
        """发送用户输入到设备"""
        if not self.is_connected or not self.scrapli_connection:
            raise BusinessException("设备未连接")

        try:
            self.last_activity = datetime.now()
            self.command_count += 1

            # 处理特殊键和控制字符
            if user_input == "\r" or user_input == "\n":
                # 回车键 - 执行缓冲区中的命令
                if self._input_buffer.strip():
                    command = self._input_buffer.strip()
                    self._input_buffer = ""

                    # 检查是否是进入/退出配置模式的命令
                    self._update_config_mode(command)

                    # 发送命令到设备
                    response = await self.scrapli_connection.send_command(
                        command,
                        timeout_ops=30,
                        failed_when_contains=[],  # 不自动判断命令失败
                    )

                    return response.result if hasattr(response, "result") else str(response)
                else:
                    # 空回车，获取当前提示符
                    try:
                        prompt = await self.scrapli_connection.get_prompt()
                        return f"\r\n{prompt}"
                    except Exception:
                        return f"\r\n{self._device_prompt}"

            elif user_input == "\x03":  # Ctrl+C
                # 发送中断信号
                try:
                    await self.scrapli_connection.channel.send_input("\x03")
                    response = await self.scrapli_connection.get_prompt()
                    return response
                except Exception:
                    return "^C\r\n"

            elif user_input == "\x1b[A":  # 上箭头
                # 命令历史 - 简单实现
                return "\x1b[A"

            elif user_input == "\x1b[B":  # 下箭头
                return "\x1b[B"

            elif user_input == "\x1b[C":  # 右箭头
                return "\x1b[C"

            elif user_input == "\x1b[D":  # 左箭头
                return "\x1b[D"

            elif user_input == "\x7f" or user_input == "\x08":  # 退格键
                if self._input_buffer:
                    self._input_buffer = self._input_buffer[:-1]
                    return "\x08 \x08"  # 退格、空格、退格
                return ""

            elif user_input == "\t":  # Tab键 - 命令补全
                if self._input_buffer.strip():
                    try:
                        # 简单的Tab补全实现
                        partial_command = self._input_buffer + "?"
                        response = await self.scrapli_connection.send_command(
                            partial_command, timeout_ops=5, failed_when_contains=[]
                        )
                        return response.result if hasattr(response, "result") else ""
                    except Exception:
                        return ""
                return ""

            else:
                # 普通字符输入
                if user_input.isprintable():
                    self._input_buffer += user_input
                    return user_input  # 回显用户输入

                return ""

        except ScrapliException as e:
            logger.error(f"CLI会话 {self.session_id} Scrapli错误: {e}")
            return f"\r\nScrapli错误: {e}\r\n{self._device_prompt}"

        except Exception as e:
            logger.error(f"CLI会话 {self.session_id} 处理输入失败: {e}")
            return f"\r\n错误: {e}\r\n{self._device_prompt}"

    def _update_config_mode(self, command: str) -> None:
        """更新配置模式状态"""
        command_lower = command.lower().strip()

        # 进入配置模式的命令
        config_enter_commands = [
            "system-view",
            "configure terminal",
            "configure",
            "conf t",
            "configuration terminal",
            "enable",
            "config",
        ]

        # 退出配置模式的命令
        config_exit_commands = ["quit", "exit", "end", "return", "disable"]

        if any(cmd in command_lower for cmd in config_enter_commands):
            self._in_config_mode = True
        elif any(cmd in command_lower for cmd in config_exit_commands):
            self._in_config_mode = False

    def _get_scrapli_platform(self, vendor: Vendor) -> str:
        """获取Scrapli平台标识"""
        if vendor and vendor.scrapli_platform:
            return vendor.scrapli_platform
        if vendor:
            return get_platform_for_vendor(vendor.vendor_code)
        return "generic"

    def get_session_info(self) -> dict[str, Any]:
        """获取会话信息"""
        device_info = {}
        if self.device:
            device_info = {
                "device_id": str(self.device.id),
                "hostname": self.device.hostname,
                "ip_address": self.device.ip_address,
                "device_type": self.device.device_type,
            }
        elif self.device_config:
            device_info = {
                "ip_address": self.device_config["ip_address"],
                "platform": self.device_config.get("platform", "generic"),
                "ssh_port": self.device_config.get("ssh_port", 22),
            }

        return {
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "is_connected": self.is_connected,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "command_count": self.command_count,
            "in_config_mode": self._in_config_mode,
            "device_prompt": self._device_prompt,
            "device_info": device_info,
        }


class CLISessionManager:
    """CLI会话管理器 - 管理所有活跃的CLI会话"""

    def __init__(self):
        self.sessions: dict[str, CLISession] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._session_lock = asyncio.Lock()

    async def start(self) -> None:
        """启动会话管理器"""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("CLI会话管理器已启动")

    async def stop(self) -> None:
        """停止会话管理器"""
        # 取消清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 关闭所有会话
        await self.close_all_sessions()
        logger.info("CLI会话管理器已停止")

    async def create_session(
        self,
        user_id: UUID,
        websocket: WebSocket,
        device: Device | None = None,
        device_config: dict[str, Any] | None = None,
    ) -> CLISession:
        """创建新的CLI会话"""
        async with self._session_lock:
            session_id = str(uuid.uuid4())
            session = CLISession(
                session_id=session_id, user_id=user_id, websocket=websocket, device=device, device_config=device_config
            )

            self.sessions[session_id] = session
            logger.info(f"创建CLI会话: {session_id}, 用户: {user_id}")
            return session

    async def get_session(self, session_id: str) -> CLISession | None:
        """获取会话"""
        return self.sessions.get(session_id)

    async def remove_session(self, session_id: str) -> bool:
        """移除会话"""
        async with self._session_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                await session.disconnect()
                del self.sessions[session_id]
                logger.info(f"移除CLI会话: {session_id}")
                return True
            return False

    async def close_all_sessions(self) -> None:
        """关闭所有会话"""
        async with self._session_lock:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.remove_session(session_id)
            logger.info("所有CLI会话已关闭")

    async def get_user_sessions(self, user_id: UUID) -> list[CLISession]:
        """获取用户的所有会话"""
        return [session for session in self.sessions.values() if session.user_id == user_id]

    async def _cleanup_loop(self) -> None:
        """清理循环 - 定期清理无效会话"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._cleanup_inactive_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"CLI会话清理循环出错: {e}")

    async def _cleanup_inactive_sessions(self) -> None:
        """清理非活跃会话"""
        async with self._session_lock:
            inactive_sessions = []
            now = datetime.now()

            for session_id, session in self.sessions.items():
                # 清理条件：
                # 1. 超过1小时未活动
                # 2. WebSocket连接已断开
                # 3. 设备连接已断开且超过10分钟
                idle_time = (now - session.last_activity).total_seconds()

                should_cleanup = False

                if idle_time > 3600:  # 1小时未活动
                    should_cleanup = True
                    logger.info(f"会话 {session_id} 因长时间未活动被清理")
                elif not session.is_connected and idle_time > 600:  # 设备未连接且10分钟未活动
                    should_cleanup = True
                    logger.info(f"会话 {session_id} 因设备未连接且长时间未活动被清理")

                if should_cleanup:
                    inactive_sessions.append(session_id)

            # 移除非活跃会话
            for session_id in inactive_sessions:
                await self.remove_session(session_id)

            if inactive_sessions:
                logger.info(f"清理了 {len(inactive_sessions)} 个非活跃CLI会话")

    def get_stats(self) -> dict[str, Any]:
        """获取会话统计信息"""
        total_sessions = len(self.sessions)
        connected_sessions = sum(1 for s in self.sessions.values() if s.is_connected)
        total_commands = sum(s.command_count for s in self.sessions.values())

        # 按用户统计
        user_sessions = {}
        for session in self.sessions.values():
            user_id = str(session.user_id)
            if user_id not in user_sessions:
                user_sessions[user_id] = 0
            user_sessions[user_id] += 1

        return {
            "total_sessions": total_sessions,
            "connected_sessions": connected_sessions,
            "disconnected_sessions": total_sessions - connected_sessions,
            "total_commands_executed": total_commands,
            "user_sessions": user_sessions,
            "avg_commands_per_session": total_commands / max(total_sessions, 1),
        }


# 全局会话管理器实例
_global_session_manager: CLISessionManager | None = None


def get_cli_session_manager() -> CLISessionManager:
    """获取全局CLI会话管理器实例"""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = CLISessionManager()
    return _global_session_manager


async def start_cli_session_manager() -> None:
    """启动全局CLI会话管理器"""
    manager = get_cli_session_manager()
    await manager.start()
    logger.info("全局CLI会话管理器已启动")


async def stop_cli_session_manager() -> None:
    """停止全局CLI会话管理器"""
    global _global_session_manager
    if _global_session_manager:
        await _global_session_manager.stop()
        _global_session_manager = None
        logger.info("全局CLI会话管理器已停止")
