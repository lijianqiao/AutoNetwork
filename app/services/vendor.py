"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor.py
@DateTime: 2025/07/23
@Docs: 设备厂商服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.device import DeviceDAO
from app.dao.vendor import VendorDAO
from app.dao.vendor_command import VendorCommandDAO
from app.models.vendor import Vendor
from app.schemas.vendor import (
    VendorCreateRequest,
    VendorDetailResponse,
    VendorListRequest,
    VendorResponse,
    VendorUpdateRequest,
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
from app.utils.redis_cache import get_redis_cache


class VendorService(BaseService[Vendor]):
    """设备厂商服务"""

    def __init__(self):
        self.dao = VendorDAO()
        super().__init__(self.dao)
        self.device_dao = DeviceDAO()
        self.vendor_command_dao = VendorCommandDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查厂商代码唯一性"""
        if "vendor_code" in data and await self.dao.exists(vendor_code=data["vendor_code"]):
            logger.warning(f"创建厂商失败: 厂商代码已存在 {data['vendor_code']}")
            raise BusinessException("厂商代码已存在")
        return data

    async def before_update(self, obj: Vendor, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查厂商代码唯一性"""
        if "vendor_code" in data and await self.dao.exists(vendor_code=data["vendor_code"], id__not=obj.id):
            logger.warning(f"更新厂商失败: 厂商代码已存在 {data['vendor_code']}")
            raise BusinessException("厂商代码已存在")
        return data

    @log_create_with_context("vendor")
    @log_create_with_context("vendor")
    async def create_vendor(self, request: VendorCreateRequest, operation_context: OperationContext) -> VendorResponse:
        """创建厂商"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        vendor = await self.create(operation_context=operation_context, **create_data)
        if not vendor:
            logger.error("厂商创建失败")
            raise BusinessException("厂商创建失败")

        # 清除相关缓存
        redis_cache = await get_redis_cache()
        await redis_cache.delete_pattern("vendor:list:*")

        return VendorResponse.model_validate(vendor)

    @log_update_with_context("vendor")
    async def update_vendor(
        self, vendor_id: UUID, request: VendorUpdateRequest, operation_context: OperationContext
    ) -> VendorResponse:
        """更新厂商"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            logger.error("更新请求必须包含 version 字段。")
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_vendor = await self.update(
            vendor_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_vendor:
            logger.error("厂商更新失败或版本冲突")
            raise BusinessException("厂商更新失败或版本冲突")

        # 清除相关缓存
        redis_cache = await get_redis_cache()
        await redis_cache.delete_pattern("vendor:list:*")
        await redis_cache.delete(f"vendor:detail:{vendor_id}")

        return VendorResponse.model_validate(updated_vendor)

    @log_delete_with_context("vendor")
    async def delete_vendor(self, vendor_id: UUID, operation_context: OperationContext) -> None:
        """删除厂商，检查是否仍有设备或命令关联"""
        vendor = await self.dao.get_by_id(vendor_id)
        if not vendor:
            logger.error("厂商未找到")
            raise BusinessException("厂商未找到")

        # 检查是否有设备正在使用此厂商
        device_count = await self.device_dao.count(vendor_id=vendor_id)
        if device_count > 0:
            logger.warning(f"删除厂商失败: 厂商 '{vendor.vendor_name}' 正在被 {device_count} 个设备使用")
            raise BusinessException(f"厂商 '{vendor.vendor_name}' 正在被 {device_count} 个设备使用，无法删除")

        # 检查是否有厂商命令关联
        command_count = await self.vendor_command_dao.count(vendor_id=vendor_id)
        if command_count > 0:
            logger.warning(f"删除厂商失败: 厂商 '{vendor.vendor_name}' 还有 {command_count} 个命令配置，无法删除")
            raise BusinessException(f"厂商 '{vendor.vendor_name}' 还有 {command_count} 个命令配置，无法删除")

        await self.delete(vendor_id, operation_context=operation_context)

    @log_query_with_context("vendor")
    async def get_vendors(
        self, query: VendorListRequest, operation_context: OperationContext
    ) -> tuple[list[VendorResponse], int]:
        """获取厂商列表 - 添加缓存优化"""
        from app.utils.query_utils import list_query_to_orm_filters

        # 生成缓存键
        query_dict = query.model_dump(exclude_unset=True)
        cache_key = f"vendor:list:{hash(str(sorted(query_dict.items())))}"

        # 尝试从缓存获取
        redis_cache = await get_redis_cache()
        cached_result = await redis_cache.get(cache_key)
        if cached_result:
            logger.debug(f"厂商列表缓存命中: {cache_key}")
            return cached_result

        VENDOR_MODEL_FIELDS = {"vendor_code", "scrapli_platform"}
        search_fields = ["vendor_name", "scrapli_platform"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, VENDOR_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        vendors, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        # 为每个厂商添加统计信息 - 优化：批量查询避免N+1问题
        vendor_responses = []
        if vendors:
            vendor_ids = [vendor.id for vendor in vendors]

            # 批量查询设备数量
            device_counts = await self.device_dao.get_count_by_vendor_ids(vendor_ids)
            # 批量查询命令数量
            command_counts = await self.vendor_command_dao.get_count_by_vendor_ids(vendor_ids)

            for vendor in vendors:
                vendor_data = VendorResponse.model_validate(vendor)
                vendor_data.device_count = device_counts.get(vendor.id, 0)
                vendor_data.command_count = command_counts.get(vendor.id, 0)
                vendor_responses.append(vendor_data)

        result = (vendor_responses, total)

        # 缓存结果 - 厂商信息相对稳定，缓存5分钟
        await redis_cache.set(cache_key, result, ttl=300)

        return result

    @log_query_with_context("vendor")
    async def get_vendor_detail(self, vendor_id: UUID, operation_context: OperationContext) -> VendorDetailResponse:
        """获取厂商详情"""
        vendor = await self.dao.get_by_id(vendor_id)
        if not vendor:
            logger.error("厂商未找到")
            raise BusinessException("厂商未找到")
        return VendorDetailResponse.model_validate(vendor)

    @log_query_with_context("vendor")
    async def get_vendor_by_code(self, vendor_code: str, operation_context: OperationContext) -> VendorResponse:
        """根据厂商代码获取厂商"""
        vendor = await self.dao.get_by_vendor_code(vendor_code)
        if not vendor:
            logger.error(f"厂商代码 '{vendor_code}' 未找到")
            raise BusinessException(f"厂商代码 '{vendor_code}' 未找到")
        vendor_data = VendorResponse.model_validate(vendor)
        vendor_data.device_count = await self.device_dao.count(vendor_id=vendor.id)
        vendor_data.command_count = await self.vendor_command_dao.count(vendor_id=vendor.id)
        return vendor_data

    @log_query_with_context("vendor")
    async def get_all_vendors(self, operation_context: OperationContext) -> list[VendorResponse]:
        """获取所有厂商列表（用于下拉选择等）"""
        vendors = await self.dao.get_all(is_deleted=False)
        vendor_responses = []
        for vendor in vendors:
            vendor_data = VendorResponse.model_validate(vendor)
            vendor_data.device_count = await self.device_dao.count(vendor_id=vendor.id)
            vendor_data.command_count = await self.vendor_command_dao.count(vendor_id=vendor.id)
            vendor_responses.append(vendor_data)
        return vendor_responses

    @log_query_with_context("vendor")
    async def get_vendors_with_devices(self, operation_context: OperationContext) -> list[VendorResponse]:
        """获取包含设备信息的厂商列表"""
        vendors = await self.dao.get_vendors_with_devices()
        vendor_responses = []
        for vendor in vendors:
            vendor_data = VendorResponse.model_validate(vendor)
            vendor_data.device_count = len(getattr(vendor, "devices", []))
            vendor_data.command_count = await self.vendor_command_dao.count(vendor_id=vendor.id)
            vendor_responses.append(vendor_data)
        return vendor_responses

    # ===== 批量操作方法 =====

    @log_create_with_context("vendor")
    async def batch_create_vendors(
        self, vendors_data: list[VendorCreateRequest], operation_context: OperationContext
    ) -> list[VendorResponse]:
        """批量创建厂商"""
        # 转换为字典列表
        data_list = [vendor_data.model_dump() for vendor_data in vendors_data]

        # 批量验证厂商代码唯一性
        vendor_codes = [data.get("vendor_code") for data in data_list if data.get("vendor_code")]
        existing_codes = []
        for code in vendor_codes:
            if await self.dao.exists(vendor_code=code):
                existing_codes.append(code)

        if existing_codes:
            raise BusinessException(f"以下厂商代码已存在: {', '.join(existing_codes)}")

        # 使用BaseService的批量创建方法
        created_vendors = await self.bulk_create(data_list)
        return [VendorResponse.model_validate(vendor) for vendor in created_vendors]

    @log_update_with_context("vendor")
    async def batch_update_vendors(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> list[VendorResponse]:
        """批量更新厂商"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有厂商是否存在
        existing_vendors = await self.get_by_ids(update_ids)
        existing_ids = {str(vendor.id) for vendor in existing_vendors}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下厂商不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            update_data["id"] = update_item["id"]
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 返回更新后的数据
        updated_vendors = await self.get_by_ids(update_ids)
        return [VendorResponse.model_validate(vendor) for vendor in updated_vendors]

    @log_delete_with_context("vendor")
    async def batch_delete_vendors(self, vendor_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除厂商"""
        # 检查是否有设备关联
        for vendor_id in vendor_ids:
            device_count = await self.device_dao.count(vendor_id=vendor_id)
            if device_count > 0:
                vendor = await self.dao.get_by_id(vendor_id)
                vendor_name = vendor.vendor_name if vendor else str(vendor_id)
                raise BusinessException(f"厂商 '{vendor_name}' 下还有 {device_count} 台设备，无法删除")

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(vendor_ids, operation_context)
