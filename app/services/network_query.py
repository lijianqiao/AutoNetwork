"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_query.py
@DateTime: 2025/07/23
@Docs: 网络查询服务层 - 使用操作上下文依赖注入
"""

import time
from typing import Any
from uuid import UUID, uuid4

from app.core.exceptions import BusinessException
from app.dao.device import DeviceDAO
from app.dao.query_history import QueryHistoryDAO
from app.dao.query_template import QueryTemplateDAO
from app.dao.vendor_command import VendorCommandDAO
from app.schemas.network_query import (
    AvailableQueryTemplate,
    CustomCommandQueryRequest,
    CustomCommandResult,
    InterfaceStatusQueryRequest,
    InterfaceStatusResult,
    MacQueryRequest,
    MacQueryResult,
    NetworkQueryByIPRequest,
    NetworkQueryRequest,
    NetworkQueryResponse,
    NetworkQueryResult,
    NetworkQueryTemplateListRequest,
    NetworkQueryTemplateListResponse,
)
from app.services.device_connection import DeviceConnectionService
from app.services.query_history import QueryHistoryService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import log_query_with_context


class NetworkQueryService:
    """网络查询服务"""

    def __init__(self):
        self.device_dao = DeviceDAO()
        self.query_template_dao = QueryTemplateDAO()
        self.vendor_command_dao = VendorCommandDAO()
        self.query_history_dao = QueryHistoryDAO()
        self.query_history_service = QueryHistoryService()
        self.connection_service = DeviceConnectionService()

    @log_query_with_context("network_query")
    async def execute_query(
        self, request: NetworkQueryRequest, operation_context: OperationContext
    ) -> NetworkQueryResponse:
        """执行网络查询"""
        start_time = time.time()
        query_id = str(uuid4())

        try:
            # 获取目标设备（包含vendor关系）
            devices = []
            for device_id in request.target_devices:
                device = await self.device_dao.get_with_related(device_id, select_related=["vendor"])
                if device:
                    devices.append(device)
            if not devices:
                raise BusinessException("没有找到指定的设备")

            results = []
            success_count = 0

            # 模拟查询执行（实际应该调用网络查询引擎）
            for device in devices:
                try:
                    # 这里应该调用实际的网络查询逻辑
                    result = await self._execute_device_query(device, request)
                    if result.success:
                        success_count += 1
                    results.append(result)
                except Exception as e:
                    logger.error(f"设备 {device.hostname} 查询失败: {e}")
                    results.append(
                        NetworkQueryResult(
                            device_id=device.id,
                            hostname=device.hostname,
                            ip_address=device.ip_address,
                            success=False,
                            error_message=str(e),
                            execution_time=0.0,
                        )
                    )

            total_execution_time = time.time() - start_time

            # 记录查询历史
            await self._save_query_history(
                operation_context.user.id,
                request.query_type,
                request.model_dump(),
                [device.ip_address for device in devices],
                total_execution_time,
                "success" if success_count > 0 else "failed",
            )

            return NetworkQueryResponse(
                query_id=query_id,
                total_count=len(devices),
                success_count=success_count,
                failed_count=len(devices) - success_count,
                results=results,
                total_execution_time=total_execution_time,
            )

        except Exception as e:
            total_execution_time = time.time() - start_time

            # 记录失败的查询历史
            await self._save_query_history(
                operation_context.user.id,
                request.query_type,
                request.model_dump(),
                [str(device_id) for device_id in request.target_devices],
                total_execution_time,
                "failed",
                str(e),
            )

            raise BusinessException(f"网络查询执行失败: {e}") from e

    @log_query_with_context("network_query")
    async def execute_query_by_ip(
        self, request: NetworkQueryByIPRequest, operation_context: OperationContext
    ) -> NetworkQueryResponse:
        """按IP地址执行网络查询"""
        start_time = time.time()
        query_id = str(uuid4())

        try:
            results = []
            success_count = 0

            # 模拟按IP查询（实际应该调用网络查询引擎）
            for ip_address in request.target_ips:
                try:
                    # 尝试从数据库查找设备（包含vendor关系）
                    device = await self.device_dao.get_by_ip_address(ip_address)
                    if device:
                        device = await self.device_dao.get_with_related(device.id, select_related=["vendor"])

                    result = NetworkQueryResult(
                        device_id=device.id if device else None,
                        hostname=device.hostname if device else "Unknown",
                        ip_address=ip_address,
                        success=True,  # 实际应该进行网络查询
                        result_data={"status": "reachable"},  # 模拟结果
                        execution_time=0.5,
                    )
                    success_count += 1
                    results.append(result)

                except Exception as e:
                    logger.error(f"IP {ip_address} 查询失败: {e}")
                    results.append(
                        NetworkQueryResult(
                            device_id=None,
                            hostname="Unknown",
                            ip_address=ip_address,
                            success=False,
                            error_message=str(e),
                            execution_time=0.0,
                        )
                    )

            total_execution_time = time.time() - start_time

            # 记录查询历史
            await self._save_query_history(
                operation_context.user.id,
                request.query_type,
                request.model_dump(),
                request.target_ips,
                total_execution_time,
                "success" if success_count > 0 else "failed",
            )

            return NetworkQueryResponse(
                query_id=query_id,
                total_count=len(request.target_ips),
                success_count=success_count,
                failed_count=len(request.target_ips) - success_count,
                results=results,
                total_execution_time=total_execution_time,
            )

        except Exception as e:
            total_execution_time = time.time() - start_time

            # 记录失败的查询历史
            await self._save_query_history(
                operation_context.user.id,
                request.query_type,
                request.model_dump(),
                request.target_ips,
                total_execution_time,
                "failed",
                str(e),
            )

            raise BusinessException(f"网络查询执行失败: {e}") from e

    @log_query_with_context("network_query")
    async def query_mac_address(
        self, request: MacQueryRequest, operation_context: OperationContext
    ) -> list[MacQueryResult]:
        """MAC地址查询"""
        devices = await self.device_dao.get_by_ids(request.target_devices)
        if not devices:
            raise BusinessException("没有找到指定的设备")

        results = []

        for device in devices:
            try:
                # 这里应该调用实际的MAC地址查询逻辑
                # 模拟MAC查询结果
                result = MacQueryResult(
                    device_id=device.id,
                    hostname=device.hostname,
                    ip_address=device.ip_address,
                    found=True,  # 模拟找到MAC
                    interface="GigabitEthernet0/1/1",
                    vlan="VLAN100",
                    port_type="access",
                    port_status="up",
                )
                results.append(result)

            except Exception as e:
                logger.error(f"设备 {device.hostname} MAC查询失败: {e}")
                results.append(
                    MacQueryResult(
                        device_id=device.id,
                        hostname=device.hostname,
                        ip_address=device.ip_address,
                        found=False,
                        error_message=str(e),
                    )
                )

        return results

    @log_query_with_context("network_query")
    async def query_interface_status(
        self, request: InterfaceStatusQueryRequest, operation_context: OperationContext
    ) -> list[InterfaceStatusResult]:
        """接口状态查询"""
        devices = await self.device_dao.get_by_ids(request.target_devices)
        if not devices:
            raise BusinessException("没有找到指定的设备")

        results = []

        for device in devices:
            try:
                # 这里应该调用实际的接口状态查询逻辑
                # 模拟接口状态查询结果
                from app.schemas.network_query import InterfaceStatus

                interfaces = [
                    InterfaceStatus(
                        interface="GigabitEthernet0/1/1",
                        status="up",
                        protocol="up",
                        description="To-Server-1",
                        speed="1000M",
                        duplex="full",
                    ),
                    InterfaceStatus(
                        interface="GigabitEthernet0/1/2",
                        status="down",
                        protocol="down",
                        description="",
                        speed="1000M",
                        duplex="auto",
                    ),
                ]

                result = InterfaceStatusResult(
                    device_id=device.id,
                    hostname=device.hostname,
                    ip_address=device.ip_address,
                    success=True,
                    interfaces=interfaces,
                )
                results.append(result)

            except Exception as e:
                logger.error(f"设备 {device.hostname} 接口状态查询失败: {e}")
                results.append(
                    InterfaceStatusResult(
                        device_id=device.id,
                        hostname=device.hostname,
                        ip_address=device.ip_address,
                        success=False,
                        interfaces=[],
                        error_message=str(e),
                    )
                )

        return results

    @log_query_with_context("network_query")
    async def execute_custom_commands(
        self, request: CustomCommandQueryRequest, operation_context: OperationContext
    ) -> list[CustomCommandResult]:
        """执行自定义命令"""
        devices = await self.device_dao.get_by_ids(request.target_devices)
        if not devices:
            raise BusinessException("没有找到指定的设备")

        results = []

        for device in devices:
            try:
                # 这里应该调用实际的命令执行逻辑
                # 模拟命令执行结果
                from app.schemas.network_query import CommandResult

                command_results = []
                for command in request.commands:
                    command_result = CommandResult(
                        command=command,
                        success=True,
                        output=f"模拟执行命令 '{command}' 的输出",  # 实际应该是真实输出
                        execution_time=0.3,
                    )
                    command_results.append(command_result)

                result = CustomCommandResult(
                    device_id=device.id,
                    hostname=device.hostname,
                    ip_address=device.ip_address,
                    success=True,
                    commands=command_results,
                    total_execution_time=sum(cmd.execution_time for cmd in command_results),
                )
                results.append(result)

            except Exception as e:
                logger.error(f"设备 {device.hostname} 自定义命令执行失败: {e}")
                results.append(
                    CustomCommandResult(
                        device_id=device.id,
                        hostname=device.hostname,
                        ip_address=device.ip_address,
                        success=False,
                        commands=[],
                        total_execution_time=0.0,
                        error_message=str(e),
                    )
                )

        return results

    @log_query_with_context("network_query")
    async def get_available_templates(
        self, request: NetworkQueryTemplateListRequest, operation_context: OperationContext
    ) -> NetworkQueryTemplateListResponse:
        """获取可用的查询模板列表"""
        try:
            # 获取活跃的查询模板
            filters = {"is_active": True, "is_deleted": False}
            if request.template_type:
                # 使用专门的搜索方法而不是直接添加到filters
                templates = await self.query_template_dao.search_templates(
                    template_type=request.template_type, is_active=True
                )
            else:
                templates = await self.query_template_dao.get_all(**filters)

            available_templates = []
            for template in templates:
                # 获取支持的厂商列表
                vendor_commands = await self.vendor_command_dao.get_by_template(template.id)
                supported_vendors = []

                for cmd in vendor_commands:
                    vendor = await cmd.vendor.load() if hasattr(cmd, "vendor") else None
                    if vendor:
                        supported_vendors.append(vendor.vendor_name)

                available_template = AvailableQueryTemplate(
                    template_id=template.id,
                    template_name=template.template_name,
                    template_type=template.template_type,
                    description=template.description,
                    supported_vendors=supported_vendors,
                    required_params=[],  # 实际应该从模板配置中获取
                )
                available_templates.append(available_template)

            return NetworkQueryTemplateListResponse(templates=available_templates)

        except Exception as e:
            logger.error(f"获取可用查询模板失败: {e}")
            raise BusinessException(f"获取可用查询模板失败: {e}") from e

    async def _execute_device_query(self, device: Any, request: NetworkQueryRequest) -> NetworkQueryResult:
        """执行单个设备的查询"""
        start_time = time.time()

        try:
            # 首先测试设备连接
            connection_test = await self.connection_service.test_device_connection(device.id)

            if not connection_test["success"]:
                return NetworkQueryResult(
                    device_id=device.id,
                    hostname=device.hostname,
                    ip_address=device.ip_address,
                    success=False,
                    error_message=f"设备连接失败: {connection_test.get('error_message', '未知错误')}",
                    execution_time=time.time() - start_time,
                )

            # 根据查询类型执行相应的命令
            result_data = await self._execute_query_commands(device, request)

            return NetworkQueryResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=True,
                result_data=result_data,
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"设备 {device.hostname} 查询执行失败: {e}")
            return NetworkQueryResult(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
            )

    async def _execute_query_commands(self, device: Any, request: NetworkQueryRequest) -> dict[str, Any]:
        """执行查询命令"""
        try:
            # 根据查询类型获取相应的命令模板
            templates = await self.query_template_dao.get_by_template_type(request.query_type)
            if not templates:
                raise BusinessException(f"未找到查询类型 {request.query_type} 的模板")
            template = templates[0]  # 使用第一个匹配的模板

            # 获取设备厂商对应的命令
            vendor_command = await self.vendor_command_dao.get_by_template_and_vendor(template.id, device.vendor_id)
            if not vendor_command:
                raise BusinessException(f"未找到厂商 {device.vendor.vendor_name} 的查询命令")

            # 执行命令
            commands = (
                vendor_command.commands if isinstance(vendor_command.commands, list) else [vendor_command.commands]
            )
            command_results = []

            for command in commands:
                try:
                    # 使用设备连接服务执行命令
                    response = await self.connection_service.execute_command(device.id, command)
                    command_results.append(
                        {
                            "command": command,
                            "success": response["success"],
                            "output": response.get("output", ""),
                            "elapsed_time": response.get("elapsed_time", 0.0),
                        }
                    )
                except Exception as cmd_error:
                    logger.error(f"命令 {command} 执行失败: {cmd_error}")
                    command_results.append(
                        {
                            "command": command,
                            "success": False,
                            "error": str(cmd_error),
                            "elapsed_time": 0.0,
                        }
                    )

            return {
                "query_type": request.query_type,
                "device_info": {
                    "hostname": device.hostname,
                    "vendor": device.vendor.vendor_name if hasattr(device, "vendor") and device.vendor else "Unknown",
                    "platform": device.platform if hasattr(device, "platform") else "Unknown",
                },
                "template_info": {
                    "template_name": template.template_name,
                    "template_type": template.template_type,
                },
                "command_results": command_results,
                "total_commands": len(commands),
                "successful_commands": sum(1 for result in command_results if result["success"]),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"执行查询命令失败: {e}")
            raise

    async def _save_query_history(
        self,
        user_id: UUID,
        query_type: str,
        query_params: dict[str, Any],
        target_devices: list[str],
        execution_time: float,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """保存查询历史"""
        try:
            # 实际记录历史，这里暂时只是日志记录
            # 如果需要完整的历史记录功能，需要传递operation_context
            logger.info(f"查询历史记录: 用户={user_id}, 类型={query_type}, 状态={status}")

        except Exception as e:
            logger.error(f"保存查询历史失败: {e}")
            # 不影响主要查询流程
