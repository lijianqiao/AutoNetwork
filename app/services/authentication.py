"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: authentication.py
@DateTime: 2025/07/23
@Docs: 设备认证管理服务 - 动态/静态密码管理器
"""

from uuid import UUID

from app.core.exceptions import BadRequestException, BusinessException
from app.dao.device import DeviceDAO
from app.dao.region import RegionDAO
from app.dao.vendor import VendorDAO
from app.models.device import Device
from app.models.region import Region
from app.models.vendor import Vendor
from app.utils.encryption import decrypt_text
from app.utils.logger import logger


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


class AuthenticationManager:
    """设备认证管理器 - 实现动态/静态密码管理"""

    def __init__(self):
        self.device_dao = DeviceDAO()
        self.region_dao = RegionDAO()
        self.vendor_dao = VendorDAO()

        # 用户名生成规则配置
        self.username_patterns = {
            "access": "op{region_code}jr",  # 接入层
            "aggregation": "op{region_code}jr",  # 汇聚层
            "core": "op{region_code}jr",  # 核心层
        }

        # 动态密码输入缓存（仅在会话期间有效）
        self._dynamic_password_cache: dict[str, str] = {}

    async def get_device_credentials(self, device_id: UUID, dynamic_password: str | None = None) -> DeviceCredentials:
        """获取设备认证凭据

        Args:
            device_id: 设备ID
            dynamic_password: 动态密码（用户手动输入）

        Returns:
            设备认证凭据

        Raises:
            BusinessException: 当认证凭据缺失或无效时
        """
        logger.info(f"开始获取设备认证凭据: device_id={device_id}")

        # 获取设备信息
        device = await self.device_dao.get_by_id(device_id)
        if not device:
            raise BadRequestException(f"设备不存在: {device_id}")

        # 获取关联的基地和厂商信息
        region = await device.region
        vendor = await device.vendor

        if not region or not vendor:
            raise BusinessException(f"设备关联的基地或厂商信息缺失: device_id={device_id}")

        logger.debug(
            f"设备信息: hostname={device.hostname}, auth_type={device.auth_type}, network_layer={device.network_layer}"
        )

        # 根据认证类型获取凭据
        if device.auth_type == "dynamic":
            credentials = await self._handle_dynamic_password_input(device, region, dynamic_password)
        elif device.auth_type == "static":
            credentials = await self._get_static_password_from_db(device, region, vendor)
        else:
            raise BusinessException(f"不支持的认证类型: {device.auth_type}")

        logger.info(f"成功获取设备认证凭据: device_id={device_id}, auth_type={device.auth_type}")
        return credentials

    async def _handle_dynamic_password_input(
        self, device: Device, region: Region, dynamic_password: str | None = None
    ) -> DeviceCredentials:
        """处理动态密码输入

        Args:
            device: 设备对象
            region: 基地对象
            dynamic_password: 用户输入的动态密码

        Returns:
            设备认证凭据

        Raises:
            BusinessException: 当动态密码未提供时
        """
        logger.debug(f"处理动态密码认证: device={device.hostname}")

        # 检查是否提供了动态密码
        if not dynamic_password:
            # 尝试从缓存中获取（仅在同一会话中有效）
            cache_key = f"{device.id}_{device.hostname}"
            cached_password = self._dynamic_password_cache.get(cache_key)
            if not cached_password:
                raise BusinessException(
                    f"设备 {device.hostname} 使用动态密码认证，请提供密码",
                    detail={
                        "device_id": str(device.id),
                        "hostname": device.hostname,
                        "auth_type": "dynamic",
                        "requires_password_input": True,
                    },
                )
            dynamic_password = cached_password
        else:
            # 缓存动态密码（仅在会话期间有效）
            cache_key = f"{device.id}_{device.hostname}"
            self._dynamic_password_cache[cache_key] = dynamic_password

        # 生成动态用户名
        username = self._generate_dynamic_username(device, region)

        return DeviceCredentials(
            username=username,
            password=dynamic_password,  # 直接使用动态密码
            auth_type="dynamic",
            snmp_community=region.snmp_community,  # 直接使用SNMP社区字符串
            ssh_port=device.ssh_port,
        )

    async def _get_static_password_from_db(self, device: Device, region: Region, vendor: Vendor) -> DeviceCredentials:
        """从数据库获取静态密码

        Args:
            device: 设备对象
            region: 基地对象
            vendor: 厂商对象

        Returns:
            设备认证凭据

        Raises:
            BusinessException: 当静态凭据缺失时
        """
        logger.debug(f"获取静态密码认证: device={device.hostname}")

        # 检查静态凭据是否完整
        if not device.static_username or not device.static_password:
            raise BusinessException(
                f"设备 {device.hostname} 的静态认证凭据不完整",
                detail={
                    "device_id": str(device.id),
                    "hostname": device.hostname,
                    "auth_type": "static",
                    "missing_username": not device.static_username,
                    "missing_password": not device.static_password,
                },
            )

        # 检查密码是否为空
        if not device.static_password or device.static_password.strip() == "":
            raise BusinessException(f"设备 {device.hostname} 的静态密码为空")

        # 解密静态凭据
        try:
            decrypted_password = decrypt_text(device.static_password)
            logger.debug(f"设备 {device.hostname} 的密码已成功解密")

            snmp_community = region.snmp_community
            if snmp_community and snmp_community.strip():
                snmp_community = decrypt_text(snmp_community)
                logger.debug(f"基地 {region.region_name} 的SNMP社区字符串已成功解密")

        except Exception as e:
            logger.error(f"解密静态凭据失败: device={device.hostname}, error={e}")
            raise BusinessException(f"设备 {device.hostname} 的静态凭据解密失败") from e

        return DeviceCredentials(
            username=device.static_username,
            password=decrypted_password,
            auth_type="static",
            snmp_community=snmp_community,
            ssh_port=device.ssh_port,
        )

    def _generate_dynamic_username(self, device: Device, region: Region) -> str:
        """根据设备网络层级和基地代码生成动态用户名

        Args:
            device: 设备对象
            region: 基地对象

        Returns:
            生成的用户名
        """
        # 获取用户名模式
        pattern = self.username_patterns.get(device.network_layer, "{region_code}_{network_layer}_admin")

        # 生成用户名
        username = pattern.format(region_code=region.region_code.lower(), network_layer=device.network_layer)

        logger.debug(
            f"生成动态用户名: device={device.hostname}, "
            f"network_layer={device.network_layer}, "
            f"region_code={region.region_code}, "
            f"username={username}"
        )

        return username

    async def validate_device_credentials(self, device_id: UUID, credentials: DeviceCredentials) -> bool:
        """验证设备认证凭据（基础验证）

        Args:
            device_id: 设备ID
            credentials: 认证凭据

        Returns:
            验证结果
        """
        logger.debug(f"验证设备认证凭据: device_id={device_id}")

        # 基础验证
        if not credentials.username or not credentials.password:
            logger.warning(f"设备认证凭据不完整: device_id={device_id}")
            return False

        # 检查用户名和密码长度
        if len(credentials.username) < 1 or len(credentials.password) < 1:
            logger.warning(f"设备认证凭据长度不符合要求: device_id={device_id}")
            return False

        return True

    def clear_dynamic_password_cache(self, device_id: UUID | None = None) -> None:
        """清除动态密码缓存

        Args:
            device_id: 设备ID，如果为None则清除所有缓存
        """
        if device_id is None:
            # 清除所有缓存
            self._dynamic_password_cache.clear()
            logger.info("已清除所有动态密码缓存")
        else:
            # 清除特定设备的缓存
            keys_to_remove = [key for key in self._dynamic_password_cache.keys() if key.startswith(str(device_id))]
            for key in keys_to_remove:
                del self._dynamic_password_cache[key]
            logger.info(f"已清除设备 {device_id} 的动态密码缓存")

    def get_cached_password_count(self) -> int:
        """获取缓存的动态密码数量

        Returns:
            缓存的密码数量
        """
        return len(self._dynamic_password_cache)
