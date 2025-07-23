"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region.py
@DateTime: 2025/07/23
@Docs: 基地服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.device import DeviceDAO
from app.dao.region import RegionDAO
from app.models.region import Region
from app.schemas.region import (
    RegionCreateRequest,
    RegionDetailResponse,
    RegionListRequest,
    RegionResponse,
    RegionUpdateRequest,
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


class RegionService(BaseService[Region]):
    """基地服务"""

    def __init__(self):
        self.dao = RegionDAO()
        super().__init__(self.dao)
        self.device_dao = DeviceDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查基地代码唯一性"""
        if "region_code" in data and await self.dao.exists(region_code=data["region_code"]):
            logger.warning(f"创建基地失败: 基地代码已存在 {data['region_code']}")
            raise BusinessException("基地代码已存在")
        return data

    async def before_update(self, obj: Region, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查基地代码唯一性"""
        if "region_code" in data and await self.dao.exists(region_code=data["region_code"], id__not=obj.id):
            logger.warning(f"更新基地失败: 基地代码已存在 {data['region_code']}")
            raise BusinessException("基地代码已存在")
        return data

    @log_create_with_context("region")
    async def create_region(self, request: RegionCreateRequest, operation_context: OperationContext) -> RegionResponse:
        """创建基地"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        region = await self.create(operation_context=operation_context, **create_data)
        if not region:
            logger.error("基地创建失败")
            raise BusinessException("基地创建失败")
        return RegionResponse.model_validate(region)

    @log_update_with_context("region")
    async def update_region(
        self, region_id: UUID, request: RegionUpdateRequest, operation_context: OperationContext
    ) -> RegionResponse:
        """更新基地"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            logger.error("更新请求必须包含 version 字段。")
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_region = await self.update(
            region_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_region:
            logger.error("基地更新失败或版本冲突")
            raise BusinessException("基地更新失败或版本冲突")
        return RegionResponse.model_validate(updated_region)

    @log_delete_with_context("region")
    async def delete_region(self, region_id: UUID, operation_context: OperationContext) -> None:
        """删除基地，检查是否仍有设备关联"""
        region = await self.dao.get_by_id(region_id)
        if not region:
            logger.error("基地未找到")
            raise BusinessException("基地未找到")

        # 检查是否有设备正在使用此基地
        device_count = await self.device_dao.count(region_id=region_id)
        if device_count > 0:
            logger.error(f"基地 '{region.region_name}' 正在被 {device_count} 个设备使用，无法删除")
            raise BusinessException(f"基地 '{region.region_name}' 正在被 {device_count} 个设备使用，无法删除")

        await self.delete(region_id, operation_context=operation_context)

    @log_query_with_context("region")
    async def get_regions(
        self, query: RegionListRequest, operation_context: OperationContext
    ) -> tuple[list[RegionResponse], int]:
        """获取基地列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        REGION_MODEL_FIELDS = {"region_code"}
        search_fields = ["region_name", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, REGION_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        regions, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        # 为每个基地添加设备数量统计
        region_responses = []
        for region in regions:
            region_data = RegionResponse.model_validate(region)
            region_data.device_count = await self.device_dao.count(region_id=region.id)
            region_responses.append(region_data)

        return region_responses, total

    @log_query_with_context("region")
    async def get_region_detail(self, region_id: UUID, operation_context: OperationContext) -> RegionDetailResponse:
        """获取基地详情"""
        region = await self.dao.get_by_id(region_id)
        if not region:
            logger.error("基地未找到")
            raise BusinessException("基地未找到")
        return RegionDetailResponse.model_validate(region)

    @log_query_with_context("region")
    async def get_region_by_code(self, region_code: str, operation_context: OperationContext) -> RegionResponse:
        """根据基地代码获取基地"""
        region = await self.dao.get_by_region_code(region_code)
        if not region:
            logger.error(f"基地代码 '{region_code}' 未找到")
            raise BusinessException(f"基地代码 '{region_code}' 未找到")
        region_data = RegionResponse.model_validate(region)
        region_data.device_count = await self.device_dao.count(region_id=region.id)
        return region_data

    @log_query_with_context("region")
    async def get_all_regions(self, operation_context: OperationContext) -> list[RegionResponse]:
        """获取所有基地列表（用于下拉选择等）"""
        regions = await self.dao.get_all(is_deleted=False)
        region_responses = []
        for region in regions:
            region_data = RegionResponse.model_validate(region)
            region_data.device_count = await self.device_dao.count(region_id=region.id)
            region_responses.append(region_data)
        return region_responses
