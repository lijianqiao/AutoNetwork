"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_config.py
@DateTime: 2025/07/23
@Docs: 设备配置快照数据访问层
"""

from datetime import datetime, timedelta
from uuid import UUID

from app.dao.base import BaseDAO
from app.models.device_config import DeviceConfig
from app.utils.logger import logger


class DeviceConfigDAO(BaseDAO[DeviceConfig]):
    """设备配置快照数据访问层"""

    def __init__(self):
        super().__init__(DeviceConfig)

    async def get_by_device(self, device_id: UUID, limit: int = 50) -> list[DeviceConfig]:
        """根据设备获取配置快照列表"""
        try:
            return (
                await self.model.filter(device_id=device_id, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"根据设备获取配置快照失败: {e}")
            return []

    async def get_by_device_and_type(self, device_id: UUID, config_type: str, limit: int = 20) -> list[DeviceConfig]:
        """根据设备和配置类型获取快照列表"""
        try:
            return (
                await self.model.filter(device_id=device_id, config_type=config_type, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"根据设备和配置类型获取快照失败: {e}")
            return []

    async def get_latest_config(self, device_id: UUID, config_type: str) -> DeviceConfig | None:
        """获取设备最新的配置快照"""
        try:
            return (
                await self.model.filter(device_id=device_id, config_type=config_type, is_deleted=False)
                .order_by("-created_at")
                .first()
            )
        except Exception as e:
            logger.error(f"获取最新配置快照失败: {e}")
            return None

    async def get_by_hash(self, config_hash: str) -> DeviceConfig | None:
        """根据配置哈希值获取快照"""
        try:
            return await self.model.get_or_none(config_hash=config_hash, is_deleted=False)
        except Exception as e:
            logger.error(f"根据哈希值获取配置快照失败: {e}")
            return None

    async def check_hash_exists(self, config_hash: str, exclude_id: UUID | None = None) -> bool:
        """检查配置哈希值是否已存在"""
        try:
            filters: dict = {"config_hash": config_hash, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查配置哈希值是否存在失败: {e}")
            return False

    async def search_configs(
        self,
        device_id: UUID | None = None,
        config_type: str | None = None,
        backup_by: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[DeviceConfig]:
        """搜索配置快照"""
        try:
            filters: dict = {"is_deleted": False}
            if device_id:
                filters["device_id"] = device_id
            if config_type:
                filters["config_type"] = config_type
            if backup_by:
                filters["backup_by_id"] = backup_by

            queryset = self.model.filter(**filters)

            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)

            return await queryset.order_by("-created_at").all()
        except Exception as e:
            logger.error(f"搜索配置快照失败: {e}")
            return []

    async def get_configs_by_user(self, backup_by: UUID, limit: int = 100) -> list[DeviceConfig]:
        """根据备份用户获取配置快照"""
        try:
            return (
                await self.model.filter(backup_by_id=backup_by, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"根据备份用户获取配置快照失败: {e}")
            return []

    async def get_recent_configs(self, days: int = 7, limit: int = 100) -> list[DeviceConfig]:
        """获取最近几天的配置快照"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            return (
                await self.model.filter(created_at__gte=since_date, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"获取最近配置快照失败: {e}")
            return []

    async def get_config_changes(self, device_id: UUID, days: int = 30) -> list[DeviceConfig]:
        """获取设备配置变更记录"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            configs = (
                await self.model.filter(device_id=device_id, created_at__gte=since_date, is_deleted=False)
                .order_by("-created_at")
                .all()
            )

            # 去重，只保留配置实际发生变化的记录
            unique_configs = []
            seen_hashes = set()
            for config in configs:
                if config.config_hash not in seen_hashes:
                    unique_configs.append(config)
                    seen_hashes.add(config.config_hash)

            return unique_configs
        except Exception as e:
            logger.error(f"获取配置变更记录失败: {e}")
            return []

    async def cleanup_old_configs(self, device_id: UUID, keep_count: int = 50) -> int:
        """清理设备的旧配置快照，保留最新的指定数量"""
        try:
            # 获取所有配置快照，按创建时间倒序
            all_configs = await self.model.filter(device_id=device_id, is_deleted=False).order_by("-created_at").all()

            if len(all_configs) <= keep_count:
                return 0

            # 标记需要删除的配置为软删除
            configs_to_delete = all_configs[keep_count:]
            delete_ids = [config.id for config in configs_to_delete]

            count = await self.model.filter(id__in=delete_ids).update(is_deleted=True)
            logger.info(f"已清理设备 {device_id} 的 {count} 条旧配置快照")
            return count
        except Exception as e:
            logger.error(f"清理旧配置快照失败: {e}")
            return 0

    async def get_configs_with_relations(self) -> list[DeviceConfig]:
        """获取配置快照及其关联的设备和用户信息"""
        try:
            return await self.get_all_with_related(
                select_related=["device", "backup_by"],
            )
        except Exception as e:
            logger.error(f"获取配置快照及关联信息失败: {e}")
            return []

    async def get_config_with_details(self, config_id: UUID) -> DeviceConfig | None:
        """获取配置快照详细信息"""
        try:
            return await self.get_with_related(
                id=config_id,
                select_related=["device", "backup_by"],
            )
        except Exception as e:
            logger.error(f"获取配置快照详细信息失败: {e}")
            return None

    async def get_configs_paginated_optimized(
        self,
        page: int = 1,
        page_size: int = 20,
        device_id: UUID | None = None,
        config_type: str | None = None,
    ) -> tuple[list[DeviceConfig], int]:
        """分页获取配置快照"""
        try:
            filters: dict = {"is_deleted": False}
            if device_id:
                filters["device_id"] = device_id
            if config_type:
                filters["config_type"] = config_type

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["-created_at"],
                select_related=["device", "backup_by"],
                prefetch_related=None,
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取配置快照失败: {e}")
            return [], 0
