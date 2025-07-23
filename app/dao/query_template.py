"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_template.py
@DateTime: 2025/07/23
@Docs: 查询模板数据访问层
"""

from uuid import UUID

from app.dao.base import BaseDAO
from app.models.query_template import QueryTemplate
from app.utils.logger import logger


class QueryTemplateDAO(BaseDAO[QueryTemplate]):
    """查询模板数据访问层"""

    def __init__(self):
        super().__init__(QueryTemplate)

    async def get_by_template_type(self, template_type: str) -> list[QueryTemplate]:
        """根据模板类型获取模板列表"""
        try:
            return await self.model.filter(template_type=template_type, is_deleted=False).all()
        except Exception as e:
            logger.error(f"根据模板类型获取模板失败: {e}")
            return []

    async def get_active_templates(self) -> list[QueryTemplate]:
        """获取所有激活的模板"""
        try:
            return await self.model.filter(is_active=True, is_deleted=False).order_by("template_name").all()
        except Exception as e:
            logger.error(f"获取激活模板失败: {e}")
            return []

    async def search_templates(
        self, keyword: str | None = None, template_type: str | None = None, is_active: bool | None = None
    ) -> list[QueryTemplate]:
        """搜索模板"""
        try:
            filters: dict = {"is_deleted": False}
            if template_type:
                filters["template_type"] = template_type
            if is_active is not None:
                filters["is_active"] = is_active

            queryset = self.model.filter(**filters)

            if keyword:
                from tortoise.expressions import Q

                queryset = queryset.filter(Q(template_name__icontains=keyword) | Q(description__icontains=keyword))

            return await queryset.order_by("template_name").all()
        except Exception as e:
            logger.error(f"搜索模板失败: {e}")
            return []

    async def activate_template(self, template_id: UUID) -> bool:
        """激活模板"""
        try:
            count = await self.model.filter(id=template_id, is_deleted=False).update(is_active=True)
            return count > 0
        except Exception as e:
            logger.error(f"激活模板失败: {e}")
            return False

    async def deactivate_template(self, template_id: UUID) -> bool:
        """停用模板"""
        try:
            count = await self.model.filter(id=template_id, is_deleted=False).update(is_active=False)
            return count > 0
        except Exception as e:
            logger.error(f"停用模板失败: {e}")
            return False

    async def get_templates_with_commands(self) -> list[QueryTemplate]:
        """获取模板及其关联的厂商命令信息"""
        try:
            return await self.get_all_with_related(
                prefetch_related=["vendor_commands"],
            )
        except Exception as e:
            logger.error(f"获取模板及命令信息失败: {e}")
            return []

    async def get_template_with_details(self, template_id: UUID) -> QueryTemplate | None:
        """获取模板详细信息"""
        try:
            return await self.get_with_related(
                id=template_id,
                prefetch_related=["vendor_commands"],
            )
        except Exception as e:
            logger.error(f"获取模板详细信息失败: {e}")
            return None

    async def get_templates_paginated_optimized(
        self, page: int = 1, page_size: int = 20, is_active: bool | None = None
    ) -> tuple[list[QueryTemplate], int]:
        """分页获取模板"""
        try:
            filters: dict = {"is_deleted": False}
            if is_active is not None:
                filters["is_active"] = is_active

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["template_name"],
                select_related=None,
                prefetch_related=["vendor_commands"],
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取模板失败: {e}")
            return [], 0
