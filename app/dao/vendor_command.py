"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor_command.py
@DateTime: 2025/07/23
@Docs: 厂商命令数据访问层
"""

from uuid import UUID

from app.dao.base import BaseDAO
from app.models.vendor_command import VendorCommand
from app.utils.logger import logger


class VendorCommandDAO(BaseDAO[VendorCommand]):
    """厂商命令数据访问层"""

    def __init__(self):
        super().__init__(VendorCommand)

    async def get_by_template_and_vendor(self, template_id: UUID, vendor_id: UUID) -> VendorCommand | None:
        """根据模板和厂商获取命令"""
        try:
            return (
                await self.model.filter(template_id=template_id, vendor_id=vendor_id, is_deleted=False)
                .select_related("template", "vendor")
                .first()
            )
        except Exception as e:
            logger.error(f"根据模板和厂商获取命令失败: {e}")
            return None

    async def get_by_template(self, template_id: UUID) -> list[VendorCommand]:
        """根据模板获取所有厂商命令"""
        try:
            return (
                await self.model.filter(template_id=template_id, is_deleted=False)
                .select_related("template", "vendor")
                .all()
            )
        except Exception as e:
            logger.error(f"根据模板获取命令失败: {e}")
            return []

    async def get_by_vendor(self, vendor_id: UUID) -> list[VendorCommand]:
        """根据厂商获取所有命令"""
        try:
            return (
                await self.model.filter(vendor_id=vendor_id, is_deleted=False)
                .select_related("template", "vendor")
                .all()
            )
        except Exception as e:
            logger.error(f"根据厂商获取命令失败: {e}")
            return []

    async def check_exists(self, template_id: UUID, vendor_id: UUID, exclude_id: UUID | None = None) -> bool:
        """检查模板-厂商组合是否已存在"""
        try:
            filters: dict = {"template_id": template_id, "vendor_id": vendor_id, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查模板-厂商组合是否存在失败: {e}")
            return False

    async def search_commands(
        self,
        template_id: UUID | None = None,
        vendor_id: UUID | None = None,
        parser_type: str | None = None,
    ) -> list[VendorCommand]:
        """搜索厂商命令"""
        try:
            filters: dict = {"is_deleted": False}
            if template_id:
                filters["template_id"] = template_id
            if vendor_id:
                filters["vendor_id"] = vendor_id
            if parser_type:
                filters["parser_type"] = parser_type

            return await self.model.filter(**filters).all()
        except Exception as e:
            logger.error(f"搜索厂商命令失败: {e}")
            return []

    async def get_commands_with_relations(self) -> list[VendorCommand]:
        """获取厂商命令及其关联的模板和厂商信息"""
        try:
            return await self.get_all_with_related(
                select_related=["template", "vendor"],
            )
        except Exception as e:
            logger.error(f"获取厂商命令及关联信息失败: {e}")
            return []

    async def get_command_with_details(self, command_id: UUID) -> VendorCommand | None:
        """获取厂商命令详细信息"""
        try:
            return await self.get_with_related(
                id=command_id,
                select_related=["template", "vendor"],
            )
        except Exception as e:
            logger.error(f"获取厂商命令详细信息失败: {e}")
            return None

    async def get_commands_paginated_optimized(
        self,
        page: int = 1,
        page_size: int = 20,
        template_id: UUID | None = None,
        vendor_id: UUID | None = None,
    ) -> tuple[list[VendorCommand], int]:
        """分页获取厂商命令"""
        try:
            filters: dict = {"is_deleted": False}
            if template_id:
                filters["template_id"] = template_id
            if vendor_id:
                filters["vendor_id"] = vendor_id

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["created_at"],
                select_related=["template", "vendor"],
                prefetch_related=None,
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取厂商命令失败: {e}")
            return [], 0

    async def get_count_by_vendor_ids(self, vendor_ids: list[UUID]) -> dict[UUID, int]:
        """批量获取厂商命令数量统计

        Args:
            vendor_ids: 厂商ID列表

        Returns:
            {厂商ID: 命令数量} 的字典
        """
        try:
            from tortoise.functions import Count

            # 使用聚合查询批量获取统计信息
            stats = (
                await VendorCommand.filter(vendor_id__in=vendor_ids, is_deleted=False)
                .group_by("vendor_id")
                .annotate(count=Count("id"))
                .values("vendor_id", "count")
            )

            # 转换为字典格式
            result = {stat["vendor_id"]: stat["count"] for stat in stats}

            # 确保所有厂商ID都有对应的值（没有命令的厂商返回0）
            for vendor_id in vendor_ids:
                if vendor_id not in result:
                    result[vendor_id] = 0

            return result

        except Exception as e:
            logger.error(f"批量获取厂商命令数量失败: {e}")
            # 返回默认值
            return dict.fromkeys(vendor_ids, 0)

    async def get_count_by_template_ids(self, template_ids: list[UUID]) -> dict[UUID, int]:
        """批量获取模板命令数量统计

        Args:
            template_ids: 模板ID列表

        Returns:
            {模板ID: 命令数量} 的字典
        """
        try:
            from tortoise.functions import Count

            # 使用聚合查询批量获取统计信息
            stats = (
                await VendorCommand.filter(template_id__in=template_ids, is_deleted=False)
                .group_by("template_id")
                .annotate(count=Count("id"))
                .values("template_id", "count")
            )

            # 转换为字典格式
            result = {stat["template_id"]: stat["count"] for stat in stats}

            # 确保所有模板ID都有对应的值（没有命令的模板返回0）
            for template_id in template_ids:
                if template_id not in result:
                    result[template_id] = 0

            return result

        except Exception as e:
            logger.error(f"批量获取模板命令数量失败: {e}")
            # 返回默认值
            return dict.fromkeys(template_ids, 0)
