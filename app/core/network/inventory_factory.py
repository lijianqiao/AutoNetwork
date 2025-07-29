"""Nornir动态设备清单工厂模块

提供便捷的动态设备清单创建和管理接口
"""

from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from nornir.core.inventory import Group, Host, Inventory

from app.core.network.dynamic_inventory import DynamicInventoryBuilder

# 移除不需要的导入
from app.utils.logger import logger


class InventoryFactory:
    """动态设备清单工厂类

    提供便捷的静态方法来创建和管理动态设备清单
    """

    @staticmethod
    @asynccontextmanager
    async def create_builder():
        """创建动态清单构建器的上下文管理器

        使用示例:
            async with InventoryFactory.create_builder() as builder:
                inventory = await builder.build_inventory()
        """
        builder = DynamicInventoryBuilder()
        yield builder

    @staticmethod
    async def build_inventory(
        device_hostnames: list[str] | None = None,
        region_ids: list[UUID] | None = None,
        vendor_ids: list[UUID] | None = None,
        device_types: list[str] | None = None,
        user_id: UUID | None = None,
    ) -> Inventory:
        """快速构建设备清单

        Args:
            device_hostnames: 指定设备主机名列表
            region_ids: 区域ID列表过滤
            vendor_ids: 厂商ID列表过滤
            device_types: 设备类型列表过滤
            user_id: 用户ID，用于获取认证信息

        Returns:
            Inventory: Nornir设备清单对象
        """
        async with InventoryFactory.create_builder() as builder:
            # 根据参数构建过滤条件
            filter_hostname = device_hostnames[0] if device_hostnames and len(device_hostnames) == 1 else None
            filter_device_type = device_types[0] if device_types and len(device_types) == 1 else None

            return await builder.build_inventory(
                filter_hostname=filter_hostname,
                filter_device_type=filter_device_type,
                include_inactive=False,
            )

    @staticmethod
    async def get_device(hostname: str, user_id: int | None = None) -> Host | None:
        """获取单个设备

        Args:
            hostname: 设备主机名
            user_id: 用户ID，用于获取认证信息

        Returns:
            Host: 设备Host对象，不存在则返回None
        """
        async with InventoryFactory.create_builder() as builder:
            inventory = await builder.build_inventory(filter_hostname=hostname)
            return inventory.hosts.get(hostname)

    @staticmethod
    async def get_devices_by_vendor(vendor_name: str, user_id: int | None = None) -> list[Host]:
        """根据厂商名称获取设备列表

        Args:
            vendor_name: 厂商名称
            user_id: 用户ID，用于获取认证信息

        Returns:
            List[Host]: 设备Host对象列表
        """
        async with InventoryFactory.create_builder() as builder:
            devices = await builder.get_devices_by_vendor(vendor_name)
            # 构建包含这些设备的清单
            if devices:
                inventory = await builder.build_inventory(filter_vendor=vendor_name)
                return list(inventory.hosts.values())
            return []

    @staticmethod
    async def get_devices_by_region(region_name: str, user_id: int | None = None) -> list[Host]:
        """根据区域名称获取设备列表

        Args:
            region_name: 区域名称
            user_id: 用户ID，用于获取认证信息

        Returns:
            List[Host]: 设备Host对象列表
        """
        async with InventoryFactory.create_builder() as builder:
            devices = await builder.get_devices_by_region(region_name)
            # 构建包含这些设备的清单
            if devices:
                inventory = await builder.build_inventory(filter_region=region_name)
                return list(inventory.hosts.values())
            return []

    @staticmethod
    async def get_devices_by_type(device_type: str, user_id: UUID | None = None) -> list[Host]:
        """根据设备类型获取设备列表

        Args:
            device_type: 设备类型
            user_id: 用户ID，用于获取认证信息

        Returns:
            List[Host]: 设备Host对象列表
        """
        inventory = await InventoryFactory.build_inventory(device_types=[device_type], user_id=user_id)
        return list(inventory.hosts.values())

    @staticmethod
    async def get_inventory_stats() -> dict[str, Any]:
        """获取设备清单统计信息

        Returns:
            Dict: 统计信息字典
        """
        async with InventoryFactory.create_builder() as builder:
            inventory = await builder.build_inventory()

            # 统计设备数量
            total_devices = len(inventory.hosts)

            # 按厂商统计
            vendor_stats = {}
            # 按区域统计
            region_stats = {}
            # 按设备类型统计
            type_stats = {}

            for _hostname, host in inventory.hosts.items():
                # 厂商统计
                vendor_name = host.data.get("vendor_name", "未知")
                vendor_stats[vendor_name] = vendor_stats.get(vendor_name, 0) + 1

                # 区域统计
                region_name = host.data.get("region_name", "未知")
                region_stats[region_name] = region_stats.get(region_name, 0) + 1

                # 设备类型统计
                device_type = host.data.get("device_type", "未知")
                type_stats[device_type] = type_stats.get(device_type, 0) + 1

            return {
                "total_devices": total_devices,
                "total_groups": len(inventory.groups),
                "vendor_distribution": vendor_stats,
                "region_distribution": region_stats,
                "type_distribution": type_stats,
            }

    @staticmethod
    async def validate_devices(device_hostnames: list[str]) -> dict[str, bool]:
        """验证设备是否存在

        Args:
            device_hostnames: 设备主机名列表

        Returns:
            Dict[str, bool]: 设备存在性映射
        """
        inventory = await InventoryFactory.build_inventory(device_hostnames=device_hostnames)

        result = {}
        for hostname in device_hostnames:
            result[hostname] = hostname in inventory.hosts

        return result

    @staticmethod
    async def get_device_groups(hostname: str) -> list[Group]:
        """获取设备所属的组列表

        Args:
            hostname: 设备主机名

        Returns:
            List[Group]: 组对象列表
        """
        device = await InventoryFactory.get_device(hostname)
        if device and hasattr(device, "groups") and device.groups:
            # device.groups 是字符串列表
            return list(device.groups)
        return []

    @staticmethod
    async def filter_devices_by_groups(group_names: list[str], user_id: UUID | None = None) -> list[Host]:
        """根据组名过滤设备

        Args:
            group_names: 组名列表
            user_id: 用户ID，用于获取认证信息

        Returns:
            List[Host]: 符合条件的设备列表
        """
        inventory = await InventoryFactory.build_inventory(user_id=user_id)

        filtered_devices = []
        for _hostname, host in inventory.hosts.items():
            # 检查设备是否属于指定的任一组
            if any(group in host.groups for group in group_names):
                filtered_devices.append(host)

        return filtered_devices


