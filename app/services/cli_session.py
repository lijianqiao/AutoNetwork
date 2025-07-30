"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_session.py
@DateTime: 2025/07/30
@Docs: CLI会话服务 - 管理WebSocket CLI终端会话的业务逻辑
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network.websocket_cli import CLISession, get_cli_session_manager

if TYPE_CHECKING:
    from app.core.permissions.simple_decorators import OperationContext
from app.dao.device import DeviceDAO
from app.dao.vendor import VendorDAO
from app.services.base import BaseService
from app.utils.logger import logger
from app.utils.operation_logger import operation_log_with_context


class CLISessionService(BaseService):
    """CLI会话服务 - 提供CLI终端会话管理的业务接口"""

    def __init__(self):
        self.device_dao = DeviceDAO()
        self.vendor_dao = VendorDAO()
        self.cli_manager = get_cli_session_manager()

    @operation_log_with_context("create", "创建设备CLI会话", "cli_session")
    async def create_device_session(
        self, device_id: UUID, websocket, operation_context: "OperationContext", dynamic_password: str | None = None
    ) -> CLISession:
        """为数据库中的设备创建CLI会话

        Args:
            device_id: 设备ID
            websocket: WebSocket连接
            operation_context: 操作上下文
            dynamic_password: 动态密码

        Returns:
            CLI会话对象
        """
        try:
            # 获取设备信息
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessException(f"设备不存在: {device_id}")

            # 检查设备是否激活
            if not device.is_active:
                raise BusinessException(f"设备已禁用: {device.hostname}")

            # 创建CLI会话
            session = await self.cli_manager.create_session(
                user_id=operation_context.user.id, websocket=websocket, device=device
            )

            # 连接到设备
            await session.connect_to_device(dynamic_password)

            logger.info(
                f"用户 {operation_context.user.username} 创建设备 {device.hostname} 的CLI会话: {session.session_id}"
            )

            return session

        except Exception as e:
            logger.error(f"创建设备CLI会话失败: {e}")
            raise BusinessException(f"创建CLI会话失败: {e}") from e

    @operation_log_with_context("create", "创建手动CLI会话", "cli_session")
    async def create_manual_session(
        self, device_config: dict[str, Any], websocket, operation_context: "OperationContext"
    ) -> CLISession:
        """为手动输入的设备信息创建CLI会话

        Args:
            device_config: 设备配置信息
            websocket: WebSocket连接
            operation_context: 操作上下文

        Returns:
            CLI会话对象
        """
        try:
            # 验证设备配置
            required_fields = ["ip_address", "username", "password"]
            for field in required_fields:
                if field not in device_config or not device_config[field]:
                    raise BusinessException(f"缺少必需的设备配置字段: {field}")

            # 设置默认值
            device_config.setdefault("ssh_port", 22)
            device_config.setdefault("platform", "generic")

            # 验证平台类型
            await self._validate_platform(device_config["platform"])

            # 创建CLI会话
            session = await self.cli_manager.create_session(
                user_id=operation_context.user.id, websocket=websocket, device_config=device_config
            )

            # 连接到设备
            await session.connect_to_device()

            logger.info(
                f"用户 {operation_context.user.username} 创建手动设备 {device_config['ip_address']} 的CLI会话: {session.session_id}"
            )

            return session

        except Exception as e:
            logger.error(f"创建手动CLI会话失败: {e}")
            raise BusinessException(f"创建CLI会话失败: {e}") from e

    async def get_session(self, session_id: str) -> CLISession | None:
        """获取CLI会话

        Args:
            session_id: 会话ID

        Returns:
            CLI会话对象或None
        """
        return await self.cli_manager.get_session(session_id)

    async def close_session(self, session_id: str, operation_context: "OperationContext") -> bool:
        """关闭CLI会话

        Args:
            session_id: 会话ID
            operation_context: 操作上下文

        Returns:
            是否成功关闭
        """
        try:
            session = await self.cli_manager.get_session(session_id)
            if not session:
                return False

            # 检查权限 - 只能关闭自己的会话或管理员可以关闭任何会话
            if session.user_id != operation_context.user.id:
                # TODO: 检查是否是管理员
                raise BusinessException("没有权限关闭此会话")

            success = await self.cli_manager.remove_session(session_id)

            if success:
                logger.info(f"用户 {operation_context.user.username} 关闭CLI会话: {session_id}")

            return success

        except Exception as e:
            logger.error(f"关闭CLI会话失败: {e}")
            return False

    async def get_user_sessions(self, operation_context: "OperationContext") -> list[dict[str, Any]]:
        """获取用户的所有CLI会话

        Args:
            operation_context: 操作上下文

        Returns:
            会话信息列表
        """
        try:
            sessions = await self.cli_manager.get_user_sessions(operation_context.user.id)
            return [session.get_session_info() for session in sessions]

        except Exception as e:
            logger.error(f"获取用户CLI会话失败: {e}")
            return []

    async def get_all_sessions(self, operation_context: "OperationContext") -> list[dict[str, Any]]:
        """获取所有CLI会话（管理员功能）

        Args:
            operation_context: 操作上下文

        Returns:
            会话信息列表
        """
        try:
            # TODO: 检查管理员权限

            all_sessions = []
            for session in self.cli_manager.sessions.values():
                session_info = session.get_session_info()
                all_sessions.append(session_info)

            return all_sessions

        except Exception as e:
            logger.error(f"获取所有CLI会话失败: {e}")
            return []

    async def get_session_stats(self) -> dict[str, Any]:
        """获取CLI会话统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = self.cli_manager.get_stats()
            stats["timestamp"] = datetime.now().isoformat()
            return stats

        except Exception as e:
            logger.error(f"获取CLI会话统计失败: {e}")
            return {"error": str(e)}

    async def send_session_input(
        self, session_id: str, user_input: str, operation_context: "OperationContext"
    ) -> str | None:
        """向CLI会话发送用户输入

        Args:
            session_id: 会话ID
            user_input: 用户输入
            operation_context: 操作上下文

        Returns:
            设备响应或None
        """
        try:
            session = await self.cli_manager.get_session(session_id)
            if not session:
                raise BusinessException("会话不存在")

            # 检查权限 - 只能向自己的会话发送输入
            if session.user_id != operation_context.user.id:
                raise BusinessException("没有权限操作此会话")

            # 发送输入到设备
            response = await session.send_input(user_input)
            return response

        except Exception as e:
            logger.error(f"发送CLI会话输入失败: {e}")
            raise BusinessException(f"发送输入失败: {e}") from e

    async def reconnect_session(
        self, session_id: str, operation_context: "OperationContext", dynamic_password: str | None = None
    ) -> bool:
        """重连CLI会话

        Args:
            session_id: 会话ID
            operation_context: 操作上下文
            dynamic_password: 动态密码

        Returns:
            是否重连成功
        """
        try:
            session = await self.cli_manager.get_session(session_id)
            if not session:
                raise BusinessException("会话不存在")

            # 检查权限
            if session.user_id != operation_context.user.id:
                raise BusinessException("没有权限操作此会话")

            # 断开并重连
            await session.disconnect()
            success = await session.connect_to_device(dynamic_password)

            if success:
                logger.info(f"CLI会话重连成功: {session_id}")

            return success

        except Exception as e:
            logger.error(f"CLI会话重连失败: {e}")
            return False

    async def get_supported_platforms(self) -> list[dict[str, str]]:
        """获取支持的设备平台列表

        Returns:
            平台信息列表
        """
        try:
            # 从数据库获取所有厂商信息
            vendors = await self.vendor_dao.get_all()

            platforms = []
            for vendor in vendors:
                platforms.append(
                    {
                        "vendor_code": vendor.vendor_code,
                        "vendor_name": vendor.vendor_name,
                        "scrapli_platform": vendor.scrapli_platform,
                        "description": f"{vendor.vendor_name} ({vendor.scrapli_platform})",
                    }
                )

            # 添加通用平台
            platforms.append(
                {
                    "vendor_code": "generic",
                    "vendor_name": "通用",
                    "scrapli_platform": "generic",
                    "description": "通用设备平台",
                }
            )

            return platforms

        except Exception as e:
            logger.error(f"获取支持平台列表失败: {e}")
            return []

    async def _validate_platform(self, platform: str) -> None:
        """验证平台类型是否支持

        Args:
            platform: 平台标识
        """
        if platform == "generic":
            return

        # 检查是否是已知的Scrapli平台
        known_platforms = [
            "hp_comware",
            "huawei_vrp",
            "cisco_iosxe",
            "cisco_ios",
            "cisco_nxos",
            "juniper_junos",
            "arista_eos",
            "nokia_sros",
            "extreme_exos",
            "mikrotik_routeros",
            "vyos",
            "linux",
        ]

        if platform not in known_platforms:
            # 检查数据库中是否存在此平台
            vendor = await self.vendor_dao.get_one(scrapli_platform=platform)
            if not vendor:
                logger.warning(f"未知的设备平台: {platform}，将使用通用平台")

    async def validate_device_connection(
        self, device_config: dict[str, Any], operation_context: "OperationContext"
    ) -> dict[str, Any]:
        """验证设备连接配置

        Args:
            device_config: 设备配置
            operation_context: 操作上下文

        Returns:
            验证结果
        """
        try:
            # 验证必需字段
            required_fields = ["ip_address", "username", "password"]
            missing_fields = []

            for field in required_fields:
                if field not in device_config or not device_config[field]:
                    missing_fields.append(field)

            if missing_fields:
                return {"valid": False, "error": f"缺少必需字段: {', '.join(missing_fields)}"}

            # 验证IP地址格式
            import ipaddress

            try:
                ipaddress.ip_address(device_config["ip_address"])
            except ValueError:
                return {"valid": False, "error": "IP地址格式无效"}

            # 验证端口范围
            ssh_port = device_config.get("ssh_port", 22)
            if not isinstance(ssh_port, int) or ssh_port < 1 or ssh_port > 65535:
                return {"valid": False, "error": "SSH端口范围无效 (1-65535)"}

            # 验证平台
            platform = device_config.get("platform", "generic")
            await self._validate_platform(platform)

            return {"valid": True, "message": "设备配置验证通过"}

        except Exception as e:
            logger.error(f"验证设备连接配置失败: {e}")
            return {"valid": False, "error": f"验证失败: {e}"}
