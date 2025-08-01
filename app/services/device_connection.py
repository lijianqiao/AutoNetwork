"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection.py
@DateTime: 2025/07/25 20:59:51
@Docs: 设备连接管理服务层 - 门面模式统一设备连接管理，委托给核心组件并添加业务逻辑
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network import (
    AuthenticationTester,
    ConnectionPool,
    DeviceConnectionManager,
    get_connection_pool,
)
from app.core.network.exceptions import (
    AuthenticationException,
    DeviceConnectionException,
    NetworkException,
)
from app.dao.device import DeviceDAO
from app.services.authentication import AuthenticationManager
from app.utils.encryption import encrypt_text
from app.utils.logger import logger


class DeviceConnectionService:
    """设备连接管理服务门面 - 委托给核心组件，添加业务逻辑"""

    def __init__(self):
        """初始化服务门面，依赖核心组件"""
        # 核心组件依赖
        self.device_dao = DeviceDAO()
        self.auth_manager = AuthenticationManager()
        self.connection_manager = DeviceConnectionManager(auth_provider=self.auth_manager)

        # 认证测试器 - 核心功能委托对象
        self.auth_tester = AuthenticationTester(
            auth_provider=self.auth_manager,
            connection_provider=self.connection_manager,
            device_dao=self.device_dao,
        )

        # 连接池实例
        self._connection_pool: ConnectionPool | None = None

    async def get_connection_pool(self) -> ConnectionPool:
        """获取连接池实例"""
        if self._connection_pool is None:
            self._connection_pool = await get_connection_pool()
        return self._connection_pool

    async def test_device_connection(self, device_id: UUID, dynamic_password: str | None = None) -> dict[str, Any]:
        """测试单个设备连接 - 委托给AuthenticationTester并添加业务逻辑"""
        logger.info(f"开始测试设备连接: {device_id}")

        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise DeviceConnectionException(
                    device_info=str(device_id),
                    message="设备不存在",
                    detail={"device_id": str(device_id)},
                )

            # 委托给AuthenticationTester执行核心测试逻辑
            result = await self.auth_tester.test_single_device(device, dynamic_password)

            # 添加服务层业务逻辑：更新设备最后连接时间
            if result.success:
                await self._update_device_status(device_id, "online")
                await self._record_connection_log(device_id, result)

            return self._format_connection_result(device, result)

        except Exception as e:
            logger.error(f"测试设备连接失败: {e}")
            if isinstance(e, NetworkException):
                raise
            raise DeviceConnectionException(
                device_info=str(device_id),
                message="测试设备连接失败",
                detail={"error": str(e)},
            ) from e

    async def test_batch_device_connections(
        self,
        device_ids: list[UUID],
        dynamic_passwords: dict[UUID, str] | None = None,
        max_concurrent: int = 10,
    ) -> dict[str, Any]:
        """批量测试设备连接 - 委托给AuthenticationTester并添加业务逻辑"""
        logger.info(f"开始批量测试设备连接，设备数量: {len(device_ids)}")

        try:
            # 委托给AuthenticationTester执行核心批量测试逻辑
            batch_result = await self.auth_tester.test_batch_devices(device_ids, dynamic_passwords, max_concurrent)

            # 添加服务层业务逻辑：更新成功连接的设备状态和日志
            successful_device_ids = [result.device_id for result in batch_result.results if result.success]
            if successful_device_ids:
                await self._batch_update_device_status(successful_device_ids, "online")
                await self._batch_record_connection_logs(batch_result.results)

            return batch_result.to_dict()

        except Exception as e:
            logger.error(f"批量测试设备连接失败: {e}")
            if isinstance(e, NetworkException):
                raise
            raise DeviceConnectionException(
                device_info=f"批量测试({len(device_ids)}个设备)",
                message="批量测试设备连接失败",
                detail={"device_count": len(device_ids), "error": str(e)},
            ) from e

    async def test_connection_stability(
        self, device_id: UUID, duration: int = 60, interval: int = 10
    ) -> dict[str, Any]:
        """测试设备连接稳定性"""
        logger.info(f"开始测试设备连接稳定性: {device_id}，持续时间: {duration}秒")

        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessException(f"设备不存在: {device_id}")

            # 获取连接池
            pool = await self.get_connection_pool()

            # 执行稳定性测试
            result = await pool.test_connection_stability(device, duration, interval)

            return result

        except Exception as e:
            logger.error(f"测试设备连接稳定性失败: {e}")
            raise BusinessException(f"测试设备连接稳定性失败: {e}") from e

    async def execute_command(
        self, device_id: UUID, command: str, dynamic_password: str | None = None, timeout: int | None = None
    ) -> dict[str, Any]:
        """在设备上执行命令 - 委托给ConnectionManager"""
        logger.info(f"在设备 {device_id} 上执行命令: {command}")

        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessException(f"设备不存在: {device_id}")

            # 委托给ConnectionManager执行命令
            result = await self.connection_manager.execute_device_command(device, command, dynamic_password, timeout)

            return {
                "device_id": str(device_id),
                "command": command,
                "success": result.get("success", False),
                "output": result.get("output", ""),
                "elapsed_time": result.get("elapsed_time", 0.0),
                "error_message": result.get("error_message"),
                "executed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"执行设备命令失败: {device_id}, 命令: {command}, 错误: {e}")
            return {
                "device_id": str(device_id),
                "command": command,
                "success": False,
                "output": "",
                "elapsed_time": 0.0,
                "error_message": str(e),
                "executed_at": datetime.now().isoformat(),
            }

    async def get_device_credentials(self, device_id: UUID, dynamic_password: str | None = None) -> dict[str, Any]:
        """获取设备认证凭据 - 委托给AuthenticationManager"""
        try:
            credentials = await self.auth_manager.get_device_credentials(device_id, dynamic_password)

            return {
                "device_id": str(device_id),
                "username": credentials.username,
                "auth_type": credentials.auth_type,
                "ssh_port": credentials.ssh_port,
                "snmp_community": credentials.snmp_community,
                # 注意：不返回明文密码
                "has_password": bool(credentials.password),
            }

        except Exception as e:
            logger.error(f"获取设备认证凭据失败: {e}")
            if isinstance(e, NetworkException):
                raise
            raise AuthenticationException(
                device_info=str(device_id),
                message="获取设备认证凭据失败",
                detail={"error": str(e)},
            ) from e

    async def encrypt_device_password(self, password: str) -> dict[str, str]:
        """加密设备密码"""
        try:
            encrypted_password = encrypt_text(password)
            return {
                "encrypted_password": encrypted_password,
                "encryption_status": "success",
            }
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise NetworkException(f"密码加密失败: {e}") from e

    async def get_connection_pool_stats(self) -> dict[str, Any]:
        """获取连接池统计信息"""
        try:
            pool = await self.get_connection_pool()
            return pool.get_stats()
        except Exception as e:
            logger.error(f"获取连接池统计信息失败: {e}")
            raise NetworkException(f"获取连接池统计信息失败: {e}") from e

    async def get_connection_manager_stats(self) -> dict[str, Any]:
        """获取连接管理器统计信息 - 委托给ConnectionManager"""
        try:
            return await self.connection_manager.get_connection_stats()
        except Exception as e:
            logger.error(f"获取连接管理器统计信息失败: {e}")
            raise NetworkException(f"获取连接管理器统计信息失败: {e}") from e

    async def cleanup_idle_connections(self, idle_timeout: int | None = None) -> dict[str, Any]:
        """清理空闲连接"""
        try:
            pool = await self.get_connection_pool()

            # 获取清理前的统计信息
            stats_before = pool.get_stats()
            connections_before = stats_before["pool_size"]

            # 执行清理
            await pool._cleanup_idle_connections()

            # 获取清理后的统计信息
            stats_after = pool.get_stats()
            connections_after = stats_after["pool_size"]

            cleaned_count = connections_before - connections_after

            logger.info(f"清理空闲连接完成，清理数量: {cleaned_count}")

            return {
                "cleaned_connections": cleaned_count,
                "connections_before": connections_before,
                "connections_after": connections_after,
                "cleanup_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"清理空闲连接失败: {e}")
            raise NetworkException(f"清理空闲连接失败: {e}") from e

    async def close_device_connection(self, device_id: UUID) -> dict[str, Any]:
        """关闭指定设备连接 - 委托给连接池和连接管理器"""
        try:
            # 从连接池中移除
            pool = await self.get_connection_pool()
            pool_removed = await pool.remove_connection(device_id)

            # 从连接管理器中移除
            manager_removed = await self.connection_manager.close_connection(device_id)

            logger.info(f"关闭设备连接: {device_id}")

            return {
                "device_id": str(device_id),
                "pool_removed": pool_removed,
                "manager_removed": manager_removed,
                "closed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"关闭设备连接失败: {e}")
            raise DeviceConnectionException(
                device_info=str(device_id),
                message="关闭设备连接失败",
                detail={"error": str(e)},
            ) from e

    async def start_connection_pool(self) -> dict[str, Any]:
        """启动连接池"""
        try:
            pool = await self.get_connection_pool()
            await pool.start()

            logger.info("连接池已启动")

            return {
                "status": "started",
                "started_at": datetime.now().isoformat(),
                "pool_config": {
                    "max_size": pool.max_size,
                    "min_size": pool.min_size,
                    "idle_timeout": pool.idle_timeout,
                    "max_lifetime": pool.max_lifetime,
                },
            }

        except Exception as e:
            logger.error(f"启动连接池失败: {e}")
            raise NetworkException(f"启动连接池失败: {e}") from e

    async def stop_connection_pool(self) -> dict[str, Any]:
        """停止连接池"""
        try:
            if self._connection_pool:
                await self._connection_pool.stop()
                self._connection_pool = None

            logger.info("连接池已停止")

            return {
                "status": "stopped",
                "stopped_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"停止连接池失败: {e}")
            raise NetworkException(f"停止连接池失败: {e}") from e

    async def validate_device_credentials(
        self, device_id: UUID, username: str, password: str, ssh_port: int = 22
    ) -> dict[str, Any]:
        """验证设备认证凭据 - 委托给AuthenticationTester"""
        try:
            result = await self.auth_tester.validate_credentials(device_id, username, password, ssh_port)

            return {
                "device_id": str(device_id),
                "validation_success": result.success,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "platform": result.platform,
                "tested_at": result.tested_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"验证设备认证凭据失败: {e}")
            if isinstance(e, NetworkException):
                raise
            raise AuthenticationException(
                device_info=str(device_id),
                message="验证设备认证凭据失败",
                detail={"error": str(e)},
            ) from e

    async def test_devices_by_criteria(
        self,
        vendor_id: UUID | None = None,
        region_id: UUID | None = None,
        device_type: str | None = None,
        network_layer: str | None = None,
        is_active: bool = True,
        max_concurrent: int = 10,
    ) -> dict[str, Any]:
        """根据条件批量测试设备 - 委托给AuthenticationTester并添加业务逻辑"""
        try:
            batch_result = await self.auth_tester.test_devices_by_criteria(
                vendor_id=vendor_id,
                region_id=region_id,
                device_type=device_type,
                network_layer=network_layer,
                is_active=is_active,
                max_concurrent=max_concurrent,
            )

            # 添加服务层业务逻辑：更新成功连接的设备状态和日志
            successful_device_ids = [result.device_id for result in batch_result.results if result.success]
            if successful_device_ids:
                await self._batch_update_device_status(successful_device_ids, "online")
                await self._batch_record_connection_logs(batch_result.results)

            return batch_result.to_dict()

        except Exception as e:
            logger.error(f"根据条件批量测试设备失败: {e}")
            if isinstance(e, NetworkException):
                raise
            raise DeviceConnectionException(
                device_info="批量测试(按条件)",
                message="根据条件批量测试设备失败",
                detail={"error": str(e)},
            ) from e

    def clear_dynamic_password_cache(self, device_id: UUID | None = None) -> dict[str, Any]:
        """清除动态密码缓存 - 委托给AuthenticationManager"""
        try:
            cache_count_before = self.auth_manager.get_cached_password_count()
            self.auth_manager.clear_dynamic_password_cache(device_id)
            cache_count_after = self.auth_manager.get_cached_password_count()

            cleared_count = cache_count_before - cache_count_after

            logger.info(f"清除动态密码缓存，清除数量: {cleared_count}")

            return {
                "cleared_count": cleared_count,
                "cache_count_before": cache_count_before,
                "cache_count_after": cache_count_after,
                "device_id": str(device_id) if device_id else None,
                "cleared_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"清除动态密码缓存失败: {e}")
            raise NetworkException(f"清除动态密码缓存失败: {e}") from e

    def get_cached_password_info(self) -> dict[str, Any]:
        """获取缓存密码信息 - 委托给AuthenticationManager"""
        try:
            cache_count = self.auth_manager.get_cached_password_count()

            return {
                "cached_password_count": cache_count,
                "cache_status": "active" if cache_count > 0 else "empty",
                "checked_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取缓存密码信息失败: {e}")
            raise NetworkException(f"获取缓存密码信息失败: {e}") from e

    async def get_test_statistics(self, device_ids: list[UUID] | None = None) -> dict[str, Any]:
        """获取测试统计信息"""
        try:
            if device_ids:
                # 获取指定设备的测试结果
                devices = await self.device_dao.get_by_ids(device_ids)
                results = []
                for device in devices:
                    result = await self.auth_tester.test_single_device(device)
                    results.append(result)
            else:
                # 获取所有活跃设备的测试结果
                devices = await self.device_dao.get_all(filters={"is_active": True})
                results = []
                for device in devices[:50]:  # 限制数量避免过多请求
                    result = await self.auth_tester.test_single_device(device)
                    results.append(result)

            statistics = self.auth_tester.get_test_statistics(results)

            return {
                "statistics": statistics,
                "generated_at": datetime.now().isoformat(),
                "sample_size": len(results),
            }

        except Exception as e:
            logger.error(f"获取测试统计信息失败: {e}")
            raise NetworkException(f"获取测试统计信息失败: {e}") from e

    # ==================== 私有辅助方法 - 服务层业务逻辑 ====================

    async def _update_device_status(self, device_id: UUID, status: str) -> None:
        """更新设备状态"""
        try:
            await self.device_dao.update_last_connected(device_id)
            logger.debug(f"更新设备状态: {device_id} -> {status}")
        except Exception as e:
            logger.warning(f"更新设备状态失败: {device_id}, {e}")

    async def _record_connection_log(self, device_id: UUID, result) -> None:
        """记录连接日志"""
        try:
            # TODO: 集成操作日志服务记录连接操作
            logger.debug(f"记录连接日志: {device_id}, 成功={result.success}")
        except Exception as e:
            logger.warning(f"记录连接日志失败: {device_id}, {e}")

    def _format_connection_result(self, device, result) -> dict[str, Any]:
        """格式化连接测试结果"""
        return {
            "device_id": str(device.id),
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "success": result.success,
            "execution_time": result.execution_time,
            "error_message": result.error_message,
            "platform": result.platform,
            "auth_type": result.auth_type,
            "tested_at": result.tested_at.isoformat(),
        }

    async def _batch_update_device_status(self, device_ids: list[UUID], status: str) -> None:
        """批量更新设备状态"""
        try:
            for device_id in device_ids:
                await self.device_dao.update_last_connected(device_id)
            logger.debug(f"批量更新设备状态: {len(device_ids)}个设备 -> {status}")
        except Exception as e:
            logger.warning(f"批量更新设备状态失败: {e}")

    async def _batch_record_connection_logs(self, results: list) -> None:
        """批量记录连接日志"""
        try:
            # TODO: 集成操作日志服务批量记录连接操作
            success_count = sum(1 for result in results if result.success)
            logger.debug(f"批量记录连接日志: {len(results)}个结果, 成功={success_count}")
        except Exception as e:
            logger.warning(f"批量记录连接日志失败: {e}")
