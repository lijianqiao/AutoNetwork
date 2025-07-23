"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_config.py
@DateTime: 2025/07/23
@Docs: 设备配置快照服务层
"""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from app.dao.device_config import DeviceConfigDAO
from app.models.device_config import DeviceConfig
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import log_create_with_context, log_delete_with_context, log_update_with_context


class DeviceConfigService(BaseService[DeviceConfig]):
    """设备配置快照服务"""

    def __init__(self):
        super().__init__(DeviceConfigDAO())
        self.dao: DeviceConfigDAO = self.dao

    def _generate_config_hash(self, config_content: str) -> str:
        """生成配置内容的哈希值"""
        return hashlib.sha256(config_content.encode("utf-8")).hexdigest()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前的数据处理"""
        # 自动生成配置哈希值
        if "config_content" in data and "config_hash" not in data:
            data["config_hash"] = self._generate_config_hash(data["config_content"])

        return data

    @log_create_with_context("device_config")
    async def create_config_snapshot(
        self,
        device_id: UUID,
        config_type: str,
        config_content: str,
        backup_reason: str | None = None,
        operation_context: OperationContext | None = None,
    ) -> DeviceConfig:
        """创建设备配置快照"""
        # 检查是否已存在相同的配置快照
        config_hash = self._generate_config_hash(config_content)
        existing_config = await self.dao.get_by_hash(config_hash)

        if existing_config:
            logger.warning(f"配置快照已存在，哈希值: {config_hash}")
            return existing_config

        # 创建新的配置快照
        create_data = {
            "device_id": device_id,
            "config_type": config_type,
            "config_content": config_content,
            "config_hash": config_hash,
            "backup_reason": backup_reason,
            "backup_by_id": operation_context.user.id if operation_context else None,
        }

        config = await self.dao.create(**create_data)
        if not config:
            raise ValueError("创建配置快照失败")
        return config

    async def get_device_configs(
        self, device_id: UUID, config_type: str | None = None, limit: int = 50
    ) -> list[DeviceConfig]:
        """获取设备的配置快照列表"""
        if config_type:
            return await self.dao.get_by_device_and_type(device_id, config_type, limit)
        return await self.dao.get_by_device(device_id, limit)

    async def get_latest_config(self, device_id: UUID, config_type: str = "running") -> DeviceConfig | None:
        """获取设备的最新配置快照"""
        return await self.dao.get_latest_config(device_id, config_type)

    async def compare_configs(self, config1_id: UUID, config2_id: UUID) -> dict[str, Any]:
        """对比两个配置快照"""
        config1 = await self.dao.get_by_id(config1_id)
        config2 = await self.dao.get_by_id(config2_id)

        if not config1 or not config2:
            raise ValueError("配置快照不存在")

        # 简单的配置对比
        lines1 = config1.config_content.splitlines()
        lines2 = config2.config_content.splitlines()

        differences = []
        max_lines = max(len(lines1), len(lines2))

        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""

            if line1 != line2:
                differences.append(
                    {
                        "line_number": i + 1,
                        "config1_line": line1,
                        "config2_line": line2,
                    }
                )

        return {
            "config1": {
                "id": config1.id,
                "created_at": config1.created_at,
                "config_type": config1.config_type,
                "config_hash": config1.config_hash,
            },
            "config2": {
                "id": config2.id,
                "created_at": config2.created_at,
                "config_type": config2.config_type,
                "config_hash": config2.config_hash,
            },
            "differences": differences,
            "total_differences": len(differences),
            "is_identical": len(differences) == 0,
        }

    async def get_config_changes(self, device_id: UUID, days: int = 30) -> list[DeviceConfig]:
        """获取设备配置变更历史"""
        return await self.dao.get_config_changes(device_id, days)

    async def search_configs(
        self,
        device_id: UUID | None = None,
        config_type: str | None = None,
        backup_by: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[DeviceConfig]:
        """搜索配置快照"""
        return await self.dao.search_configs(device_id, config_type, backup_by, start_date, end_date)

    async def get_user_configs(self, user_id: UUID, limit: int = 100) -> list[DeviceConfig]:
        """获取用户备份的配置快照"""
        return await self.dao.get_configs_by_user(user_id, limit)

    async def get_recent_configs(self, days: int = 7, limit: int = 100) -> list[DeviceConfig]:
        """获取最近的配置快照"""
        return await self.dao.get_recent_configs(days, limit)

    @log_delete_with_context("device_config")
    async def cleanup_old_configs(
        self, device_id: UUID, operation_context: OperationContext, keep_count: int = 50
    ) -> dict[str, Any]:
        """清理设备的旧配置快照"""
        deleted_count = await self.dao.cleanup_old_configs(device_id, keep_count)

        return {
            "device_id": device_id,
            "deleted_count": deleted_count,
            "keep_count": keep_count,
            "message": f"已清理 {deleted_count} 条旧配置快照",
        }

    @log_delete_with_context("device_config")
    async def batch_cleanup_configs(
        self, device_ids: list[UUID], operation_context: OperationContext, keep_count: int = 50
    ) -> dict[str, Any]:
        """批量清理多个设备的旧配置快照"""
        total_deleted = 0
        results = []

        for device_id in device_ids:
            deleted_count = await self.dao.cleanup_old_configs(device_id, keep_count)
            total_deleted += deleted_count
            results.append(
                {
                    "device_id": device_id,
                    "deleted_count": deleted_count,
                }
            )

        return {
            "total_devices": len(device_ids),
            "total_deleted": total_deleted,
            "keep_count": keep_count,
            "results": results,
        }

    async def get_config_statistics(self, device_id: UUID | None = None) -> dict[str, Any]:
        """获取配置快照统计信息"""
        base_filters = {"is_deleted": False}

        if device_id:
            total_configs = await self.dao.count(device_id=device_id, **base_filters)
            running_count = await self.dao.count(device_id=device_id, config_type="running", **base_filters)
            startup_count = await self.dao.count(device_id=device_id, config_type="startup", **base_filters)
        else:
            total_configs = await self.dao.count(**base_filters)
            running_count = await self.dao.count(config_type="running", **base_filters)
            startup_count = await self.dao.count(config_type="startup", **base_filters)

        # 最近7天的配置数量
        recent_configs = await self.dao.get_recent_configs(days=7)
        recent_count = len(recent_configs)

        return {
            "total_configs": total_configs,
            "by_type": {
                "running": running_count,
                "startup": startup_count,
            },
            "recent_7_days": recent_count,
            "device_id": device_id,
        }

    async def get_config_with_details(self, config_id: UUID) -> DeviceConfig | None:
        """获取配置快照的详细信息"""
        return await self.dao.get_config_with_details(config_id)

    async def validate_config_content(self, config_content: str, config_type: str) -> dict[str, Any]:
        """验证配置内容的有效性"""
        # 基本验证
        if not config_content.strip():
            return {
                "is_valid": False,
                "errors": ["配置内容不能为空"],
            }

        # 简单的配置格式验证
        lines = config_content.splitlines()
        errors = []
        warnings = []

        # 检查常见的配置错误
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 检查是否有明显的配置错误
            if line.startswith("!") and "error" in line.lower():
                errors.append(f"第 {i} 行: 检测到错误配置 - {line}")

            # 检查是否有密码明文
            if any(keyword in line.lower() for keyword in ["password", "secret"]) and "****" not in line:
                warnings.append(f"第 {i} 行: 可能包含明文密码，建议检查安全性")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "line_count": len(lines),
            "size_bytes": len(config_content.encode("utf-8")),
        }

    @log_update_with_context("device_config")
    async def update_config_reason(
        self, config_id: UUID, new_reason: str, operation_context: OperationContext
    ) -> DeviceConfig:
        """更新配置快照的备份原因"""
        config = await self.dao.get_by_id(config_id)
        if not config:
            raise ValueError("配置快照不存在")

        await self.dao.update_by_id(config_id, backup_reason=new_reason)
        updated_config = await self.dao.get_by_id(config_id)
        if not updated_config:
            raise ValueError("更新配置快照失败")
        return updated_config

    # ===== 批量操作方法 =====

    @log_create_with_context("device_config")
    async def batch_create_configs(
        self, configs_data: list[dict], operation_context: OperationContext
    ) -> list[DeviceConfig]:
        """批量创建设备配置快照"""
        # 转换为字典列表并进行验证
        data_list = []
        for config_data in configs_data:
            # 应用前置验证
            validated_data = await self.before_create(config_data)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_configs = await self.bulk_create(data_list)
        return created_configs

    @log_update_with_context("device_config")
    async def batch_update_configs(
        self, updates_data: list[dict], operation_context: OperationContext
    ) -> list[DeviceConfig]:
        """批量更新设备配置快照"""
        # 提取所有要更新的ID
        update_ids = [update_item["id"] for update_item in updates_data]

        # 检查所有配置是否存在
        existing_configs = await self.get_by_ids(update_ids)
        existing_ids = {str(config.id) for config in existing_configs}
        missing_ids = [str(id) for id in update_ids if str(id) not in existing_ids]

        if missing_ids:
            from app.core.exceptions import BusinessException

            raise BusinessException(f"以下配置快照不存在: {', '.join(missing_ids)}")

        # 准备批量更新数据，处理配置哈希
        bulk_update_data = []
        for update_item in updates_data:
            update_data = update_item.copy()
            if "config_content" in update_data:
                update_data["config_hash"] = self._generate_config_hash(update_data["config_content"])
            bulk_update_data.append(update_data)

        # 使用BaseService的批量更新方法
        await self.bulk_update(bulk_update_data)

        # 返回更新后的数据
        updated_configs = await self.get_by_ids(update_ids)
        return updated_configs

    @log_delete_with_context("device_config")
    async def batch_delete_configs(self, config_ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除配置快照"""
        # 检查配置是否存在
        existing_configs = await self.get_by_ids(config_ids)
        if len(existing_configs) != len(config_ids):
            missing_ids = {str(id) for id in config_ids} - {str(c.id) for c in existing_configs}
            from app.core.exceptions import BusinessException

            raise BusinessException(f"以下配置快照不存在: {', '.join(missing_ids)}")

        # 使用BaseService的批量删除方法
        return await self.delete_by_ids(config_ids, operation_context)

    async def get_configs_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        device_id: UUID | None = None,
        config_type: str | None = None,
    ) -> tuple[list[DeviceConfig], int]:
        """分页获取配置快照"""
        return await self.dao.get_configs_paginated_optimized(page, page_size, device_id, config_type)
