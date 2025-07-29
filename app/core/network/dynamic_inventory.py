"""Nornir动态设备清单构建器

该模块提供从数据库动态构建Nornir设备清单的功能，
支持多厂商设备、认证集成、智能分组等特性。
"""

from typing import Any

from nornir.core.inventory import Defaults, Group, Groups, Host, Hosts, Inventory, ParentGroups

from app.dao.device import DeviceDAO
from app.dao.region import RegionDAO
from app.dao.vendor import VendorDAO
from app.models.device import Device
from app.models.region import Region
from app.models.vendor import Vendor
from app.utils.logger import logger


class DynamicInventoryBuilder:
    """动态设备清单构建器"""

    def __init__(self):
        """初始化动态清单构建器"""
        self.device_dao = DeviceDAO()
        self.vendor_dao = VendorDAO()
        self.region_dao = RegionDAO()

    async def build_inventory(
        self,
        filter_hostname: str | None = None,
        filter_vendor: str | None = None,
        filter_region: str | None = None,
        filter_device_type: str | None = None,
        filter_network_layer: str | None = None,
        include_inactive: bool = False,
    ) -> Inventory:
        """构建Nornir设备清单

        Args:
            filter_hostname: 主机名过滤
            filter_vendor: 厂商过滤
            filter_region: 区域过滤
            filter_device_type: 设备类型过滤
            filter_network_layer: 网络层级过滤
            include_inactive: 是否包含非活跃设备

        Returns:
            Nornir Inventory对象
        """
        logger.info("开始构建动态设备清单")

        # 获取设备列表
        devices = await self._get_filtered_devices(
            hostname=filter_hostname,
            vendor=filter_vendor,
            region=filter_region,
            device_type=filter_device_type,
            network_layer=filter_network_layer,
            include_inactive=include_inactive,
        )

        # 获取厂商和区域信息
        vendors = await self.vendor_dao.get_all()
        regions = await self.region_dao.get_all()

        # 构建主机字典
        hosts_dict = {}
        for device in devices:
            host = await self._build_host(device, vendors, regions)
            if host:
                hosts_dict[device.hostname] = host

        # 构建组字典
        groups_dict = await self._build_groups(devices, vendors, regions)

        # 设置默认值
        defaults = Defaults(hostname="", port=22, username="", password="", platform="", data={})

        # 创建 Nornir 类型的 hosts 和 groups
        hosts = Hosts(hosts_dict)
        groups = Groups(groups_dict)

        inventory = Inventory(hosts=hosts, groups=groups, defaults=defaults)

        logger.info(f"动态设备清单构建完成，包含 {len(hosts)} 台设备")
        return inventory

    async def _get_filtered_devices(
        self,
        hostname: str | None = None,
        vendor: str | None = None,
        region: str | None = None,
        device_type: str | None = None,
        network_layer: str | None = None,
        include_inactive: bool = False,
    ) -> list[Device]:
        """获取过滤后的设备列表"""

        # 构建过滤条件
        vendor_id = None
        if vendor:
            vendor_obj = await self.vendor_dao.get_by_vendor_code(vendor)
            if vendor_obj:
                vendor_id = vendor_obj.id

        region_id = None
        if region:
            region_obj = await self.region_dao.get_by_region_code(region)
            if region_obj:
                region_id = region_obj.id

        # 搜索设备
        devices = await self.device_dao.search_devices(
            keyword=hostname,
            vendor_id=vendor_id,
            region_id=region_id,
            device_type=device_type,
            network_layer=network_layer,
            is_active=None if include_inactive else True,
        )

        return devices

    async def _build_host(self, device: Device, vendors: list[Vendor], regions: list[Region]) -> Host | None:
        """构建单个主机对象"""
        try:
            # 获取厂商信息
            vendor = next((v for v in vendors if v.id == device.vendor.id), None)
            if not vendor:
                logger.warning(f"设备 {device.hostname} 的厂商信息未找到")
                return None

            # 获取区域信息
            region = next((r for r in regions if r.id == device.region.id), None)
            if not region:
                logger.warning(f"设备 {device.hostname} 的区域信息未找到")
                return None

            # 构建连接选项
            connection_options = await self._build_connection_options(device, vendor)

            # 构建主机数据
            host_data = {
                "device_id": str(device.id),
                "device_type": device.device_type,
                "network_layer": device.network_layer,
                "vendor_code": vendor.vendor_code,
                "vendor_name": vendor.vendor_name,
                "region_code": region.region_code,
                "region_name": region.region_name,
                "model": device.model,
                "serial_number": device.serial_number,
                "location": device.location,
                "auth_type": device.auth_type,
                "is_active": device.is_active,
                "last_connected_at": device.last_connected_at.isoformat() if device.last_connected_at else None,
            }

            # 构建组列表
            group_names = [
                f"vendor_{vendor.vendor_code}",
                f"region_{region.region_code}",
                f"type_{device.device_type}",
                f"layer_{device.network_layer}",
            ]

            # 创建 Group 对象列表
            group_objects = [Group(name=group_name) for group_name in group_names]

            host = Host(
                name=device.hostname,
                hostname=device.ip_address,
                port=device.ssh_port,
                username="",  # 将在运行时动态设置
                password="",  # 将在运行时动态设置
                platform=vendor.scrapli_platform,
                groups=ParentGroups(group_objects),
                data=host_data,
                connection_options=connection_options,
            )

            return host

        except Exception as e:
            logger.error(f"构建主机 {device.hostname} 失败: {e}")
            return None

    async def _build_connection_options(self, device: Device, vendor: Vendor) -> dict[str, Any]:
        """构建连接选项"""
        return {
            "scrapli": {
                "platform": vendor.scrapli_platform,
                "transport": "ssh2",
                "transport_options": {
                    "open_cmd": ["-o", "KexAlgorithms=+diffie-hellman-group1-sha1"],
                },
                "timeout_socket": vendor.connection_timeout,
                "timeout_transport": vendor.connection_timeout,
                "timeout_ops": vendor.command_timeout,
                "comms_prompt_pattern": r"^[a-zA-Z0-9.\-_\[\]<>]+[#>]\s*$",
                "comms_return_char": "\n",
                "ssh_config_file": False,
                "auth_strict_key": False,
                "auth_bypass": False,
            }
        }

    async def _build_groups(
        self, devices: list[Device], vendors: list[Vendor], regions: list[Region]
    ) -> dict[str, Group]:
        """构建组字典"""
        groups = {}

        # 厂商组
        for vendor in vendors:
            group_name = f"vendor_{vendor.vendor_code}"
            vendor_devices = [d for d in devices if d.vendor.id == vendor.id]
            if vendor_devices:
                groups[group_name] = Group(
                    name=group_name,
                    data={
                        "vendor_code": vendor.vendor_code,
                        "vendor_name": vendor.vendor_name,
                        "scrapli_platform": vendor.scrapli_platform,
                        "device_count": len(vendor_devices),
                    },
                )

        # 区域组
        for region in regions:
            group_name = f"region_{region.region_code}"
            region_devices = [d for d in devices if d.region.id == region.id]
            if region_devices:
                groups[group_name] = Group(
                    name=group_name,
                    data={
                        "region_code": region.region_code,
                        "region_name": region.region_name,
                        "device_count": len(region_devices),
                    },
                )

        # 设备类型组
        device_types = {d.device_type for d in devices}
        for device_type in device_types:
            group_name = f"type_{device_type}"
            type_devices = [d for d in devices if d.device_type == device_type]
            groups[group_name] = Group(
                name=group_name, data={"device_type": device_type, "device_count": len(type_devices)}
            )

        # 网络层级组
        network_layers = {d.network_layer for d in devices}
        for network_layer in network_layers:
            group_name = f"layer_{network_layer}"
            layer_devices = [d for d in devices if d.network_layer == network_layer]
            groups[group_name] = Group(
                name=group_name, data={"network_layer": network_layer, "device_count": len(layer_devices)}
            )

        return groups

    async def get_devices_by_hostname(self, hostname: str) -> list[Device]:
        """根据主机名获取设备"""
        device = await self.device_dao.get_by_hostname(hostname)
        return [device] if device else []

    async def get_devices_by_vendor(self, vendor_code: str) -> list[Device]:
        """根据厂商代码获取设备列表"""
        vendor = await self.vendor_dao.get_by_vendor_code(vendor_code)
        if not vendor:
            return []
        return await self.device_dao.get_devices_by_vendor(vendor.id)

    async def get_devices_by_region(self, region_code: str) -> list[Device]:
        """根据区域代码获取设备列表"""
        region = await self.region_dao.get_by_region_code(region_code)
        if not region:
            return []
        return await self.device_dao.get_devices_by_region(region.id)
