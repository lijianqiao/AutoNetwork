"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/07/23
@Docs: 设备数据访问层
"""

from uuid import UUID

from app.core.network.interfaces import IDeviceDAO
from app.dao.base import BaseDAO
from app.models.device import Device
from app.utils.logger import logger


class DeviceDAO(BaseDAO[Device], IDeviceDAO):
    """设备数据访问层"""

    def __init__(self):
        super().__init__(Device)

    async def get_by_id(self, id: UUID, include_deleted: bool = True) -> Device | None:
        """根据设备ID获取设备

        Args:
            id: 设备ID
            include_deleted: 是否包含已删除的设备

        Returns:
            设备对象或None
        """
        return await super().get_by_id(id, include_deleted)

    async def get_by_ids(self, ids: list[UUID]) -> list[Device]:
        """根据设备ID列表获取设备

        Args:
            ids: 设备ID列表

        Returns:
            设备对象列表
        """
        return await super().get_by_ids(ids)

    async def get_all(self, include_deleted: bool = True, **filters) -> list[Device]:
        """获取所有设备

        Args:
            include_deleted: 是否包含已删除的设备
            **filters: 过滤条件

        Returns:
            设备对象列表
        """
        try:
            return await super().get_all(include_deleted=include_deleted, **filters)
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []

    async def get_by_hostname(self, hostname: str) -> Device | None:
        """根据主机名获取设备"""
        try:
            return await self.model.get_or_none(hostname=hostname, is_deleted=False)
        except Exception as e:
            logger.error(f"根据主机名获取设备失败: {e}")
            return None

    async def get_by_ip_address(self, ip_address: str) -> Device | None:
        """根据IP地址获取设备"""
        try:
            return await self.model.get_or_none(ip_address=ip_address, is_deleted=False)
        except Exception as e:
            logger.error(f"根据IP地址获取设备失败: {e}")
            return None

    async def check_hostname_exists(self, hostname: str, exclude_id: UUID | None = None) -> bool:
        """检查主机名是否已存在"""
        try:
            filters = {"hostname": hostname, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查主机名是否存在失败: {e}")
            return False

    async def check_ip_exists(self, ip_address: str, exclude_id: UUID | None = None) -> bool:
        """检查IP地址是否已存在"""
        try:
            filters = {"ip_address": ip_address, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查IP地址是否存在失败: {e}")
            return False

    async def get_active_devices(self) -> list[Device]:
        """获取所有在用的设备"""
        try:
            return await self.model.filter(is_active=True, is_deleted=False).order_by("hostname").all()
        except Exception as e:
            logger.error(f"获取在用设备失败: {e}")
            return []

    async def search_devices(
        self,
        keyword: str | None = None,
        vendor_id: UUID | None = None,
        region_id: UUID | None = None,
        device_type: str | None = None,
        network_layer: str | None = None,
        is_active: bool | None = None,
    ) -> list[Device]:
        """搜索设备"""
        try:
            filters: dict = {"is_deleted": False}
            if vendor_id:
                filters["vendor_id"] = vendor_id
            if region_id:
                filters["region_id"] = region_id
            if device_type:
                filters["device_type"] = device_type
            if network_layer:
                filters["network_layer"] = network_layer
            if is_active is not None:
                filters["is_active"] = is_active

            queryset = self.model.filter(**filters)

            if keyword:
                from tortoise.expressions import Q

                queryset = queryset.filter(
                    Q(hostname__icontains=keyword)
                    | Q(ip_address__icontains=keyword)
                    | Q(model__icontains=keyword)
                    | Q(location__icontains=keyword)
                )

            return await queryset.order_by("hostname").all()
        except Exception as e:
            logger.error(f"搜索设备失败: {e}")
            return []

    async def get_devices_by_vendor(self, vendor_id: UUID) -> list[Device]:
        """根据厂商获取设备列表"""
        try:
            return await self.model.filter(vendor_id=vendor_id, is_deleted=False).all()
        except Exception as e:
            logger.error(f"根据厂商获取设备失败: {e}")
            return []

    async def get_devices_by_region(self, region_id: UUID) -> list[Device]:
        """根据基地获取设备列表"""
        try:
            return await self.model.filter(region_id=region_id, is_deleted=False).all()
        except Exception as e:
            logger.error(f"根据基地获取设备失败: {e}")
            return []

    async def activate_device(self, device_id: UUID) -> bool:
        """激活设备"""
        try:
            count = await self.model.filter(id=device_id, is_deleted=False).update(is_active=True)
            return count > 0
        except Exception as e:
            logger.error(f"激活设备失败: {e}")
            return False

    async def deactivate_device(self, device_id: UUID) -> bool:
        """停用设备"""
        try:
            count = await self.model.filter(id=device_id, is_deleted=False).update(is_active=False)
            return count > 0
        except Exception as e:
            logger.error(f"停用设备失败: {e}")
            return False

    async def update_last_connected(self, device_id: UUID) -> None:
        """更新设备最后连接时间"""
        try:
            from datetime import datetime

            await self.model.filter(id=device_id, is_deleted=False).update(last_connected_at=datetime.now())
        except Exception as e:
            logger.error(f"更新设备连接时间失败: {e}")
            raise

    async def get_devices_with_relations(self) -> list[Device]:
        """获取设备及其关联的厂商和基地信息"""
        try:
            return await self.get_all_with_related(
                select_related=["vendor", "region"],
                prefetch_related=["configs"],
            )
        except Exception as e:
            logger.error(f"获取设备及关联信息失败: {e}")
            return []

    async def get_device_with_details(self, device_id: UUID) -> Device | None:
        """获取设备详细信息"""
        try:
            return await self.get_with_related(
                id=device_id,
                select_related=["vendor", "region"],
                prefetch_related=["configs"],
            )
        except Exception as e:
            logger.error(f"获取设备详细信息失败: {e}")
            return None

    async def get_devices_paginated_optimized(
        self,
        page: int = 1,
        page_size: int = 20,
        vendor_id: UUID | None = None,
        region_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Device], int]:
        """分页获取设备"""
        try:
            filters: dict = {"is_deleted": False}
            if vendor_id:
                filters["vendor_id"] = vendor_id
            if region_id:
                filters["region_id"] = region_id
            if is_active is not None:
                filters["is_active"] = is_active

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["hostname"],
                select_related=["vendor", "region"],
                prefetch_related=None,
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取设备失败: {e}")
            return [], 0

    async def get_count_by_vendor_ids(self, vendor_ids: list[UUID]) -> dict[UUID, int]:
        """批量获取厂商设备数量统计

        Args:
            vendor_ids: 厂商ID列表

        Returns:
            {厂商ID: 设备数量} 的字典
        """
        try:
            from tortoise.functions import Count

            # 使用聚合查询批量获取统计信息
            stats = (
                await Device.filter(vendor_id__in=vendor_ids, deleted_at__isnull=True)
                .group_by("vendor_id")
                .annotate(count=Count("id"))
                .values("vendor_id", "count")
            )

            # 转换为字典格式
            result = {stat["vendor_id"]: stat["count"] for stat in stats}

            # 确保所有厂商ID都有对应的值（没有设备的厂商返回0）
            for vendor_id in vendor_ids:
                if vendor_id not in result:
                    result[vendor_id] = 0

            return result

        except Exception as e:
            logger.error(f"批量获取厂商设备数量失败: {e}")
            # 返回默认值
            return dict.fromkeys(vendor_ids, 0)
