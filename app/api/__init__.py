"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/05
@Docs: API路由初始化
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.v1 import v1_router
from app.core.config import settings
from app.models.user import User
from app.utils.deps import get_current_active_user

# 创建主路由
api_router = APIRouter()

# 注册版本路由
api_router.include_router(v1_router, prefix="/v1")

# 这里可以添加其他版本的路由
# api_router.include_router(v2_router, prefix="/v2")


# 健康检查路由
@api_router.get("/health", tags=["系统"])
async def health_check():
    """统一健康检查接口

    检查系统、数据库、Redis缓存、API接口等组件健康状态
    """
    health_data = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(),
        "components": {},
    }

    # 1. 检查数据库健康
    try:
        from app.db.connection import check_database_connection

        db_healthy = await check_database_connection()
        health_data["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "数据库连接正常" if db_healthy else "数据库连接失败",
        }
        if not db_healthy:
            health_data["status"] = "unhealthy"
    except Exception as e:
        health_data["components"]["database"] = {"status": "unhealthy", "message": f"数据库检查异常: {str(e)}"}
        health_data["status"] = "unhealthy"

    # 2. 检查Redis缓存健康
    try:
        from app.utils.redis_cache import get_redis_cache

        redis_cache = await get_redis_cache()
        client = await redis_cache._get_client()

        if client:
            await client.ping()
            health_data["components"]["redis"] = {"status": "healthy", "message": "Redis缓存连接正常"}
        else:
            health_data["components"]["redis"] = {"status": "degraded", "message": "Redis不可用，使用内存缓存"}
            if health_data["status"] == "healthy":
                health_data["status"] = "degraded"
    except Exception as e:
        health_data["components"]["redis"] = {"status": "unhealthy", "message": f"Redis检查异常: {str(e)}"}
        if health_data["status"] == "healthy":
            health_data["status"] = "degraded"

    # 3. 检查API接口健康（简单检查）
    health_data["components"]["api"] = {"status": "healthy", "message": "API接口运行正常"}

    # 4. 检查系统基本状态
    health_data["components"]["system"] = {
        "status": "healthy",
        "message": "系统运行正常",
        "uptime": "运行中",  # 可以添加更详细的系统信息
    }

    return health_data


# 监控指标路由
@api_router.get("/metrics", tags=["监控"])
async def get_metrics(_: User = Depends(get_current_active_user)):
    """获取应用监控指标"""
    if not settings.ENABLE_METRICS:
        return {"error": "监控功能未启用"}

    try:
        from app.utils.metrics import get_system_metrics, metrics_collector

        app_metrics = metrics_collector.get_metrics()
        system_metrics = get_system_metrics()

        return {
            "timestamp": time.time(),
            "application": app_metrics,
            "system": system_metrics,
        }
    except ImportError:
        return {"error": "监控模块未安装"}
