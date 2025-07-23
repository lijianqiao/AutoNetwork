"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region.py
@DateTime: 2025/07/23
@Docs: 基地数据访问层
"""

from uuid import UUID

from app.dao.base import BaseDAO
from app.models.region import Region
from app.utils.logger import logger


class RegionDAO(BaseDAO[Region]):
    """基地数据访问层"""

    def __init__(self):
        super().__init__(Region)

    async def get_by_region_code(self, code: str) -> Region | None:
        """根据基地编码获取基地"""
        try:
            return await self.model.get_or_none(region_code=code, is_deleted=False)
        except Exception as e:
            logger.error(f"根据基地编码获取基地失败: {e}")
            return None

    async def check_code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        """检查基地编码是否已存在"""
        try:
            filters = {"region_code": code, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查基地编码是否存在失败: {e}")
            return False

    async def search_regions(self, keyword: str | None = None) -> list[Region]:
        """搜索基地"""
        try:
            filters = {"is_deleted": False}
            queryset = self.model.filter(**filters)

            if keyword:
                from tortoise.expressions import Q

                queryset = queryset.filter(Q(region_name__icontains=keyword) | Q(region_code__icontains=keyword))

            return await queryset.order_by("region_name").all()
        except Exception as e:
            logger.error(f"搜索基地失败: {e}")
            return []

    async def get_regions_with_devices(self) -> list[Region]:
        """获取基地及其关联的设备信息"""
        try:
            return await self.get_all_with_related(
                prefetch_related=["devices"],
            )
        except Exception as e:
            logger.error(f"获取基地及设备信息失败: {e}")
            return []

    async def get_region_with_details(self, region_id: UUID) -> Region | None:
        """获取基地详细信息"""
        try:
            return await self.get_with_related(
                id=region_id,
                prefetch_related=["devices"],
            )
        except Exception as e:
            logger.error(f"获取基地详细信息失败: {e}")
            return None

    async def get_regions_paginated_optimized(self, page: int = 1, page_size: int = 20) -> tuple[list[Region], int]:
        """分页获取基地"""
        try:
            filters = {"is_deleted": False}

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["region_name"],
                select_related=None,
                prefetch_related=["devices"],
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取基地失败: {e}")
            return [], 0
