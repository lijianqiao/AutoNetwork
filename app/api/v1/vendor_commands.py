"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor_commands.py
@DateTime: 2025/07/23
@Docs: 厂商命令管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.vendor_command import (
    VendorCommandBatchCreateRequest,
    VendorCommandCreateRequest,
    VendorCommandListRequest,
    VendorCommandListResponse,
    VendorCommandResponse,
    VendorCommandUpdateRequest,
)
from app.services.vendor_command import VendorCommandService
from app.utils.deps import OperationContext, get_vendor_command_service

router = APIRouter(prefix="/vendor-commands", tags=["厂商命令管理"])


@router.get("", response_model=VendorCommandListResponse, summary="获取厂商命令列表")
async def list_vendor_commands(
    query: VendorCommandListRequest = Depends(),
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_READ)),
):
    """获取厂商命令列表，支持筛选"""
    return await service.get_vendor_command_list(query, operation_context)


@router.get("/{command_id}", response_model=VendorCommandResponse, summary="获取厂商命令详情")
async def get_vendor_command(
    command_id: UUID,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_READ)),
):
    """获取厂商命令详情"""
    return await service.get_vendor_command_by_id(command_id, operation_context)


@router.post("", response_model=VendorCommandResponse, status_code=status.HTTP_201_CREATED, summary="创建厂商命令")
async def create_vendor_command(
    command_data: VendorCommandCreateRequest,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_CREATE)),
):
    """创建新厂商命令"""
    return await service.create_vendor_command(command_data, operation_context)


@router.put("/{command_id}", response_model=VendorCommandResponse, summary="更新厂商命令")
async def update_vendor_command(
    command_id: UUID,
    command_data: VendorCommandUpdateRequest,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_UPDATE)),
):
    """更新厂商命令信息"""
    return await service.update_vendor_command(command_id, command_data, operation_context)


@router.delete("/{command_id}", response_model=SuccessResponse, summary="删除厂商命令")
async def delete_vendor_command(
    command_id: UUID,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_DELETE)),
):
    """删除厂商命令"""
    await service.delete_vendor_command(command_id, operation_context)
    return SuccessResponse(message="厂商命令删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[VendorCommandResponse], summary="批量创建厂商命令")
async def batch_create_vendor_commands(
    batch_data: VendorCommandBatchCreateRequest,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_CREATE)),
):
    """批量创建厂商命令"""
    return await service.batch_create_commands(batch_data, operation_context)


@router.put("/batch/status", response_model=SuccessResponse, summary="批量更新命令状态")
async def batch_update_command_status(
    command_ids: list[UUID],
    is_active: bool,
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_UPDATE)),
):
    """批量更新厂商命令状态"""
    updated_count = await service.batch_update_status(command_ids, is_active, operation_context)
    return SuccessResponse(message=f"成功更新 {updated_count} 个厂商命令状态")


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除厂商命令")
async def batch_delete_vendor_commands(
    command_ids: list[UUID],
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_DELETE)),
):
    """批量删除厂商命令"""
    deleted_count = await service.batch_delete_commands(command_ids, operation_context)
    return SuccessResponse(message=f"成功删除 {deleted_count} 个厂商命令")


# ===== 统计功能 =====


@router.get("/statistics/overview", response_model=dict, summary="获取厂商命令统计信息")
async def get_command_statistics(
    service: VendorCommandService = Depends(get_vendor_command_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_COMMAND_READ)),
):
    """获取厂商命令统计信息"""
    return await service.get_command_statistics(operation_context)
