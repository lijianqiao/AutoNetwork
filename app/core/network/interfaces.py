"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: interfaces.py
@DateTime: 2025/07/25
@Docs: 网络模块接口定义 - 解决循环依赖问题
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.models.device import Device


class DeviceCredentials:
    """设备认证凭据"""

    def __init__(
        self,
        username: str,
        password: str,
        auth_type: str,
        snmp_community: str | None = None,
        ssh_port: int = 22,
    ):
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.snmp_community = snmp_community
        self.ssh_port = ssh_port

    def __repr__(self) -> str:
        return f"DeviceCredentials(username={self.username}, auth_type={self.auth_type}, ssh_port={self.ssh_port})"


class IAuthenticationProvider(ABC):
    """认证提供者接口"""

    @abstractmethod
    async def get_device_credentials(self, device_id: UUID, dynamic_password: str | None = None) -> DeviceCredentials:
        """获取设备认证凭据

        Args:
            device_id: 设备ID
            dynamic_password: 动态密码（用户手动输入）

        Returns:
            设备认证凭据

        Raises:
            AuthenticationException: 当认证凭据缺失或无效时
        """
        pass

    @abstractmethod
    async def validate_device_credentials(self, device_id: UUID, credentials: DeviceCredentials) -> bool:
        """验证设备认证凭据

        Args:
            device_id: 设备ID
            credentials: 认证凭据

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def clear_dynamic_password_cache(self, device_id: UUID | None = None) -> None:
        """清除动态密码缓存

        Args:
            device_id: 设备ID，如果为None则清除所有缓存
        """
        pass

    @abstractmethod
    def get_cached_password_count(self) -> int:
        """获取缓存的动态密码数量

        Returns:
            缓存的密码数量
        """
        pass


class IConnectionProvider(ABC):
    """连接提供者接口"""

    @abstractmethod
    async def test_connection(self, device: Device, dynamic_password: str | None = None) -> dict[str, Any]:
        """测试设备连接

        Args:
            device: 设备对象
            dynamic_password: 动态密码

        Returns:
            测试结果字典
        """
        pass

    @abstractmethod
    async def execute_device_command(
        self,
        device: Device,
        command: str,
        dynamic_password: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """在设备上执行命令

        Args:
            device: 设备对象
            command: 要执行的命令
            dynamic_password: 动态密码
            timeout: 超时时间

        Returns:
            执行结果字典
        """
        pass

    @abstractmethod
    async def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息

        Returns:
            连接统计信息
        """
        pass

    @abstractmethod
    async def close_connection(self, device_id: UUID) -> bool:
        """关闭指定设备连接

        Args:
            device_id: 设备ID

        Returns:
            是否成功关闭连接
        """
        pass


class IDeviceDAO(ABC):
    """设备数据访问接口"""

    @abstractmethod
    async def get_by_id(self, id: UUID, include_deleted: bool = True) -> Device | None:
        """根据ID获取设备

        Args:
            id: 设备ID
            include_deleted: 是否包含已删除的设备

        Returns:
            设备对象或None
        """
        pass

    @abstractmethod
    async def get_by_ids(self, ids: list[UUID]) -> list[Device]:
        """根据ID列表获取设备

        Args:
            ids: 设备ID列表

        Returns:
            设备对象列表
        """
        pass

    @abstractmethod
    async def get_all(self, include_deleted: bool = True, **filters) -> list[Device]:
        """获取所有设备

        Args:
            include_deleted: 是否包含已删除的设备
            **filters: 过滤条件

        Returns:
            设备对象列表
        """
        pass

    @abstractmethod
    async def update_last_connected(self, device_id: UUID) -> None:
        """更新设备最后连接时间

        Args:
            device_id: 设备ID
        """
        pass
