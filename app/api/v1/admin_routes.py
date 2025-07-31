"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: admin_routes.py
@DateTime: 2025/07/10
@Docs: 管理员专用路由
"""

import platform
from datetime import datetime
from typing import Any

import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse
from app.services.role import RoleService
from app.services.user import UserService
from app.utils.deps import (
    OperationContext,
    get_role_service,
    get_user_service,
)


# 响应模型定义
class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""

    system: str
    platform: str
    python_version: str
    cpu_count: int
    memory_total: str
    memory_available: str
    memory_percent: float
    disk_usage: dict[str, Any]
    uptime: str
    current_time: str


class SystemConfigRequest(BaseModel):
    """系统配置请求模型"""

    config_key: str
    config_value: str
    description: str = ""


class UsersOverviewResponse(BaseModel):
    """用户概览响应模型"""

    total_users: int
    active_users: int
    inactive_users: int
    superusers: int
    total_roles: int
    users_by_role: dict[str, int]
    recent_logins: int  # 最近7天登录用户数


# 创建具有路由器级权限控制的路由器
admin_router = APIRouter(
    prefix="/admin",
    tags=["管理员专用"],
    dependencies=[Depends(require_permission(Permissions.SYSTEM_ADMIN))],  # 路由器级权限控制
)


@admin_router.get("/system-info", response_model=BaseResponse[SystemInfoResponse], summary="获取系统信息")
async def get_system_info(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_CONFIG)),
):
    """获取系统信息 - 需要系统管理员权限和系统配置权限"""
    # 获取系统信息
    memory = psutil.virtual_memory()
    # Windows系统使用C盘，Linux/Mac使用根目录
    disk_path = "C:\\" if platform.system() == "Windows" else "/"
    disk = psutil.disk_usage(disk_path)

    # 计算系统运行时间
    boot_time = psutil.boot_time()
    uptime_seconds = datetime.now().timestamp() - boot_time
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)

    system_info = SystemInfoResponse(
        system=platform.system(),
        platform=platform.platform(),
        python_version=platform.python_version(),
        cpu_count=psutil.cpu_count() or 0,  # 处理None值
        memory_total=f"{memory.total / (1024**3):.2f} GB",
        memory_available=f"{memory.available / (1024**3):.2f} GB",
        memory_percent=memory.percent,
        disk_usage={
            "total": f"{disk.total / (1024**3):.2f} GB",
            "used": f"{disk.used / (1024**3):.2f} GB",
            "free": f"{disk.free / (1024**3):.2f} GB",
            "percent": (disk.used / disk.total) * 100,
        },
        uptime=f"{uptime_hours}小时{uptime_minutes}分钟",
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    return BaseResponse(data=system_info, message="系统信息获取成功")


@admin_router.get("/users-overview", response_model=BaseResponse[UsersOverviewResponse], summary="用户概览")
async def get_users_overview(
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """获取用户概览 - 只需要系统管理员权限"""

    from app.schemas.role import RoleListRequest
    from app.schemas.user import UserListRequest

    # 获取用户统计数据
    users, total_users = await user_service.get_users(UserListRequest(page=1, page_size=1), operation_context)

    # 获取活跃和非活跃用户数
    active_users_request = UserListRequest(page=1, page_size=1, is_active=True)
    _, active_users_count = await user_service.get_users(active_users_request, operation_context)

    inactive_users_count = total_users - active_users_count

    # 获取超级用户数（这里需要根据实际的用户模型调整）
    # 假设有 is_superuser 字段
    superusers_count = 0  # 这里可以添加实际的查询逻辑

    # 获取角色统计
    roles, total_roles = await role_service.get_roles(RoleListRequest(page=1, page_size=1), operation_context)

    # 获取用户角色分布（简化版本）
    users_by_role = {
        "管理员": 1,  # 这里可以添加实际的统计逻辑
        "普通用户": total_users - 1,
    }

    # 最近7天登录用户数（简化版本）
    recent_logins = min(total_users, 10)  # 模拟数据

    overview_data = UsersOverviewResponse(
        total_users=total_users,
        active_users=active_users_count,
        inactive_users=inactive_users_count,
        superusers=superusers_count,
        total_roles=total_roles,
        users_by_role=users_by_role,
        recent_logins=recent_logins,
    )

    return BaseResponse(data=overview_data, message="用户概览获取成功")
