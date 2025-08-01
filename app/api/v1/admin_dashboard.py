"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: admin_dashboard.py
@DateTime: 2025-01-29 10:08:28
@Docs: 后台管理相关的API接口
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import OperationContext, Permissions, require_permission
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.dashboard import UserPermissionCheck
from app.services.role import RoleService
from app.services.user import UserService
from app.utils.deps import (
    get_role_service,
    get_user_service,
)

router = APIRouter(prefix="/admin", tags=["后台管理仪表板"])


# 权限验证端点


async def _get_user_permissions_data(
    user_id: UUID,
    user_service: UserService,
    role_service: RoleService,
    operation_context: OperationContext,
):
    """获取用户权限数据的通用方法"""
    user_detail = await user_service.get_user_detail(user_id, operation_context)
    direct_permissions_response = await user_service.get_user_permissions(user_id, operation_context)
    direct_permissions = direct_permissions_response.data or []
    user_roles_response = await user_service.get_user_roles(user_id, operation_context)
    user_roles = user_roles_response.data or []

    role_permissions = {}
    for role in user_roles:
        role_perms = await role_service.get_role_permissions(role.id, operation_context)
        role_permissions[role.role_name] = [
            {
                "id": str(perm["id"]),
                "name": perm["permission_name"],
                "code": perm["permission_code"],
                "type": perm["permission_type"],
            }
            for perm in role_perms
        ]

    return {
        "user_detail": user_detail,
        "direct_permissions": direct_permissions,
        "user_roles": user_roles,
        "role_permissions": role_permissions,
    }


@router.post("/permissions/check", response_model=BaseResponse[UserPermissionCheck], summary="检查用户权限")
async def check_user_permission(
    user_id: UUID,
    permission_code: str,
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """检查用户是否拥有指定权限"""
    permissions_data = await _get_user_permissions_data(user_id, user_service, role_service, operation_context)

    has_permission = False
    permission_source = None

    # 检查直接权限
    for perm in permissions_data["direct_permissions"]:
        if perm.permission_code == permission_code:
            has_permission = True
            permission_source = "direct"
            break

    # 检查角色权限
    if not has_permission:
        for role in permissions_data["user_roles"]:
            role_perms = permissions_data["role_permissions"].get(role.role_name, [])
            for perm in role_perms:
                if perm["code"] == permission_code:
                    has_permission = True
                    permission_source = f"role:{role.role_name}"
                    break
            if has_permission:
                break

    permission_check = UserPermissionCheck(
        user_id=user_id,
        username=permissions_data["user_detail"].data.username if permissions_data["user_detail"].data else "Unknown",
        permission_code=permission_code,
        has_permission=has_permission,
        permission_source=permission_source,
    )
    return BaseResponse(data=permission_check, message="权限检查完成")


@router.get("/permissions/inheritance/{user_id}", response_model=BaseResponse[dict], summary="获取用户权限继承关系")
async def get_user_permission_inheritance(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """获取用户完整的权限继承关系"""
    permissions_data = await _get_user_permissions_data(user_id, user_service, role_service, operation_context)

    inheritance_data = {
        "user_id": str(user_id),
        "username": permissions_data["user_detail"].data.username
        if permissions_data["user_detail"].data
        else "Unknown",
        "direct_permissions": [
            {
                "id": str(perm.id),
                "name": perm.permission_name,
                "code": perm.permission_code,
                "description": perm.description,
            }
            for perm in permissions_data["direct_permissions"]
        ],
        "roles": [
            {
                "id": str(role.id),
                "name": role.role_name,
                "description": role.description or "",
            }
            for role in permissions_data["user_roles"]
        ],
        "role_permissions": permissions_data["role_permissions"],
    }
    return BaseResponse(data=inheritance_data, message="获取用户权限继承关系成功")


# 快速操作端点


async def _batch_update_user_status(
    user_ids: list[UUID],
    is_active: bool,
    user_service: UserService,
    operation_context: OperationContext,
) -> tuple[int, int]:
    """批量更新用户状态的通用方法

    Args:
        user_ids: 用户ID列表
        is_active: 目标状态
        user_service: 用户服务
        operation_context: 操作上下文

    Returns:
        tuple[成功数量, 总数量]
    """
    from app.schemas.user import UserUpdateRequest

    success_count = 0
    for user_id in user_ids:
        try:
            user = await user_service.get_by_id(user_id)
            if not user:
                continue

            update_request = UserUpdateRequest(is_active=is_active, version=user.version)
            await user_service.update_user(user_id, update_request, operation_context)
            success_count += 1
        except Exception:
            # 记录错误但继续处理其他用户
            continue

    return success_count, len(user_ids)


@router.post("/quick-actions/batch-enable-users", response_model=SuccessResponse, summary="批量启用用户")
async def batch_enable_users(
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """批量启用用户"""
    success_count, total_count = await _batch_update_user_status(user_ids, True, user_service, operation_context)
    return SuccessResponse(message=f"成功启用 {success_count}/{total_count} 个用户")


@router.post("/quick-actions/batch-disable-users", response_model=SuccessResponse, summary="批量禁用用户")
async def batch_disable_users(
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """批量禁用用户"""
    success_count, total_count = await _batch_update_user_status(user_ids, False, user_service, operation_context)
    return SuccessResponse(message=f"成功禁用 {success_count}/{total_count} 个用户")


# 数据导出端点


@router.get("/export/users", response_model=BaseResponse[list[dict]], summary="导出用户数据")
async def export_users(
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """导出用户数据"""
    from app.schemas.user import UserListRequest

    # 获取所有用户（分页获取以避免内存问题）
    all_users = []
    page = 1
    page_size = 100

    while True:
        users, total = await user_service.get_users(UserListRequest(page=page, page_size=page_size), operation_context)
        if not users:
            break

        for user in users:
            all_users.append(
                {
                    "id": str(user.id),
                    "username": user.username,
                    "phone": user.phone,
                    "nickname": user.nickname,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
            )

        if len(users) < page_size:
            break
        page += 1

    return BaseResponse(data=all_users, message="导出用户数据成功")


@router.get("/export/roles", response_model=BaseResponse[list[dict]], summary="导出角色数据")
async def export_roles(
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """导出角色数据"""
    from app.schemas.role import RoleListRequest

    # 获取所有角色
    all_roles = []
    page = 1
    page_size = 100

    while True:
        roles, total = await role_service.get_roles(RoleListRequest(page=page, page_size=page_size), operation_context)
        if not roles:
            break

        for role in roles:
            all_roles.append(
                {
                    "id": str(role.id),
                    "role_name": role.role_name,
                    "description": role.description,
                    "is_active": role.is_active,
                    "created_at": role.created_at.isoformat() if role.created_at else None,
                    "updated_at": role.updated_at.isoformat() if role.updated_at else None,
                }
            )

        if len(roles) < page_size:
            break
        page += 1

    return BaseResponse(data=all_roles, message="导出角色数据成功")
