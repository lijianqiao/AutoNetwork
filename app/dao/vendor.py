"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor.py
@DateTime: 2025/07/23
@Docs: 厂商数据访问层
"""

from uuid import UUID

from app.dao.base import BaseDAO
from app.models.vendor import Vendor
from app.utils.logger import logger


class VendorDAO(BaseDAO[Vendor]):
    """厂商数据访问层"""

    def __init__(self):
        super().__init__(Vendor)

    async def get_by_vendor_code(self, code: str) -> Vendor | None:
        """根据厂商编码获取厂商"""
        try:
            return await self.model.get_or_none(vendor_code=code, is_deleted=False)
        except Exception as e:
            logger.error(f"根据厂商编码获取厂商失败: {e}")
            return None

    async def check_code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        """检查厂商编码是否已存在"""
        try:
            filters = {"vendor_code": code, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查厂商编码是否存在失败: {e}")
            return False

    async def search_vendors(self, keyword: str | None = None) -> list[Vendor]:
        """搜索厂商"""
        try:
            filters = {"is_deleted": False}
            queryset = self.model.filter(**filters)

            if keyword:
                from tortoise.expressions import Q

                queryset = queryset.filter(Q(vendor_name__icontains=keyword) | Q(vendor_code__icontains=keyword))

            return await queryset.order_by("vendor_name").all()
        except Exception as e:
            logger.error(f"搜索厂商失败: {e}")
            return []

    async def get_vendors_with_devices(self) -> list[Vendor]:
        """获取厂商及其关联的设备信息"""
        try:
            return await self.get_all_with_related(
                prefetch_related=["devices", "vendor_commands"],
            )
        except Exception as e:
            logger.error(f"获取厂商及设备信息失败: {e}")
            return []

    async def get_vendor_with_details(self, vendor_id: UUID) -> Vendor | None:
        """获取厂商详细信息"""
        try:
            return await self.get_with_related(
                id=vendor_id,
                prefetch_related=["devices", "vendor_commands"],
            )
        except Exception as e:
            logger.error(f"获取厂商详细信息失败: {e}")
            return None

    async def get_vendors_paginated_optimized(self, page: int = 1, page_size: int = 20) -> tuple[list[Vendor], int]:
        """分页获取厂商"""
        try:
            filters = {"is_deleted": False}

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["vendor_name"],
                select_related=None,
                prefetch_related=["devices"],
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取厂商失败: {e}")
            return [], 0
