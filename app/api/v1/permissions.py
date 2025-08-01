"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permissions.py
@DateTime: 2025/07/08
@Docs: 权限管理API端点 - 使用依赖注入权限控制
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.permission import (
    PermissionCreateRequest,
    PermissionListRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from app.services.permission import PermissionService
from app.utils.deps import OperationContext, get_permission_service

router = APIRouter(prefix="/permissions", tags=["权限管理"])


@router.get("", response_model=BaseResponse[PermissionListResponse], summary="获取权限列表")
async def list_permissions(
    query: PermissionListRequest = Depends(),
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_READ)),
):
    """获取权限列表（分页），支持搜索和筛选"""
    permissions, total = await service.get_permissions(query, operation_context=operation_context)
    response = PermissionListResponse(
        data=[PermissionResponse.model_validate(permission) for permission in permissions],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
    return BaseResponse(data=response)


@router.get("/{permission_id}", response_model=BaseResponse[PermissionResponse], summary="获取权限详情")
async def get_permission(
    permission_id: UUID,
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_READ)),
):
    """获取权限详情"""
    result = await service.get_permission_detail(permission_id, operation_context=operation_context)
    return BaseResponse(data=result)


@router.post(
    "", response_model=BaseResponse[PermissionResponse], status_code=status.HTTP_201_CREATED, summary="创建权限"
)
async def create_permission(
    permission_data: PermissionCreateRequest,
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_CREATE)),
):
    """创建新权限"""
    result = await service.create_permission(permission_data, operation_context=operation_context)
    return BaseResponse(data=result)


@router.put("/{permission_id}", response_model=BaseResponse[PermissionResponse], summary="更新权限")
async def update_permission(
    permission_id: UUID,
    permission_data: PermissionUpdateRequest,
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_UPDATE)),
):
    """更新权限信息"""
    result = await service.update_permission(permission_id, permission_data, operation_context=operation_context)
    return BaseResponse(data=result)


@router.delete("/{permission_id}", response_model=SuccessResponse, summary="删除权限")
async def delete_permission(
    permission_id: UUID,
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_DELETE)),
):
    """删除权限"""
    await service.delete_permission(permission_id, operation_context=operation_context)
    return SuccessResponse()


@router.put("/{permission_id}/status", response_model=SuccessResponse, summary="更新权限状态")
async def update_permission_status(
    permission_id: UUID,
    is_active: bool,
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_UPDATE)),
):
    """更新权限状态"""
    await service.update_permission_status(permission_id, is_active, operation_context=operation_context)
    return SuccessResponse()


# ===== 批量操作功能 =====


@router.post("/batch", response_model=BaseResponse[list[PermissionResponse]], summary="批量创建权限")
async def batch_create_permissions(
    permissions_data: list[PermissionCreateRequest],
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_CREATE)),
):
    """批量创建权限"""
    result = await service.batch_create_permissions(permissions_data, operation_context)
    return BaseResponse(data=result)


@router.put("/batch", response_model=BaseResponse[list[PermissionResponse]], summary="批量更新权限")
async def batch_update_permissions(
    updates_data: list[dict],  # [{"id": UUID, **update_fields}]
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_UPDATE)),
):
    """批量更新权限"""
    result = await service.batch_update_permissions(updates_data, operation_context)
    return BaseResponse(data=result)


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除权限")
async def batch_delete_permissions(
    permission_ids: list[UUID],
    service: PermissionService = Depends(get_permission_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.PERMISSION_DELETE)),
):
    """批量删除权限"""
    deleted_count = await service.batch_delete_permissions(permission_ids, operation_context)
    return SuccessResponse(message=f"成功删除 {deleted_count} 个权限")
