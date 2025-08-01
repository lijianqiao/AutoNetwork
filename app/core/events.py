"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: events.py
@DateTime: 2025/03/08 04:35:00
@Docs: 应用程序事件管理
"""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from tortoise import Tortoise

from app.core.config import settings
from app.utils.logger import logger
from app.utils.permission_cache_utils import clear_all_permission_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期上下文管理器

    Args:
        app (FastAPI): FastAPI应用实例
    """
    # 启动事件
    await startup(app)

    # 生命周期运行
    yield

    # 关闭事件
    await shutdown(app)


async def startup(app: FastAPI) -> None:
    """应用程序启动事件

    Args:
        app (FastAPI): FastAPI应用实例
    """
    logger.info(f"应用程序 {settings.APP_NAME} 正在启动...")

    # 初始化数据库连接
    await init_db()

    # 初始化Redis连接
    await init_redis(app)

    # 初始化权限缓存
    await init_permission_cache()

    # 初始化设备连接池
    await init_device_connection_pool()

    # 初始化CLI会话管理器
    await init_cli_session_manager()

    logger.info(f"应用程序 {settings.APP_NAME} 启动完成")


async def shutdown(app: FastAPI) -> None:
    """应用程序关闭事件

    Args:
        app (FastAPI): FastAPI应用实例
    """
    logger.info(f"应用程序 {settings.APP_NAME} 正在关闭...")

    # 关闭数据库连接
    await close_db()

    # 关闭设备连接池
    await close_device_connection_pool()

    # 关闭CLI会话管理器
    await close_cli_session_manager()

    # 关闭Redis连接
    await clear_all_permission_cache()  # 清除权限缓存
    await close_redis(app)

    logger.info(f"应用程序 {settings.APP_NAME} 已关闭")


async def init_db() -> None:
    """初始化数据库连接"""
    try:
        logger.info("正在初始化数据库连接...")
        await Tortoise.init(config=settings.TORTOISE_ORM_CONFIG)
        logger.info("数据库连接初始化完成")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise


async def close_db() -> None:
    """关闭数据库连接"""
    try:
        logger.info("正在关闭数据库连接...")
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


# Redis 连接管理
async def init_redis(app: FastAPI) -> None:
    """初始化Redis连接"""
    logger.info("正在初始化Redis连接...")
    try:
        # 从 settings.REDIS_URI 创建连接池
        # 注意: redis-py 的 from_url 不直接返回连接池，而是返回一个 Redis 实例，该实例内部管理连接。
        # 对于简单的场景，直接使用这个实例即可。如果需要精细控制连接池，可以使用 redis.asyncio.ConnectionPool
        app.state.redis = redis.from_url(
            settings.REDIS_URI,
            encoding="utf-8",
            decode_responses=True,  # 通常希望自动解码响应
        )
        # 测试连接
        await app.state.redis.ping()
        logger.info("Redis连接初始化完成并通过ping测试")
    except Exception as e:
        logger.error(f"Redis连接初始化失败: {e}")
        app.state.redis = None  # 明确设置redis状态为None


async def close_redis(app: FastAPI) -> None:
    """关闭Redis连接"""
    logger.info("正在关闭Redis连接...")
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.close()  # 关闭连接
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接时出错: {e}")
    else:
        logger.info("没有活动的Redis连接需要关闭")


async def init_permission_cache() -> None:
    """初始化权限缓存系统"""
    try:
        logger.info("正在初始化权限缓存系统...")
        from app.utils.redis_cache import get_redis_cache

        # 测试Redis缓存是否可用
        cache = await get_redis_cache()
        test_key = "permission:cache:test"
        test_value = {"test": "permissions"}

        # 测试缓存操作
        await cache.set(test_key, test_value, 60)  # 设置60秒TTL
        cached_value = await cache.get(test_key)

        if cached_value and cached_value.get("test") == "permissions":
            logger.info("权限缓存系统初始化成功，Redis缓存工作正常")
            # 清除测试数据
            await cache.delete(test_key)
        else:
            logger.warning("权限缓存系统测试失败，将使用内存缓存作为备用方案")

        # 获取缓存统计
        from app.utils.permission_cache_utils import get_permission_cache_stats

        stats = await get_permission_cache_stats()
        logger.info(f"权限缓存统计: {stats}")

    except Exception as e:
        logger.error(f"权限缓存系统初始化失败: {e}")
        logger.info("将使用内存缓存作为备用方案")


async def init_device_connection_pool() -> None:
    """初始化设备连接池"""
    try:
        logger.info("正在初始化设备连接池...")
        from app.core.network import get_connection_pool

        # 获取全局连接池实例
        pool = await get_connection_pool()
        await pool.start()

        logger.info("设备连接池初始化完成")

    except Exception as e:
        logger.error(f"设备连接池初始化失败: {e}")
        logger.info("设备连接池将在首次使用时延迟初始化")


async def close_device_connection_pool() -> None:
    """关闭设备连接池"""
    try:
        logger.info("正在关闭设备连接池...")
        from app.core.network import close_connection_pool

        # 关闭全局连接池
        await close_connection_pool()

        logger.info("设备连接池已关闭")

    except Exception as e:
        logger.error(f"关闭设备连接池时出错: {e}")


async def init_cli_session_manager() -> None:
    """初始化CLI会话管理器"""
    try:
        logger.info("正在初始化CLI会话管理器...")
        from app.core.network.websocket_cli import start_cli_session_manager

        # 启动全局CLI会话管理器
        await start_cli_session_manager()

        logger.info("CLI会话管理器初始化完成")

    except Exception as e:
        logger.error(f"CLI会话管理器初始化失败: {e}")
        logger.info("CLI会话管理器将在首次使用时延迟初始化")


async def close_cli_session_manager() -> None:
    """关闭CLI会话管理器"""
    try:
        logger.info("正在关闭CLI会话管理器...")
        from app.core.network.websocket_cli import stop_cli_session_manager

        # 关闭全局CLI会话管理器
        await stop_cli_session_manager()

        logger.info("CLI会话管理器已关闭")

    except Exception as e:
        logger.error(f"关闭CLI会话管理器时出错: {e}")
