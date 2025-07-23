"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_history.py
@DateTime: 2025/07/23
@Docs: 查询历史管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.query_history import (
    QueryHistoryCreateRequest,
    QueryHistoryDetailResponse,
    QueryHistoryListRequest,
    QueryHistoryListResponse,
    QueryHistoryResponse,
)
from app.services.query_history import QueryHistoryService
from app.utils.deps import OperationContext, get_query_history_service

router = APIRouter(prefix="/query-history", tags=["查询历史管理"])


@router.get("", response_model=QueryHistoryListResponse, summary="获取查询历史列表")
async def list_query_histories(
    query: QueryHistoryListRequest = Depends(),
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_READ)),
):
    """获取查询历史列表（分页），支持搜索和筛选"""
    return await service.get_history_list(query, operation_context=operation_context)


@router.get("/{history_id}", response_model=QueryHistoryDetailResponse, summary="获取查询历史详情")
async def get_query_history(
    history_id: UUID,
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_READ)),
):
    """获取查询历史详情"""
    history = await service.get_history_by_id(history_id, operation_context=operation_context)
    if not history:
        raise HTTPException(status_code=404, detail="查询历史不存在")
    return QueryHistoryDetailResponse(**history.model_dump())


@router.post("", response_model=QueryHistoryResponse, status_code=status.HTTP_201_CREATED, summary="创建查询历史")
async def create_query_history(
    history_data: QueryHistoryCreateRequest,
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_CREATE)),
):
    """创建新查询历史记录"""
    return await service.create(operation_context, **history_data.model_dump())


@router.delete("/{history_id}", response_model=SuccessResponse, summary="删除查询历史")
async def delete_query_history(
    history_id: UUID,
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_DELETE)),
):
    """删除查询历史"""
    await service.delete(history_id, operation_context)
    return SuccessResponse(message="查询历史删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[QueryHistoryResponse], summary="批量创建查询历史")
async def batch_create_query_histories(
    histories_data: list[QueryHistoryCreateRequest],
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_CREATE)),
):
    """批量创建查询历史记录"""
    results = []
    for history_data in histories_data:
        result = await service.create(operation_context, **history_data.model_dump())
        results.append(result)
    return results


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除查询历史")
async def batch_delete_query_histories(
    history_ids: list[UUID],
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_DELETE)),
):
    """批量删除查询历史"""
    for history_id in history_ids:
        await service.delete(history_id, operation_context)
    return SuccessResponse(message=f"成功删除 {len(history_ids)} 条查询历史")


# ===== 统计和搜索功能 =====


@router.get("/recent", response_model=list[QueryHistoryResponse], summary="获取最近查询历史")
async def get_recent_query_histories(
    days: int = Query(default=7, description="查询天数", ge=1, le=365),
    limit: int = Query(default=100, description="返回数量限制", ge=1, le=500),
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_READ)),
):
    """获取最近的查询历史"""
    # TODO: 实现根据时间筛选的查询逻辑
    return []


@router.get("/statistics", response_model=dict, summary="获取查询历史统计")
async def get_query_history_statistics(
    user_id: UUID | None = Query(default=None, description="用户ID筛选"),
    device_id: UUID | None = Query(default=None, description="设备ID筛选"),
    days: int = Query(default=30, description="统计天数", ge=1, le=365),
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_STATISTICS)),
):
    """获取查询历史统计信息"""
    return {"total_queries": 0, "user_queries": 0, "device_queries": 0, "query_types": {}, "daily_stats": []}


# ===== 清理功能 =====


@router.delete("/cleanup", response_model=SuccessResponse, summary="清理旧查询历史")
async def cleanup_old_query_histories(
    days: int = Query(default=90, description="保留天数", ge=7, le=365),
    service: QueryHistoryService = Depends(get_query_history_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_HISTORY_CLEANUP)),
):
    """清理指定天数之前的查询历史"""
    deleted_count = 0  # TODO: 实现实际清理逻辑
    return SuccessResponse(message=f"成功清理 {deleted_count} 条旧查询历史")
