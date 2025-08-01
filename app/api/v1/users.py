"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: users.py
@DateTime: 2025/07/08
@Docs: 用户管理API端点

职责说明：
- 用户基本信息的CRUD操作（创建、查询、更新、删除）
- 用户状态管理（启用/禁用）
- 用户密码管理
- 用户批量操作（批量创建、更新、删除）

重要说明：
- 本模块专注于用户基本信息管理
- 用户-角色关系管理请使用 user_relations.py 模块
- 用户-权限关系管理请使用 user_relations.py 模块
- 职责边界清晰，避免功能重复
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.user import (
    UserCreateRequest,
    UserCreateResponse,
    UserDeleteResponse,
    UserDetailResponseWrapper,
    UserListRequest,
    UserListResponseWrapper,
    UserResponse,
    UserStatusUpdateResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.services.user import UserService
from app.utils.deps import OperationContext, get_user_service

router = APIRouter(prefix="/users", tags=["用户管理"])

# 保持分页响应的原有格式，但其他响应统一使用BaseResponse
UserListResponse = PaginatedResponse[UserResponse]


@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def list_users(
    query: UserListRequest = Depends(),
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户列表（分页）"""
    users, total = await user_service.get_users(query, operation_context=operation_context)
    return UserListResponse(data=users, total=total, page=query.page, page_size=query.page_size)


@router.get("/{user_id}", response_model=UserDetailResponseWrapper, summary="获取用户详情")
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户详情"""
    result = await user_service.get_user_detail(user_id, operation_context=operation_context)
    return result


@router.post("", response_model=UserCreateResponse, summary="创建用户", status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_CREATE)),
):
    """创建新用户"""
    result = await user_service.create_user(user_data, operation_context=operation_context)
    return result


@router.put("/{user_id}", response_model=UserUpdateResponse, summary="更新用户")
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """更新用户信息"""
    result = await user_service.update_user(user_id, user_data, operation_context=operation_context)
    return result


@router.delete("/{user_id}", response_model=UserDeleteResponse, summary="删除用户")
async def delete_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_DELETE)),
):
    """删除用户"""
    await user_service.delete_user(user_id, operation_context=operation_context)
    result = SuccessResponse()
    return result


@router.put("/{user_id}/status", response_model=UserStatusUpdateResponse, summary="更新用户状态")
async def update_user_status(
    user_id: UUID,
    is_active: bool,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """更新用户状态"""
    await user_service.update_user_status(user_id, is_active, operation_context=operation_context)
    result = SuccessResponse()
    return result


# ===== 批量操作功能 =====


@router.post("/batch", response_model=UserListResponseWrapper, summary="批量创建用户")
async def batch_create_users(
    users_data: list[UserCreateRequest],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_CREATE)),
):
    """批量创建用户"""
    result = await user_service.batch_create_users(users_data, operation_context)
    return result


@router.put("/batch", response_model=UserListResponseWrapper, summary="批量更新用户")
async def batch_update_users(
    updates_data: list[dict],  # [{"id": UUID, **update_fields}]
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """批量更新用户"""
    result = await user_service.batch_update_users(updates_data, operation_context)
    return result


@router.delete("/batch", response_model=UserDeleteResponse, summary="批量删除用户")
async def batch_delete_users(
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_DELETE)),
):
    """批量删除用户"""
    deleted_count = await user_service.batch_delete_users(user_ids, operation_context)
    result = SuccessResponse(message=f"成功删除 {deleted_count} 个用户")
    return result
