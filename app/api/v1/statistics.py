"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: statistics.py
@DateTime: 2025/08/01
@Docs: 统一统计模块API - 所有系统统计功能的入口
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import Permissions, require_permission
from app.schemas.base import BaseResponse
from app.schemas.statistics import (
    APIStatsResponse,
    DashboardStatsResponse,
    ModuleStatsResponse,
    OverallStatsResponse,
    StatsFilterQuery,
    StatsPeriodQuery,
)
from app.services.statistics import StatisticsService
from app.utils.deps import (
    OperationContext,
    get_cli_service,
    get_device_connection_service,
    get_statistics_service,
)
from app.utils.logger import logger

router = APIRouter(prefix="/stats", tags=["系统统计"])


@router.get("/overall", response_model=OverallStatsResponse, summary="获取整体统计信息")
async def get_overall_stats(
    period: StatsPeriodQuery = Depends(),
    operation_context: OperationContext = Depends(require_permission(Permissions.STATISTICS_READ)),
    statistics_service: StatisticsService = Depends(get_statistics_service),
):
    """获取整体统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取整体统计")
    return await statistics_service.get_overall_stats(period)


@router.get("/api", response_model=APIStatsResponse, summary="获取API统计信息")
async def get_api_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.STATISTICS_API_STATS)),
    statistics_service: StatisticsService = Depends(get_statistics_service),
):
    """获取API统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取API统计")
    return await statistics_service.get_api_stats()


@router.get("/modules", response_model=ModuleStatsResponse, summary="获取模块统计信息")
async def get_module_stats(
    filter_query: StatsFilterQuery = Depends(),
    operation_context: OperationContext = Depends(require_permission(Permissions.STATISTICS_READ)),
    statistics_service: StatisticsService = Depends(get_statistics_service),
):
    """获取模块统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取模块统计")
    return await statistics_service.get_module_stats(filter_query)


@router.get("/dashboard", response_model=DashboardStatsResponse, summary="获取仪表板统计信息")
async def get_dashboard_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.STATISTICS_DASHBOARD)),
    statistics_service: StatisticsService = Depends(get_statistics_service),
):
    """获取仪表板统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取仪表板统计")
    return await statistics_service.get_dashboard_stats()


# 设备连接统计
@router.get("/connections", response_model=BaseResponse[dict], summary="获取设备连接统计信息")
async def get_connection_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_READ)),
    device_connection_service=Depends(get_device_connection_service),
):
    """获取设备连接统计信息（包括连接池和管理器统计）"""
    logger.info(f"用户 {operation_context.user.username} 获取设备连接统计")

    try:
        # 获取连接池统计
        pool_stats = await device_connection_service.get_connection_pool_stats()

        # 获取连接管理器统计
        manager_stats = await device_connection_service.get_connection_manager_stats()

        # 合并统计数据
        connection_stats = {
            "pool_stats": pool_stats,
            "manager_stats": manager_stats,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),  # 使用当前时间戳
        }

        logger.info("设备连接统计获取成功")
        return BaseResponse(data=connection_stats, message="获取设备连接统计成功")

    except Exception as e:
        logger.error(f"获取设备连接统计失败: {e}")
        return BaseResponse(data={"error": str(e)}, message="获取设备连接统计失败")


# 权限缓存统计
@router.get("/permissions", response_model=BaseResponse[dict], summary="获取权限缓存统计信息")
async def get_permission_cache_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """获取权限缓存统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取权限缓存统计")

    from app.utils.permission_cache_utils import get_permission_cache_stats

    try:
        # 获取权限缓存统计
        cache_stats = await get_permission_cache_stats()

        return BaseResponse(data=cache_stats, message="获取权限缓存统计成功")

    except Exception as e:
        logger.error(f"获取权限缓存统计失败: {e}")
        return BaseResponse(data={"error": str(e)}, message="获取权限缓存统计失败")


# CLI会话统计
@router.get("/cli-sessions", response_model=BaseResponse[dict], summary="获取CLI会话统计信息")
async def get_cli_session_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service=Depends(get_cli_service),
):
    """获取CLI会话统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取CLI会话统计")

    try:
        # 获取CLI会话统计
        session_stats = await cli_service.get_session_stats()

        return BaseResponse(data=session_stats, message="获取CLI会话统计成功")

    except Exception as e:
        logger.error(f"获取CLI会话统计失败: {e}")
        return BaseResponse(data={"error": str(e)}, message="获取CLI会话统计失败")
