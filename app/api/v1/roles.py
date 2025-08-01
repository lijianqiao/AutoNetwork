"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: roles.py
@DateTime: 2025/07/08
@Docs: 角色管理API端点 - 使用依赖注入权限控制

职责说明：
- 角色基本信息的CRUD操作（创建、查询、更新、删除）
- 角色状态管理（启用/禁用）
- 角色-权限关系管理（分配、添加、移除角色权限）
- 角色权限查询和统计

设计原则：
- 专注于角色本身的管理和角色权限的维护
- 不直接处理用户-角色关系，该功能由 user_relations.py 负责
- 与用户关系的协调通过服务层完成
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.role import (
    RoleCreateRequest,
    RoleDetailResponse,
    RoleListRequest,
    RoleListResponse,
    RolePermissionAssignRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.role import RoleService
from app.utils.deps import OperationContext, get_role_service

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("", response_model=RoleListResponse, summary="获取角色列表")
async def list_roles(
    query: RoleListRequest = Depends(),
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色列表（分页），支持搜索和筛选"""
    roles, total = await service.get_roles(query, operation_context=operation_context)
    result = RoleListResponse(
        data=[RoleResponse.model_validate(role) for role in roles],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
    return result


@router.get("/{role_id}", response_model=RoleDetailResponse, summary="获取角色详情")
async def get_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色详情，包含其所有权限"""
    result = await service.get_role_detail(role_id, operation_context=operation_context)
    return result


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="创建角色")
async def create_role(
    role_data: RoleCreateRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_CREATE)),
):
    """创建新角色"""
    result = await service.create_role(role_data, operation_context=operation_context)
    return result


@router.put("/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(
    role_id: UUID,
    role_data: RoleUpdateRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_UPDATE)),
):
    """更新角色信息"""
    result = await service.update_role(role_id, role_data, operation_context=operation_context)
    return result


@router.delete("/{role_id}", response_model=SuccessResponse, summary="删除角色")
async def delete_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_DELETE)),
):
    """删除角色"""
    await service.delete_role(role_id, operation_context=operation_context)
    result = SuccessResponse()
    return result


@router.put("/{role_id}/status", response_model=SuccessResponse, summary="更新角色状态")
async def update_role_status(
    role_id: UUID,
    is_active: bool,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_UPDATE)),
):
    """更新角色状态"""
    await service.update_role_status(role_id, is_active, operation_context=operation_context)
    result = SuccessResponse()
    return result


@router.post("/{role_id}/permissions", response_model=RoleDetailResponse, summary="分配角色权限")
async def assign_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """分配角色权限（全量设置）"""
    result = await service.assign_permissions_to_role(role_id, permission_data, operation_context=operation_context)
    return result


# 角色权限关系管理端点


@router.post("/{role_id}/permissions/add", response_model=RoleDetailResponse, summary="为角色添加权限")
async def add_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """为角色增量添加权限"""
    result = await service.add_role_permissions(
        role_id, permission_data.permission_ids, operation_context=operation_context
    )
    return result


@router.delete("/{role_id}/permissions/remove", response_model=RoleDetailResponse, summary="移除角色权限")
async def remove_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """移除角色的指定权限"""
    result = await service.remove_role_permissions(
        role_id, permission_data.permission_ids, operation_context=operation_context
    )
    return result


@router.get("/{role_id}/permissions", response_model=list[dict], summary="获取角色权限列表")
async def get_role_permissions(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色的权限列表"""
    result = await service.get_role_permissions(role_id, operation_context=operation_context)
    return result


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[RoleResponse], summary="批量创建角色")
async def batch_create_roles(
    roles_data: list[RoleCreateRequest],
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_CREATE)),
):
    """批量创建角色"""
    result = await service.batch_create_roles(roles_data, operation_context)
    return result


@router.put("/batch", response_model=list[RoleResponse], summary="批量更新角色")
async def batch_update_roles(
    updates_data: list[dict],  # [{"id": UUID, **update_fields}]
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_UPDATE)),
):
    """批量更新角色"""
    result = await service.batch_update_roles(updates_data, operation_context)
    return result


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除角色")
async def batch_delete_roles(
    role_ids: list[UUID],
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_DELETE)),
):
    """批量删除角色"""
    deleted_count = await service.batch_delete_roles(role_ids, operation_context)
    result = SuccessResponse(message=f"成功删除 {deleted_count} 个角色")
    return result
