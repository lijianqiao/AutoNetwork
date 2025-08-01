"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: statistics.py
@DateTime: 2025/08/01
@Docs: 统一统计模块 Schema
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class APIStatsItem(BaseModel):
    """单个API统计项"""

    module_name: str = Field(..., description="模块名称")
    endpoint_count: int = Field(..., description="接口数量")
    active_endpoints: int = Field(default=0, description="活跃接口数量")
    deprecated_endpoints: int = Field(default=0, description="废弃接口数量")
    last_access_time: datetime | None = Field(None, description="最后访问时间")


class ModuleStatsItem(BaseModel):
    """模块统计项"""

    name: str = Field(..., description="模块名称")
    type: str = Field(..., description="模块类型")
    item_count: int = Field(..., description="数据项数量")
    active_count: int = Field(default=0, description="活跃数量")
    created_today: int = Field(default=0, description="今日新增")
    updated_today: int = Field(default=0, description="今日更新")


class UserStatsOverview(BaseModel):
    """用户统计概览"""

    total_users: int = Field(..., description="用户总数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    total_roles: int = Field(..., description="角色总数")
    total_permissions: int = Field(..., description="权限总数")
    users_with_roles: int = Field(..., description="已分配角色的用户数")
    users_with_permissions: int = Field(..., description="已分配权限的用户数")


class DeviceStatsOverview(BaseModel):
    """设备统计概览"""

    total_devices: int = Field(..., description="设备总数")
    active_devices: int = Field(..., description="活跃设备数")
    offline_devices: int = Field(..., description="离线设备数")
    devices_by_vendor: dict[str, int] = Field(default_factory=dict, description="按厂商分组的设备数")
    devices_by_region: dict[str, int] = Field(default_factory=dict, description="按基地分组的设备数")
    connection_success_rate: float = Field(default=0.0, description="连接成功率")


class QueryStatsOverview(BaseModel):
    """查询统计概览"""

    total_queries: int = Field(..., description="查询总数")
    successful_queries: int = Field(..., description="成功查询数")
    failed_queries: int = Field(..., description="失败查询数")
    queries_today: int = Field(..., description="今日查询数")
    popular_templates: list[dict[str, Any]] = Field(default_factory=list, description="热门查询模板")
    query_success_rate: float = Field(default=0.0, description="查询成功率")


class SystemStatsOverview(BaseModel):
    """系统统计概览"""

    uptime_days: int = Field(..., description="系统运行天数")
    total_operations: int = Field(..., description="总操作数")
    operations_today: int = Field(..., description="今日操作数")
    cache_hit_rate: float = Field(default=0.0, description="缓存命中率")
    active_sessions: int = Field(default=0, description="活跃会话数")
    storage_usage: dict[str, Any] = Field(default_factory=dict, description="存储使用情况")


class OverallStatsResponse(BaseResponse):
    """整体统计响应"""

    user_stats: UserStatsOverview
    device_stats: DeviceStatsOverview
    query_stats: QueryStatsOverview
    system_stats: SystemStatsOverview


class APIStatsResponse(BaseResponse):
    """API统计响应"""

    total_modules: int = Field(..., description="模块总数")
    total_endpoints: int = Field(..., description="接口总数")
    active_endpoints: int = Field(..., description="活跃接口数")
    deprecated_endpoints: int = Field(..., description="废弃接口数")
    api_stats: list[APIStatsItem] = Field(..., description="API统计详情")


class ModuleStatsResponse(BaseResponse):
    """模块统计响应"""

    modules: list[ModuleStatsItem] = Field(..., description="模块统计详情")


class DashboardStatsResponse(BaseResponse):
    """仪表板统计响应"""

    overall_stats: OverallStatsResponse
    api_stats: APIStatsResponse
    recent_activities: list[dict[str, Any]] = Field(default_factory=list, description="最近活动")
    system_alerts: list[dict[str, Any]] = Field(default_factory=list, description="系统警告")


class StatsPeriodQuery(BaseModel):
    """统计查询时间段"""

    start_date: datetime | None = Field(None, description="开始时间")
    end_date: datetime | None = Field(None, description="结束时间")
    period: str | None = Field("day", description="统计周期：hour/day/week/month")


class StatsFilterQuery(BaseModel):
    """统计过滤查询"""

    module_name: str | None = Field(None, description="模块名称")
    user_id: int | None = Field(None, description="用户ID")
    region_id: int | None = Field(None, description="基地ID")
    vendor_id: int | None = Field(None, description="厂商ID")
    include_inactive: bool = Field(False, description="是否包含非活跃数据")
