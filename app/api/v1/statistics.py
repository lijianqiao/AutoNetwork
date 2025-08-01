"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: statistics.py
@DateTime: 2025/08/01
@Docs: 统一统计模块API - 所有系统统计功能的入口
"""

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
from app.utils.deps import OperationContext, get_statistics_service
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
):
    """获取设备连接统计信息（包括连接池和管理器统计）"""
    logger.info(f"用户 {operation_context.user.username} 获取设备连接统计")
    # TODO: 实现统一的连接统计逻辑
    return BaseResponse(data={"message": "连接统计功能正在开发中"}, message="获取连接统计成功")


# 查询引擎统计
@router.get("/queries", response_model=BaseResponse[dict], summary="获取查询引擎统计信息")
async def get_query_engine_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_ACCESS)),
):
    """获取查询引擎统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取查询引擎统计")
    # TODO: 实现统一的查询引擎统计逻辑
    return BaseResponse(data={"message": "查询引擎统计功能正在开发中"}, message="获取查询引擎统计成功")


# 权限缓存统计
@router.get("/permissions", response_model=BaseResponse[dict], summary="获取权限缓存统计信息")
async def get_permission_cache_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """获取权限缓存统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取权限缓存统计")
    # TODO: 实现统一的权限缓存统计逻辑
    return BaseResponse(data={"message": "权限缓存统计功能正在开发中"}, message="获取权限缓存统计成功")


# CLI会话统计
@router.get("/cli-sessions", response_model=BaseResponse[dict], summary="获取CLI会话统计信息")
async def get_cli_session_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
):
    """获取CLI会话统计信息"""
    logger.info(f"用户 {operation_context.user.username} 获取CLI会话统计")
    # TODO: 实现统一的CLI会话统计逻辑
    return BaseResponse(data={"message": "CLI会话统计功能正在开发中"}, message="获取CLI会话统计成功")
