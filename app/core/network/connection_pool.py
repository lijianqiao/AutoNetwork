"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: connection_pool.py
@DateTime: 2025/07/25 20:57:23
@Docs: 设备连接池管理器 - 提供连接复用、负载均衡和高效的连接管理功能
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network.connection_manager import DeviceConnection, DeviceConnectionManager
from app.models.device import Device
from app.utils.logger import logger


class ConnectionPoolStats:
    """连接池统计信息"""

    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.connection_errors = 0
        self.active_connections = 0
        self.peak_connections = 0
        self.created_at = datetime.now()

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_requests == 0:
            return 0.0
        return (self.connection_errors / self.total_requests) * 100

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        uptime = datetime.now() - self.created_at
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hit_rate, 2),
            "connection_errors": self.connection_errors,
            "error_rate": round(self.error_rate, 2),
            "active_connections": self.active_connections,
            "peak_connections": self.peak_connections,
            "uptime_seconds": int(uptime.total_seconds()),
            "created_at": self.created_at.isoformat(),
        }


class ConnectionPool:
    """设备连接池"""

    def __init__(
        self,
        max_size: int = 50,
        min_size: int = 5,
        idle_timeout: int = 300,
        max_lifetime: int = 3600,
        health_check_interval: int = 60,
    ):
        self.max_size = max_size
        self.min_size = min_size
        self.idle_timeout = idle_timeout
        self.max_lifetime = max_lifetime
        self.health_check_interval = health_check_interval

        self.connection_manager = DeviceConnectionManager()
        self.stats = ConnectionPoolStats()
        self._pool: dict[UUID, DeviceConnection] = {}
        self._reserved: set[UUID] = set()  # 正在使用的连接
        self._lock = asyncio.Lock()
        self._health_check_task: asyncio.Task | None = None
        self._is_running = False

    async def start(self) -> None:
        """启动连接池"""
        if self._is_running:
            return

        self._is_running = True
        await self.connection_manager.start()

        # 启动健康检查任务
        if not self._health_check_task or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(f"连接池已启动，最大连接数: {self.max_size}，最小连接数: {self.min_size}")

    async def stop(self) -> None:
        """停止连接池"""
        if not self._is_running:
            return

        self._is_running = False

        # 停止健康检查任务
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 关闭所有连接
        await self._close_all_connections()
        await self.connection_manager.stop()

        logger.info("连接池已停止")

    async def get_connection(self, device: Device, dynamic_password: str | None = None) -> DeviceConnection:
        """从连接池获取连接"""
        async with self._lock:
            self.stats.total_requests += 1

            # 检查是否有可用的连接
            if device.id in self._pool and device.id not in self._reserved:
                connection = self._pool[device.id]
                if await self._is_connection_healthy(connection):
                    self._reserved.add(device.id)
                    connection.last_used_at = datetime.now()
                    self.stats.cache_hits += 1
                    logger.debug(f"从连接池获取设备 {device.hostname} 的连接")
                    return connection
                else:
                    # 连接不健康，移除并重新创建
                    await self._remove_connection(device.id)

            # 检查连接池大小限制
            if len(self._pool) >= self.max_size:
                # 尝试清理空闲连接
                await self._cleanup_idle_connections()
                if len(self._pool) >= self.max_size:
                    raise BusinessException("连接池已满，请稍后重试")

            # 创建新连接
            try:
                connection = await self.connection_manager.get_connection(
                    device, dynamic_password, force_reconnect=True
                )
                self._pool[device.id] = connection
                self._reserved.add(device.id)
                self.stats.cache_misses += 1
                self.stats.active_connections = len(self._pool)
                if self.stats.active_connections > self.stats.peak_connections:
                    self.stats.peak_connections = self.stats.active_connections

                logger.info(f"为设备 {device.hostname} 创建新的连接池连接")
                return connection

            except Exception as e:
                self.stats.connection_errors += 1
                logger.error(f"创建设备 {device.hostname} 连接失败: {e}")
                raise

    async def return_connection(self, device_id: UUID) -> None:
        """归还连接到连接池"""
        async with self._lock:
            if device_id in self._reserved:
                self._reserved.remove(device_id)
                logger.debug(f"连接已归还到连接池: {device_id}")

    async def remove_connection(self, device_id: UUID) -> bool:
        """从连接池移除连接"""
        async with self._lock:
            return await self._remove_connection(device_id)

    async def _remove_connection(self, device_id: UUID) -> bool:
        """内部移除连接方法"""
        if device_id in self._pool:
            connection = self._pool[device_id]
            await connection.disconnect()
            del self._pool[device_id]
            self._reserved.discard(device_id)
            self.stats.active_connections = len(self._pool)
            logger.debug(f"从连接池移除连接: {connection.hostname}")
            return True
        return False

    async def _close_all_connections(self) -> None:
        """关闭所有连接"""
        device_ids = list(self._pool.keys())
        for device_id in device_ids:
            await self._remove_connection(device_id)
        self._reserved.clear()
        logger.info("连接池中所有连接已关闭")

    async def _is_connection_healthy(self, connection: DeviceConnection) -> bool:
        """检查连接是否健康"""
        try:
            # 检查连接是否存活
            if not await connection.is_alive():
                return False

            # 检查连接是否超过最大生命周期
            age = datetime.now() - connection.created_at
            if age.total_seconds() > self.max_lifetime:
                logger.debug(f"连接 {connection.hostname} 已超过最大生命周期")
                return False

            return True

        except Exception as e:
            logger.error(f"检查连接 {connection.hostname} 健康状态失败: {e}")
            return False

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                if self._is_running:
                    await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")

    async def _perform_health_check(self) -> None:
        """执行健康检查"""
        async with self._lock:
            unhealthy_connections = []

            for device_id, connection in self._pool.items():
                if device_id not in self._reserved:  # 只检查未使用的连接
                    if not await self._is_connection_healthy(connection):
                        unhealthy_connections.append(device_id)

            # 移除不健康的连接
            for device_id in unhealthy_connections:
                await self._remove_connection(device_id)

            if unhealthy_connections:
                logger.info(f"健康检查移除了 {len(unhealthy_connections)} 个不健康的连接")

    async def _cleanup_idle_connections(self) -> None:
        """清理空闲连接"""
        idle_connections = []

        for device_id, connection in self._pool.items():
            if device_id not in self._reserved and connection.is_idle(self.idle_timeout):
                idle_connections.append(device_id)

        # 保留最小连接数
        connections_to_remove = max(0, len(idle_connections) - (self.max_size - self.min_size))
        if connections_to_remove > 0:
            idle_connections = idle_connections[:connections_to_remove]

        for device_id in idle_connections:
            await self._remove_connection(device_id)

        if idle_connections:
            logger.info(f"清理了 {len(idle_connections)} 个空闲连接")

    def get_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        pool_stats = self.stats.to_dict()
        pool_stats.update(
            {
                "pool_size": len(self._pool),
                "reserved_connections": len(self._reserved),
                "available_connections": len(self._pool) - len(self._reserved),
                "max_size": self.max_size,
                "min_size": self.min_size,
                "idle_timeout": self.idle_timeout,
                "max_lifetime": self.max_lifetime,
                "health_check_interval": self.health_check_interval,
                "is_running": self._is_running,
            }
        )
        return pool_stats

    async def test_connection_stability(self, device: Device, duration: int = 60, interval: int = 10) -> dict[str, Any]:
        """测试连接稳定性"""
        start_time = datetime.now()
        test_results = []
        success_count = 0
        total_tests = 0

        logger.info(f"开始测试设备 {device.hostname} 连接稳定性，持续时间: {duration}秒")

        try:
            # 获取连接
            connection = await self.get_connection(device)

            while (datetime.now() - start_time).total_seconds() < duration:
                test_start = datetime.now()
                total_tests += 1

                try:
                    # 执行简单命令测试连接
                    _ = await connection.execute_command("display version", timeout=5)
                    test_success = True
                    error_msg = None
                    success_count += 1
                except Exception as e:
                    test_success = False
                    error_msg = str(e)

                test_duration = (datetime.now() - test_start).total_seconds()
                test_results.append(
                    {
                        "test_number": total_tests,
                        "timestamp": test_start.isoformat(),
                        "success": test_success,
                        "duration": test_duration,
                        "error_message": error_msg,
                    }
                )

                # 等待下次测试
                if (datetime.now() - start_time).total_seconds() < duration:
                    await asyncio.sleep(interval)

            # 归还连接
            await self.return_connection(device.id)

        except Exception as e:
            logger.error(f"连接稳定性测试失败: {e}")
            test_results.append(
                {
                    "test_number": 1,
                    "timestamp": start_time.isoformat(),
                    "success": False,
                    "duration": 0,
                    "error_message": str(e),
                }
            )
            total_tests = 1

        total_duration = (datetime.now() - start_time).total_seconds()
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0

        return {
            "device_id": str(device.id),
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "test_duration": total_duration,
            "total_tests": total_tests,
            "success_count": success_count,
            "failed_count": total_tests - success_count,
            "success_rate": round(success_rate, 2),
            "test_interval": interval,
            "test_results": test_results,
        }


# 全局连接池实例
_connection_pool: ConnectionPool | None = None


async def get_connection_pool() -> ConnectionPool:
    """获取全局连接池实例"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool()
        await _connection_pool.start()
    return _connection_pool


async def close_connection_pool() -> None:
    """关闭全局连接池"""
    global _connection_pool
    if _connection_pool is not None:
        await _connection_pool.stop()
        _connection_pool = None
