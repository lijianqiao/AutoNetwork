"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/07/23
@Docs: 用户服务层 - 集成 Pydantic schemas 进行数据校验和序列化
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.security import hash_password, verify_password
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.models.permission import Permission
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleResponse
from app.schemas.user import (
    UserAssignPermissionsRequest,
    UserAssignPermissionsResponse,
    UserAssignRolesResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserDeleteResponse,
    UserDetailResponse,
    UserDetailResponseWrapper,
    UserListRequest,
    UserListResponseWrapper,
    UserResponse,
    UserStatusUpdateResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)
from app.utils.permission_cache_utils import invalidate_user_permission_cache


class UserService(BaseService[User]):
    """用户服务"""

    def __init__(self):
        self.dao = UserDAO()
        self.role_dao = RoleDAO()
        self.permission_dao = PermissionDAO()
        super().__init__(self.dao)

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查用户名和手机号唯一性"""
        if "username" in data and await self.dao.exists(username=data["username"]):
            raise BusinessException("用户名已存在")
        if "phone" in data and data["phone"] and await self.dao.exists(phone=data["phone"]):
            raise BusinessException("手机号已被注册")
        return data

    async def before_update(self, obj: User, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查用户名和手机号唯一性"""
        if "username" in data and await self.dao.exists(username=data["username"], id__not=obj.id):
            raise BusinessException("用户名已存在")
        if "phone" in data and data["phone"] and await self.dao.exists(phone=data["phone"], id__not=obj.id):
            raise BusinessException("手机号已被注册")
        return data

    @log_create_with_context("user")
    async def create_user(self, request: UserCreateRequest, operation_context: OperationContext) -> UserCreateResponse:
        """创建用户，并可选择性地关联角色"""
        current_user = operation_context.user
        create_data = request.model_dump(exclude={"role_ids", "password"}, exclude_unset=True)
        create_data["password_hash"] = hash_password(request.password)
        create_data["creator_id"] = current_user.id
        create_data["is_active"] = True

        user = await self.create(operation_context=operation_context, **create_data)
        if not user:
            raise BusinessException("用户创建失败")

        if request.role_ids:
            roles = await self.role_dao.get_by_ids(request.role_ids)
            await user.roles.add(*roles)

        return UserCreateResponse(message="用户创建成功", data=UserResponse.model_validate(user))

    @log_update_with_context("user")
    async def update_user(
        self, user_id: UUID, request: UserUpdateRequest, operation_context: OperationContext
    ) -> UserUpdateResponse:
        """更新用户信息"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_user = await self.update(user_id, operation_context=operation_context, version=version, **update_data)
        if not updated_user:
            raise BusinessException("用户更新失败或版本冲突")

        return UserUpdateResponse(message="用户更新成功", data=UserResponse.model_validate(updated_user))

    @log_delete_with_context("user")
    async def delete_user(self, user_id: UUID, operation_context: OperationContext) -> UserDeleteResponse:
        """删除用户"""
        await self.delete(user_id, operation_context=operation_context)
        return UserDeleteResponse(message="用户删除成功", data={"deleted_id": str(user_id)})

    @log_query_with_context("user")
    async def get_user_detail(self, user_id: UUID, operation_context: OperationContext) -> UserDetailResponseWrapper:
        """获取用户详情，包含角色和所有权限"""
        # 确保不返回软删除的用户
        user = await self.dao.get_with_related(
            user_id, prefetch_related=["roles", "permissions"], include_deleted=False
        )
        if not user:
            raise BusinessException("用户未找到")

        all_permissions = await self._get_user_permissions(user)
        user_detail = UserDetailResponse.model_validate(user)
        user_detail.permissions = [PermissionResponse.model_validate(p) for p in all_permissions]
        return UserDetailResponseWrapper(message="获取用户详情成功", data=user_detail)

    @log_query_with_context("user")
    async def get_users(
        self, query: UserListRequest, operation_context: OperationContext
    ) -> tuple[list[UserResponse], int]:
        """获取用户列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        USER_MODEL_FIELDS = {"is_superuser", "is_active"}

        search_fields = ["username", "phone", "nickname"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, USER_MODEL_FIELDS)

        if query.role_code:
            role = await self.role_dao.get_one(role_code=query.role_code)
            if role:
                user_ids = await self.dao.get_user_ids_by_role(role.id)
                if not user_ids:
                    return [], 0
                model_filters["id__in"] = user_ids
            else:
                return [], 0

        order_by = (
            [f"-{query.sort_by}" if query.sort_order == "desc" else query.sort_by] if query.sort_by else ["-created_at"]
        )

        q_objects = model_filters.pop("q_objects", [])

        users, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )
        return [UserResponse.model_validate(user) for user in users], total

    async def authenticate(self, username: str, password: str) -> User | None:
        """用户认证"""
        user = await self.dao.get_one(username=username, is_active=True)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    async def update_user_status(
        self, user_id: UUID, is_active: bool, operation_context: OperationContext
    ) -> UserStatusUpdateResponse:
        """更新用户状态"""
        current_user = operation_context.user
        if current_user.id == user_id:
            raise BusinessException("不能修改自己的状态")

        user_to_update = await self.dao.get_by_id(user_id)
        if not user_to_update:
            raise BusinessException("用户未找到")

        await self.update(
            user_id,
            operation_context=operation_context,
            version=user_to_update.version,
            is_active=is_active,
        )

        # 重新获取更新后的用户信息
        updated_user = await self.get_by_id(user_id)
        if not updated_user:
            raise ValueError("用户不存在")

        return UserStatusUpdateResponse(
            message="用户状态更新成功", data=UserResponse.model_validate(updated_user)
        )

    @invalidate_user_permission_cache("user_id")
    async def assign_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserAssignRolesResponse:
        """为用户分配角色（全量设置）"""
        # 在服务层确保预加载关系，这是最可靠的位置
        user = await self.dao.get_with_related(user_id, prefetch_related=["roles"])
        if not user:
            raise BusinessException("用户未找到")

        # 现在 user.roles 已经被加载，可以安全地将 user 对象传递给 DAO 层
        await self.dao.set_user_roles(user, role_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignRolesResponse(message="用户角色分配成功", data=user_detail_response.data)

    @invalidate_user_permission_cache("user_id")
    async def add_user_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserAssignRolesResponse:
        """为用户增量添加角色"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.add_user_roles(user_id, role_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignRolesResponse(message="用户角色添加成功", data=user_detail_response.data)

    @invalidate_user_permission_cache("user_id")
    async def remove_user_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserAssignRolesResponse:
        """移除用户的指定角色"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.remove_user_roles(user_id, role_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignRolesResponse(message="用户角色移除成功", data=user_detail_response.data)

    async def get_user_roles(self, user_id: UUID, operation_context: OperationContext) -> BaseResponse[list[RoleResponse]]:
        """获取用户的角色列表"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        roles = await self.dao.get_user_roles(user_id)
        roles_data = [RoleResponse.model_validate(role) for role in roles]
        return BaseResponse[list[RoleResponse]](message="获取用户角色列表成功", data=roles_data)

    @invalidate_user_permission_cache("user_id")
    async def assign_permissions_to_user(
        self, user_id: UUID, request: UserAssignPermissionsRequest, operation_context: OperationContext
    ) -> UserAssignPermissionsResponse:
        """为用户分配直接权限（全量设置）"""
        await self.dao.set_user_permissions(user_id, request.permission_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignPermissionsResponse(message="用户权限分配成功", data=user_detail_response.data)

    async def add_user_permissions(
        self, user_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> UserAssignPermissionsResponse:
        """为用户增量添加权限"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.add_user_permissions(user_id, permission_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignPermissionsResponse(message="用户权限添加成功", data=user_detail_response.data)

    async def remove_user_permissions(
        self, user_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> UserAssignPermissionsResponse:
        """移除用户的指定权限"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.remove_user_permissions(user_id, permission_ids)
        user_detail_response = await self.get_user_detail(user_id, operation_context)
        return UserAssignPermissionsResponse(message="用户权限移除成功", data=user_detail_response.data)

    async def get_user_permissions(self, user_id: UUID, operation_context: OperationContext) -> BaseResponse[list[PermissionResponse]]:
        """获取用户的直接权限列表"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        permissions = await self.dao.get_user_permissions(user_id)
        permissions_data = [PermissionResponse.model_validate(perm) for perm in permissions]
        return BaseResponse[list[PermissionResponse]](message="获取用户权限列表成功", data=permissions_data)

    async def get_users_by_role_id(self, role_id: UUID, operation_context: OperationContext) -> UserListResponseWrapper:
        """根据角色ID获取用户列表"""
        users = await self.dao.find_by_fields(roles__id=role_id, include_deleted=False)
        users_data = [UserResponse.model_validate(user) for user in users]
        return UserListResponseWrapper(message="获取角色用户列表成功", data=users_data)

    async def _get_user_permissions(self, user: User) -> set[Permission]:
        """获取用户的所有权限，包括直接权限和通过角色继承的权限。"""
        if user.is_superuser:
            return set(await self.permission_dao.get_all())

        # 为确保数据最新，重新获取用户并预加载所有需要的嵌套关系
        fresh_user = await self.dao.get_with_related(user.id, prefetch_related=["permissions", "roles__permissions"])
        if not fresh_user:
            return set()

        # 收集直接权限
        direct_permissions = set(fresh_user.permissions)

        # 收集通过角色继承的权限
        role_permissions = set()
        for role in fresh_user.roles:
            # "roles__permissions" 预加载确保了 role.permissions 已被加载
            role_permissions.update(role.permissions)

        return direct_permissions.union(role_permissions)

    # ===== 批量操作方法 =====

    @log_create_with_context("user")
    async def batch_create_users(
        self, users_data: list[UserCreateRequest], operation_context: OperationContext
    ) -> UserListResponseWrapper:
        """批量创建用户"""
        # 转换为字典列表并进行验证
        data_list = []
        for user_data in users_data:
            data = user_data.model_dump()
            # 应用前置验证
            validated_data = await self.before_create(data)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_users = await self.bulk_create(data_list)
        users_response_data = [UserResponse.model_validate(user) for user in created_users]
        return UserListResponseWrapper(message="批量创建用户成功", data=users_response_data)

    @log_update_with_context("user")
    async def batch_update_users(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> UserListResponseWrapper:
        """批量更新用户"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有用户是否存在
        existing_users = await self.get_by_ids(update_ids)
        existing_ids = {str(user.id) for user in existing_users}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下用户不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据，处理密码哈希
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            if "password" in update_data and update_data["password"]:
                update_data["password"] = hash_password(update_data["password"])
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 清除相关用户的权限缓存
        for user_id in update_ids:
            invalidate_user_permission_cache(user_id)

        # 返回更新后的数据
        updated_users = await self.get_by_ids(update_ids)
        users_response_data = [UserResponse.model_validate(user) for user in updated_users]
        return UserListResponseWrapper(message="批量更新用户成功", data=users_response_data)

    @log_delete_with_context("user")
    async def batch_delete_users(self, user_ids: list[UUID], operation_context: OperationContext) -> UserDeleteResponse:
        """批量删除用户"""
        # 检查用户是否存在
        existing_users = await self.get_by_ids(user_ids)
        if len(existing_users) != len(user_ids):
            missing_ids = {str(id) for id in user_ids} - {str(u.id) for u in existing_users}
            raise BusinessException(f"以下用户不存在: {', '.join(missing_ids)}")

        # 检查是否尝试删除超级用户
        for user in existing_users:
            if user.is_superuser:
                raise BusinessException(f"不能删除超级用户: {user.username}")

        # 清除相关用户的权限缓存
        for user_id in user_ids:
            invalidate_user_permission_cache(user_id)

        # 使用BaseService的批量删除方法
        deleted_count = await self.delete_by_ids(user_ids, operation_context)
        return UserDeleteResponse(
            message="批量删除用户成功",
            data={"deleted_count": deleted_count, "deleted_ids": [str(id) for id in user_ids]},
        )
