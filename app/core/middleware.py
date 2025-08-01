"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: middleware.py
@DateTime: 2025/07/05
@Docs: 中间件配置
"""

import time
import uuid
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.exceptions import RateLimitException
from app.utils.logger import logger


# 简单的内存限流器
class RateLimiter:
    """简单的内存限流器"""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str, limit: int = 60, window: int = 60) -> bool:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - window

        # 清理过期的记录
        self._requests[client_ip] = [req_time for req_time in self._requests[client_ip] if req_time > window_start]

        # 检查是否超出限制
        if len(self._requests[client_ip]) >= limit:
            return False

        # 记录本次请求
        self._requests[client_ip].append(now)
        return True


# 全局限流器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理限流逻辑"""
        client_ip = request.client.host if request.client else "unknown"

        if not rate_limiter.is_allowed(client_ip, settings.RATE_LIMIT_PER_MINUTE):
            logger.warning(f"IP 地址的速率限制已超过： {client_ip}")
            raise RateLimitException(detail="请求过于频繁，请稍后再试")

        return await call_next(request)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}]")

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"Request finished: {request.method} {request.url.path} Status: {response.status_code} [ID: {request_id}]"
        )
        return response


def setup_middlewares(app: FastAPI) -> None:
    """
    注册中间件
    """
    # CORS 中间件，处理跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip 压缩中间件，减少响应体大小
    if settings.ENABLE_GZIP:
        app.add_middleware(GZipMiddleware, minimum_size=settings.GZIP_MINIMUM_SIZE)

    # Session 中间件，用于管理用户会话
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # 请求日志中间件
    app.add_middleware(RequestLoggerMiddleware)

    # 安全中间件（生产环境）
    if settings.IS_PRODUCTION and settings.ENABLE_TRUSTED_HOST and settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    if settings.IS_PRODUCTION and settings.ENABLE_HTTPS_REDIRECT:
        app.add_middleware(HTTPSRedirectMiddleware)

    # 限流中间件
    app.add_middleware(RateLimitMiddleware)
