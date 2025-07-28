"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: connection_manager.py
@DateTime: 2025/07/25 20:56:45
@Docs: 网络设备连接管理器
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from scrapli import AsyncScrapli
from scrapli.response import Response
from scrapli_community.hp.comware.async_driver import AsyncHPComwareDriver

from app.core.exceptions import BusinessException
from app.core.network.config import get_platform_for_vendor, network_config
from app.models.device import Device
from app.models.vendor import Vendor
from app.services.authentication import AuthenticationManager, DeviceCredentials
from app.utils.logger import logger


class DeviceConnection:
    """设备连接对象

    基于Scrapli库实现多品牌设备的统一异步SSH连接管理
    支持自动选择平台标识和自动重连机制
    """

    def __init__(
        self,
        device_id: UUID,
        hostname: str,
        ip_address: str,
        connection: AsyncScrapli | AsyncHPComwareDriver,
        credentials: DeviceCredentials,
        vendor: Vendor,
        platform: str,
    ):
        self.device_id = device_id
        self.hostname = hostname
        self.ip_address = ip_address
        self.connection = connection
        self.credentials = credentials
        self.vendor = vendor
        self.platform = platform
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self.is_connected = False
        self.retry_count = 0
        self.max_retries = network_config.connection.MAX_RETRY_ATTEMPTS
        self.connection_lifetime = network_config.connection_pool.MAX_CONNECTION_LIFETIME
        self._lock = asyncio.Lock()
        self._command_count = 0
        self._last_health_check = datetime.now()

    async def connect(self) -> bool:
        """建立连接"""
        async with self._lock:
            try:
                if not self.is_connected:
                    await self.connection.open()
                    self.is_connected = True
                    self.retry_count = 0
                    logger.info(f"设备 {self.hostname} 连接成功")
                return True
            except Exception as e:
                self.is_connected = False
                self.retry_count += 1
                auth_details = {
                    "username": self.credentials.username,
                    "auth_type": self.credentials.auth_type,
                    "ssh_port": self.credentials.ssh_port,
                }
                logger.error(f"设备 {self.hostname} 连接失败: {e}, 认证参数: {auth_details}")
                return False

    async def disconnect(self) -> None:
        """断开连接"""
        async with self._lock:
            try:
                if self.is_connected and self.connection.isalive():
                    await self.connection.close()
                self.is_connected = False
                logger.info(f"设备 {self.hostname} 连接已断开")
            except Exception as e:
                logger.error(f"设备 {self.hostname} 断开连接时出错: {e}")
                self.is_connected = False

    async def execute_command(self, command: str, timeout: int | None = None) -> Response:
        """执行命令"""
        async with self._lock:
            if not self.is_connected:
                if not await self.connect():
                    raise BusinessException(f"设备 {self.hostname} 连接失败")

            try:
                self.last_used_at = datetime.now()
                self._command_count += 1

                # 使用配置的超时时间
                cmd_timeout = timeout or network_config.connection.COMMAND_TIMEOUT
                response = await self.connection.send_command(command, timeout_ops=cmd_timeout)

                logger.debug(f"设备 {self.hostname} 执行命令成功: {command[:50]}...")
                return response
            except Exception as e:
                logger.error(f"设备 {self.hostname} 执行命令失败: {e}")
                self.is_connected = False
                raise BusinessException(f"设备 {self.hostname} 执行命令失败: {e}") from e

    async def is_alive(self) -> bool:
        """检查连接是否存活"""
        try:
            if not self.is_connected:
                return False
            return self.connection.isalive()
        except Exception:
            self.is_connected = False
            return False

    def should_retry(self) -> bool:
        """是否应该重试连接"""
        return self.retry_count < self.max_retries

    def is_idle(self, idle_timeout: int | None = None) -> bool:
        """检查连接是否空闲"""
        timeout = idle_timeout or network_config.connection_pool.IDLE_CONNECTION_TIMEOUT
        idle_time = datetime.now() - self.last_used_at
        return idle_time.total_seconds() > timeout

    def is_expired(self) -> bool:
        """检查连接是否过期"""
        lifetime = datetime.now() - self.created_at
        return lifetime.total_seconds() > self.connection_lifetime

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.is_connected:
                return False

            # 检查连接是否存活
            if not self.connection.isalive():
                self.is_connected = False
                return False

            # 定期执行健康检查命令
            now = datetime.now()
            check_interval = network_config.connection_pool.HEALTH_CHECK_INTERVAL
            if (now - self._last_health_check).total_seconds() > check_interval:
                try:
                    await self.execute_command("show version | include uptime", timeout=10)
                    self._last_health_check = now
                except Exception:
                    self.is_connected = False
                    return False

            return True
        except Exception:
            self.is_connected = False
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取连接统计信息"""
        return {
            "device_id": str(self.device_id),
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "platform": self.platform,
            "is_connected": self.is_connected,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "command_count": self._command_count,
            "retry_count": self.retry_count,
            "is_idle": self.is_idle(),
            "is_expired": self.is_expired(),
        }


class DeviceConnectionManager:
    """设备连接管理器"""

    def __init__(self):
        self.connections: dict[UUID, DeviceConnection] = {}
        self.auth_manager = AuthenticationManager()
        self._cleanup_task: asyncio.Task | None = None
        self._health_check_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._connection_semaphore = asyncio.Semaphore(network_config.concurrency.MAX_CONCURRENT_CONNECTIONS)

        # 统计信息
        self._stats = {
            "total_connections_created": 0,
            "total_connections_closed": 0,
            "total_commands_executed": 0,
            "connection_failures": 0,
            "last_cleanup_time": None,
            "last_health_check_time": None,
        }

    async def start(self) -> None:
        """启动连接管理器"""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        if not self._health_check_task or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("设备连接管理器已启动")

    async def stop(self) -> None:
        """停止连接管理器"""
        # 取消后台任务
        for task in [self._cleanup_task, self._health_check_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # 关闭所有连接
        await self.close_all_connections()
        logger.info("设备连接管理器已停止")

    async def get_connection(
        self, device: Device, dynamic_password: str | None = None, force_reconnect: bool = False
    ) -> DeviceConnection:
        """获取设备连接"""
        # 使用信号量控制并发连接数
        async with self._connection_semaphore:
            async with self._lock:
                # 检查是否已存在连接
                if device.id in self.connections and not force_reconnect:
                    connection = self.connections[device.id]
                    if await connection.is_alive() and not connection.is_expired():
                        connection.last_used_at = datetime.now()
                        return connection
                    else:
                        # 连接已断开或过期，移除并重新创建
                        await self._remove_connection(device.id)

                # 检查连接数限制
                max_connections = network_config.connection_pool.MAX_POOL_SIZE
                if len(self.connections) >= max_connections:
                    await self._cleanup_idle_connections()
                    if len(self.connections) >= max_connections:
                        raise BusinessException("连接数已达到上限，请稍后重试")

                # 创建新连接
                connection = await self._create_connection(device, dynamic_password)
                self.connections[device.id] = connection
                self._stats["total_connections_created"] += 1
                return connection

    async def _create_connection(self, device: Device, dynamic_password: str | None = None) -> DeviceConnection:
        """创建设备连接"""
        try:
            # 获取设备认证凭据
            credentials = await self.auth_manager.get_device_credentials(device.id, dynamic_password)

            # 获取厂商信息
            vendor = await device.vendor
            if not vendor:
                raise BusinessException(f"设备 {device.hostname} 缺少厂商信息")

            # 确定Scrapli平台
            platform = self._get_scrapli_platform(vendor)

            # 创建优化的Scrapli连接配置
            scrapli_config = {
                "host": device.ip_address,
                "auth_username": credentials.username,
                "auth_password": credentials.password,
                "auth_strict_key": network_config.security.ENABLE_CONNECTION_ENCRYPTION,
                "ssh_config_file": network_config.connection.SSH_CONFIG_FILE,
                "timeout_socket": network_config.connection.CONNECT_TIMEOUT,
                "timeout_transport": network_config.connection.CONNECT_TIMEOUT,
                "port": credentials.ssh_port,
                "platform": platform,
                "transport": "asyncssh",  # 使用asyncssh传输层
                "timeout_ops": network_config.connection.COMMAND_TIMEOUT,
                "transport_options": {
                    "known_hosts": None,  # 禁用known_hosts检查，提高连接速度
                    "server_host_key_algs": [],  # 禁用服务器主机密钥算法检查
                    "client_keys": [],  # 不使用客户端密钥
                    "compression_algs": [],  # 禁用压缩，减少CPU开销
                },
            }

            scrapli_conn = AsyncScrapli(**scrapli_config)

            # 创建设备连接对象
            connection = DeviceConnection(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                connection=scrapli_conn,
                credentials=credentials,
                vendor=vendor,
                platform=platform,
            )

            logger.info(f"为设备 {device.hostname} 创建连接，平台: {platform}")
            return connection

        except Exception as e:
            self._stats["connection_failures"] += 1
            logger.error(f"创建设备 {device.hostname} 连接失败: {e}")
            raise BusinessException(f"创建设备连接失败: {e}") from e

    def _get_scrapli_platform(self, vendor: Vendor) -> str:
        """获取Scrapli平台标识"""
        # 优先使用厂商配置的平台标识
        if vendor.scrapli_platform:
            return vendor.scrapli_platform

        # 根据厂商代码自动映射
        platform = get_platform_for_vendor(vendor.vendor_code)
        if platform != network_config.scrapli_platform.DEFAULT_PLATFORM:
            return platform

        # 默认使用通用平台
        logger.warning(f"未找到厂商 {vendor.vendor_code} 的平台映射，使用默认平台: {platform}")
        return platform

    async def close_connection(self, device_id: UUID) -> bool:
        """关闭指定设备连接"""
        async with self._lock:
            return await self._remove_connection(device_id)

    async def _remove_connection(self, device_id: UUID) -> bool:
        """移除连接"""
        if device_id in self.connections:
            connection = self.connections[device_id]
            await connection.disconnect()
            del self.connections[device_id]
            self._stats["total_connections_closed"] += 1
            logger.info(f"设备 {connection.hostname} 连接已移除")
            return True
        return False

    async def close_all_connections(self) -> None:
        """关闭所有连接"""
        async with self._lock:
            device_ids = list(self.connections.keys())
            for device_id in device_ids:
                await self._remove_connection(device_id)
            logger.info("所有设备连接已关闭")

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            try:
                cleanup_interval = network_config.connection_pool.CLEANUP_INTERVAL
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_idle_connections()
                self._stats["last_cleanup_time"] = datetime.now().isoformat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"连接清理循环出错: {e}")

    async def _cleanup_idle_connections(self) -> None:
        """清理空闲连接"""
        async with self._lock:
            idle_connections = []
            expired_connections = []

            for device_id, connection in self.connections.items():
                if connection.is_expired():
                    expired_connections.append(device_id)
                elif connection.is_idle() or not await connection.is_alive():
                    idle_connections.append(device_id)

            # 清理过期连接
            for device_id in expired_connections:
                await self._remove_connection(device_id)

            # 清理空闲连接
            for device_id in idle_connections:
                await self._remove_connection(device_id)

            total_cleaned = len(idle_connections) + len(expired_connections)
            if total_cleaned > 0:
                logger.info(
                    f"清理了 {total_cleaned} 个连接 (空闲: {len(idle_connections)}, 过期: {len(expired_connections)})"
                )

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while True:
            try:
                check_interval = network_config.connection_pool.HEALTH_CHECK_INTERVAL
                await asyncio.sleep(check_interval)
                await self._perform_health_checks()
                self._stats["last_health_check_time"] = datetime.now().isoformat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")

    async def _perform_health_checks(self) -> None:
        """执行健康检查"""
        async with self._lock:
            unhealthy_connections = []

            for device_id, connection in self.connections.items():
                if not await connection.health_check():
                    unhealthy_connections.append(device_id)

            # 移除不健康的连接
            for device_id in unhealthy_connections:
                await self._remove_connection(device_id)

            if unhealthy_connections:
                logger.info(f"健康检查移除了 {len(unhealthy_connections)} 个不健康连接")

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息"""
        total_connections = len(self.connections)
        active_connections = 0
        idle_connections = 0
        expired_connections = 0
        connected_count = 0
        total_commands = 0

        platforms = {}
        vendors = {}

        for connection in self.connections.values():
            if connection.is_expired():
                expired_connections += 1
            elif connection.is_idle():
                idle_connections += 1
            else:
                active_connections += 1

            if connection.is_connected:
                connected_count += 1

            total_commands += connection._command_count

            # 统计平台分布
            platform = connection.platform
            platforms[platform] = platforms.get(platform, 0) + 1

            # 统计厂商分布
            vendor = connection.vendor.vendor_code
            vendors[vendor] = vendors.get(vendor, 0) + 1

        return {
            "current_connections": {
                "total": total_connections,
                "active": active_connections,
                "idle": idle_connections,
                "expired": expired_connections,
                "connected": connected_count,
            },
            "lifetime_stats": self._stats.copy(),
            "configuration": {
                "max_pool_size": network_config.connection_pool.MAX_POOL_SIZE,
                "max_concurrent_connections": network_config.concurrency.MAX_CONCURRENT_CONNECTIONS,
                "cleanup_interval": network_config.connection_pool.CLEANUP_INTERVAL,
                "idle_timeout": network_config.connection_pool.IDLE_CONNECTION_TIMEOUT,
                "health_check_interval": network_config.connection_pool.HEALTH_CHECK_INTERVAL,
            },
            "distribution": {
                "platforms": platforms,
                "vendors": vendors,
            },
            "performance": {
                "total_commands_executed": total_commands,
                "avg_commands_per_connection": total_commands / max(total_connections, 1),
            },
        }

    async def test_connection(self, device: Device, dynamic_password: str | None = None) -> dict[str, Any]:
        """测试设备连接 - 优化版本，减少不必要操作"""
        start_time = datetime.now()
        platform = None
        vendor = None

        try:
            # 获取厂商信息用于平台识别
            vendor = await device.vendor
            if vendor:
                platform = self._get_scrapli_platform(vendor)

            # 获取连接
            connection = await self.get_connection(device, dynamic_password, force_reconnect=True)

            # 尝试连接并执行测试命令
            if await connection.connect():
                try:
                    # 使用最优轻量测试命令，减少超时时间
                    test_cmd = self._get_optimal_test_command(platform)
                    response = await connection.execute_command(test_cmd, timeout=3)  # 减少超时时间

                    success = True
                    error_message = None
                    # 不返回完整响应数据，减少传输开销
                    response_data = "连接测试成功" if response else None

                except Exception as cmd_error:
                    success = False
                    error_message = f"命令执行失败: {cmd_error}"
                    response_data = None
            else:
                success = False
                error_message = "连接建立失败"
                response_data = None

            execution_time = (datetime.now() - start_time).total_seconds()

            # 异步更新设备最后连接时间（不等待完成）
            if success:
                asyncio.create_task(self._update_device_last_connected(device.id))

            return {
                "success": success,
                "execution_time": execution_time,
                "error_message": error_message,
                "response_data": response_data,
                "platform": platform,
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                    "device_type": device.device_type,
                    "network_layer": device.network_layer,
                },
                "connection_info": {
                    "ssh_port": device.ssh_port,
                    "auth_type": device.auth_type,
                    "vendor_code": vendor.vendor_code if vendor else None,
                },
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._stats["connection_failures"] += 1

            return {
                "success": False,
                "execution_time": execution_time,
                "error_message": str(e),
                "response_data": None,
                "platform": platform,
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                    "device_type": device.device_type,
                    "network_layer": device.network_layer,
                },
                "connection_info": {
                    "ssh_port": device.ssh_port,
                    "auth_type": device.auth_type,
                    "vendor_code": vendor.vendor_code if vendor else None,
                },
            }
        finally:
            # 确保连接被关闭
            try:
                await self.close_connection(device.id)
            except Exception:
                pass  # 忽略关闭连接时的错误

    async def execute_device_command(
        self, device: Device, command: str, dynamic_password: str | None = None, timeout: int | None = None
    ) -> dict[str, Any]:
        """在设备上执行命令"""
        start_time = datetime.now()

        try:
            # 获取连接
            connection = await self.get_connection(device, dynamic_password)

            # 执行命令
            response = await connection.execute_command(command, timeout)
            self._stats["total_commands_executed"] += 1

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "execution_time": execution_time,
                "command": command,
                "response": response.result if hasattr(response, "result") else str(response),
                "error_message": None,
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                },
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": False,
                "execution_time": execution_time,
                "command": command,
                "response": None,
                "error_message": str(e),
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                },
            }

    def _get_optimal_test_command(self, platform: str | None) -> str:
        """根据平台获取最优的轻量测试命令"""
        test_commands = {
            "hp_comware": "display clock",
            "huawei_vrp": "display clock",
            "cisco_iosxe": "show clock",
            "cisco_ios": "show clock",
            "cisco_nxos": "show clock",
            "juniper_junos": "show system uptime | display terse",
            "arista_eos": "show clock",
            "nokia_sros": "show time",
            "extreme_exos": "show time",
            "mikrotik_routeros": "system clock print",
            "vyos": "show date",
            "linux": "date",
            "generic": "show clock",
        }
        return test_commands.get(platform or "generic", "show clock")

    async def _update_device_last_connected(self, device_id: UUID) -> None:
        """异步更新设备最后连接时间"""
        try:
            from app.dao.device import DeviceDAO

            device_dao = DeviceDAO()
            await device_dao.update_last_connected(device_id)
            logger.debug(f"已更新设备 {device_id} 的最后连接时间")
        except Exception as e:
            logger.warning(f"更新设备最后连接时间失败: {e}")

    async def test_connection_stability(
        self, device: Device, dynamic_password: str | None = None, duration: int | None = None
    ) -> dict[str, Any]:
        """测试连接稳定性"""
        test_duration = duration or network_config.connection_pool.STABILITY_TEST_DURATION
        test_interval = network_config.connection_pool.STABILITY_TEST_INTERVAL

        # 获取设备厂商信息用于选择最优测试命令
        vendor = await device.vendor
        platform = self._get_scrapli_platform(vendor) if vendor else None
        test_command = self._get_optimal_test_command(platform)

        start_time = datetime.now()
        test_results = []
        connection = None

        try:
            # 获取连接
            connection = await self.get_connection(device, dynamic_password)

            # 连接测试
            if not await connection.connect():
                return {
                    "success": False,
                    "error_message": "初始连接失败",
                    "test_results": [],
                    "statistics": {},
                }

            # 执行稳定性测试
            test_count = 0
            success_count = 0

            while (datetime.now() - start_time).total_seconds() < test_duration:
                test_start = datetime.now()
                test_count += 1

                try:
                    _ = await connection.execute_command(test_command, timeout=10)
                    test_success = True
                    error_msg = None
                    success_count += 1
                except Exception as e:
                    test_success = False
                    error_msg = str(e)

                test_time = (datetime.now() - test_start).total_seconds()

                test_results.append(
                    {
                        "test_number": test_count,
                        "success": test_success,
                        "execution_time": test_time,
                        "error_message": error_msg,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # 等待下次测试
                if (datetime.now() - start_time).total_seconds() < test_duration:
                    await asyncio.sleep(test_interval)

            total_time = (datetime.now() - start_time).total_seconds()
            success_rate = (success_count / test_count) * 100 if test_count > 0 else 0

            return {
                "success": True,
                "error_message": None,
                "test_results": test_results,
                "statistics": {
                    "total_tests": test_count,
                    "successful_tests": success_count,
                    "failed_tests": test_count - success_count,
                    "success_rate": success_rate,
                    "total_duration": total_time,
                    "average_response_time": sum(r["execution_time"] for r in test_results if r["success"])
                    / max(success_count, 1),
                },
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "test_results": test_results,
                "statistics": {},
                "device_info": {
                    "hostname": device.hostname,
                    "ip_address": device.ip_address,
                },
            }
        finally:
            # 清理连接
            if connection:
                await self.close_connection(device.id)


# 全局连接管理器实例
_global_connection_manager: DeviceConnectionManager | None = None


def get_connection_manager() -> DeviceConnectionManager:
    """获取全局连接管理器实例"""
    global _global_connection_manager
    if _global_connection_manager is None:
        _global_connection_manager = DeviceConnectionManager()
    return _global_connection_manager


async def start_connection_manager() -> None:
    """启动全局连接管理器"""
    manager = get_connection_manager()
    await manager.start()
    logger.info("全局设备连接管理器已启动")


async def stop_connection_manager() -> None:
    """停止全局连接管理器"""
    global _global_connection_manager
    if _global_connection_manager:
        await _global_connection_manager.stop()
        _global_connection_manager = None
        logger.info("全局设备连接管理器已停止")
