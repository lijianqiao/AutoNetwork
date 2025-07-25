"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: authentication_tester.py
@DateTime: 2025/07/25 20:58:27
@Docs: 设备认证测试器 - 提供设备连接认证测试功能，支持单个和批量测试
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network.connection_manager import DeviceConnectionManager
from app.dao.device import DeviceDAO
from app.models.device import Device
from app.services.authentication import AuthenticationManager
from app.utils.logger import logger


class AuthenticationTestResult:
    """认证测试结果"""

    def __init__(
        self,
        device_id: UUID,
        hostname: str,
        ip_address: str,
        success: bool,
        execution_time: float,
        error_message: str | None = None,
        platform: str | None = None,
        auth_type: str | None = None,
        response_data: str | None = None,
    ):
        self.device_id = device_id
        self.hostname = hostname
        self.ip_address = ip_address
        self.success = success
        self.execution_time = execution_time
        self.error_message = error_message
        self.platform = platform
        self.auth_type = auth_type
        self.response_data = response_data
        self.tested_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "device_id": str(self.device_id),
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "success": self.success,
            "execution_time": round(self.execution_time, 3),
            "error_message": self.error_message,
            "platform": self.platform,
            "auth_type": self.auth_type,
            "response_data": self.response_data,
            "tested_at": self.tested_at.isoformat(),
        }


