"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor_command.py
@DateTime: 2025/07/23
@Docs: 厂商命令服务层 - 基础CRUD功能
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.query_template import QueryTemplateDAO
from app.dao.vendor import VendorDAO
from app.dao.vendor_command import VendorCommandDAO
from app.models.vendor_command import VendorCommand
from app.schemas.vendor_command import (
    VendorCommandBatchCreateRequest,
    VendorCommandCreateRequest,
    VendorCommandListRequest,
    VendorCommandListResponse,
    VendorCommandResponse,
    VendorCommandUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)


class VendorCommandService(BaseService[VendorCommand]):
    """厂商命令服务"""

    def __init__(self):
        super().__init__(VendorCommandDAO())
        self.vendor_dao = VendorDAO()
        self.query_template_dao = QueryTemplateDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前验证"""
        # 验证厂商存在
        vendor_id = data.get("vendor_id")
        if vendor_id:
            vendor = await self.vendor_dao.get_by_id(vendor_id)
            if not vendor:
                raise BusinessException("指定的厂商不存在")

        # 验证查询模板存在
        template_id = data.get("template_id")
        if template_id:
            template = await self.query_template_dao.get_by_id(template_id)
            if not template:
                raise BusinessException("指定的查询模板不存在")

        # 验证同一厂商和模板下的命令唯一性
        existing = await self.get_one(vendor_id=data.get("vendor_id"), template_id=data.get("template_id"))
        if existing:
            raise BusinessException("该厂商下已存在相同模板的命令配置")

        return data

    async def before_update(self, obj: VendorCommand, data: dict[str, Any]) -> dict[str, Any]:
        """更新前验证"""
        # 验证厂商存在
        if "vendor_id" in data:
            vendor = await self.vendor_dao.get_by_id(data["vendor_id"])
            if not vendor:
                raise BusinessException("指定的厂商不存在")

        # 验证查询模板存在
        if "template_id" in data:
            template = await self.query_template_dao.get_by_id(data["template_id"])
            if not template:
                raise BusinessException("指定的查询模板不存在")

        return data

    @log_create_with_context("vendor_command")
    async def create_vendor_command(
        self, data: VendorCommandCreateRequest, operation_context: OperationContext
    ) -> VendorCommandResponse:
        """创建厂商命令"""
        command_data = data.model_dump()
        command = await self.create(operation_context, **command_data)
        return VendorCommandResponse.model_validate(command)

    @log_update_with_context("vendor_command")
    async def update_vendor_command(
        self, command_id: UUID, data: VendorCommandUpdateRequest, operation_context: OperationContext
    ) -> VendorCommandResponse:
        """更新厂商命令"""
        command = await self.get_by_id(command_id)
        if not command:
            raise BusinessException("厂商命令不存在")

        # 如果更新厂商或模板，检查唯一性
        update_data = data.model_dump(exclude_unset=True)
        if "vendor_id" in update_data or "template_id" in update_data:
            new_vendor_id = update_data.get("vendor_id", getattr(command, "vendor_id", None))
            new_template_id = update_data.get("template_id", getattr(command, "template_id", None))

            existing = await self.get_one(vendor_id=new_vendor_id, template_id=new_template_id)
            if existing and existing.id != command_id:
                raise BusinessException("该厂商下已存在相同模板的命令配置")

        updated_command = await self.update(command_id, operation_context, **update_data)
        return VendorCommandResponse.model_validate(updated_command)

    @log_delete_with_context("vendor_command")
    async def delete_vendor_command(self, command_id: UUID, operation_context: OperationContext) -> bool:
        """删除厂商命令"""
        command = await self.get_by_id(command_id)
        if not command:
            raise BusinessException("厂商命令不存在")

        return await self.soft_delete(command_id)

    @log_query_with_context("vendor_command")
    async def get_vendor_command_list(
        self, params: VendorCommandListRequest, operation_context: OperationContext
    ) -> VendorCommandListResponse:
        """获取厂商命令列表"""
        # 构建过滤条件
        filters = {}
        if hasattr(params, "vendor_id") and params.vendor_id:
            filters["vendor_id"] = params.vendor_id
        if hasattr(params, "template_id") and params.template_id:
            filters["template_id"] = params.template_id
        if hasattr(params, "is_active") and params.is_active is not None:
            filters["is_active"] = params.is_active

        # 查询数据
        commands = await self.get_all(**filters)
        total = await self.count(**filters)

        return VendorCommandListResponse(
            data=[VendorCommandResponse.model_validate(cmd) for cmd in commands], total=total
        )

    @log_query_with_context("vendor_command")
    async def get_vendor_command_by_id(
        self, command_id: UUID, operation_context: OperationContext
    ) -> VendorCommandResponse:
        """根据ID获取厂商命令详情"""
        command = await self.get_by_id(command_id)
        if not command:
            raise BusinessException("厂商命令不存在")

        return VendorCommandResponse.model_validate(command)

    @log_create_with_context("vendor_command")
    async def batch_create_commands(
        self, data: VendorCommandBatchCreateRequest, operation_context: OperationContext
    ) -> list[VendorCommandResponse]:
        """批量创建厂商命令"""
        if not data.commands:
            raise BusinessException("请提供要创建的命令列表")

        # 转换为字典列表并添加template_id
        data_list = []
        for command_data in data.commands:
            command_dict = command_data if isinstance(command_data, dict) else command_data.model_dump()
            command_dict["template_id"] = data.template_id

            # 应用前置验证
            validated_data = await self.before_create(command_dict)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_commands = await self.bulk_create(data_list)
        return [VendorCommandResponse.model_validate(command) for command in created_commands]

    @log_update_with_context("vendor_command")
    async def batch_update_status(
        self, command_ids: list[UUID], is_active: bool, operation_context: OperationContext
    ) -> int:
        """批量更新命令状态"""
        if not command_ids:
            raise BusinessException("请提供要更新的命令ID")

        # 检查所有命令是否存在
        existing_commands = await self.get_by_ids(command_ids)
        existing_ids = {str(command.id) for command in existing_commands}
        missing_ids = [str(id) for id in command_ids if str(id) not in existing_ids]

        if missing_ids:
            raise BusinessException(f"以下厂商命令不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据
        bulk_update_data = []
        for command_id in command_ids:
            bulk_update_data.append({"id": command_id, "is_active": is_active})

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)
        return len(command_ids)

    @log_delete_with_context("vendor_command")
    async def batch_delete_commands(self, command_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除厂商命令"""
        if not command_ids:
            raise BusinessException("请提供要删除的命令ID")

        # 检查命令是否存在
        existing_commands = await self.get_by_ids(command_ids)
        if len(existing_commands) != len(command_ids):
            missing_ids = {str(id) for id in command_ids} - {str(cmd.id) for cmd in existing_commands}
            raise BusinessException(f"以下厂商命令不存在: {', '.join(missing_ids)}")

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(command_ids, operation_context)

    @log_query_with_context("vendor_command")
    async def get_command_statistics(self, operation_context: OperationContext) -> dict[str, Any]:
        """获取厂商命令统计信息"""
        try:
            # 总命令数
            total_commands = await self.count()

            # 活跃命令数
            active_commands = await self.count(is_active=True)

            # 停用命令数
            inactive_commands = total_commands - active_commands

            return {
                "total_commands": total_commands,
                "active_commands": active_commands,
                "inactive_commands": inactive_commands,
            }

        except Exception as e:
            logger.error(f"获取厂商命令统计信息失败: {e}")
            raise BusinessException(f"获取统计信息失败: {e}") from e
