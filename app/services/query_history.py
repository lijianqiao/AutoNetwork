"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_history.py
@DateTime: 2025/07/23
@Docs: 查询历史服务层 - 使用操作上下文依赖注入
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.query_history import QueryHistoryDAO
from app.models.query_history import QueryHistory
from app.schemas.query_history import (
    QueryHistoryCreateRequest,
    QueryHistoryListRequest,
    QueryHistoryListResponse,
    QueryHistoryResponse,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
)


class QueryHistoryService(BaseService[QueryHistory]):
    """查询历史服务"""

    def __init__(self):
        super().__init__(QueryHistoryDAO())

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前验证"""
        # 验证查询类型
        valid_query_types = ["mac_query", "interface_status", "custom_command", "template_query"]
        if data.get("query_type") not in valid_query_types:
            raise BusinessException(f"无效的查询类型: {data.get('query_type')}")

        # 验证查询状态
        valid_statuses = ["success", "failed", "partial"]
        if data.get("status") not in valid_statuses:
            raise BusinessException(f"无效的查询状态: {data.get('status')}")

        # 验证执行时间
        if data.get("execution_time", 0) < 0:
            raise BusinessException("执行时间不能为负数")

        return data

    @log_create_with_context("query_history")
    async def create_history(
        self, data: QueryHistoryCreateRequest, operation_context: OperationContext
    ) -> QueryHistoryResponse:
        """创建查询历史记录"""
        history_data = data.model_dump()
        history_data["user_id"] = operation_context.user.id

        history = await self.create(operation_context, **history_data)
        return QueryHistoryResponse.model_validate(history)

    @log_delete_with_context("query_history")
    async def delete_history(self, history_id: UUID, operation_context: OperationContext) -> bool:
        """删除查询历史记录"""
        history = await self.get_by_id(history_id)
        if not history:
            raise BusinessException("查询历史记录不存在")

        # 只有创建者或管理员可以删除
        if (
            hasattr(history, "user")
            and history.user.id != operation_context.user.id
            and not operation_context.user.is_superuser
        ):
            raise BusinessException("无权限删除该查询历史记录")

        return await self.soft_delete(history_id)

    @log_query_with_context("query_history")
    async def get_history_list(
        self, params: QueryHistoryListRequest, operation_context: OperationContext
    ) -> QueryHistoryListResponse:
        """获取查询历史列表"""
        # 非管理员只能查看自己的历史记录
        filters = {}
        if not operation_context.user.is_superuser:
            filters["user_id"] = operation_context.user.id

        # 添加其他过滤条件
        if hasattr(params, "user_id") and params.user_id:
            if operation_context.user.is_superuser:
                filters["user_id"] = params.user_id

        if hasattr(params, "query_type") and params.query_type:
            filters["query_type"] = params.query_type

        if hasattr(params, "status") and params.status:
            filters["status"] = params.status

        # 查询数据
        histories, total = await self.get_paginated(**filters)
        responses = [QueryHistoryResponse.model_validate(history) for history in histories]

        return QueryHistoryListResponse(data=responses, total=total, page=params.page, page_size=params.page_size)

    @log_query_with_context("query_history")
    @log_query_with_context("query_history")
    async def get_history_by_id(self, history_id: UUID, operation_context: OperationContext) -> QueryHistoryResponse:
        """根据ID获取查询历史详情"""
        history = await self.get_by_id(history_id)
        if not history:
            raise BusinessException("查询历史记录不存在")

        # 非管理员只能查看自己的历史记录
        if (
            hasattr(history, "user_id")
            and history.user.id != operation_context.user.id
            and not operation_context.user.is_superuser
        ):
            raise BusinessException("无权限查看该查询历史记录")

        return QueryHistoryResponse.model_validate(history)

    @log_query_with_context("query_history")
    async def get_user_statistics(self, user_id: UUID | None, operation_context: OperationContext) -> dict[str, Any]:
        """获取用户查询统计信息"""
        # 如果没有指定用户ID，统计当前用户的数据
        target_user_id = user_id if user_id else operation_context.user.id

        # 非管理员只能查看自己的统计信息
        if target_user_id != operation_context.user.id and not operation_context.user.is_superuser:
            raise BusinessException("无权限查看该用户的统计信息")

        try:
            # 总查询次数
            total_queries = await self.count(user_id=target_user_id)

            # 成功查询次数
            success_queries = await self.count(user_id=target_user_id, status="success")

            # 失败查询次数
            failed_queries = await self.count(user_id=target_user_id, status="failed")

            # 获取最近查询 - 使用基础方法实现
            recent_histories = await self.get_paginated(
                page=1, page_size=5, order_by=["-created_at"], user_id=target_user_id
            )
            recent_query_types = [h.query_type for h in recent_histories[0] if hasattr(h, "query_type")]
            last_query_time = (
                recent_histories[0][0].created_at
                if recent_histories[0] and hasattr(recent_histories[0][0], "created_at")
                else None
            )

            return {
                "total_queries": total_queries,
                "success_queries": success_queries,
                "failed_queries": failed_queries,
                "success_rate": round(success_queries / total_queries * 100, 2) if total_queries > 0 else 0.0,
                "recent_query_types": recent_query_types,
                "last_query_time": last_query_time,
            }

        except Exception as e:
            logger.error(f"获取用户 {target_user_id} 的查询统计信息失败: {e}")
            raise BusinessException(f"获取查询统计信息失败: {e}") from e

    # ===== 批量操作方法 =====

    @log_create_with_context("query_history")
    async def batch_create_histories(
        self, histories_data: list[QueryHistoryCreateRequest], operation_context: OperationContext
    ) -> list[QueryHistoryResponse]:
        """批量创建查询历史记录"""
        # 转换为字典列表并进行验证
        data_list = []
        for history_data in histories_data:
            data = history_data.model_dump()
            # 应用前置验证
            validated_data = await self.before_create(data)
            data_list.append(validated_data)

        # 使用BaseService的批量创建方法
        created_histories = await self.bulk_create(data_list)
        return [QueryHistoryResponse.model_validate(history) for history in created_histories]

    @log_delete_with_context("query_history")
    async def batch_delete_histories(
        self, history_ids: list[UUID], operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量删除查询历史记录"""
        if not history_ids:
            raise BusinessException("请提供要删除的历史记录ID")

        success_count = 0
        failed_items = []

        for history_id in history_ids:
            try:
                history = await self.get_by_id(history_id)
                if not history:
                    failed_items.append({"id": str(history_id), "reason": "记录不存在"})
                    continue

                # 只有创建者或管理员可以删除
                if (
                    hasattr(history, "user_id")
                    and history.user.id != operation_context.user.id
                    and not operation_context.user.is_superuser
                ):
                    failed_items.append({"id": str(history_id), "reason": "无权限删除"})
                    continue

                await self.soft_delete(history_id)
                success_count += 1

            except Exception as e:
                logger.error(f"删除查询历史记录 {history_id} 失败: {e}")
                failed_items.append({"id": str(history_id), "reason": str(e)})

        return {"success_count": success_count, "failed_count": len(failed_items), "failed_items": failed_items}

    @log_delete_with_context("query_history")
    async def cleanup_old_histories(self, days: int, operation_context: OperationContext) -> dict[str, Any]:
        """清理旧的查询历史记录"""
        if days <= 0:
            raise BusinessException("清理天数必须大于0")

        # 只有管理员可以执行清理操作
        if not operation_context.user.is_superuser:
            raise BusinessException("只有管理员可以执行清理操作")

        try:
            # 使用基础方法实现旧记录清理
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = await self.soft_delete_by_filter(created_at__lt=cutoff_date)

            return {
                "deleted_count": deleted_count,
                "cleanup_days": days,
                "message": f"成功清理 {days} 天前的 {deleted_count} 条查询历史记录",
            }

        except Exception as e:
            logger.error(f"清理 {days} 天前的查询历史记录失败: {e}")
            raise BusinessException(f"清理操作失败: {e}") from e
