"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_template.py
@DateTime: 2025/07/23
@Docs: 查询模板服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.query_template import QueryTemplateDAO
from app.dao.vendor_command import VendorCommandDAO
from app.models.query_template import QueryTemplate
from app.schemas.query_template import (
    QueryTemplateActivateRequest,
    QueryTemplateCreateRequest,
    QueryTemplateDetailResponse,
    QueryTemplateListRequest,
    QueryTemplateResponse,
    QueryTemplateUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)


class QueryTemplateService(BaseService[QueryTemplate]):
    """查询模板服务"""

    def __init__(self):
        self.dao = QueryTemplateDAO()
        super().__init__(self.dao)
        self.vendor_command_dao = VendorCommandDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查模板名称唯一性"""
        if "template_name" in data and await self.dao.exists(template_name=data["template_name"]):
            logger.warning(f"模板名称已存在: {data['template_name']}")
            raise BusinessException("模板名称已存在")
        return data

    async def before_update(self, obj: QueryTemplate, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查模板名称唯一性"""
        if "template_name" in data and await self.dao.exists(template_name=data["template_name"], id__not=obj.id):
            logger.warning(f"模板名称已存在: {data['template_name']}")
            raise BusinessException("模板名称已存在")
        return data

    @log_create_with_context("query_template")
    async def create_template(
        self, request: QueryTemplateCreateRequest, operation_context: OperationContext
    ) -> QueryTemplateResponse:
        """创建查询模板"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        template = await self.create(operation_context=operation_context, **create_data)
        if not template:
            logger.error("查询模板创建失败")
            raise BusinessException("查询模板创建失败")
        return QueryTemplateResponse.model_validate(template)

    @log_update_with_context("query_template")
    async def update_template(
        self, template_id: UUID, request: QueryTemplateUpdateRequest, operation_context: OperationContext
    ) -> QueryTemplateResponse:
        """更新查询模板"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            logger.error("更新请求必须包含 version 字段。")
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_template = await self.update(
            template_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_template:
            logger.error("查询模板更新失败或版本冲突")
            raise BusinessException("查询模板更新失败或版本冲突")
        return QueryTemplateResponse.model_validate(updated_template)

    @log_delete_with_context("query_template")
    async def delete_template(self, template_id: UUID, operation_context: OperationContext) -> None:
        """删除查询模板，检查是否仍有厂商命令关联"""
        template = await self.dao.get_by_id(template_id)
        if not template:
            logger.error("查询模板未找到")
            raise BusinessException("查询模板未找到")

        # 检查是否有厂商命令正在使用此模板
        command_count = await self.vendor_command_dao.count(template_id=template_id)
        if command_count > 0:
            logger.error(f"查询模板 '{template.template_name}' 正在被 {command_count} 个厂商命令使用，无法删除")
            raise BusinessException(
                f"查询模板 '{template.template_name}' 正在被 {command_count} 个厂商命令使用，无法删除"
            )

        await self.delete(template_id, operation_context=operation_context)

    @log_query_with_context("query_template")
    async def get_templates(
        self, query: QueryTemplateListRequest, operation_context: OperationContext
    ) -> tuple[list[QueryTemplateResponse], int]:
        """获取查询模板列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        TEMPLATE_MODEL_FIELDS = {"template_type", "is_active"}
        search_fields = ["template_name", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, TEMPLATE_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        templates, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        # 为每个模板添加命令数量统计
        template_responses = []
        for template in templates:
            template_data = QueryTemplateResponse.model_validate(template)
            template_data.command_count = await self.vendor_command_dao.count(template_id=template.id)
            template_responses.append(template_data)

        return template_responses, total

    @log_query_with_context("query_template")
    async def get_template_detail(
        self, template_id: UUID, operation_context: OperationContext
    ) -> QueryTemplateDetailResponse:
        """获取查询模板详情"""
        template = await self.dao.get_by_id(template_id)
        if not template:
            logger.error("查询模板未找到")
            raise BusinessException("查询模板未找到")
        return QueryTemplateDetailResponse.model_validate(template)

    @log_query_with_context("query_template")
    async def get_templates_by_type(
        self, template_type: str, operation_context: OperationContext
    ) -> list[QueryTemplateResponse]:
        """根据模板类型获取查询模板"""
        templates = await self.dao.get_by_template_type(template_type)
        template_responses = []
        for template in templates:
            template_data = QueryTemplateResponse.model_validate(template)
            template_data.command_count = await self.vendor_command_dao.count(template_id=template.id)
            template_responses.append(template_data)
        return template_responses

    @log_update_with_context("query_template")
    async def activate_template(self, template_id: UUID, operation_context: OperationContext) -> QueryTemplateResponse:
        """激活查询模板"""
        updated_template = await self.update(template_id, operation_context=operation_context, is_active=True)
        if not updated_template:
            logger.error("查询模板激活失败")
            raise BusinessException("查询模板激活失败")
        return QueryTemplateResponse.model_validate(updated_template)

    @log_update_with_context("query_template")
    async def deactivate_template(
        self, template_id: UUID, operation_context: OperationContext
    ) -> QueryTemplateResponse:
        """停用查询模板"""
        updated_template = await self.update(template_id, operation_context=operation_context, is_active=False)
        if not updated_template:
            logger.error("查询模板停用失败")
            raise BusinessException("查询模板停用失败")
        return QueryTemplateResponse.model_validate(updated_template)

    @log_update_with_context("query_template")
    async def batch_activate_templates(
        self, request: QueryTemplateActivateRequest, operation_context: OperationContext
    ) -> dict[str, int]:
        """批量激活/停用查询模板"""
        template_ids = request.template_ids
        is_active = request.is_active

        # 验证模板存在
        existing_templates = await self.dao.get_by_ids(template_ids)
        if len(existing_templates) != len(template_ids):
            logger.error("部分查询模板不存在")
            raise BusinessException("部分查询模板不存在")

        success_count = 0

        if is_active:
            success_count = await self.bulk_activate(template_ids)
        else:
            success_count = await self.bulk_deactivate(template_ids)

        return {
            "total_count": len(template_ids),
            "success_count": success_count,
            "failed_count": len(template_ids) - success_count,
        }

    @log_query_with_context("query_template")
    async def get_active_templates(self, operation_context: OperationContext) -> list[QueryTemplateResponse]:
        """获取所有激活的查询模板"""
        templates = await self.dao.get_all(is_active=True, is_deleted=False)
        template_responses = []
        for template in templates:
            template_data = QueryTemplateResponse.model_validate(template)
            template_data.command_count = await self.vendor_command_dao.count(template_id=template.id)
            template_responses.append(template_data)
        return template_responses

    @log_query_with_context("query_template")
    async def get_templates_with_commands(self, operation_context: OperationContext) -> list[QueryTemplateResponse]:
        """获取包含厂商命令的查询模板"""
        templates = await self.dao.get_templates_with_commands()
        template_responses = []
        for template in templates:
            template_data = QueryTemplateResponse.model_validate(template)
            template_data.command_count = len(getattr(template, "vendor_commands", []))
            template_responses.append(template_data)
        return template_responses

    # ===== 批量操作方法 =====

    @log_create_with_context("query_template")
    async def batch_create_templates(
        self, templates_data: list[QueryTemplateCreateRequest], operation_context: OperationContext
    ) -> list[QueryTemplateResponse]:
        """批量创建查询模板"""
        # 转换为字典列表
        data_list = [template_data.model_dump() for template_data in templates_data]

        # 批量验证模板名称唯一性
        template_names = [data.get("template_name") for data in data_list if data.get("template_name")]
        existing_names = []
        for name in template_names:
            if await self.dao.exists(template_name=name):
                existing_names.append(name)

        if existing_names:
            raise BusinessException(f"以下模板名称已存在: {', '.join(existing_names)}")

        # 使用BaseService的批量创建方法
        created_templates = await self.bulk_create(data_list)
        return [QueryTemplateResponse.model_validate(template) for template in created_templates]

    @log_update_with_context("query_template")
    async def batch_update_templates(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> list[QueryTemplateResponse]:
        """批量更新查询模板"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有模板是否存在
        existing_templates = await self.get_by_ids(update_ids)
        existing_ids = {str(template.id) for template in existing_templates}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下查询模板不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            update_data["id"] = update_item["id"]
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 返回更新后的数据
        updated_templates = await self.get_by_ids(update_ids)
        return [QueryTemplateResponse.model_validate(template) for template in updated_templates]

    @log_delete_with_context("query_template")
    async def batch_delete_templates(self, template_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除查询模板"""
        # 检查模板是否存在
        existing_templates = await self.get_by_ids(template_ids)
        if len(existing_templates) != len(template_ids):
            missing_ids = {str(id) for id in template_ids} - {str(t.id) for t in existing_templates}
            raise BusinessException(f"以下查询模板不存在: {', '.join(missing_ids)}")

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(template_ids, operation_context)
