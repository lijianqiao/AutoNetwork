"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/07/08
@Docs: 角色服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.models.role import Role
from app.schemas.role import (
    RoleCreateRequest,
    RoleDetailResponse,
    RoleListRequest,
    RolePermissionAssignRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)
from app.utils.permission_cache_utils import invalidate_role_permission_cache


class RoleService(BaseService[Role]):
    """角色服务"""

    def __init__(self):
        self.dao = RoleDAO()
        super().__init__(self.dao)
        self.permission_dao = PermissionDAO()
        self.user_dao = UserDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查角色名称和编码唯一性"""
        if "role_code" in data and await self.dao.exists(role_code=data["role_code"]):
            raise BusinessException("角色编码已存在")
        if "role_name" in data and await self.dao.exists(role_name=data["role_name"]):
            raise BusinessException("角色名称已存在")
        return data

    async def before_update(self, obj: Role, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查角色名称和编码唯一性"""
        if "role_code" in data and await self.dao.exists(role_code=data["role_code"], id__not=obj.id):
            raise BusinessException("角色编码已存在")
        if "role_name" in data and await self.dao.exists(role_name=data["role_name"], id__not=obj.id):
            raise BusinessException("角色名称已存在")
        return data

    @log_create_with_context("role")
    async def create_role(self, request: RoleCreateRequest, operation_context: OperationContext) -> RoleResponse:
        """创建角色"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        role = await self.create(operation_context=operation_context, **create_data)
        if not role:
            raise BusinessException("角色创建失败")
        return RoleResponse.model_validate(role)

    @log_update_with_context("role")
    async def update_role(
        self, role_id: UUID, request: RoleUpdateRequest, operation_context: OperationContext
    ) -> RoleResponse:
        """更新角色"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_role = await self.update(role_id, operation_context=operation_context, version=version, **update_data)
        if not updated_role:
            raise BusinessException("角色更新失败或版本冲突")
        return RoleResponse.model_validate(updated_role)

    @log_delete_with_context("role")
    async def delete_role(self, role_id: UUID, operation_context: OperationContext) -> None:
        """删除角色，检查是否仍有用户关联"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")
        # 检查是否有用户正在使用此角色
        user_count = await self.user_dao.count(roles__id=role_id)
        if user_count > 0:
            raise BusinessException(f"角色 '{role.role_name}' 正在被 {user_count} 个用户使用，无法删除")
        await self.delete(role_id, operation_context=operation_context)

    @log_query_with_context("role")
    async def get_roles(
        self, query: RoleListRequest, operation_context: OperationContext
    ) -> tuple[list[RoleResponse], int]:
        """获取角色列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        ROLE_MODEL_FIELDS = {"role_code", "is_active"}
        search_fields = ["role_name", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, ROLE_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        roles, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )
        return [RoleResponse.model_validate(role) for role in roles], total

    @log_query_with_context("role")
    async def get_role_detail(self, role_id: UUID, operation_context: OperationContext) -> RoleDetailResponse:
        """获取带权限的角色详情"""
        role = await self.dao.get_with_related(role_id, prefetch_related=["permissions"], include_deleted=False)
        if not role:
            raise BusinessException("角色未找到")
        return RoleDetailResponse.model_validate(role)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def assign_permissions_to_role(
        self, role_id: UUID, request: RolePermissionAssignRequest, operation_context: OperationContext
    ) -> RoleDetailResponse:
        """为角色分配权限（全量设置）"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")

        # 使用 DAO 层的全量设置方法
        await self.dao.set_permissions(role_id, request.permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def add_role_permissions(
        self, role_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> RoleDetailResponse:
        """为角色增量添加权限"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")

        await self.dao.add_permissions(role_id, permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def remove_role_permissions(
        self, role_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> RoleDetailResponse:
        """移除角色的指定权限"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")

        await self.dao.remove_permissions(role_id, permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    async def get_role_permissions(self, role_id: UUID, operation_context: OperationContext) -> list[dict]:
        """获取角色的权限列表"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")

        permissions = await self.dao.get_role_permissions(role_id)
        return [
            {
                "id": perm.id,
                "permission_name": perm.permission_name,
                "permission_code": perm.permission_code,
                "permission_type": perm.permission_type,
            }
            for perm in permissions
        ]

    @log_query_with_context("role")
    async def get_role_by_code(self, role_code: str, operation_context: OperationContext) -> RoleResponse:
        """根据编码获取角色"""
        role = await self.get_one(role_code=role_code)
        if not role:
            raise BusinessException("角色未找到")
        return RoleResponse.model_validate(role)

    @log_update_with_context("role")
    async def update_role_status(self, role_id: UUID, is_active: bool, operation_context: OperationContext) -> None:
        """更新角色状态"""
        role = await self.dao.get_by_id(role_id)
        if not role:
            raise BusinessException("角色未找到")
        await self.update(role_id, operation_context=operation_context, version=role.version, is_active=is_active)

    # ===== 批量操作方法 =====

    @log_create_with_context("role")
    async def batch_create_roles(
        self, roles_data: list[RoleCreateRequest], operation_context: OperationContext
    ) -> list[RoleResponse]:
        """批量创建角色"""
        # 转换为字典列表并进行验证
        data_list = []
        for role_data in roles_data:
            data = role_data.model_dump()
            # 应用前置验证
            validated_data = await self.before_create(data)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_roles = await self.bulk_create(data_list)
        return [RoleResponse.model_validate(role) for role in created_roles]

    @log_update_with_context("role")
    async def batch_update_roles(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> list[RoleResponse]:
        """批量更新角色"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有角色是否存在
        existing_roles = await self.get_by_ids(update_ids)
        existing_ids = {str(role.id) for role in existing_roles}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下角色不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 清除相关角色的权限缓存
        for role_id in update_ids:
            invalidate_role_permission_cache(role_id)

        # 返回更新后的数据
        updated_roles = await self.get_by_ids(update_ids)
        return [RoleResponse.model_validate(role) for role in updated_roles]

    @log_delete_with_context("role")
    async def batch_delete_roles(self, role_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除角色"""
        # 检查角色是否存在
        existing_roles = await self.get_by_ids(role_ids)
        if len(existing_roles) != len(role_ids):
            missing_ids = {str(id) for id in role_ids} - {str(r.id) for r in existing_roles}
            raise BusinessException(f"以下角色不存在: {', '.join(missing_ids)}")

        # 检查是否存在内置角色不可删除
        for role in existing_roles:
            if role.role_code in ["admin", "user", "super_admin"]:  # 假设这些是系统内置角色
                raise BusinessException(f"不能删除系统内置角色: {role.role_name}")

        # 清除相关角色的权限缓存
        for role_id in role_ids:
            invalidate_role_permission_cache(role_id)

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(role_ids, operation_context)
