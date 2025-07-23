"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_history.py
@DateTime: 2025/07/23
@Docs: 查询历史数据访问层
"""

from datetime import datetime, timedelta
from uuid import UUID

from app.dao.base import BaseDAO
from app.models.query_history import QueryHistory
from app.utils.logger import logger


class QueryHistoryDAO(BaseDAO[QueryHistory]):
    """查询历史数据访问层"""

    def __init__(self):
        super().__init__(QueryHistory)

    async def get_by_user(self, user_id: UUID, limit: int = 100) -> list[QueryHistory]:
        """根据用户获取查询历史"""
        try:
            return await self.model.filter(user_id=user_id, is_deleted=False).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"根据用户获取查询历史失败: {e}")
            return []

    async def get_by_query_type(self, query_type: str, limit: int = 100) -> list[QueryHistory]:
        """根据查询类型获取历史"""
        try:
            return (
                await self.model.filter(query_type=query_type, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"根据查询类型获取历史失败: {e}")
            return []

    async def search_histories(
        self,
        user_id: UUID | None = None,
        query_type: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[QueryHistory]:
        """搜索查询历史"""
        try:
            filters: dict = {"is_deleted": False}
            if user_id:
                filters["user_id"] = user_id
            if query_type:
                filters["query_type"] = query_type
            if status:
                filters["status"] = status

            queryset = self.model.filter(**filters)

            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)

            return await queryset.order_by("-created_at").all()
        except Exception as e:
            logger.error(f"搜索查询历史失败: {e}")
            return []

    async def get_recent_histories(self, days: int = 7, limit: int = 100) -> list[QueryHistory]:
        """获取最近几天的查询历史"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            return (
                await self.model.filter(created_at__gte=since_date, is_deleted=False)
                .order_by("-created_at")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"获取最近查询历史失败: {e}")
            return []

    async def get_failed_queries(self, limit: int = 50) -> list[QueryHistory]:
        """获取失败的查询记录"""
        try:
            return await self.model.filter(status="failed", is_deleted=False).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"获取失败查询记录失败: {e}")
            return []

    async def get_slow_queries(self, min_execution_time: float = 10.0, limit: int = 50) -> list[QueryHistory]:
        """获取慢查询记录"""
        try:
            return (
                await self.model.filter(execution_time__gte=min_execution_time, is_deleted=False)
                .order_by("-execution_time")
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"获取慢查询记录失败: {e}")
            return []

    async def get_user_query_stats(self, user_id: UUID, days: int = 30) -> dict:
        """获取用户查询统计"""
        try:
            since_date = datetime.now() - timedelta(days=days)

            total_count = await self.model.filter(user_id=user_id, created_at__gte=since_date, is_deleted=False).count()

            success_count = await self.model.filter(
                user_id=user_id, status="success", created_at__gte=since_date, is_deleted=False
            ).count()

            failed_count = await self.model.filter(
                user_id=user_id, status="failed", created_at__gte=since_date, is_deleted=False
            ).count()

            return {
                "total_count": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / total_count if total_count > 0 else 0.0,
            }
        except Exception as e:
            logger.error(f"获取用户查询统计失败: {e}")
            return {"total_count": 0, "success_count": 0, "failed_count": 0, "success_rate": 0.0}

    async def cleanup_old_records(self, days: int = 90) -> int:
        """清理旧的查询记录"""
        try:
            cleanup_date = datetime.now() - timedelta(days=days)
            count = await self.model.filter(created_at__lt=cleanup_date).update(is_deleted=True)
            logger.info(f"已清理 {count} 条超过 {days} 天的查询记录")
            return count
        except Exception as e:
            logger.error(f"清理旧查询记录失败: {e}")
            return 0

    async def get_histories_with_user(self) -> list[QueryHistory]:
        """获取查询历史及其关联的用户信息"""
        try:
            return await self.get_all_with_related(
                select_related=["user"],
            )
        except Exception as e:
            logger.error(f"获取查询历史及用户信息失败: {e}")
            return []

    async def get_history_with_details(self, history_id: UUID) -> QueryHistory | None:
        """获取查询历史详细信息"""
        try:
            return await self.get_with_related(
                id=history_id,
                select_related=["user"],
            )
        except Exception as e:
            logger.error(f"获取查询历史详细信息失败: {e}")
            return None

    async def get_histories_paginated_optimized(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: UUID | None = None,
        query_type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[QueryHistory], int]:
        """分页获取查询历史"""
        try:
            filters: dict = {"is_deleted": False}
            if user_id:
                filters["user_id"] = user_id
            if query_type:
                filters["query_type"] = query_type
            if status:
                filters["status"] = status

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["-created_at"],
                select_related=["user"],
                prefetch_related=None,
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取查询历史失败: {e}")
            return [], 0