class BatchTestResult:
    """批量测试结果"""

    def __init__(self):
        self.results: list[AuthenticationTestResult] = []
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.total_count = 0
        self.success_count = 0
        self.failed_count = 0

    def add_result(self, result: AuthenticationTestResult) -> None:
        """添加测试结果"""
        self.results.append(result)
        self.total_count += 1
        if result.success:
            self.success_count += 1
        else:
            self.failed_count += 1

    def finish(self) -> None:
        """完成测试"""
        self.end_time = datetime.now()

    @property
    def total_execution_time(self) -> float:
        """总执行时间"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": round(self.success_rate, 2),
            "total_execution_time": round(self.total_execution_time, 3),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": [result.to_dict() for result in self.results],
        }


class AuthenticationTester:
    """设备认证测试器"""

    def __init__(self):
        self.connection_manager = DeviceConnectionManager()
        self.auth_manager = AuthenticationManager()
        self.device_dao = DeviceDAO()

    async def test_single_device(
        self, device: Device, dynamic_password: str | None = None, test_command: str = "display version"
    ) -> AuthenticationTestResult:
        """测试单个设备认证"""
        start_time = datetime.now()

        try:
            logger.info(f"开始测试设备 {device.hostname} 的认证")

            # 获取设备认证凭据
            credentials = await self.auth_manager.get_device_credentials(device.id, dynamic_password)

            # 获取厂商信息
            vendor = await device.vendor
            if not vendor:
                raise BusinessException(f"设备 {device.hostname} 缺少厂商信息")

            # 测试连接
            test_result = await self.connection_manager.test_connection(device, dynamic_password)

            execution_time = (datetime.now() - start_time).total_seconds()

            result = AuthenticationTestResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=test_result["success"],
                execution_time=execution_time,
                error_message=test_result.get("error_message"),
                platform=test_result.get("platform"),
                auth_type=credentials.auth_type,
                response_data=test_result.get("response_data"),
            )

            if result.success:
                logger.info(f"设备 {device.hostname} 认证测试成功")
            else:
                logger.warning(f"设备 {device.hostname} 认证测试失败: {result.error_message}")

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"设备 {device.hostname} 认证测试异常: {e}")

            return AuthenticationTestResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
                platform=None,
                auth_type=device.auth_type,
                response_data=None,
            )

    async def test_device_by_id(self, device_id: UUID, dynamic_password: str | None = None) -> AuthenticationTestResult:
        """根据设备ID测试认证"""
        device = await self.device_dao.get_by_id(device_id)
        if not device:
            raise BusinessException(f"设备不存在: {device_id}")

        return await self.test_single_device(device, dynamic_password)

    async def test_batch_devices(
        self,
        device_ids: list[UUID],
        dynamic_passwords: dict[UUID, str] | None = None,
        max_concurrent: int = 10,
    ) -> BatchTestResult:
        """批量测试设备认证"""
        logger.info(f"开始批量测试 {len(device_ids)} 个设备的认证")

        batch_result = BatchTestResult()

        # 获取设备信息
        devices = await self.device_dao.get_by_ids(device_ids)
        device_map = {device.id: device for device in devices}

        # 检查缺失的设备
        missing_devices = set(device_ids) - set(device_map.keys())
        if missing_devices:
            logger.warning(f"以下设备不存在: {missing_devices}")

        # 创建测试任务
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        for device_id in device_ids:
            if device_id in device_map:
                device = device_map[device_id]
                dynamic_password = dynamic_passwords.get(device_id) if dynamic_passwords else None
                task = self._test_device_with_semaphore(semaphore, device, dynamic_password)
                tasks.append(task)

        # 执行并发测试
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, AuthenticationTestResult):
                    batch_result.add_result(result)
                elif isinstance(result, Exception):
                    logger.error(f"批量测试中出现异常: {result}")
                    # 为异常创建失败结果
                    batch_result.add_result(
                        AuthenticationTestResult(
                            device_id=UUID("00000000-0000-0000-0000-000000000000"),
                            hostname="Unknown",
                            ip_address="Unknown",
                            success=False,
                            execution_time=0.0,
                            error_message=str(result),
                        )
                    )

        except Exception as e:
            logger.error(f"批量测试执行失败: {e}")
            raise BusinessException(f"批量测试执行失败: {e}") from e

        batch_result.finish()

        logger.info(
            f"批量测试完成，总数: {batch_result.total_count}, "
            f"成功: {batch_result.success_count}, "
            f"失败: {batch_result.failed_count}, "
            f"成功率: {batch_result.success_rate:.2f}%"
        )

        return batch_result

    async def _test_device_with_semaphore(
        self, semaphore: asyncio.Semaphore, device: Device, dynamic_password: str | None = None
    ) -> AuthenticationTestResult:
        """使用信号量限制并发的设备测试"""
        async with semaphore:
            return await self.test_single_device(device, dynamic_password)

    async def test_devices_by_criteria(
        self,
        vendor_id: UUID | None = None,
        region_id: UUID | None = None,
        device_type: str | None = None,
        network_layer: str | None = None,
        is_active: bool = True,
        max_concurrent: int = 10,
    ) -> BatchTestResult:
        """根据条件批量测试设备"""
        # 构建查询条件
        filters: dict[str, Any] = {"is_active": is_active}
        if vendor_id:
            filters["vendor_id"] = vendor_id
        if region_id:
            filters["region_id"] = region_id
        if device_type:
            filters["device_type"] = device_type
        if network_layer:
            filters["network_layer"] = network_layer

        # 获取符合条件的设备
        devices = await self.device_dao.get_all(filters=filters)
        device_ids = [device.id for device in devices]

        logger.info(f"根据条件找到 {len(device_ids)} 个设备进行测试")

        if not device_ids:
            batch_result = BatchTestResult()
            batch_result.finish()
            return batch_result

        return await self.test_batch_devices(device_ids, max_concurrent=max_concurrent)

    async def validate_credentials(
        self, device_id: UUID, username: str, password: str, ssh_port: int = 22
    ) -> AuthenticationTestResult:
        """验证指定的认证凭据"""
        start_time = datetime.now()

        try:
            device = await self.device_dao.get_by_id(device_id)
            if not device:
                raise BusinessException(f"设备不存在: {device_id}")

            vendor = await device.vendor
            if not vendor:
                raise BusinessException(f"设备 {device.hostname} 缺少厂商信息")

            # 创建临时连接进行测试
            from scrapli import AsyncScrapli

            from app.core.network.connection_manager import DeviceCredentials

            credentials = DeviceCredentials(
                username=username,
                password=password,
                auth_type="manual",
                ssh_port=ssh_port,
            )

            # 确定Scrapli平台
            platform_mapping = {
                "h3c": "hp_comware",
                "huawei": "huawei_vrp",
                "cisco": "cisco_iosxe",
                "juniper": "juniper_junos",
                "arista": "arista_eos",
                "nokia": "nokia_sros",
            }

            platform = vendor.scrapli_platform or platform_mapping.get(vendor.vendor_code.lower(), "generic")

            # 创建Scrapli连接配置
            scrapli_config = {
                "host": device.ip_address,
                "auth_username": username,
                "auth_password": password,
                "auth_strict_key": False,
                "platform": platform,
                "port": ssh_port,
                "timeout_socket": vendor.connection_timeout,
                "timeout_transport": vendor.connection_timeout,
                "timeout_ops": vendor.command_timeout,
            }

            # 测试连接
            async with AsyncScrapli(**scrapli_config) as conn:
                response = await conn.send_command("display version")
                success = True
                error_message = None
                response_data = response.result if hasattr(response, "result") else str(response)

            execution_time = (datetime.now() - start_time).total_seconds()

            return AuthenticationTestResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=success,
                execution_time=execution_time,
                error_message=error_message,
                platform=platform,
                auth_type="manual",
                response_data=response_data,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"凭据验证失败: {e}")

            # 安全获取变量值
            device_hostname = "Unknown"
            device_ip = "Unknown"
            platform_name = None

            try:
                if "device" in locals() and locals().get("device"):
                    device_hostname = locals()["device"].hostname
                    device_ip = locals()["device"].ip_address
            except Exception:
                pass

            try:
                if "platform" in locals():
                    platform_name = locals().get("platform")
            except Exception:
                pass

            return AuthenticationTestResult(
                device_id=device_id,
                hostname=device_hostname,
                ip_address=device_ip,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
                platform=platform_name,
                auth_type="manual",
                response_data=None,
            )

    def get_test_statistics(self, results: list[AuthenticationTestResult]) -> dict[str, Any]:
        """获取测试统计信息"""
        if not results:
            return {
                "total_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "min_execution_time": 0.0,
                "max_execution_time": 0.0,
                "platform_stats": {},
                "auth_type_stats": {},
                "error_stats": {},
            }

        total_count = len(results)
        success_count = sum(1 for r in results if r.success)
        failed_count = total_count - success_count
        success_rate = (success_count / total_count) * 100

        execution_times = [r.execution_time for r in results]
        avg_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)

        # 平台统计
        platform_stats = {}
        for result in results:
            if result.platform:
                if result.platform not in platform_stats:
                    platform_stats[result.platform] = {"total": 0, "success": 0}
                platform_stats[result.platform]["total"] += 1
                if result.success:
                    platform_stats[result.platform]["success"] += 1

        # 认证类型统计
        auth_type_stats = {}
        for result in results:
            if result.auth_type:
                if result.auth_type not in auth_type_stats:
                    auth_type_stats[result.auth_type] = {"total": 0, "success": 0}
                auth_type_stats[result.auth_type]["total"] += 1
                if result.success:
                    auth_type_stats[result.auth_type]["success"] += 1

        # 错误统计
        error_stats = {}
        for result in results:
            if not result.success and result.error_message:
                error_type = result.error_message.split(":")[0] if ":" in result.error_message else result.error_message
                error_stats[error_type] = error_stats.get(error_type, 0) + 1

        return {
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 3),
            "min_execution_time": round(min_execution_time, 3),
            "max_execution_time": round(max_execution_time, 3),
            "platform_stats": platform_stats,
            "auth_type_stats": auth_type_stats,
            "error_stats": error_stats,
        }
