"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_logs.py
@DateTime: 2025/07/08
@Docs: 操作日志API端点 - 使用依赖注入权限控制
"""

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.operation_log import (
    OperationLogListRequest,
    OperationLogListResponse,
    OperationLogResponse,
    OperationLogStatisticsRequest,
    OperationLogStatisticsResponse,
)
from app.services.operation_log import OperationLogService
from app.utils.deps import OperationContext, get_operation_log_service

router = APIRouter(prefix="/operation-logs", tags=["操作日志管理"])


@router.get("", response_model=BaseResponse[OperationLogListResponse], summary="获取操作日志列表")
async def list_operation_logs(
    query: OperationLogListRequest = Depends(),
    service: OperationLogService = Depends(get_operation_log_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.LOG_VIEW)),
):
    """获取操作日志列表（分页），支持搜索和筛选"""
    logs, total = await service.get_logs(query, operation_context=operation_context)
    response = OperationLogListResponse(
        data=[OperationLogResponse.model_validate(log) for log in logs],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
    return BaseResponse(data=response)


@router.get("/statistics", response_model=BaseResponse[OperationLogStatisticsResponse], summary="获取操作日志统计")
async def get_operation_log_statistics(
    query: OperationLogStatisticsRequest = Depends(),
    service: OperationLogService = Depends(get_operation_log_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.LOG_VIEW)),
):
    """获取操作日志统计信息"""
    result = await service.get_statistics(query, operation_context=operation_context)
    return BaseResponse(data=result)


@router.delete("/cleanup", response_model=SuccessResponse, summary="清理操作日志")
async def cleanup_operation_logs(
    days: int = 30,
    service: OperationLogService = Depends(get_operation_log_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.LOG_DELETE)),
):
    """清理指定天数之前的操作日志"""
    await service.cleanup_logs(days, operation_context=operation_context)
    return SuccessResponse()
