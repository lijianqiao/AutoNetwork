"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/25 20:59:30
@Docs: 网络设备连接管理模块 - 提供基于Scrapli的多品牌设备统一异步SSH连接管理功能
"""

from .authentication_tester import AuthenticationTester, AuthenticationTestResult, BatchTestResult
from .connection_manager import DeviceConnection, DeviceConnectionManager
from .connection_pool import ConnectionPool, ConnectionPoolStats, close_connection_pool, get_connection_pool

__all__ = [
    "DeviceConnection",
    "DeviceConnectionManager",
    "ConnectionPool",
    "ConnectionPoolStats",
    "get_connection_pool",
    "close_connection_pool",
    "AuthenticationTester",
    "AuthenticationTestResult",
    "BatchTestResult",
]
