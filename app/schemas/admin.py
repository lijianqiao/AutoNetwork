"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: admin.py
@DateTime: 2025/08/01
@Docs: 管理员相关Schema定义
"""

from typing import Any

from pydantic import BaseModel, Field


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""

    system: str = Field(..., description="操作系统")
    platform: str = Field(..., description="平台信息")
    python_version: str = Field(..., description="Python版本")
    cpu_count: int = Field(..., description="CPU核心数")
    memory_total: str = Field(..., description="总内存")
    memory_available: str = Field(..., description="可用内存")
    memory_percent: float = Field(..., description="内存使用率")
    disk_usage: dict[str, Any] = Field(..., description="磁盘使用情况")
    uptime: str = Field(..., description="系统运行时间")
    current_time: str = Field(..., description="当前时间")


class SystemConfigRequest(BaseModel):
    """系统配置请求模型"""

    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值")
    description: str = Field("", description="配置描述")


class SystemConfigResponse(BaseModel):
    """系统配置响应模型"""

    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值")
    description: str = Field(..., description="配置描述")
    updated_at: str = Field(..., description="更新时间")


class UsersOverviewResponse(BaseModel):
    """用户概览响应模型"""

    total_users: int = Field(..., description="用户总数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    superusers: int = Field(..., description="超级管理员数")
    total_roles: int = Field(..., description="角色总数")
    users_by_role: dict[str, int] = Field(..., description="按角色统计用户数")
    recent_logins: int = Field(..., description="最近7天登录用户数")


class SystemHealthResponse(BaseModel):
    """系统健康状态响应模型"""

    overall_status: str = Field(..., description="整体状态")
    database_status: str = Field(..., description="数据库状态")
    redis_status: str = Field(..., description="Redis状态")
    api_status: str = Field(..., description="API状态")
    timestamp: str = Field(..., description="检查时间")


class SystemMetricsResponse(BaseModel):
    """系统指标响应模型"""

    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    network_io: dict[str, Any] = Field(..., description="网络IO统计")
    process_count: int = Field(..., description="进程数量")
    timestamp: str = Field(..., description="采集时间")
