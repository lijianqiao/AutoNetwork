"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/07/08
@Docs: 权限服务层 - 专注业务逻辑
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.models.permission import Permission
from app.schemas.permission import (
    PermissionCreateRequest,
    PermissionListRequest,
    PermissionResponse,
    PermissionUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)


class PermissionService(BaseService[Permission]):
    """权限服务"""

    def __init__(self):
        super().__init__(PermissionDAO())
        self.role_dao = RoleDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查权限编码唯一性"""
        if "permission_code" in data and await self.dao.exists(permission_code=data["permission_code"]):
            raise BusinessException("权限编码已存在")
        return data

    async def before_update(self, obj: Permission, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查权限编码唯一性"""
        if "permission_code" in data and await self.dao.exists(permission_code=data["permission_code"], id__not=obj.id):
            raise BusinessException("权限编码已存在")
        return data

    @log_create_with_context("permission")
    async def create_permission(
        self, request: PermissionCreateRequest, operation_context: OperationContext
    ) -> PermissionResponse:
        """创建权限"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        permission = await self.create(operation_context=operation_context, **create_data)
        if not permission:
            raise BusinessException("权限创建失败")
        return PermissionResponse.model_validate(permission)

    @log_update_with_context("permission")
    async def update_permission(
        self, permission_id: UUID, request: PermissionUpdateRequest, operation_context: OperationContext
    ) -> PermissionResponse:
        """更新权限"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_permission = await self.update(
            permission_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_permission:
            raise BusinessException("权限更新失败或版本冲突")
        return PermissionResponse.model_validate(updated_permission)

    @log_delete_with_context("permission")
    async def delete_permission(self, permission_id: UUID, operation_context: OperationContext) -> None:
        """删除权限，先检查是否被角色使用"""
        role_count = await self.role_dao.count(permissions__id=permission_id)
        if role_count > 0:
            raise BusinessException(f"该权限正在被 {role_count} 个角色使用，无法删除")
        await self.delete(permission_id, operation_context=operation_context)

    @log_query_with_context("permission")
    async def get_permissions(
        self, query: PermissionListRequest, operation_context: OperationContext
    ) -> tuple[list[PermissionResponse], int]:
        """获取权限列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        PERMISSION_MODEL_FIELDS = {"permission_type", "is_active"}
        search_fields = ["permission_name", "permission_code", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, PERMISSION_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        permissions, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        if not permissions:
            return [], 0
        result = [PermissionResponse.model_validate(p) for p in permissions]
        return result, total

    @log_query_with_context("permission")
    async def get_all_permissions(self, operation_context: OperationContext) -> list[PermissionResponse]:
        """获取所有权限（通常用于前端权限树）"""
        permissions = await self.dao.get_all(order_by=["permission_type", "created_at"])
        return [PermissionResponse.model_validate(p) for p in permissions]

    @log_query_with_context("permission")
    async def get_permission_detail(
        self, permission_id: UUID, operation_context: OperationContext
    ) -> PermissionResponse:
        """根据ID获取权限详情"""
        permission = await self.dao.get_by_id(permission_id, include_deleted=False)
        if not permission:
            raise BusinessException("权限未找到")
        return PermissionResponse.model_validate(permission)

    async def update_permission_status(
        self, permission_id: UUID, is_active: bool, operation_context: OperationContext
    ) -> None:
        """更新权限状态"""
        await self.update(permission_id, is_active=is_active, operation_context=operation_context)

    # ===== 批量操作方法 =====

    @log_create_with_context("permission")
    async def batch_create_permissions(
        self, permissions_data: list[PermissionCreateRequest], operation_context: OperationContext
    ) -> list[PermissionResponse]:
        """批量创建权限"""
        # 转换为字典列表并进行验证
        data_list = []
        for permission_data in permissions_data:
            data = permission_data.model_dump()
            # 应用前置验证
            validated_data = await self.before_create(data)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_permissions = await self.bulk_create(data_list)
        return [PermissionResponse.model_validate(permission) for permission in created_permissions]

    @log_update_with_context("permission")
    async def batch_update_permissions(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> list[PermissionResponse]:
        """批量更新权限"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有权限是否存在
        existing_permissions = await self.get_by_ids(update_ids)
        existing_ids = {str(perm.id) for perm in existing_permissions}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下权限不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 返回更新后的数据
        updated_permissions = await self.get_by_ids(update_ids)
        return [PermissionResponse.model_validate(permission) for permission in updated_permissions]

    @log_delete_with_context("permission")
    async def batch_delete_permissions(self, permission_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除权限"""
        # 检查权限是否存在
        existing_permissions = await self.get_by_ids(permission_ids)
        if len(existing_permissions) != len(permission_ids):
            missing_ids = {str(id) for id in permission_ids} - {str(p.id) for p in existing_permissions}
            raise BusinessException(f"以下权限不存在: {', '.join(missing_ids)}")

        # 检查是否存在系统权限不可删除
        system_permission_codes = [
            "user_create",
            "user_read",
            "user_update",
            "user_delete",
            "role_manage",
            "permission_manage",
        ]
        for permission in existing_permissions:
            if permission.permission_code in system_permission_codes:
                raise BusinessException(f"不能删除系统权限: {permission.permission_name}")

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(permission_ids, operation_context)
