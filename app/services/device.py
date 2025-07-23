"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/07/23
@Docs: 网络设备服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.device import DeviceDAO
from app.dao.region import RegionDAO
from app.dao.vendor import VendorDAO
from app.models.device import Device
from app.schemas.device import (
    DeviceAuthTypeUpdateRequest,
    DeviceBatchOperationRequest,
    DeviceConnectionResult,
    DeviceConnectionTestRequest,
    DeviceConnectionTestResponse,
    DeviceCreateRequest,
    DeviceDetailResponse,
    DeviceListRequest,
    DeviceResponse,
    DeviceUpdateRequest,
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


class DeviceService(BaseService[Device]):
    """网络设备服务"""

    def __init__(self):
        self.dao = DeviceDAO()
        super().__init__(self.dao)
        self.vendor_dao = VendorDAO()
        self.region_dao = RegionDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查设备主机名和IP地址唯一性，验证关联关系"""
        if "hostname" in data and await self.dao.exists(hostname=data["hostname"]):
            logger.warning(f"创建设备失败: 设备主机名已存在 {data['hostname']}")
            raise BusinessException("设备主机名已存在")

        if "ip_address" in data and await self.dao.exists(ip_address=str(data["ip_address"])):
            logger.warning(f"创建设备失败: 设备IP地址已存在 {data['ip_address']}")
            raise BusinessException("设备IP地址已存在")

        # 验证厂商存在
        if "vendor_id" in data:
            if not await self.vendor_dao.exists(id=data["vendor_id"]):
                logger.warning(f"创建设备失败: 指定的厂商不存在 {data['vendor_id']}")
                raise BusinessException("指定的厂商不存在")

        # 验证基地存在
        if "region_id" in data:
            if not await self.region_dao.exists(id=data["region_id"]):
                logger.warning(f"创建设备失败: 指定的基地不存在 {data['region_id']}")
                raise BusinessException("指定的基地不存在")

        # 转换IP地址为字符串
        if "ip_address" in data:
            data["ip_address"] = str(data["ip_address"])

        return data

    async def before_update(self, obj: Device, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查设备主机名和IP地址唯一性，验证关联关系"""
        if "hostname" in data and await self.dao.exists(hostname=data["hostname"], id__not=obj.id):
            logger.warning(f"更新设备失败: 设备主机名已存在 {data['hostname']}")
            raise BusinessException("设备主机名已存在")

        if "ip_address" in data:
            ip_str = str(data["ip_address"])
            if await self.dao.exists(ip_address=ip_str, id__not=obj.id):
                logger.warning(f"更新设备失败: 设备IP地址已存在 {ip_str}")
                raise BusinessException("设备IP地址已存在")
            data["ip_address"] = ip_str

        # 验证厂商存在
        if "vendor_id" in data:
            if not await self.vendor_dao.exists(id=data["vendor_id"]):
                logger.warning(f"更新设备失败: 指定的厂商不存在 {data['vendor_id']}")
                raise BusinessException("指定的厂商不存在")

        # 验证基地存在
        if "region_id" in data:
            if not await self.region_dao.exists(id=data["region_id"]):
                logger.warning(f"更新设备失败: 指定的基地不存在 {data['region_id']}")
                raise BusinessException("指定的基地不存在")

        return data

    @log_create_with_context("device")
    async def create_device(self, request: DeviceCreateRequest, operation_context: OperationContext) -> DeviceResponse:
        """创建设备"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        device = await self.create(operation_context=operation_context, **create_data)
        if not device:
            logger.error("设备创建失败")
            raise BusinessException("设备创建失败")

        # 获取关联信息
        device_with_relations = await self.dao.get_with_related(device.id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_update_with_context("device")
    async def update_device(
        self, device_id: UUID, request: DeviceUpdateRequest, operation_context: OperationContext
    ) -> DeviceResponse:
        """更新设备"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            logger.error("更新请求必须包含 version 字段。")
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_device = await self.update(
            device_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_device:
            logger.error("设备更新失败或版本冲突")
            raise BusinessException("设备更新失败或版本冲突")

        # 获取关联信息
        device_with_relations = await self.dao.get_with_related(device_id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_delete_with_context("device")
    async def delete_device(self, device_id: UUID, operation_context: OperationContext) -> None:
        """删除设备"""
        device = await self.dao.get_by_id(device_id)
        if not device:
            logger.error("设备未找到")
            raise BusinessException("设备未找到")

        await self.delete(device_id, operation_context=operation_context)

    @log_query_with_context("device")
    async def get_devices(
        self, query: DeviceListRequest, operation_context: OperationContext
    ) -> tuple[list[DeviceResponse], int]:
        """获取设备列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        DEVICE_MODEL_FIELDS = {
            "hostname",
            "ip_address",
            "device_type",
            "network_layer",
            "vendor_id",
            "region_id",
            "auth_type",
            "is_active",
        }
        search_fields = ["hostname", "ip_address", "model", "serial_number", "location"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, DEVICE_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        devices, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            select_related=["vendor", "region"],
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        return [DeviceResponse.model_validate(device) for device in devices], total

    @log_query_with_context("device")
    async def get_device_detail(self, device_id: UUID, operation_context: OperationContext) -> DeviceDetailResponse:
        """获取设备详情"""
        device = await self.dao.get_with_related(device_id, select_related=["vendor", "region"])
        if not device:
            logger.error("设备未找到")
            raise BusinessException("设备未找到")
        return DeviceDetailResponse.model_validate(device)

    @log_query_with_context("device")
    async def get_device_by_hostname(self, hostname: str, operation_context: OperationContext) -> DeviceResponse:
        """根据主机名获取设备"""
        device = await self.dao.get_by_hostname(hostname)
        if not device:
            logger.error(f"主机名 '{hostname}' 未找到")
            raise BusinessException(f"主机名 '{hostname}' 未找到")

        device_with_relations = await self.dao.get_with_related(device.id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_query_with_context("device")
    async def get_device_by_ip(self, ip_address: str, operation_context: OperationContext) -> DeviceResponse:
        """根据IP地址获取设备"""
        device = await self.dao.get_by_ip_address(ip_address)
        if not device:
            logger.error(f"IP地址 '{ip_address}' 未找到")
            raise BusinessException(f"IP地址 '{ip_address}' 未找到")

        device_with_relations = await self.dao.get_with_related(device.id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_update_with_context("device")
    async def update_auth_type(
        self, device_id: UUID, request: DeviceAuthTypeUpdateRequest, operation_context: OperationContext
    ) -> DeviceResponse:
        """更新设备认证类型"""
        device = await self.dao.get_by_id(device_id)
        if not device:
            logger.error("设备未找到")
            raise BusinessException("设备未找到")

        update_data = request.model_dump(exclude_unset=True)

        # 如果切换到动态密码，清除静态密码信息
        if update_data.get("auth_type") == "dynamic":
            update_data["static_username"] = None
            update_data["static_password"] = None

        updated_device = await self.update(device_id, operation_context=operation_context, **update_data)
        if not updated_device:
            logger.error("认证类型更新失败")
            raise BusinessException("认证类型更新失败")

        device_with_relations = await self.dao.get_with_related(device_id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_update_with_context("device")
    async def activate_device(self, device_id: UUID, operation_context: OperationContext) -> DeviceResponse:
        """激活设备"""
        updated_device = await self.update(device_id, operation_context=operation_context, is_active=True)
        if not updated_device:
            logger.error("设备激活失败")
            raise BusinessException("设备激活失败")

        device_with_relations = await self.dao.get_with_related(device_id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_update_with_context("device")
    async def deactivate_device(self, device_id: UUID, operation_context: OperationContext) -> DeviceResponse:
        """停用设备"""
        updated_device = await self.update(device_id, operation_context=operation_context, is_active=False)
        if not updated_device:
            logger.error("设备停用失败")
            raise BusinessException("设备停用失败")

        device_with_relations = await self.dao.get_with_related(device_id, select_related=["vendor", "region"])
        return DeviceResponse.model_validate(device_with_relations)

    @log_update_with_context("device")
    async def batch_operation(
        self, request: DeviceBatchOperationRequest, operation_context: OperationContext
    ) -> dict[str, int]:
        """设备批量操作"""
        device_ids = request.device_ids
        operation = request.operation

        # 验证设备存在
        existing_devices = await self.dao.get_by_ids(device_ids)
        if len(existing_devices) != len(device_ids):
            logger.error("部分设备不存在")
            raise BusinessException("部分设备不存在")

        success_count = 0

        if operation == "activate":
            success_count = await self.bulk_activate(device_ids)
        elif operation == "deactivate":
            success_count = await self.bulk_deactivate(device_ids)
        elif operation == "delete":
            success_count = await self.delete_by_ids(device_ids, operation_context=operation_context)
        else:
            logger.error(f"不支持的操作类型: {operation}")
            raise BusinessException(f"不支持的操作类型: {operation}")

        return {
            "total_count": len(device_ids),
            "success_count": success_count,
            "failed_count": len(device_ids) - success_count,
        }

    @log_query_with_context("device")
    async def test_connection(
        self, request: DeviceConnectionTestRequest, operation_context: OperationContext
    ) -> DeviceConnectionTestResponse:
        """测试设备连接"""
        device_ids = request.device_ids
        devices = await self.dao.get_by_ids(device_ids)

        if not devices:
            logger.error("没有找到指定的设备")
            raise BusinessException("没有找到指定的设备")

        results = []
        success_count = 0

        for device in devices:
            # 这里应该调用实际的网络连接测试逻辑
            # 暂时返回模拟结果
            result = DeviceConnectionResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=True,  # 实际应该进行连接测试
                connection_time=0.5,
            )

            if result.success:
                success_count += 1

            results.append(result)

        return DeviceConnectionTestResponse(
            total_count=len(devices),
            success_count=success_count,
            failed_count=len(devices) - success_count,
            results=results,
        )
