"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: devices.py
@DateTime: 2025/07/23
@Docs: 设备管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceDetailResponse,
    DeviceListRequest,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdateRequest,
)
from app.services.device import DeviceService
from app.utils.deps import OperationContext, get_device_service

router = APIRouter(prefix="/devices", tags=["设备管理"])


@router.get("", response_model=DeviceListResponse, summary="获取设备列表")
async def list_devices(
    query: DeviceListRequest = Depends(),
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_READ)),
):
    """获取设备列表（分页），支持搜索和筛选"""
    devices, total = await service.get_devices(query, operation_context=operation_context)
    return DeviceListResponse(data=devices, total=total, page=query.page, page_size=query.page_size)


@router.get("/{device_id}", response_model=DeviceDetailResponse, summary="获取设备详情")
async def get_device(
    device_id: UUID,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_READ)),
):
    """获取设备详情"""
    device = await service.get_device_detail(device_id, operation_context=operation_context)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED, summary="创建设备")
async def create_device(
    device_data: DeviceCreateRequest,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CREATE)),
):
    """创建新设备"""
    return await service.create_device(device_data, operation_context=operation_context)


@router.put("/{device_id}", response_model=DeviceResponse, summary="更新设备")
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdateRequest,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_UPDATE)),
):
    """更新设备信息"""
    return await service.update_device(device_id, device_data, operation_context=operation_context)


@router.delete("/{device_id}", response_model=SuccessResponse, summary="删除设备")
async def delete_device(
    device_id: UUID,
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_DELETE)),
):
    """删除设备"""
    await service.delete_device(device_id, operation_context=operation_context)
    return SuccessResponse(message="设备删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[DeviceResponse], summary="批量创建设备")
async def batch_create_devices(
    devices_data: list[DeviceCreateRequest],
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CREATE)),
):
    """批量创建设备"""
    results = []
    for device_data in devices_data:
        result = await service.create_device(device_data, operation_context=operation_context)
        results.append(result)
    return results


@router.put("/batch", response_model=list[DeviceResponse], summary="批量更新设备")
async def batch_update_devices(
    updates_data: list[dict],  # [{"id": UUID, "data": DeviceUpdateRequest}]
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_UPDATE)),
):
    """批量更新设备"""
    results = []
    for update_item in updates_data:
        device_id = update_item["id"]
        device_data = DeviceUpdateRequest(**update_item["data"])
        result = await service.update_device(device_id, device_data, operation_context=operation_context)
        results.append(result)
    return results


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除设备")
async def batch_delete_devices(
    device_ids: list[UUID],
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_DELETE)),
):
    """批量删除设备"""
    for device_id in device_ids:
        await service.delete_device(device_id, operation_context=operation_context)
    return SuccessResponse(message=f"成功删除 {len(device_ids)} 台设备")


@router.post("/{device_id}/test-connection", response_model=dict, summary="测试设备连接")
async def test_device_connection(
    device_id: UUID,
    username: str = Query(description="登录用户名"),
    password: str = Query(description="登录密码"),
    service: DeviceService = Depends(get_device_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONNECTION_TEST)),
):
    """测试设备连接性"""
    # TODO: 实现实际的设备连接测试逻辑
    return {
        "device_id": device_id,
        "connection_status": "success",
        "message": "设备连接测试成功",
        "response_time": 150,
    }
