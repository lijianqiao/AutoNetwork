"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: devices.py
@DateTime: 2025/07/23
@Docs: 设备管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.exceptions import NotFoundException
from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse
from app.schemas.device import (
    DeviceBatchCreateResponse,
    DeviceBatchDeleteResponse,
    DeviceBatchUpdateResponse,
    DeviceCreateRequest,
    DeviceCreateResponse,
    DeviceDeleteResponse,
    DeviceDetailResponseWrapper,
    DeviceListRequest,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdateRequest,
    DeviceUpdateResponse,
)
from app.services.device import DeviceService
from app.utils.deps import OperationContext, get_device_service

router = APIRouter(prefix="/devices", tags=["设备管理"])


@router.get("", response_model=BaseResponse[DeviceListResponse], summary="获取设备列表")
async def list_devices(
    query: DeviceListRequest = Depends(),
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_READ)),
):
    """获取设备列表（分页），支持搜索和筛选"""
    devices, total = await service.get_devices(query, operation_context=operation_context)
    response_data = DeviceListResponse(
        data=[DeviceResponse.model_validate(device) for device in devices],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
    return BaseResponse(data=response_data)


@router.get("/{device_id}", response_model=BaseResponse[DeviceDetailResponseWrapper], summary="获取设备详情")
async def get_device(
    device_id: UUID,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_READ)),
):
    """获取设备详情"""
    device = await service.get_device_detail(device_id, operation_context=operation_context)
    if not device:
        raise NotFoundException(detail="设备不存在")
    return BaseResponse(data=device)


@router.post(
    "", response_model=BaseResponse[DeviceCreateResponse], status_code=status.HTTP_201_CREATED, summary="创建设备"
)
async def create_device(
    device_data: DeviceCreateRequest,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CREATE)),
):
    """创建新设备"""
    result = await service.create_device(device_data, operation_context=operation_context)
    return BaseResponse(data=result)


@router.put("/{device_id}", response_model=BaseResponse[DeviceUpdateResponse], summary="更新设备")
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdateRequest,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_UPDATE)),
):
    """更新设备信息"""
    result = await service.update_device(device_id, device_data, operation_context=operation_context)
    return BaseResponse(data=result)


@router.delete("/{device_id}", response_model=BaseResponse[dict], summary="删除设备")
async def delete_device(
    device_id: UUID,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_DELETE)),
):
    """删除设备"""
    await service.delete_device(device_id, operation_context=operation_context)
    return BaseResponse(data={"message": "设备删除成功"})


# ===== 批量操作功能 =====


@router.post("/batch", response_model=BaseResponse[DeviceBatchCreateResponse], summary="批量创建设备")
async def batch_create_devices(
    devices_data: list[DeviceCreateRequest],
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CREATE)),
):
    """批量创建设备"""
    result = await service.batch_create_devices(devices_data, operation_context)
    return BaseResponse(data=result)


@router.put("/batch", response_model=BaseResponse[DeviceBatchUpdateResponse], summary="批量更新设备")
async def batch_update_devices(
    updates_data: list[dict],  # [{"id": UUID, "data": DeviceUpdateRequest}]
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_UPDATE)),
):
    """批量更新设备"""
    result = await service.batch_update_devices(updates_data, operation_context)
    return BaseResponse(data=result)


@router.delete("/batch", response_model=DeviceBatchDeleteResponse, summary="批量删除设备")
async def batch_delete_devices(
    device_ids: list[UUID],
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_DELETE)),
):
    """批量删除设备"""
    deleted_count = await service.batch_delete_devices(device_ids, operation_context)
    return BaseResponse(data={"message": f"成功删除 {deleted_count} 台设备"})


@router.post("/{device_id}/test-connection", response_model=DeviceDeleteResponse, summary="测试设备连接")
async def test_device_connection(
    device_id: UUID,
    username: str = Query(description="登录用户名"),
    password: str = Query(description="登录密码"),
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONNECTION_TEST)),
):
    """测试设备连接性"""
    # TODO: 实现实际的设备连接测试逻辑
    result = {
        "device_id": device_id,
        "connection_status": "success",
        "message": "设备连接测试成功",
        "response_time": 150,
    }
    return BaseResponse(data=result)
