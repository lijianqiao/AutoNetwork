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

from app.core.network.connection_manager import get_connection_manager
from app.dao.device_config import DeviceConfigDAO
from app.models.device_config import DeviceConfig
from app.services.base import BaseService
from app.utils.config_differ import ConfigDiffResult, NetworkConfigDiffer
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import log_create_with_context, log_delete_with_context, log_update_with_context


class DeviceConfigService(BaseService[DeviceConfig]):
    """设备配置快照服务"""

    def __init__(self):
        super().__init__(DeviceConfigDAO())
        self.dao: DeviceConfigDAO = self.dao
        self.config_differ = NetworkConfigDiffer()

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

    async def compare_configs(
        self,
        config1_id: UUID,
        config2_id: UUID,
        ignore_whitespace: bool = True,
        ignore_comments: bool = False,
        context_lines: int = 3,
    ) -> ConfigDiffResult:
        """智能对比两个配置快照

        Args:
            config1_id: 第一个配置快照ID
            config2_id: 第二个配置快照ID
            ignore_whitespace: 是否忽略空白字符差异
            ignore_comments: 是否忽略注释行差异
            context_lines: 上下文行数

        Returns:
            配置差异结果
        """
        config1 = await self.dao.get_by_id(config1_id)
        config2 = await self.dao.get_by_id(config2_id)

        if not config1 or not config2:
            raise ValueError("配置快照不存在")

        # 构建配置信息
        config1_info = {
            "id": str(config1.id),
            "created_at": config1.created_at.isoformat() if config1.created_at else None,
            "config_type": config1.config_type,
            "config_hash": config1.config_hash,
            "backup_reason": config1.backup_reason,
            "device_id": str(config1.device.id) if config1.device.id else None,
        }

        config2_info = {
            "id": str(config2.id),
            "created_at": config2.created_at.isoformat() if config2.created_at else None,
            "config_type": config2.config_type,
            "config_hash": config2.config_hash,
            "backup_reason": config2.backup_reason,
            "device_id": str(config2.device.id) if config2.device.id else None,
        }

        # 使用智能差异分析器
        diff_result = self.config_differ.analyze_config_differences(
            config1_content=config1.config_content,
            config2_content=config2.config_content,
            config1_info=config1_info,
            config2_info=config2_info,
            ignore_whitespace=ignore_whitespace,
            ignore_comments=ignore_comments,
            context_lines=context_lines,
        )

        logger.info(
            f"配置对比完成: {config1_id} vs {config2_id}, "
            f"差异行数: {diff_result.summary['total_differences']}, "
            f"相似度: {diff_result.summary['similarity_ratio']:.2%}"
        )

        return diff_result

    async def compare_with_latest(
        self, config_id: UUID, ignore_whitespace: bool = True, ignore_comments: bool = False
    ) -> ConfigDiffResult:
        """将指定配置与最新配置进行对比

        Args:
            config_id: 要对比的配置快照ID
            ignore_whitespace: 是否忽略空白字符差异
            ignore_comments: 是否忽略注释行差异

        Returns:
            配置差异结果
        """
        config = await self.dao.get_by_id(config_id)
        if not config:
            raise ValueError("配置快照不存在")

        # 获取同类型的最新配置
        latest_config = await self.dao.get_latest_config(config.device.id, config.config_type)
        if not latest_config:
            raise ValueError("未找到最新配置快照")

        if latest_config.id == config.id:
            raise ValueError("指定的配置已经是最新配置")

        return await self.compare_configs(
            config1_id=config_id,
            config2_id=latest_config.id,
            ignore_whitespace=ignore_whitespace,
            ignore_comments=ignore_comments,
        )

    async def export_diff_to_html(
        self, config1_id: UUID, config2_id: UUID, ignore_whitespace: bool = True, ignore_comments: bool = False
    ) -> str:
        """将配置差异导出为HTML格式

        Args:
            config1_id: 第一个配置快照ID
            config2_id: 第二个配置快照ID
            ignore_whitespace: 是否忽略空白字符差异
            ignore_comments: 是否忽略注释行差异

        Returns:
            HTML格式的差异报告
        """
        diff_result = await self.compare_configs(
            config1_id=config1_id,
            config2_id=config2_id,
            ignore_whitespace=ignore_whitespace,
            ignore_comments=ignore_comments,
        )

        return self.config_differ.export_diff_to_html(diff_result)

    async def get_config_diff_summary(
        self, device_id: UUID, days: int = 30, config_type: str = "running"
    ) -> dict[str, Any]:
        """获取设备配置变更摘要

        Args:
            device_id: 设备ID
            days: 查看最近几天的变更
            config_type: 配置类型

        Returns:
            配置变更摘要
        """
        # 获取指定时间范围内的配置快照
        configs = await self.dao.get_config_changes(device_id, days)
        configs = [c for c in configs if c.config_type == config_type]

        if len(configs) < 2:
            return {
                "device_id": str(device_id),
                "config_type": config_type,
                "days": days,
                "total_snapshots": len(configs),
                "has_changes": False,
                "message": "时间范围内配置快照不足，无法进行变更分析",
            }

        # 对比最新和最旧的配置
        latest_config = configs[0]  # 按时间倒序排列，第一个是最新的
        oldest_config = configs[-1]  # 最后一个是最旧的

        diff_result = await self.compare_configs(
            config1_id=oldest_config.id, config2_id=latest_config.id, ignore_whitespace=True, ignore_comments=True
        )

        # 统计中间变更次数
        change_points = []
        for i in range(1, len(configs)):
            prev_config = configs[i]
            curr_config = configs[i - 1]

            # 比较哈希值，如果不同则表示发生了变更
            if prev_config.config_hash != curr_config.config_hash:
                change_points.append(
                    {
                        "from_config_id": str(prev_config.id),
                        "to_config_id": str(curr_config.id),
                        "change_time": curr_config.created_at.isoformat() if curr_config.created_at else None,
                        "backup_reason": curr_config.backup_reason,
                    }
                )

        return {
            "device_id": str(device_id),
            "config_type": config_type,
            "days": days,
            "total_snapshots": len(configs),
            "total_changes": len(change_points),
            "has_changes": len(change_points) > 0,
            "latest_config": {
                "id": str(latest_config.id),
                "created_at": latest_config.created_at.isoformat() if latest_config.created_at else None,
                "backup_reason": latest_config.backup_reason,
            },
            "oldest_config": {
                "id": str(oldest_config.id),
                "created_at": oldest_config.created_at.isoformat() if oldest_config.created_at else None,
                "backup_reason": oldest_config.backup_reason,
            },
            "overall_diff_summary": {
                "total_differences": diff_result.summary["total_differences"],
                "lines_added": diff_result.summary["lines_added"],
                "lines_removed": diff_result.summary["lines_removed"],
                "similarity_ratio": diff_result.summary["similarity_ratio"],
                "sections_affected": diff_result.summary["sections_affected"],
                "section_statistics": diff_result.summary["section_statistics"],
            },
            "change_points": change_points,
            "sections_changed": [section.value for section in diff_result.sections_changed],
        }

    async def batch_compare_configs(
        self, comparison_pairs: list[tuple[UUID, UUID]], ignore_whitespace: bool = True, ignore_comments: bool = False
    ) -> list[dict[str, Any]]:
        """批量对比配置快照

        Args:
            comparison_pairs: 配置对比对列表 [(config1_id, config2_id), ...]
            ignore_whitespace: 是否忽略空白字符差异
            ignore_comments: 是否忽略注释行差异

        Returns:
            批量对比结果列表
        """
        results = []

        for i, (config1_id, config2_id) in enumerate(comparison_pairs):
            try:
                diff_result = await self.compare_configs(
                    config1_id=config1_id,
                    config2_id=config2_id,
                    ignore_whitespace=ignore_whitespace,
                    ignore_comments=ignore_comments,
                )

                results.append(
                    {
                        "index": i,
                        "config1_id": str(config1_id),
                        "config2_id": str(config2_id),
                        "success": True,
                        "summary": diff_result.summary,
                        "sections_changed": [section.value for section in diff_result.sections_changed],
                    }
                )

            except Exception as e:
                logger.error(f"批量对比配置失败 {config1_id} vs {config2_id}: {e}")
                results.append(
                    {
                        "index": i,
                        "config1_id": str(config1_id),
                        "config2_id": str(config2_id),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

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

    # ===== 配置回滚功能 =====

    @log_update_with_context("device_config")
    async def rollback_to_config(
        self, config_id: UUID, target_device_id: UUID | None = None, operation_context: OperationContext | None = None
    ) -> dict[str, Any]:
        """回滚到指定的配置快照

        Args:
            config_id: 要回滚到的配置快照ID
            target_device_id: 目标设备ID（如果不同于配置快照的设备）
            operation_context: 操作上下文

        Returns:
            回滚操作结果
        """
        # 获取配置快照
        config = await self.dao.get_config_with_details(config_id)
        if not config:
            raise ValueError("配置快照不存在")

        # 确定目标设备
        device_id = target_device_id or config.device.id

        logger.info(f"开始回滚设备 {device_id} 到配置快照 {config_id}")

        try:
            # 1. 在实际设备上应用配置（这里需要集成网络设备连接服务）
            rollback_result = await self._apply_config_to_device(device_id, config.config_content)

            if rollback_result["success"]:
                # 2. 创建新的配置快照记录回滚操作
                new_config = await self.create_config_snapshot(
                    device_id=device_id,
                    config_type=config.config_type,
                    config_content=config.config_content,
                    backup_reason=f"回滚到配置 {config_id} ({config.backup_reason})",
                    operation_context=operation_context,
                )

                logger.info(f"配置回滚成功，新配置快照: {new_config.id}")

                return {
                    "success": True,
                    "message": "配置回滚成功",
                    "original_config_id": str(config_id),
                    "new_config_id": str(new_config.id),
                    "device_id": str(device_id),
                    "rollback_time": datetime.now().isoformat(),
                    "applied_lines": rollback_result.get("applied_lines", 0),
                    "deployment_details": rollback_result.get("details", ""),
                }
            else:
                logger.error(f"配置回滚失败: {rollback_result.get('error', '未知错误')}")
                return {
                    "success": False,
                    "message": "配置回滚失败",
                    "error": rollback_result.get("error", "未知错误"),
                    "original_config_id": str(config_id),
                    "device_id": str(device_id),
                }

        except Exception as e:
            logger.error(f"配置回滚过程中发生异常: {e}")
            return {
                "success": False,
                "message": "配置回滚失败",
                "error": str(e),
                "original_config_id": str(config_id),
                "device_id": str(device_id),
            }

    async def _apply_config_to_device(self, device_id: UUID, config_content: str) -> dict[str, Any]:
        """将配置应用到实际设备

        Args:
            device_id: 设备ID
            config_content: 配置内容

        Returns:
            应用结果
        """
        from app.dao.device import DeviceDAO

        try:
            # 获取设备信息
            device_dao = DeviceDAO()
            device = await device_dao.get_by_id(device_id)
            if not device:
                return {"success": False, "error": "设备不存在"}

            if not device.is_active:
                return {"success": False, "error": "设备已禁用"}

            # 创建网络连接
            connection_manager = get_connection_manager()

            # 连接到设备
            connection = await connection_manager.get_connection(device)
            if not connection:
                return {"success": False, "error": "无法连接到设备"}

            # 应用配置
            config_lines = [
                line.strip()
                for line in config_content.splitlines()
                if line.strip() and not line.strip().startswith("!")
            ]

            # 进入配置模式
            await connection.execute_command("configure terminal")

            applied_lines = 0
            failed_commands = []

            # 逐行应用配置
            for line in config_lines:
                try:
                    result = await connection.execute_command(line)
                    if "error" not in result.result.lower() and "invalid" not in result.result.lower():
                        applied_lines += 1
                    else:
                        failed_commands.append(f"{line}: {result.result}")
                except Exception as cmd_error:
                    failed_commands.append(f"{line}: {str(cmd_error)}")

            # 退出配置模式并保存
            await connection.execute_command("end")
            save_result = await connection.execute_command("write memory")

            # 关闭连接
            await connection.disconnect()

            success = len(failed_commands) == 0
            details = f"应用了 {applied_lines}/{len(config_lines)} 行配置"
            if failed_commands:
                details += f", 失败命令: {'; '.join(failed_commands[:5])}"  # 只显示前5个失败命令

            return {
                "success": success,
                "applied_lines": applied_lines,
                "total_lines": len(config_lines),
                "failed_commands": failed_commands,
                "details": details,
                "save_result": save_result.result if save_result else "未知",
            }

        except Exception as e:
            logger.error(f"应用配置到设备失败: {e}")
            return {"success": False, "error": f"设备连接或配置应用失败: {str(e)}"}

    async def batch_rollback_configs(
        self, rollback_requests: list[dict[str, Any]], operation_context: OperationContext | None = None
    ) -> list[dict[str, Any]]:
        """批量配置回滚

        Args:
            rollback_requests: 回滚请求列表 [{"config_id": UUID, "device_id": UUID?}, ...]
            operation_context: 操作上下文

        Returns:
            批量回滚结果列表
        """
        results = []

        for i, request in enumerate(rollback_requests):
            try:
                result = await self.rollback_to_config(
                    config_id=request["config_id"],
                    target_device_id=request.get("device_id"),
                    operation_context=operation_context,
                )
                result["index"] = i
                results.append(result)

            except Exception as e:
                logger.error(f"批量回滚第 {i} 项失败: {e}")
                results.append(
                    {
                        "index": i,
                        "success": False,
                        "message": "批量回滚失败",
                        "error": str(e),
                        "config_id": str(request.get("config_id", "")),
                        "device_id": str(request.get("device_id", "")),
                    }
                )

        return results

    async def preview_rollback(self, config_id: UUID, target_device_id: UUID | None = None) -> dict[str, Any]:
        """预览配置回滚的影响

        Args:
            config_id: 要回滚到的配置快照ID
            target_device_id: 目标设备ID

        Returns:
            回滚预览信息
        """
        # 获取回滚目标配置
        target_config = await self.dao.get_config_with_details(config_id)
        if not target_config:
            raise ValueError("目标配置快照不存在")

        # 确定设备ID
        device_id = target_device_id or target_config.device.id

        # 获取当前最新配置
        current_config = await self.dao.get_latest_config(device_id, target_config.config_type)
        if not current_config:
            return {"can_rollback": False, "error": "设备没有当前配置快照，无法进行对比"}

        # 如果要回滚到的就是当前配置，提示用户
        if current_config.id == target_config.id:
            return {"can_rollback": False, "error": "目标配置已经是当前最新配置，无需回滚"}

        # 对比配置差异
        try:
            diff_result = await self.compare_configs(
                config1_id=current_config.id, config2_id=target_config.id, ignore_whitespace=True, ignore_comments=True
            )

            # 分析配置差异的影响
            impact_analysis = self._analyze_rollback_impact(diff_result)

            return {
                "can_rollback": True,
                "current_config": {
                    "id": str(current_config.id),
                    "created_at": current_config.created_at.isoformat() if current_config.created_at else None,
                    "backup_reason": current_config.backup_reason,
                },
                "target_config": {
                    "id": str(target_config.id),
                    "created_at": target_config.created_at.isoformat() if target_config.created_at else None,
                    "backup_reason": target_config.backup_reason,
                },
                "device_id": str(device_id),
                "diff_summary": diff_result.summary,
                "sections_affected": [section.value for section in diff_result.sections_changed],
                "impact_analysis": impact_analysis,
                "total_changes": diff_result.summary.get("total_differences", 0),
                "estimated_duration": self._estimate_rollback_duration(diff_result.summary.get("total_differences", 0)),
            }

        except Exception as e:
            logger.error(f"回滚预览失败: {e}")
            return {"can_rollback": False, "error": f"无法生成回滚预览: {str(e)}"}

    def _analyze_rollback_impact(self, diff_result) -> dict[str, Any]:
        """分析回滚操作的影响

        Args:
            diff_result: 配置差异结果

        Returns:
            影响分析结果
        """
        impact = {"risk_level": "low", "warnings": [], "affected_features": [], "recommended_actions": []}

        # 分析受影响的配置段落
        section_stats = diff_result.summary.get("section_statistics", {})

        for section, stats in section_stats.items():
            if stats["total"] > 0:
                impact["affected_features"].append(section)

                # 根据不同的配置段落判断风险级别
                if section in ["interface", "routing"]:
                    if stats["total"] > 10:
                        impact["risk_level"] = "high"
                        impact["warnings"].append(f"{section}配置变更较多({stats['total']}行)，可能影响网络连通性")
                    elif stats["total"] > 5:
                        impact["risk_level"] = "medium"

                elif section == "security":
                    impact["risk_level"] = "high"
                    impact["warnings"].append("安全配置将发生变更，请确认访问权限")

        # 基于总变更量调整风险级别
        total_changes = diff_result.summary.get("total_differences", 0)
        if total_changes > 50:
            impact["risk_level"] = "high"
        elif total_changes > 20 and impact["risk_level"] == "low":
            impact["risk_level"] = "medium"

        # 生成建议操作
        if impact["risk_level"] == "high":
            impact["recommended_actions"].extend(
                ["建议在维护窗口内执行回滚操作", "确保有应急恢复方案", "建议先在测试环境验证配置"]
            )
        elif impact["risk_level"] == "medium":
            impact["recommended_actions"].extend(["建议提前通知相关人员", "确认当前网络状态正常"])
        else:
            impact["recommended_actions"].append("配置变更较小，可以安全执行回滚")

        return impact

    def _estimate_rollback_duration(self, total_changes: int) -> dict[str, Any]:
        """估算回滚操作耗时

        Args:
            total_changes: 总变更行数

        Returns:
            耗时估算
        """
        # 基础时间（秒）
        base_time = 30
        # 每行配置大约需要的时间（秒）
        time_per_line = 0.5

        estimated_seconds = base_time + (total_changes * time_per_line)

        return {
            "estimated_seconds": int(estimated_seconds),
            "estimated_minutes": round(estimated_seconds / 60, 1),
            "description": f"预计需要 {round(estimated_seconds / 60, 1)} 分钟完成回滚操作",
        }