class InventoryCache:
    """设备清单缓存管理器

    提供设备清单的缓存功能，减少数据库查询
    """

    def __init__(self, cache_ttl: int = 300):
        """初始化缓存管理器

        Args:
            cache_ttl: 缓存生存时间（秒），默认5分钟
        """
        self._cache: dict[str, Any] = {}
        self._cache_ttl = cache_ttl
        self._cache_timestamps: dict[str, float] = {}

    def _generate_cache_key(
        self,
        device_hostnames: list[str] | None = None,
        region_ids: list[UUID] | None = None,
        vendor_ids: list[UUID] | None = None,
        device_types: list[str] | None = None,
        user_id: UUID | None = None,
    ) -> str:
        """生成缓存键"""
        import hashlib
        import json

        cache_data = {
            "device_hostnames": sorted(device_hostnames) if device_hostnames else None,
            "region_ids": sorted(region_ids) if region_ids else None,
            "vendor_ids": sorted(vendor_ids) if vendor_ids else None,
            "device_types": sorted(device_types) if device_types else None,
            "user_id": user_id,
        }

        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        import time

        if cache_key not in self._cache_timestamps:
            return False

        return (time.time() - self._cache_timestamps[cache_key]) < self._cache_ttl

    async def get_inventory(
        self,
        device_hostnames: list[str] | None = None,
        region_ids: list[UUID] | None = None,
        vendor_ids: list[UUID] | None = None,
        device_types: list[str] | None = None,
        user_id: UUID | None = None,
        use_cache: bool = True,
    ) -> Inventory:
        """获取设备清单（支持缓存）

        Args:
            device_hostnames: 指定设备主机名列表
            region_ids: 区域ID列表过滤
            vendor_ids: 厂商ID列表过滤
            device_types: 设备类型列表过滤
            user_id: 用户ID，用于获取认证信息
            use_cache: 是否使用缓存

        Returns:
            Inventory: Nornir设备清单对象
        """
        cache_key = self._generate_cache_key(device_hostnames, region_ids, vendor_ids, device_types, user_id)

        # 检查缓存
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"使用缓存的设备清单: {cache_key}")
            return self._cache[cache_key]

        # 构建新的设备清单
        inventory = await InventoryFactory.build_inventory(
            device_hostnames=device_hostnames,
            region_ids=region_ids,
            vendor_ids=vendor_ids,
            device_types=device_types,
            user_id=user_id,
        )

        # 更新缓存
        if use_cache:
            import time

            self._cache[cache_key] = inventory
            self._cache_timestamps[cache_key] = time.time()
            logger.debug(f"缓存设备清单: {cache_key}")

        return inventory

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("设备清单缓存已清空")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        import time

        valid_count = 0
        expired_count = 0

        current_time = time.time()
        for _cache_key, timestamp in self._cache_timestamps.items():
            if (current_time - timestamp) < self._cache_ttl:
                valid_count += 1
            else:
                expired_count += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "cache_ttl": self._cache_ttl,
        }


# 全局缓存实例
inventory_cache = InventoryCache()
